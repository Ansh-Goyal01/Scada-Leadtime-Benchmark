# src/ablation.py
"""
Feature-group ablation on the channel-invariant feature space (Phase D11, action #10).

Question: which feature families carry the prognostic signal, and do spectral/envelope
features add anything over time-domain statistics? We hold the pipeline fixed and only
restrict the feature columns fed to each detector, by NAME-PREFIX family:

  time-domain : rms, kurt, crest, skew, p2p, var   (the invariant time stats)
  spectral    : band_*, sk_*                        (FFT band energies, spectral kurtosis)
  envelope    : env_*                               (Hilbert envelope defect-band amplitudes)
  rms_only / kurt_only : single-family probes
  time_only   : time-domain only (no spectral/envelope)
  all         : everything (time + spectral + envelope)

Because the invariant schema already gives a fixed low-dim space, sub-selecting columns
is leakage-free and dimension-comparable across runs. Each (group × method) is evaluated
with the onset-relative metrics and averaged across runs.

Entry point:
    python -m src.ablation --dataset IMS
"""

import os
import re
import logging
import argparse
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# family → prefixes that identify its columns in the invariant feature names
FAMILY_PREFIXES = {
    "rms":   ["rms"],
    "kurt":  ["kurt"],
    "crest": ["crest"],
    "skew":  ["skew"],
    "p2p":   ["p2p"],
    "var":   ["var"],
    "band":  ["band_"],
    "sk":    ["sk_"],
    "env":   ["env_"],
}

TIME_FAMILIES = ["rms", "kurt", "crest", "skew", "p2p", "var"]
SPECTRAL_FAMILIES = ["band", "sk"]
ENVELOPE_FAMILIES = ["env"]

# ablation groups expressed as sets of families
GROUPS = {
    "rms_only":      ["rms"],
    "kurt_only":     ["kurt"],
    "time_only":     TIME_FAMILIES,
    "spectral_only": SPECTRAL_FAMILIES + ENVELOPE_FAMILIES,
    "envelope_only": ENVELOPE_FAMILIES,
    "time+spectral": TIME_FAMILIES + SPECTRAL_FAMILIES + ENVELOPE_FAMILIES,
    "all":           None,   # None = keep every column
}


def _family_of(name: str) -> str:
    """Map a feature column to its family key (or '' if unknown)."""
    for fam, prefixes in FAMILY_PREFIXES.items():
        for pre in prefixes:
            if name.startswith(pre):
                return fam
    return ""


def _select_columns(feature_names: list, families) -> list:
    """Indices of columns whose family is in ``families`` (None = all)."""
    if families is None:
        return list(range(len(feature_names)))
    fam_set = set(families)
    return [i for i, n in enumerate(feature_names) if _family_of(n) in fam_set]


def ablation_for_run(run_name: str,
                     dataset: str = "IMS",
                     methods: list = None,
                     groups: dict = None,
                     use_spectral: bool = True,
                     seed: int = 42) -> pd.DataFrame:
    """Evaluate every feature group × method on one run with onset-relative metrics."""
    from src import load_pipeline
    from src.benchmark import make_detectors
    from src.lead_time import evaluate_all_methods
    from src.onset import onset_for_run
    from src.config import SPLIT, THRESHOLD, EXPERIMENT

    methods = methods or [m for m in EXPERIMENT["methods_to_run"]
                          if m not in ("conformal_if",)]
    groups = groups or GROUPS

    # spectral only available for raw-waveform datasets (IMS); fall back gracefully
    try:
        pipe = load_pipeline(run_name, dataset=dataset, use_spectral=use_spectral)
    except Exception:
        pipe = load_pipeline(run_name, dataset=dataset, use_spectral=False)

    feature_names = pipe["feature_names"]
    df = pipe["df_full"]
    n = len(df)
    train_end = df.index[min(int(n * pipe["train_fraction"]), n - 1)]
    t_fail = pd.Timestamp(pipe["failure_time"])
    onset = onset_for_run(df, train_end=train_end, t_fail=t_fail)

    rows = []
    for gname, families in groups.items():
        sel = _select_columns(feature_names, families)
        if len(sel) == 0:
            logger.warning("[%s] group '%s' selects 0 columns — skipping", run_name, gname)
            continue
        Xtr, Xte = pipe["X_train"][:, sel], pipe["X_test"][:, sel]
        Xcal = pipe["X_cal"][:, sel] if pipe.get("X_cal") is not None else None

        dets = make_detectors(methods, seed)
        _, results = evaluate_all_methods(
            detectors=dets, X_train=Xtr, X_test=Xte,
            timestamps_test=pipe["ts_test"], failure_time=pipe["failure_time"],
            normal_period_fraction=SPLIT["normal_period_fraction"],
            threshold_strategy=THRESHOLD["strategy"],
            threshold_percentile=THRESHOLD["percentile"],
            alarm_persistence=THRESHOLD["alarm_persistence"],
            t_onset=onset, far_budget=0.10, X_cal=Xcal,
        )
        for r in results:
            rows.append({
                "dataset": dataset, "run": run_name, "group": gname,
                "n_features": len(sel), "method": r["method"],
                "short_name": r["short_name"],
                "lead_time_hours": r["lead_time_hours"],
                "far_preonset_pct": r["far_preonset_pct"],
                "valid_alarm": r["valid_alarm"],
            })
    return pd.DataFrame(rows)


def run_ablation(dataset: str = "IMS",
                 runs: list = None,
                 methods: list = None,
                 use_spectral: bool = True,
                 seed: int = 42,
                 save: bool = True) -> pd.DataFrame:
    """Aggregate feature-group ablation across runs. Saves long + aggregate tables."""
    from src.config import PATHS, EXPERIMENT

    if runs is None:
        runs = ["LPC"] if dataset == "ONGC" else EXPERIMENT["runs_to_evaluate"]

    frames = []
    for r in runs:
        try:
            frames.append(ablation_for_run(r, dataset=dataset, methods=methods,
                                           use_spectral=use_spectral, seed=seed))
        except Exception as e:
            logger.error("[%s] ablation failed: %s", r, e)
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames, ignore_index=True)

    agg = (long.groupby(["dataset", "group", "method", "short_name"])
           .agg(lead_time_hours_mean=("lead_time_hours", "mean"),
                lead_time_hours_std=("lead_time_hours", "std"),
                far_preonset_pct_mean=("far_preonset_pct", "mean"),
                valid_frac=("valid_alarm", "mean"),
                n_features=("n_features", "max"),
                n_runs=("run", "nunique"))
           .reset_index())

    if save and not long.empty:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        long.to_csv(os.path.join(PATHS["results_tables"],
                                 f"ablation_features_{dataset}_long.csv"), index=False)
        agg.to_csv(os.path.join(PATHS["results_tables"],
                                f"ablation_features_{dataset}.csv"), index=False)
    return agg


def _setup_logging():
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    _setup_logging()
    ap = argparse.ArgumentParser(description="Feature-group ablation (invariant schema)")
    ap.add_argument("--dataset", default="IMS")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-spectral", action="store_true")
    args = ap.parse_args()

    agg = run_ablation(dataset=args.dataset, use_spectral=not args.no_spectral,
                       seed=args.seed, save=True)
    if agg.empty:
        print("No ablation results produced.")
        return
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print("\n=== Feature-group ablation: mean lead time (h) across runs ===")
    piv = agg.pivot_table(index="group", columns="method",
                          values="lead_time_hours_mean").round(1)
    print(piv.to_string())
    print("\n=== valid-alarm fraction across runs ===")
    pivv = agg.pivot_table(index="group", columns="method",
                           values="valid_frac").round(2)
    print(pivv.to_string())


if __name__ == "__main__":
    main()
