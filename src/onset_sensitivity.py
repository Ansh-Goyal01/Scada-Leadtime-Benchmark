# src/onset_sensitivity.py
"""
Onset-sensitivity analysis — reviewer-facing robustness evidence for the
data-anchored degradation onset that anchors the lead-time metric.

The lead-time metric in src/lead_time.py is normalized against a single per-run
degradation onset (src/onset.py). A natural reviewer question is: *how much does
that onset — and therefore every onset-relative number — move when you change the
health indicator, the change-point method, or the excursion sensitivity (sigma_k)?*

This module sweeps that grid for every IMS run and reports, per run, the spread of
onset position (as % of the run) and the maximum achievable lead time. A tight
spread means the metric is insensitive to these analyst choices (good); a wide
spread flags a run whose onset — and any lead-time claim resting on it — is fragile.

It also surfaces the practical motivation for the richer health indicators: on
1st_test the mean-RMS HI only rises ~12 h before failure, so a richer HI that
responds to early kurtosis/spectral degradation should move the onset earlier and
give genuinely-early detectors a fairer chance.

CLI:
    python -m src.onset_sensitivity
writes results/tables/onset_sensitivity.csv and prints the stability summary.
"""

import os
import logging
import itertools
import numpy as np
import pandas as pd

from src import load_pipeline
from src.config import SPLIT, ONSET, PATHS, DATASET
from src.onset import health_indicator, detect_onset

logger = logging.getLogger(__name__)

# Default sweep grid. Kept modest so the sweep runs in seconds per run.
DEFAULT_KINDS   = ["rms_mean", "rms_max", "rms_kurt", "pca1"]
DEFAULT_METHODS = ["terminal", "sigma", "cusum"]
DEFAULT_SIGMA_KS = [3.0, 4.0, 5.0]


def onset_sensitivity(run_names=None,
                      kinds=None,
                      methods=None,
                      sigma_ks=None,
                      dataset="IMS") -> pd.DataFrame:
    """
    Sweep (health-indicator kind × detect_onset method × sigma_k) for each run of
    ``dataset`` and record where the onset lands.

    ``dataset`` is threaded into ``load_pipeline`` and selects the default run list
    (via ``datasets.default_runs``) when ``run_names`` is None, so the same stability
    analysis can be run on FEMTO and XJTU-SY whose bearings are far shorter than IMS
    (reviewer W8/Q12: the fixed-sample persistence/gap parameters are a larger
    fraction of a sub-2-hour run, so onset behaviour at short run length must be
    checked, not assumed).

    Returns a long DataFrame with one row per (run, kind, method, sigma_k):
        run, kind, method, sigma_k,
        onset            : the detected onset timestamp (or NaT),
        onset_pct        : onset position as % of the run span [0, 100],
        max_lead_hours   : (t_fail - onset) / 3600,
        run_span_hours   : total run span in hours (for context).
    """
    from src.datasets import default_runs
    run_names = run_names or default_runs(dataset)
    kinds     = kinds     or DEFAULT_KINDS
    methods   = methods   or DEFAULT_METHODS
    sigma_ks  = sigma_ks  or DEFAULT_SIGMA_KS

    rows = []
    for run in run_names:
        pipe = load_pipeline(run, dataset=dataset)
        df = pipe["df_full"]
        n = len(df)
        train_end = df.index[min(int(n * SPLIT["train_fraction"]), n - 1)]
        t_fail = pd.Timestamp(pipe["failure_time"])
        t_start = df.index[0]
        run_span_s = (t_fail - t_start).total_seconds()
        run_span_h = run_span_s / 3600.0 if run_span_s > 0 else float("nan")

        # Cache the HI per kind — it is independent of method / sigma_k.
        hi_cache = {}
        for kind in kinds:
            try:
                hi_cache[kind] = health_indicator(df, kind=kind)
            except Exception as e:
                logger.error("[%s] health_indicator kind=%s failed: %s", run, kind, e)
                hi_cache[kind] = None

        for kind, method, sigma_k in itertools.product(kinds, methods, sigma_ks):
            hi = hi_cache.get(kind)
            onset = None
            if hi is not None:
                try:
                    onset = detect_onset(
                        hi,
                        train_end=train_end,
                        t_fail=t_fail,
                        method=method,
                        baseline_fraction=ONSET.get("baseline_fraction", 0.2),
                        sigma_k=sigma_k,
                        cusum_k=ONSET.get("cusum_k", 0.5),
                        cusum_h=ONSET.get("cusum_h", 5.0),
                        persistence=ONSET.get("persistence", 5),
                        gap_tol=ONSET.get("gap_tol", 10),
                    )
                except Exception as e:
                    logger.error("[%s] detect_onset kind=%s method=%s sigma_k=%s failed: %s",
                                 run, kind, method, sigma_k, e)

            if onset is not None and run_span_s > 0:
                onset_pct = 100.0 * (onset - t_start).total_seconds() / run_span_s
                max_lead = (t_fail - onset).total_seconds() / 3600.0
            else:
                onset_pct = np.nan
                max_lead = np.nan

            rows.append({
                "run": run,
                "kind": kind,
                "method": method,
                "sigma_k": sigma_k,
                "onset": onset if onset is not None else pd.NaT,
                "onset_pct": onset_pct,
                "max_lead_hours": max_lead,
                "run_span_hours": run_span_h,
            })

    return pd.DataFrame(rows)


def summarize_onset_stability(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per run, the spread (min / median / max) of onset-% and max-lead across the whole
    grid — the robustness fingerprint of the onset for that run. ``n_grid`` is the
    number of grid cells, ``n_detected`` how many produced a finite onset.

    A small (max - min) onset-% spread means the onset, and every onset-relative
    metric, is insensitive to the analyst's HI/method/sigma_k choices.
    """
    out = []
    for run, sub in df.groupby("run"):
        opct = sub["onset_pct"].dropna()
        lead = sub["max_lead_hours"].dropna()
        out.append({
            "run": run,
            "n_grid": len(sub),
            "n_detected": int(opct.shape[0]),
            "onset_pct_min":    float(opct.min())    if len(opct) else np.nan,
            "onset_pct_median": float(opct.median()) if len(opct) else np.nan,
            "onset_pct_max":    float(opct.max())    if len(opct) else np.nan,
            "onset_pct_spread": float(opct.max() - opct.min()) if len(opct) else np.nan,
            "max_lead_min":     float(lead.min())    if len(lead) else np.nan,
            "max_lead_median":  float(lead.median()) if len(lead) else np.nan,
            "max_lead_max":     float(lead.max())    if len(lead) else np.nan,
        })
    return pd.DataFrame(out)


def _setup_logging():
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    import argparse
    _setup_logging()
    ap = argparse.ArgumentParser(description="Onset-sensitivity sweep.")
    ap.add_argument("--dataset", default="IMS",
                    help="IMS (default), XJTU-SY, or FEMTO")
    args = ap.parse_args()

    run_names = None if args.dataset != "IMS" else DATASET["runs"]
    df = onset_sensitivity(run_names=run_names, dataset=args.dataset)

    os.makedirs(PATHS["results_tables"], exist_ok=True)
    suffix = "" if args.dataset == "IMS" else f"_{args.dataset}"
    out = os.path.join(PATHS["results_tables"], f"onset_sensitivity{suffix}.csv")
    df.to_csv(out, index=False)
    logger.info("Saved onset-sensitivity grid → %s (%d rows)", out, len(df))

    summary = summarize_onset_stability(df)

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n=== Onset stability across (kind x method x sigma_k) grid ===")
    print(summary.to_string(index=False))

    # Per-kind median onset-% per run: shows which HI fires earliest / most stably.
    print("\n=== Median onset-% per (run, kind) — lower = earlier onset ===")
    pivot = (df.dropna(subset=["onset_pct"])
               .pivot_table(index="kind", columns="run",
                            values="onset_pct", aggfunc="median"))
    print(pivot.to_string())

    return df, summary


if __name__ == "__main__":
    main()
