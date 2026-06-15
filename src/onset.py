# src/onset.py
"""
Degradation-onset detection — the data-anchored replacement for the old, gameable
"first 5% of the test window" normal-period marker.

Why this exists
---------------
The previous lead-time metric (lead_time.compute_VLT) credited *any* alarm fired just
after an arbitrary positional 5% mark with near-maximal lead time, and only penalised
alarms inside that first 5%. A detector that simply latches "on" at the start of the
post-5% region therefore scored near-perfect lead time at 0% false-alarm rate — the
metric measured "how early the score crosses a percentile", not predictive skill.

The fix: define a single, detector-independent *degradation onset* per run from a
health indicator (the mean-RMS trend), using ONLY the training-baseline statistics so
no test information leaks in. All onset-relative metrics anchor to this point:
  * pre-onset region  = [run start, t_onset)   → the honest normal period for FAR
  * degradation window = [t_onset, t_fail)      → where a valid early warning can fire
  * max achievable lead = t_fail - t_onset

A constant-"on" detector now fires throughout the pre-onset region, so its first alarm
lands before t_onset → zero valid lead time and ~100% pre-onset FAR. Gameability gone.

The onset is a property of the *run*, computed once at full resolution, and reused
across every detector and every sampling factor (mirroring how sampling.py anchors the
lead-time denominator to factor=1).
"""

import numpy as np
import pandas as pd
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


def health_indicator(df: pd.DataFrame,
                     channels: Optional[List[str]] = None,
                     kind: str = "rms_mean") -> pd.Series:
    """
    Scalar degradation health indicator (HI) per timestamp.

    Operates on the SNAPSHOT-level DataFrame (clean ``rms_ch*`` columns), NOT the
    rolling "stats-of-stats" feature frame (whose column names are ambiguous).

    Parameters
    ----------
    df : snapshot-level DataFrame indexed by timestamp, with rms_ch0, rms_ch1, ...
    channels : explicit list of HI columns; defaults to all columns starting "rms_ch".
               (Only consulted for the rms-based kinds; the multi-feature kinds
               'rms_kurt' and 'pca1' build their own rms_*/kurt_* column sets.)
    kind : "rms_mean" (default) | "rms_max" | "rms_kurt" | "pca1"
        * "rms_mean" : mean of the rms_* channels (amplitude only).
        * "rms_max"  : max of the rms_* channels.
        * "rms_kurt" : z-score the mean-rms trend and the mean-kurtosis trend each
                       over an early baseline, then take their element-wise MAX, so
                       the HI rises on EITHER an amplitude (rms) OR an impulsiveness
                       (kurtosis) increase. Catches incipient defects that raise
                       kurtosis days before RMS climbs.
        * "pca1"     : first principal component of the standardized rms_*+kurt_*
                       columns, sign-oriented so that degradation increases it.

    Returns
    -------
    pd.Series indexed like ``df``.
    """
    if channels is None:
        channels = [c for c in df.columns if c.startswith("rms_ch")]
    if not channels:
        raise ValueError(
            "No rms_ch* columns found for the health indicator; pass channels= explicitly."
        )
    sub = df[channels]
    if kind == "rms_mean":
        return sub.mean(axis=1)
    if kind == "rms_max":
        return sub.max(axis=1)
    if kind == "rms_kurt":
        return _hi_rms_kurt(df, channels)
    if kind == "pca1":
        return _hi_pca1(df, channels)
    raise ValueError(f"Unknown health-indicator kind: {kind!r}")


def _baseline_z(series: pd.Series, baseline_fraction: float = 0.2) -> pd.Series:
    """Standardize ``series`` to z-scores using the mean/std of its early baseline."""
    n_base = max(5, int(len(series) * baseline_fraction))
    base = series.iloc[:n_base]
    mu = float(base.mean())
    sd = float(base.std())
    if not np.isfinite(sd) or sd < 1e-12:
        sd = float(series.std()) or 1.0
    return (series - mu) / sd


def _hi_rms_kurt(df: pd.DataFrame,
                 rms_channels: List[str],
                 baseline_fraction: float = 0.2) -> pd.Series:
    """
    Amplitude-OR-impulsiveness HI: max of the baseline-z mean-rms trend and the
    baseline-z mean-kurtosis trend. Responds to whichever degradation mode appears
    first, so it leads a pure-RMS HI when kurtosis rises early (incipient defects).
    """
    kurt_channels = [c for c in df.columns if c.startswith("kurt_ch")]
    rms_trend = df[rms_channels].mean(axis=1)
    z_rms = _baseline_z(rms_trend, baseline_fraction)
    if not kurt_channels:
        logger.warning("No kurt_ch* columns found; 'rms_kurt' HI falls back to rms-only z.")
        return z_rms
    kurt_trend = df[kurt_channels].mean(axis=1)
    z_kurt = _baseline_z(kurt_trend, baseline_fraction)
    combined = pd.concat([z_rms, z_kurt], axis=1).max(axis=1)
    combined.name = "rms_kurt_hi"
    return combined


def _hi_pca1(df: pd.DataFrame, rms_channels: List[str]) -> pd.Series:
    """
    First principal component of the standardized rms_*+kurt_* columns, sign-oriented
    so degradation increases it. PCA is fit on the whole series (acceptable for a
    descriptive HI — no detector is trained on it). The sign is fixed by correlating
    PC1 with the mean-rms trend (which monotonically increases toward failure).
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA

    kurt_channels = [c for c in df.columns if c.startswith("kurt_ch")]
    feat_cols = list(rms_channels) + list(kurt_channels)
    X = df[feat_cols].to_numpy(dtype=float)
    # guard against NaNs/Infs that would poison the fit
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    Xs = StandardScaler().fit_transform(X)
    pc1 = PCA(n_components=1, random_state=0).fit_transform(Xs).ravel()
    pc1 = pd.Series(pc1, index=df.index, name="pca1_hi")
    # sign-orient: degradation should make the HI increase. Use mean-rms as the
    # known-increasing reference; flip PC1 if it is anti-correlated with it.
    rms_trend = df[rms_channels].mean(axis=1).to_numpy(dtype=float)
    if np.corrcoef(pc1.to_numpy(), rms_trend)[0, 1] < 0:
        pc1 = -pc1
    return pc1


def detect_onset(hi: pd.Series,
                 train_end: Optional[pd.Timestamp] = None,
                 method: str = "terminal",
                 baseline_fraction: float = 0.2,
                 sigma_k: float = 4.0,
                 cusum_k: float = 0.5,
                 cusum_h: float = 5.0,
                 persistence: int = 5,
                 gap_tol: int = 10,
                 t_fail: Optional[pd.Timestamp] = None) -> Optional[pd.Timestamp]:
    """
    Detect the degradation-onset timestamp on a health-indicator series.

    The baseline (normal) mean/std are estimated ONLY on the early portion of the run
    (the first ``baseline_fraction``, or ``hi`` up to ``train_end`` if given), so the
    onset is leakage-free with respect to the degradation region.

    Methods
    -------
    "terminal" (default, recommended) : the start of the LAST sustained above-band
               excursion (band = baseline_mean + sigma_k·baseline_std) before failure.
               This is the start of the *terminal* degradation that leads to failure.
               It is robust to (a) early-life run-in transients — those form earlier,
               separate excursions that are ignored — and (b) the trailing machine-off
               sample at the end of a run (which drops below band and is excluded).
               Runs separated by gaps shorter than ``gap_tol`` samples are merged.
    "sigma"  : first point where standardized HI exceeds ``sigma_k`` for ``persistence``
               consecutive samples (forward debounced rule; fooled by run-in transients).
    "cusum"  : one-sided cumulative-sum change detector on standardized HI.
    "pelt"   : optional, uses the `ruptures` package if installed; falls back to terminal.

    Returns
    -------
    pd.Timestamp of the onset, or None if no change point is found.
    """
    hi = hi.dropna()
    if len(hi) < 10:
        logger.warning("Health indicator too short (%d) for onset detection.", len(hi))
        return None

    # --- baseline statistics (normal region only) ---
    if train_end is not None:
        base = hi[hi.index <= train_end]
        if len(base) < 5:
            base = hi.iloc[:max(5, int(len(hi) * baseline_fraction))]
    else:
        n_base = max(5, int(len(hi) * baseline_fraction))
        base = hi.iloc[:n_base]
    mu = float(base.mean())
    sd = float(base.std())
    if not np.isfinite(sd) or sd < 1e-12:
        sd = float(hi.std()) or 1.0  # degenerate baseline: fall back to global spread

    idx = hi.index

    if method == "pelt":
        onset = _detect_onset_pelt(hi, mu, sd)
        if onset is not None:
            return onset
        method = "terminal"  # fall through

    if method == "terminal":
        band = mu + sigma_k * sd
        # restrict to pre-failure region so the terminal excursion is well defined
        scan = hi[hi.index <= t_fail] if t_fail is not None else hi
        above = (scan.values > band)
        runs = _merged_runs(above, gap_tol=gap_tol, min_len=persistence)
        if not runs:
            return None
        start_i, _end_i = runs[-1]          # LAST sustained excursion → terminal degradation
        return scan.index[min(start_i, len(scan.index) - 1)]

    z = (hi.values - mu) / sd
    if method == "sigma":
        over = z > sigma_k
        run = 0
        for i, flag in enumerate(over):
            run = run + 1 if flag else 0
            if run >= persistence:
                return idx[i - persistence + 1]
        return None

    if method == "cusum":
        S = 0.0
        run_start = 0
        consec = 0
        for i, zi in enumerate(z):
            inc = zi - cusum_k
            if S + inc <= 0:
                S = 0.0
                run_start = i + 1
                consec = 0
            else:
                S += inc
                consec += 1
                if S > cusum_h and consec >= persistence:
                    return idx[min(run_start, len(idx) - 1)]
        return None

    raise ValueError(f"Unknown onset method: {method!r}")


def _merged_runs(mask: np.ndarray, gap_tol: int = 10, min_len: int = 5) -> list:
    """
    Given a boolean array, return [(start, end), ...] contiguous True-runs, merging runs
    separated by a False gap shorter than ``gap_tol``, and keeping only merged runs whose
    total span is at least ``min_len``. Used to find sustained excursions robustly.
    """
    n = len(mask)
    raw = []
    i = 0
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            raw.append([i, j - 1])
            i = j
        else:
            i += 1
    if not raw:
        return []
    # merge across short gaps
    merged = [raw[0]]
    for s, e in raw[1:]:
        if s - merged[-1][1] - 1 < gap_tol:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged if (e - s + 1) >= min_len]


def _detect_onset_pelt(hi: pd.Series, mu: float, sd: float) -> Optional[pd.Timestamp]:
    """PELT change-point on standardized HI (optional dependency `ruptures`)."""
    try:
        import ruptures as rpt
    except Exception:
        logger.info("`ruptures` not installed; falling back from PELT to CUSUM.")
        return None
    z = ((hi.values - mu) / sd).reshape(-1, 1)
    try:
        algo = rpt.Pelt(model="rbf").fit(z)
        bkps = algo.predict(pen=10)
        # first breakpoint after the baseline that moves to a higher level
        for b in bkps[:-1]:
            if hi.values[b:].mean() > hi.values[:b].mean():
                return hi.index[min(b, len(hi.index) - 1)]
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("PELT failed (%s); falling back to CUSUM.", e)
    return None


def onset_for_run(df_full: pd.DataFrame,
                  train_end: Optional[pd.Timestamp] = None,
                  t_fail: Optional[pd.Timestamp] = None,
                  channels: Optional[List[str]] = None,
                  cfg: Optional[dict] = None) -> Optional[pd.Timestamp]:
    """
    Convenience wrapper: snapshot DataFrame → health indicator → onset timestamp.

    ``cfg`` defaults to src.config.ONSET. ``train_end`` bounds the leakage-free baseline;
    ``t_fail`` bounds the terminal-excursion search so it locks onto the degradation that
    actually leads to failure (and ignores the trailing machine-off sample).
    """
    if cfg is None:
        from src.config import ONSET as cfg
    hi = health_indicator(df_full, channels=channels,
                          kind=cfg.get("health_indicator", "rms_mean"))
    onset = detect_onset(
        hi,
        train_end=train_end,
        t_fail=t_fail,
        method=cfg.get("method", "terminal"),
        baseline_fraction=cfg.get("baseline_fraction", 0.2),
        sigma_k=cfg.get("sigma_k", 4.0),
        cusum_k=cfg.get("cusum_k", 0.5),
        cusum_h=cfg.get("cusum_h", 5.0),
        persistence=cfg.get("persistence", 5),
        gap_tol=cfg.get("gap_tol", 10),
    )
    if onset is None:
        logger.warning("No degradation onset detected; downstream will fall back.")
    else:
        logger.info("Degradation onset detected at %s", onset)
    return onset
