# src/feature_coarsening_ablation.py
"""
Feature-group ablation crossed with the SCADA coarsening factor (paper Table XXII).

The feature-group ablation (src/ablation.py) is validated only at full resolution
(f=1). This script repeats it at every coarsening factor f in {1, 2, 5, 10, 20} to
test whether the ``rms_only`` recommendation is robust to the historian's logging
interval. It reuses exactly the paper's *controlled* feature-level coarsening
(src.sampling.downsample_features, aggregate/bin-mean mechanism) so that the only
thing that changes across f is the effective logging interval; window content and
alarm persistence are held constant.

Prediction under test: bin-averaging preserves the RMS statistic (the mean of a
bin-averaged signal's RMS tracks the RMS of the original), so the ``rms_only`` group
should be near-invariant to f, while spectral/envelope groups -- which depend on
fine temporal structure lost to aggregation -- should degrade at coarse f.

Metric: valid-alarm fraction (fraction of the 3 IMS runs with a valid alarm) per
(feature_group, factor, detector).

Entry point:
    python -m src.feature_coarsening_ablation
"""

from __future__ import annotations

import os
import logging
import argparse
from typing import List, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Groups reported in Table XXII. rms_only / time_only / spectral_only / all mirror
# src.ablation.GROUPS; we import the canonical definitions to avoid drift.
TABLE_GROUPS = ("rms_only", "time_only", "spectral_only", "all")
TABLE_METHODS = ("three_sigma", "ewma", "isolation_forest")
FACTORS = (1, 2, 5, 10, 20)


def coarsen_ablation_for_run(run_name: str,
                             dataset: str = "IMS",
                             methods: List[str] = None,
                             groups: List[str] = None,
                             factors: List[int] = None,
                             seed: int = 42) -> pd.DataFrame:
    """Feature-group x coarsening-factor ablation for one run.

    Full-resolution invariant features are extracted once; the FEATURE-ROW stream is
    then bin-averaged by each factor (the controlled 'aggregate' mechanism). For each
    (group, factor) the columns of the selected family are split/scaled/evaluated
    against the run's fixed leakage-free onset.
    """
    from src import load_pipeline
    from src.ablation import GROUPS, _select_columns
    from src.benchmark import make_detectors
    from src.lead_time import evaluate_all_methods
    from src.onset import onset_for_run
    from src.config import SPLIT, THRESHOLD

    methods = list(methods or TABLE_METHODS)
    groups = list(groups or TABLE_GROUPS)
    factors = list(factors or FACTORS)

    rows: List[Dict] = []
    for factor in factors:
        # factor=1 => 'none' reproduces src.ablation.ablation_for_run exactly (so
        # this table's f=1 column matches the published feature-group ablation);
        # factor>1 applies the SCADA 'aggregate' (bin-mean) coarsening. The scaling,
        # top-k selection, and onset are all recomputed by load_pipeline on the
        # coarsened grid, leakage-free, exactly as in the main sampling sweep.
        mode = "none" if factor == 1 else "aggregate"
        try:
            pipe = load_pipeline(run_name, dataset=dataset, use_spectral=True,
                                 downsample_factor=factor, downsample_mode=mode)
        except Exception:
            pipe = load_pipeline(run_name, dataset=dataset,
                                 downsample_factor=factor, downsample_mode=mode)

        feature_names = pipe["feature_names"]
        df = pipe["df_full"]
        n = len(df)
        train_end = df.index[min(int(n * pipe["train_fraction"]), n - 1)]
        t_fail = pd.Timestamp(pipe["failure_time"])
        onset = onset_for_run(df, train_end=train_end, t_fail=t_fail)

        for gname in groups:
            sel = _select_columns(feature_names, GROUPS[gname])
            if not sel:
                logger.warning("[%s f=%s] group '%s' selects 0 columns", run_name, factor, gname)
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
                    "dataset": dataset, "run": run_name, "factor": factor,
                    "group": gname, "n_features": len(sel),
                    "method": r["method"], "short_name": r["short_name"],
                    "lead_time_hours": r["lead_time_hours"],
                    "far_preonset_pct": r["far_preonset_pct"],
                    "valid_alarm": bool(r["valid_alarm"]),
                })
    return pd.DataFrame(rows)


def run_coarsening_ablation(dataset: str = "IMS",
                            runs: List[str] = None,
                            methods: List[str] = None,
                            groups: List[str] = None,
                            factors: List[int] = None,
                            seed: int = 42,
                            save: bool = True) -> pd.DataFrame:
    """Aggregate the coarsening ablation across runs -> valid-alarm fraction table."""
    from src.config import PATHS
    from src.datasets import default_runs

    runs = runs or default_runs(dataset)
    frames = []
    for r in runs:
        try:
            frames.append(coarsen_ablation_for_run(
                r, dataset=dataset, methods=methods, groups=groups,
                factors=factors, seed=seed))
        except Exception as e:  # noqa: BLE001 - keep other runs going, log the failure
            logger.error("[%s] coarsening ablation failed: %s", r, e)
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames, ignore_index=True)

    agg = (long.groupby(["dataset", "group", "factor", "method", "short_name"])
           .agg(valid_frac=("valid_alarm", "mean"),
                lead_time_hours_mean=("lead_time_hours", "mean"),
                far_preonset_pct_mean=("far_preonset_pct", "mean"),
                n_runs=("run", "nunique"))
           .reset_index())

    if save and not long.empty:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        long.to_csv(os.path.join(PATHS["results_tables"],
                    f"feature_coarsening_ablation_{dataset}_long.csv"), index=False)
        agg.to_csv(os.path.join(PATHS["results_tables"],
                   f"feature_coarsening_ablation_{dataset}.csv"), index=False)
    return agg


def _setup_logging() -> None:
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")


def main() -> None:
    _setup_logging()
    ap = argparse.ArgumentParser(description="Feature-group x coarsening-factor ablation")
    ap.add_argument("--dataset", default="IMS")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    agg = run_coarsening_ablation(dataset=args.dataset, seed=args.seed, save=True)
    if agg.empty:
        print("No results produced.")
        return
    pd.set_option("display.width", 220, "display.max_columns", 30)
    for m in TABLE_METHODS:
        sub = agg[agg.short_name == m]
        if sub.empty:
            continue
        piv = sub.pivot_table(index="group", columns="factor", values="valid_frac").round(2)
        piv = piv.reindex(list(TABLE_GROUPS))
        print(f"\n=== valid-alarm fraction vs coarsening factor — {m} ===")
        print(piv.to_string())


if __name__ == "__main__":
    main()
