# src/training_sweep.py
"""
Deep-model training-data-requirement sweep on FEMTO/PRONOSTIA (paper Table XXI, Fig 8).

Practitioner question: how much normal run-in history must be collected before a deep
reconstruction model matches an SPC chart? We answer it on FEMTO, the only dataset
where all six bearings are long enough for every detector (including the seq-len-30
deep models) to run on the full n=6.

We sweep the TRAINING fraction T in {0.20, 0.30, 0.40, 0.50, 0.60} with the
calibration fraction fixed at 0.10 (so test = 1 - T - 0.10). Every other
hyperparameter is the fixed Table XVII protocol -- no per-T retuning. Because
load_pipeline reads src.config.SPLIT at call time, we sweep T by temporarily
mutating that shared dict, which reuses the pipeline's exact scaling, top-k
selection, invariant features, and onset machinery unchanged.

For a run with fewer training feature-windows than the sequence length, a deep
sequence model cannot form a sequence; evaluate_all_methods records that cell as an
explicit N/A (valid_alarm is False and lead is NaN), which we count separately from a
genuine miss.

Metric: valid-alarm fraction over the six FEMTO bearings, per (detector, T), plus the
N/A count and the mean lead over valid alarms.

Entry point:
    python -m src.training_sweep
"""

from __future__ import annotations

import os
import logging
import argparse
from typing import List, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TRAIN_FRACTIONS = (0.20, 0.30, 0.40, 0.50, 0.60)
CAL_FRACTION = 0.10


def _is_na(result: dict) -> bool:
    """A deep sequence model that could not form a length-seq_len sequence reports a
    non-finite lead with no alarm time; treat that as N/A rather than a miss."""
    lead = result.get("lead_time_hours", np.nan)
    fat = result.get("FAT", None)
    return (fat is None or (isinstance(fat, float) and np.isnan(fat))) and not np.isfinite(lead)


def sweep_bearing(bearing: str,
                  dataset: str = "FEMTO",
                  methods: List[str] = None,
                  fractions: List[float] = None,
                  seed: int = 42) -> pd.DataFrame:
    """Train-fraction sweep for one bearing over all detectors."""
    from src import load_pipeline
    from src.benchmark import make_detectors
    from src.lead_time import evaluate_all_methods
    from src.onset import onset_for_run
    from src.config import SPLIT, THRESHOLD, EXPERIMENT

    methods = list(methods or EXPERIMENT["methods_to_run"])
    fractions = list(fractions or TRAIN_FRACTIONS)

    saved = dict(SPLIT)  # restore after the sweep so we do not leak state
    rows: List[Dict] = []
    try:
        for T in fractions:
            SPLIT["train_fraction"] = T
            SPLIT["calibration_fraction"] = CAL_FRACTION
            SPLIT["test_fraction"] = round(1.0 - T - CAL_FRACTION, 4)

            pipe = load_pipeline(bearing, dataset=dataset)
            df = pipe["df_full"]
            n = len(df)
            train_end = df.index[min(int(n * T), n - 1)]
            t_fail = pd.Timestamp(pipe["failure_time"])
            onset = onset_for_run(df, train_end=train_end, t_fail=t_fail)

            dets = make_detectors(methods, seed)
            _, results = evaluate_all_methods(
                detectors=dets, X_train=pipe["X_train"], X_test=pipe["X_test"],
                timestamps_test=pipe["ts_test"], failure_time=pipe["failure_time"],
                normal_period_fraction=SPLIT["normal_period_fraction"],
                threshold_strategy=THRESHOLD["strategy"],
                threshold_percentile=THRESHOLD["percentile"],
                alarm_persistence=THRESHOLD["alarm_persistence"],
                t_onset=onset, far_budget=0.10, X_cal=pipe.get("X_cal"),
            )
            for r in results:
                na = _is_na(r)
                rows.append({
                    "dataset": dataset, "bearing": bearing, "train_fraction": T,
                    "method": r["method"], "short_name": r["short_name"],
                    "n_train_windows": len(pipe["ts_train"]),
                    "lead_time_hours": (np.nan if na else r["lead_time_hours"]),
                    "far_preonset_pct": r["far_preonset_pct"],
                    "valid_alarm": (False if na else bool(r["valid_alarm"])),
                    "na": na,
                })
    finally:
        SPLIT.update(saved)
    return pd.DataFrame(rows)


def run_training_sweep(dataset: str = "FEMTO",
                       bearings: List[str] = None,
                       methods: List[str] = None,
                       fractions: List[float] = None,
                       seed: int = 42,
                       save: bool = True) -> pd.DataFrame:
    """Aggregate the training-fraction sweep across bearings -> valid-alarm fraction."""
    from src.config import PATHS
    from src.datasets import default_runs

    bearings = bearings or default_runs(dataset)
    frames = []
    for b in bearings:
        try:
            frames.append(sweep_bearing(b, dataset=dataset, methods=methods,
                                        fractions=fractions, seed=seed))
        except Exception as e:  # noqa: BLE001 - keep other bearings going
            logger.error("[%s] training sweep failed: %s", b, e)
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames, ignore_index=True)

    agg = (long.groupby(["dataset", "train_fraction", "method", "short_name"])
           .agg(valid_frac=("valid_alarm", "mean"),
                na_count=("na", "sum"),
                mean_lead_valid=("lead_time_hours",
                                 lambda s: float(np.nanmean(s[s > 0])) if (s > 0).any() else 0.0),
                n_bearings=("bearing", "nunique"))
           .reset_index())

    if save and not long.empty:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        long.to_csv(os.path.join(PATHS["results_tables"], "femto_training_sweep_long.csv"),
                    index=False)
        agg.to_csv(os.path.join(PATHS["results_tables"], "femto_training_sweep.csv"),
                   index=False)
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
    ap = argparse.ArgumentParser(description="FEMTO deep-model training-data sweep")
    ap.add_argument("--dataset", default="FEMTO")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    agg = run_training_sweep(dataset=args.dataset, seed=args.seed, save=True)
    if agg.empty:
        print("No results produced.")
        return
    pd.set_option("display.width", 240, "display.max_columns", 40)
    piv = agg.pivot_table(index="short_name", columns="train_fraction",
                          values="valid_frac").round(2)
    print("\n=== valid-alarm fraction vs training fraction (FEMTO, n=6) ===")
    print(piv.to_string())
    pivna = agg.pivot_table(index="short_name", columns="train_fraction",
                            values="na_count").round(0)
    print("\n=== N/A count (of 6 bearings) ===")
    print(pivna.to_string())


if __name__ == "__main__":
    main()
