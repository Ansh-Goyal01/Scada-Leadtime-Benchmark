# src/d19_gap_injection.py
"""
Defect N-19 -- historian-gap injection, re-run with the pre-onset FAR captured.

Table 6 (`tab:missing`) reports mean valid lead time under random historian gaps
of 0%, 5% and 20%, and its caption asserts that "Valid-alarm fractions (not shown)
are unchanged across gap levels". The released `results/tables/gap_injection.csv`
carries only `lead` and `valid` -- it has no `far_preonset_pct` column, so the
validity flags in it cannot be re-derived or audited against Eq. 5.

Worse, no generating script for that file exists anywhere in the tree (the same
orphaned-artifact defect as N-15). This module reconstructs the sweep and records
`far_preonset_pct` alongside, so the caption can be corrected against measured
numbers rather than asserted ones.

Verification protocol: the gap=0 arm must reproduce the published gap=0 lead times
in `gap_injection.csv`. If it does not, the reconstructed configuration is wrong
and the run is reported as unreconciled rather than used to edit the manuscript.

Writes `results/tables/gap_injection_far.csv`. Does NOT overwrite the released
`gap_injection.csv`.
"""
from __future__ import annotations

import argparse
import logging
import os
from typing import Callable, Optional

import numpy as np
import pandas as pd

from src import load_pipeline
from src.benchmark import compute_run_onset, make_detectors
from src.config import SPLIT, THRESHOLD
from src.lead_time import evaluate_all_methods
from src.robustness import (
    DEFAULT_FAR_BUDGET,
    MECHANISM_METHODS,
    _signal_columns,
)

logger = logging.getLogger(__name__)

GAP_LEVELS = (0.0, 0.05, 0.20)
OUT_PATH = os.path.join("results", "tables", "gap_injection_far.csv")
RELEASED = os.path.join("results", "tables", "gap_injection.csv")


def make_gap_transform(gap_frac: float, seed: int = 42) -> Optional[Callable]:
    """Set `gap_frac` of snapshot rows to NaN in the signal columns.

    The timestamp column is left intact, matching the manuscript's description:
    rows go missing, the time grid does not move.
    """
    if gap_frac <= 0:
        return None

    def _tf(df: pd.DataFrame) -> pd.DataFrame:
        cols = _signal_columns(df)
        if not cols:
            return df
        rng = np.random.default_rng(seed)
        out = df.copy()
        n = len(out)
        k = int(round(gap_frac * n))
        if k == 0:
            return out
        idx = rng.choice(n, size=k, replace=False)
        out.loc[out.index[idx], cols] = np.nan
        return out

    return _tf


def _eval_one(run_name: str, dataset: str, factor: int, mode: str,
              methods: list, seed: int, onset_info: dict,
              signal_transform: Optional[Callable],
              far_budget: float) -> list:
    """Evaluate one (run, gap) configuration. Mirrors robustness._eval_one but
    also returns far_preonset_pct, which is the whole point of this re-run."""
    dmode = "none" if factor == 1 else mode
    try:
        pipe = load_pipeline(run_name, dataset=dataset,
                             downsample_factor=factor, downsample_mode=dmode,
                             signal_transform=signal_transform)
    except Exception as e:
        logger.error("[%s] load failed factor=%d mode=%s: %s",
                     run_name, factor, dmode, e)
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
    return [{
        "method": r["method"], "short_name": r["short_name"],
        "lead": r["lead_time_hours"],
        "far_preonset_pct": r["far_preonset_pct"],
        "valid": r["valid_alarm"],
    } for r in results]


def run_gap_sweep(dataset: str = "IMS", runs: Optional[list] = None,
                  methods: Optional[list] = None, seed: int = 42,
                  factor: int = 1, mode: str = "none",
                  far_budget: float = DEFAULT_FAR_BUDGET) -> pd.DataFrame:
    """Lead time and pre-onset FAR vs historian gap fraction."""
    from src.datasets import default_runs
    runs = runs or default_runs(dataset)
    methods = methods or MECHANISM_METHODS

    rows = []
    for run_name in runs:
        onset = compute_run_onset(run_name, dataset=dataset)
        for gap in GAP_LEVELS:
            tf = make_gap_transform(gap, seed=seed)
            for r in _eval_one(run_name, dataset, factor, mode, methods,
                               seed, onset, tf, far_budget):
                rows.append({"dataset": dataset, "run": run_name, "gap": gap,
                             "factor": factor, "mode": mode, **r})
            logger.info("[%s/%s] gap=%.2f done", dataset, run_name, gap)
    return pd.DataFrame(rows)


def reconcile(new: pd.DataFrame, tol: float = 0.01) -> pd.DataFrame:
    """Compare the gap=0 arm against the released file. Returns the mismatches."""
    if not os.path.exists(RELEASED):
        logger.warning("released file missing; cannot reconcile")
        return pd.DataFrame()
    old = pd.read_csv(RELEASED)
    key = ["dataset", "run", "gap", "short_name"]
    m = new.merge(old[key + ["lead", "valid"]], on=key,
                  suffixes=("_new", "_old"), how="inner")
    m["dlead"] = (m.lead_new - m.lead_old).abs()
    return m[(m.dlead > tol) | (m.valid_new != m.valid_old)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", nargs="+", default=["IMS", "XJTU-SY"])
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--mode", default="none")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--far-budget", type=float, default=DEFAULT_FAR_BUDGET)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    frames = [run_gap_sweep(dataset=ds, seed=args.seed, factor=args.factor,
                            mode=args.mode, far_budget=args.far_budget)
              for ds in args.datasets]
    out = pd.concat(frames, ignore_index=True)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}  rows={len(out)}")

    bad = reconcile(out[out.gap == 0.0])
    if len(bad) == 0:
        print("RECONCILED: gap=0 arm matches the released gap_injection.csv")
    else:
        print(f"UNRECONCILED: {len(bad)} gap=0 cells differ from the released file")
        print(bad[["dataset", "run", "short_name", "lead_new", "lead_old",
                   "valid_new", "valid_old"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
