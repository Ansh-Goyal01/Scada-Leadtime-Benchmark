# src/robustness.py
"""
Noise / denoising mechanism test (Phase 2.5) — addresses reviewer W8/M5/M13/Q10.

The IMS controlled sweep shows a consistent positive *trend* for aggregate
(historian bin-averaging) over decimate. The post-hoc explanation is that
bin-averaging acts as a low-pass filter that suppresses single-window noise in
the health statistic. This module converts that explanation into a TESTED claim
by asking two questions on the IMS runs:

  1. NOISE INJECTION. Add Gaussian noise to the signal stream at three SNR levels
     (10 / 20 / 30 dB) and recompute lead time under aggregate vs decimate at each
     level. If the aggregate advantage *grows* as noise rises, that is direct
     evidence for the low-pass mechanism (averaging buys more when there is more
     noise to remove).

  2. DENOISING ALTERNATIVES. Apply generic denoisers — median filter,
     moving-average, a hand-rolled constant-velocity Kalman smoother, and (if
     ``pywt`` is installed) a wavelet soft-threshold — to the DECIMATED stream and
     re-evaluate lead time. If these generic smoothers match or exceed historian
     bin-averaging, the effect is "smoothing in general", not SCADA averaging
     specifically. We report whichever the data shows (honest either way).

Design notes
------------
* All transforms operate on the snapshot signal grid (``rms_ch*`` / ``kurt_ch*``
  columns) via the ``signal_transform`` hook added to ``load_pipeline`` — the same
  injection point where historian aggregation happens — so the comparison is fair.
* The degradation onset and the maximum achievable lead are anchored to the CLEAN,
  full-resolution run (``compute_run_onset``), exactly as the sampling sweep
  anchors its denominators to factor=1. Noise/denoising must not be allowed to move
  the onset, or the metric would measure the onset shift rather than detection skill.
* Noise is added in the data's own amplitude units, scaled per channel to hit the
  requested SNR; the RNG is seeded so the whole module is reproducible.
* Depends only on numpy / pandas / scipy (+ optional pywt); no torch needed.

Outputs (results/tables/):
    noise_snr_IMS.csv     lead time vs SNR, aggregate vs decimate, per detector/run
    denoising_IMS.csv     lead time per denoiser on the decimated stream, per detector/run
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import Callable, Optional

import numpy as np
import pandas as pd

from src import load_pipeline
from src.benchmark import compute_run_onset, make_detectors, _DETERMINISTIC
from src.config import (
    PATHS, EXPERIMENT, SPLIT, THRESHOLD, SAMPLING, FEATURES,
)
from src.lead_time import evaluate_all_methods

logger = logging.getLogger(__name__)

DEFAULT_FAR_BUDGET = 0.10
SNR_LEVELS_DB = (10.0, 20.0, 30.0)
# Coarsening factor at which the mechanism is probed. factor>1 is required so that
# "aggregate" and "decimate" actually differ; 5 is the mid sweep point.
MECHANISM_FACTOR = 5

# Methods that watch a smooth scalar health statistic — the ones the low-pass
# mechanism should act on. We exclude the deep sequence models here: this test is
# about the smoothing mechanism on the classic detectors, and the deep models are
# both data-starved and slow. Kept explicit so the scope is honest.
MECHANISM_METHODS = ["rms_trend", "three_sigma", "ewma", "cusum",
                     "hotelling_t2", "isolation_forest"]


# ───────────────────────────── signal transforms ───────────────────────────────

def _signal_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c.startswith("rms_ch") or c.startswith("kurt_ch")]


def make_noise_transform(snr_db: float, seed: int = 42) -> Callable:
    """Return a df->df transform adding Gaussian noise at the given SNR (dB).

    Noise power is set per channel from the channel's signal power so every channel
    hits the requested SNR: P_noise = P_signal / 10^(SNR/10).
    """
    rng = np.random.RandomState(seed)

    def _tf(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for c in _signal_columns(out):
            x = out[c].to_numpy(dtype=float)
            p_sig = float(np.mean(x ** 2))
            if not np.isfinite(p_sig) or p_sig <= 0:
                continue
            p_noise = p_sig / (10.0 ** (snr_db / 10.0))
            out[c] = x + rng.normal(0.0, np.sqrt(p_noise), size=x.shape)
        return out

    return _tf


def _kalman_cv_smooth(x: np.ndarray, q: float = 1e-3, r: float = 1.0) -> np.ndarray:
    """Hand-rolled 1-D constant-velocity Kalman smoother (forward filter).

    State = [position, velocity]; measures position. q is process-noise scale, r is
    measurement-noise variance. No external dependency. Returns the filtered
    position estimate, same length as x.
    """
    n = len(x)
    if n == 0:
        return x
    # state transition (dt=1) and measurement model
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    H = np.array([[1.0, 0.0]])
    Q = q * np.array([[0.25, 0.5], [0.5, 1.0]])
    R = np.array([[r]])
    xs = np.zeros((n, 2))
    P = np.eye(2)
    state = np.array([x[0], 0.0])
    for t in range(n):
        # predict
        state = F @ state
        P = F @ P @ F.T + Q
        # update
        y = x[t] - (H @ state)[0]
        S = (H @ P @ H.T + R)[0, 0]
        K = (P @ H.T / S).ravel()
        state = state + K * y
        P = (np.eye(2) - np.outer(K, H)) @ P
        xs[t] = state
    return xs[:, 0]


def _wavelet_denoise(x: np.ndarray, wavelet: str = "db4", level: int = 2) -> Optional[np.ndarray]:
    """Wavelet soft-threshold denoise via pywt. Returns None if pywt is unavailable."""
    try:
        import pywt
    except ImportError:
        return None
    x = np.array(x, dtype=float, copy=True)   # pywt needs a writable, contiguous buffer
    n = len(x)
    coeffs = pywt.wavedec(x, wavelet, level=level)
    # universal threshold from the finest detail coefficients (Donoho)
    sigma = np.median(np.abs(coeffs[-1])) / 0.6745 if len(coeffs[-1]) else 0.0
    thr = sigma * np.sqrt(2.0 * np.log(max(n, 2)))
    coeffs = [coeffs[0]] + [pywt.threshold(c, thr, mode="soft") for c in coeffs[1:]]
    rec = pywt.waverec(coeffs, wavelet)
    return rec[:n]


def make_denoise_transform(kind: str, window: int = 5) -> Optional[Callable]:
    """Return a df->df denoiser transform, or None if the denoiser is unavailable.

    kind: 'median' | 'moving_average' | 'kalman' | 'wavelet'.
    """
    def _apply(df: pd.DataFrame, fn) -> pd.DataFrame:
        out = df.copy()
        for c in _signal_columns(out):
            out[c] = fn(out[c].to_numpy(dtype=float))
        return out

    if kind == "median":
        from scipy.signal import medfilt

        def med(x):
            n = len(x)
            if n < 3:
                return x
            k = window if window % 2 == 1 else window + 1   # medfilt needs odd kernel
            if k >= n:                                       # kernel must be <= length
                k = n if n % 2 == 1 else n - 1
            return medfilt(x, kernel_size=k)
        return lambda df: _apply(df, med)
    if kind == "moving_average":
        def ma(x):
            if len(x) < 2:
                return x
            return pd.Series(x).rolling(window, min_periods=1, center=True).mean().to_numpy()
        return lambda df: _apply(df, ma)
    if kind == "kalman":
        return lambda df: _apply(df, _kalman_cv_smooth)
    if kind == "wavelet":
        if _wavelet_denoise(np.arange(16.0)) is None:
            logger.warning("pywt not installed — skipping wavelet denoiser.")
            return None
        return lambda df: _apply(df, _wavelet_denoise)
    raise ValueError(f"Unknown denoiser kind: {kind!r}")


# ───────────────────────────── evaluation core ─────────────────────────────────

def _eval_one(run_name: str, dataset: str, factor: int, mode: str,
              methods: list, seed: int, onset_info: dict,
              signal_transform: Optional[Callable],
              far_budget: float) -> list:
    """Load one (run, factor, mode[, transform]) configuration and evaluate methods.

    Returns a list of per-method result dicts (lead_time_hours, far_preonset_pct,
    valid_alarm). Onset/max-lead come from the clean full-resolution run.
    """
    dmode = "none" if factor == 1 else mode
    try:
        pipe = load_pipeline(run_name, dataset=dataset,
                             downsample_factor=factor, downsample_mode=dmode,
                             signal_transform=signal_transform)
    except Exception as e:
        logger.error("[%s] load failed factor=%d mode=%s: %s", run_name, factor, dmode, e)
        return []

    dets = make_detectors(methods, seed)
    _, results = evaluate_all_methods(
        detectors=dets,
        X_train=pipe["X_train"], X_test=pipe["X_test"],
        timestamps_test=pipe["ts_test"], failure_time=pipe["failure_time"],
        normal_period_fraction=SPLIT["normal_period_fraction"],
        threshold_strategy=THRESHOLD["strategy"],
        threshold_percentile=THRESHOLD["percentile"],
        alarm_persistence=THRESHOLD["alarm_persistence"],
        t_onset=onset_info["t_onset"], far_budget=far_budget,
        X_cal=pipe.get("X_cal"),
    )
    out = []
    for r in results:
        out.append({
            "method": r["method"], "short_name": r["short_name"],
            "lead_time_hours": r["lead_time_hours"],
            "far_preonset_pct": r["far_preonset_pct"],
            "valid_alarm": r["valid_alarm"],
        })
    return out


# ─────────────────────────────── experiments ───────────────────────────────────

def run_noise_sweep(dataset: str = "IMS", runs: Optional[list] = None,
                    methods: Optional[list] = None, seed: int = 42,
                    factor: int = MECHANISM_FACTOR,
                    far_budget: float = DEFAULT_FAR_BUDGET) -> pd.DataFrame:
    """Lead time vs SNR for aggregate vs decimate. Includes a clean (no-noise)
    reference row (snr_db = inf)."""
    from src.datasets import default_runs
    runs = runs or default_runs(dataset)
    methods = methods or MECHANISM_METHODS

    rows = []
    for run_name in runs:
        onset = compute_run_onset(run_name, dataset=dataset)
        for snr in (np.inf,) + tuple(SNR_LEVELS_DB):
            tf = None if not np.isfinite(snr) else make_noise_transform(snr, seed=seed)
            for mode in ("aggregate", "decimate"):
                res = _eval_one(run_name, dataset, factor, mode, methods, seed,
                                onset, tf, far_budget)
                for r in res:
                    rows.append({
                        "dataset": dataset, "run": run_name,
                        "snr_db": snr, "mode": mode, "factor": factor,
                        **{k: r[k] for k in ("method", "short_name",
                                             "lead_time_hours", "far_preonset_pct",
                                             "valid_alarm")},
                    })
            logger.info("[%s] noise sweep snr=%s done", run_name, snr)
    return pd.DataFrame(rows)


def run_denoising_comparison(dataset: str = "IMS", runs: Optional[list] = None,
                             methods: Optional[list] = None, seed: int = 42,
                             factor: int = MECHANISM_FACTOR,
                             far_budget: float = DEFAULT_FAR_BUDGET) -> pd.DataFrame:
    """Lead time per denoiser applied to the DECIMATED stream, vs historian
    bin-averaging (aggregate) and raw decimation as references."""
    from src.datasets import default_runs
    runs = runs or default_runs(dataset)
    methods = methods or MECHANISM_METHODS

    # Each entry: (label, mode, transform). aggregate = historian averaging
    # reference; decimate = raw reference; the rest are denoisers ON the decimated
    # grid (so the comparison isolates "smoothing the decimated stream").
    configs = [("aggregate", "aggregate", None),
               ("decimate", "decimate", None)]
    for kind in ("median", "moving_average", "kalman", "wavelet"):
        tf = make_denoise_transform(kind)
        if tf is not None:
            configs.append((kind, "decimate", tf))

    rows = []
    for run_name in runs:
        onset = compute_run_onset(run_name, dataset=dataset)
        for label, mode, tf in configs:
            res = _eval_one(run_name, dataset, factor, mode, methods, seed,
                            onset, tf, far_budget)
            for r in res:
                rows.append({
                    "dataset": dataset, "run": run_name,
                    "denoiser": label, "mode": mode, "factor": factor,
                    **{k: r[k] for k in ("method", "short_name",
                                         "lead_time_hours", "far_preonset_pct",
                                         "valid_alarm")},
                })
        logger.info("[%s] denoising comparison done", run_name)
    return pd.DataFrame(rows)


# ───────────────────────────────── CLI ─────────────────────────────────────────

def main(argv=None) -> int:
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    ap = argparse.ArgumentParser(description="Noise/denoising mechanism test (Phase 2.5).")
    ap.add_argument("--dataset", default="IMS")
    ap.add_argument("--factor", type=int, default=MECHANISM_FACTOR)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--far-budget", type=float, default=DEFAULT_FAR_BUDGET)
    ap.add_argument("--skip-noise", action="store_true")
    ap.add_argument("--skip-denoise", action="store_true")
    args = ap.parse_args(argv)

    os.makedirs(PATHS["results_tables"], exist_ok=True)

    if not args.skip_noise:
        noise = run_noise_sweep(dataset=args.dataset, factor=args.factor,
                                seed=args.seed, far_budget=args.far_budget)
        out = os.path.join(PATHS["results_tables"], f"noise_snr_{args.dataset}.csv")
        noise.to_csv(out, index=False)
        logger.info("wrote %s (%d rows)", out, len(noise))
        rl = noise_runlevel(noise)
        if not rl.empty:
            rlout = os.path.join(PATHS["results_tables"],
                                 f"noise_snr_{args.dataset}_runlevel.csv")
            rl.to_csv(rlout, index=False)
            logger.info("wrote %s (%d rows)", rlout, len(rl))
        _summarize_noise(noise)

    if not args.skip_denoise:
        deno = run_denoising_comparison(dataset=args.dataset, factor=args.factor,
                                        seed=args.seed, far_budget=args.far_budget)
        out = os.path.join(PATHS["results_tables"], f"denoising_{args.dataset}.csv")
        deno.to_csv(out, index=False)
        logger.info("wrote %s (%d rows)", out, len(deno))
        _summarize_denoise(deno)

    return 0


# Magnitude-monitoring charts the low-pass mechanism should act on. The run-level
# collapse (below) is computed over these, matching the main analysis's choice of
# unit of inference (the run, not the within-run detector).
_NOISE_MAGNITUDE_METHODS = ("three_sigma", "ewma", "cusum", "hotelling_t2")


def noise_runlevel(df: pd.DataFrame,
                   methods=_NOISE_MAGNITUDE_METHODS) -> pd.DataFrame:
    """Collapse the noise sweep to the honest unit of inference: the RUN.

    Reviewer W2/Q1: reporting ``n=12`` (four magnitude charts x three runs) per SNR
    treats the four charts on the same three runs as independent observations --- the
    same pseudoreplication the main aggregate-vs-decimate analysis was corrected for.
    Here we collapse the four magnitude charts to one mean (aggregate - decimate)
    difference per run, leaving ``n = n_runs`` (3 on IMS) per SNR level. The trend is
    then reported as DIRECTIONAL; at n=3 it cannot be significance-tested (the exact
    sign test floors at p=0.25), exactly as in the main sweep.

    Returns one row per (snr_db) with the per-run diffs, their mean, and n_pos/n_runs.
    """
    if df.empty:
        return pd.DataFrame()
    d = df[df["short_name"].isin(methods)] if "short_name" in df.columns else df
    # per (run, snr) mean lead under each mode, over the magnitude charts
    piv = d.pivot_table(index=["run", "snr_db"], columns="mode",
                        values="lead_time_hours", aggfunc="mean").reset_index()
    if not {"aggregate", "decimate"}.issubset(piv.columns):
        return pd.DataFrame()
    piv["diff"] = piv["aggregate"] - piv["decimate"]
    rows = []
    for snr, g in piv.groupby("snr_db"):
        diffs = g.sort_values("run")["diff"].tolist()
        n = len(diffs)
        n_pos = int(sum(v > 0 for v in diffs))
        rows.append({
            "snr_db": snr, "n_runs": n,
            "run_diffs": ", ".join(f"{v:+.2f}" for v in diffs),
            "mean_diff": float(np.mean(diffs)) if diffs else float("nan"),
            "n_pos": n_pos, "n_neg": n - n_pos,
            "all_same_sign": (n_pos == n or n_pos == 0) and n > 0,
        })
    out = pd.DataFrame(rows)
    # order finest-noise last: inf, 30, 20, 10
    order = {np.inf: 0, 30.0: 1, 20.0: 2, 10.0: 3}
    out = out.sort_values("snr_db", key=lambda s: s.map(lambda v: order.get(v, 99)))
    return out.reset_index(drop=True)


def _summarize_noise(df: pd.DataFrame) -> None:
    if df.empty:
        return
    # aggregate-minus-decimate lead time, averaged over runs+methods, per SNR
    piv = df.pivot_table(index=["snr_db"], columns="mode",
                         values="lead_time_hours", aggfunc="mean")
    if {"aggregate", "decimate"}.issubset(piv.columns):
        piv["agg_minus_dec"] = piv["aggregate"] - piv["decimate"]
        print("\n=== Noise sweep: mean lead time (h) by SNR (pooled, for reference) ===")
        print(piv.to_string())
    rl = noise_runlevel(df)
    if not rl.empty:
        print("\n=== Noise sweep: RUN-LEVEL collapse (unit of inference = run) ===")
        print(rl.to_string(index=False))


def _summarize_denoise(df: pd.DataFrame) -> None:
    if df.empty:
        return
    s = df.groupby("denoiser")["lead_time_hours"].mean().sort_values(ascending=False)
    print("\n=== Denoiser comparison: mean lead time (h), averaged over runs+methods ===")
    print(s.to_string())


if __name__ == "__main__":
    raise SystemExit(main())
