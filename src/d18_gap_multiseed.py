"""Defect D18 -- multi-seed historian-gap injection.

The released gap_injection.csv uses ONE random gap draw per level (N-19), so the
186.1 -> 58.0 h Hotelling T^2 "collapse" the manuscript states at 5% missing rows
may be a property of that draw rather than of the gap level.

This re-runs the sweep over several independent gap draws. The detector seed is
held fixed at DET_SEED so the only thing varying is the gap draw; N-19's
generator couples the two, which would confound the question being asked.

The gap=0 arm carries no draw, so it is evaluated once.

Writes results/tables/d18_gap_injection_multiseed.csv
"""
from __future__ import annotations

import argparse
import logging
import os

import pandas as pd

from src.benchmark import compute_run_onset
from src.d19_gap_injection import _eval_one, make_gap_transform
from src.datasets import default_runs
from src.robustness import DEFAULT_FAR_BUDGET, MECHANISM_METHODS

logger = logging.getLogger(__name__)

DET_SEED = 42
GAP_SEEDS = (101, 102, 103, 104, 105)
GAP_LEVELS = (0.05, 0.20)
OUT_PATH = os.path.join("results", "tables", "d18_gap_injection_multiseed.csv")


def sweep(datasets, gap_seeds=GAP_SEEDS, factor=1, mode="none",
          far_budget=DEFAULT_FAR_BUDGET):
    rows = []
    for ds in datasets:
        for run_name in default_runs(ds):
            onset = compute_run_onset(run_name, dataset=ds)
            # gap = 0: no draw, evaluate once
            for r in _eval_one(run_name, ds, factor, mode, MECHANISM_METHODS,
                               DET_SEED, onset, None, far_budget):
                rows.append({"dataset": ds, "run": run_name, "gap": 0.0,
                             "gap_seed": -1, **r})
            for gap in GAP_LEVELS:
                for gs in gap_seeds:
                    tf = make_gap_transform(gap, seed=gs)
                    for r in _eval_one(run_name, ds, factor, mode,
                                       MECHANISM_METHODS, DET_SEED, onset, tf,
                                       far_budget):
                        rows.append({"dataset": ds, "run": run_name, "gap": gap,
                                     "gap_seed": gs, **r})
            logger.info("[%s/%s] done", ds, run_name)
    return pd.DataFrame(rows)


def per_seed_table(df):
    """The manuscript's basis: mean lead over the runs whose alarm is valid."""
    v = df[df["valid"].astype(str) == "True"]
    return (v.groupby(["dataset", "short_name", "gap", "gap_seed"])["lead"]
             .mean().reset_index(name="mean_valid_lead"))


def summarise(df):
    t = per_seed_table(df)
    g = t[t.gap > 0].groupby(["dataset", "short_name", "gap"])["mean_valid_lead"]
    out = g.agg(seeds="count", mean="mean", lo="min", hi="max").reset_index()
    base = (t[t.gap == 0][["dataset", "short_name", "mean_valid_lead"]]
            .rename(columns={"mean_valid_lead": "gap0"}))
    return out.merge(base, on=["dataset", "short_name"], how="left")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", nargs="+", default=["IMS", "XJTU-SY"])
    ap.add_argument("--seeds", nargs="+", type=int, default=list(GAP_SEEDS))
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    df = sweep(args.datasets, gap_seeds=tuple(args.seeds))
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print("wrote %s rows=%d" % (OUT_PATH, len(df)))
    print(summarise(df).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
