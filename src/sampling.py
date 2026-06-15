# src/sampling.py
"""
SCADA-rate sampling sweep — the central experiment behind the paper title.

Progressively coarsens the logging rate (simulating a SCADA historian that records
less often) and measures how detection lead time degrades, under two constraint
mechanisms:

    aggregate — mean over each coarser bin   (realistic SCADA averaging; smooths away
                                              transient kurtosis/crest signatures)
    decimate  — keep every k-th sample        (lower logging frequency, values intact)

The feature window and alarm-persistence are held constant in WALL-CLOCK time across
all sampling rates, so lead-time differences reflect genuine information loss rather
than an artifact of counting a fixed number of windows over an ever-longer real interval.

Each row also carries VLT_norm — the valid lead time as a fraction of that run's maximum
achievable lead time (t_fail − t_normal_end) — so results are comparable across runs whose
test windows differ several-fold in wall-clock length.

Outputs (under results/tables/):
    sampling_sweep_{run}.csv        one row per (mode, factor, method) for a run
    sampling_sweep_all.csv          all runs concatenated
    sampling_sweep_aggregate.csv    across-run stats per (mode, factor, method): raw VLT
                                    mean/std/median, normalized VLT mean/std/median/min/max,
                                    FAR mean/std/median
"""

import os
import logging
import numpy as np
import pandas as pd

from src import load_pipeline
from src.config import (
    PATHS, DATASET, FEATURES, SPLIT, THRESHOLD, MODELS, EXPERIMENT, SAMPLING,
)
from src.models import get_all_models
from src.lead_time import evaluate_all_methods

logger = logging.getLogger(__name__)


# Wall-clock → window/persistence counts


def derive_counts(base_min: float,
                  factor: int,
                  window_minutes: float,
                  persistence_minutes: float,
                  overlap: float,
                  min_window_rows: int = 3) -> dict:
    """
    Convert fixed wall-clock durations into per-rate integer counts.

    At the effective spacing (base_min × factor):
      window_rows        = window_minutes / effective_min      (floored at min_window_rows)
      persistence_windows = persistence_minutes / stride_min   (floored at 1)
    where stride_min is the wall-clock gap between consecutive window centers.

    Returns a dict with the derived counts plus a `window_floored` flag (logged upstream).
    """
    effective_min = base_min * factor

    raw_window = window_minutes / effective_min
    window_rows = int(round(raw_window))
    window_floored = window_rows < min_window_rows
    window_rows = max(min_window_rows, window_rows)

    stride_rows = max(1, int(round(window_rows * (1.0 - overlap))))
    stride_min = stride_rows * effective_min
    persistence_windows = max(1, int(round(persistence_minutes / stride_min)))

    return {
        "effective_min":       effective_min,
        "window_rows":         window_rows,
        "persistence_windows": persistence_windows,
        "window_floored":      window_floored,
    }


# Single-run sweep


def run_sampling_sweep(run_name: str = "2nd_test",
                       factors: list = None,
                       modes: list = None,
                       methods: list = None,
                       save: bool = True) -> pd.DataFrame:
    """
    Sweep one run over (mode × factor), evaluating every configured detector at each
    sampling rate. Returns a tidy DataFrame (one row per mode × factor × method).
    """
    factors = factors or SAMPLING["factors"]
    modes   = modes   or SAMPLING["modes"]
    methods = methods or EXPERIMENT["methods_to_run"]

    overlap = FEATURES["overlap"]
    min_window_rows = SAMPLING["min_window_rows"]

    # Establish the base grid spacing from an undownsampled load (factor=1 is a no-op).
    base_pipe = load_pipeline(run_name)
    base_min = base_pipe["effective_interval_min"]
    if not np.isfinite(base_min) or base_min <= 0:
        raise RuntimeError(f"[{run_name}] could not determine base grid spacing")

    # Maximum achievable valid lead time for this run, used to normalize VLT onto a
    # run-independent [0, 1] scale. A detector can at best alarm right after the normal
    # period ends, so VLT_max = t_fail − t_normal_end. We anchor this to the factor=1
    # (full-resolution) test grid so the denominator is a single per-run constant: it
    # rescales runs onto a common axis WITHOUT distorting the within-run shape of the
    # VLT-vs-sampling curve. Raw test windows differ ~6× in wall-clock length across the
    # three IMS runs, which otherwise makes a cross-run mean/std meaningless.
    t_fail = pd.Timestamp(base_pipe["failure_time"])
    available_lead_hours = (t_fail - base_pipe["t_normal_end"]).total_seconds() / 3600.0
    if not np.isfinite(available_lead_hours) or available_lead_hours <= 0:
        logger.warning(
            f"[{run_name}] non-positive available lead window "
            f"({available_lead_hours:.2f} h) — normalized VLT will be NaN"
        )
        available_lead_hours = np.nan
    else:
        logger.info(f"[{run_name}] max achievable lead time = {available_lead_hours:.1f} h")

    # Window + persistence durations held constant in wall-clock. Defaults are derived
    # from the base grid so that factor=1 reproduces the standard pipeline exactly:
    #   window_minutes      = FEATURES window_size × base spacing
    #   persistence_minutes = THRESHOLD persistence × base window-stride
    window_minutes = SAMPLING["window_minutes"]
    if window_minutes is None:
        window_minutes = FEATURES["window_size"] * base_min

    persistence_minutes = SAMPLING["persistence_minutes"]
    if persistence_minutes is None:
        base_stride_min = FEATURES["window_size"] * (1.0 - overlap) * base_min
        persistence_minutes = THRESHOLD["alarm_persistence"] * base_stride_min

    logger.info(
        f"[{run_name}] base spacing = {base_min:.2f} min | "
        f"window held at {window_minutes:.1f} min | persistence at {persistence_minutes:.1f} min"
    )

    rows = []
    for mode in modes:
        for factor in factors:
            c = derive_counts(
                base_min, factor, window_minutes, persistence_minutes,
                overlap, min_window_rows,
            )
            if c["window_floored"]:
                logger.warning(
                    f"[{run_name}] mode={mode} factor={factor} "
                    f"(≈{c['effective_min']:.0f} min): window floored to "
                    f"{c['window_rows']} rows — constant wall-clock window not preserved here"
                )

            # factor=1 is identical across modes (no downsampling) — load once is fine,
            # but we keep the call inside the loop for clarity; it is cheap.
            pipe = load_pipeline(
                run_name,
                window_size=c["window_rows"],
                downsample_factor=factor,
                downsample_mode=mode,
            )

            detectors = get_all_models({
                "methods_to_run": methods,
                "model_params":   MODELS,
            })

            summary_df, _ = evaluate_all_methods(
                detectors=detectors,
                X_train=pipe["X_train"],
                X_test=pipe["X_test"],
                timestamps_test=pipe["ts_test"],
                failure_time=pipe["failure_time"],
                normal_period_fraction=SPLIT["normal_period_fraction"],
                threshold_strategy=THRESHOLD["strategy"],
                threshold_percentile=THRESHOLD["percentile"],
                alarm_persistence=c["persistence_windows"],
            )

            for _, r in summary_df.iterrows():
                vlt = r["VLT (hours)"]
                if np.isfinite(available_lead_hours) and available_lead_hours > 0:
                    # Clip to [0, 1]: a coarse-grid t_normal_end can shift slightly from
                    # the factor=1 anchor, so a near-maximal VLT may marginally exceed it.
                    vlt_norm = min(1.0, max(0.0, vlt / available_lead_hours))
                else:
                    vlt_norm = np.nan
                rows.append({
                    "run":                    run_name,
                    "mode":                   mode,
                    "factor":                 factor,
                    "effective_interval_min": round(pipe["effective_interval_min"], 2),
                    "method":                 r["Method"],
                    "VLT_hours":              vlt,
                    "VLT_norm":               round(vlt_norm, 4) if np.isfinite(vlt_norm) else np.nan,
                    "available_lead_hours":   round(available_lead_hours, 2)
                                              if np.isfinite(available_lead_hours) else np.nan,
                    "FAR_pct":                r["FAR (%)"],
                    "FAT":                    r["FAT"],
                    "valid_alarm":            r["Valid Alarm"],
                    "n_test_windows":         len(pipe["ts_test"]),
                    "window_rows":            c["window_rows"],
                    "persistence_windows":    c["persistence_windows"],
                    "window_floored":         c["window_floored"],
                })

            logger.info(
                f"[{run_name}] mode={mode} factor={factor} "
                f"(≈{pipe['effective_interval_min']:.0f} min) — done "
                f"({len(pipe['ts_test'])} test windows)"
            )

    sweep_df = pd.DataFrame(rows)

    if save:
        out = os.path.join(PATHS["results_tables"], f"sampling_sweep_{run_name}.csv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sweep_df.to_csv(out, index=False)
        logger.info(f"Saved sampling sweep → {out}")

    return sweep_df


# All-runs sweep + aggregate stats


def run_sampling_sweep_all_runs(runs: list = None,
                                factors: list = None,
                                modes: list = None,
                                methods: list = None,
                                save: bool = True) -> tuple:
    """
    Run the sampling sweep over multiple runs, concatenate, and compute aggregate
    statistics (mean ± std of VLT/FAR across runs, per mode × factor × method).

    Returns (all_df, aggregate_df).
    """
    runs = runs or EXPERIMENT["runs_to_evaluate"]

    frames = []
    for run_name in runs:
        try:
            frames.append(
                run_sampling_sweep(run_name, factors, modes, methods, save=save)
            )
        except Exception as e:
            logger.error(f"Sampling sweep failed for {run_name}: {e}")

    if not frames:
        raise RuntimeError("No runs completed — nothing to aggregate.")

    all_df = pd.concat(frames, ignore_index=True)

    agg = (
        all_df
        .groupby(["mode", "factor", "effective_interval_min", "method"], as_index=False)
        .agg(
            # Raw VLT (hours) — kept for the appendix; mean/std is scale-dominated by the
            # longest-window run, which is exactly why the headline uses VLT_norm instead.
            VLT_hours_mean=("VLT_hours", "mean"),
            VLT_hours_std=("VLT_hours", "std"),
            VLT_hours_median=("VLT_hours", "median"),
            # Normalized VLT (fraction of each run's max achievable lead time) — the
            # cross-run-comparable quantity. Median + min/max band is robust to the n=3
            # outlier (3rd_test, which fails to detect at fine sampling).
            VLT_norm_mean=("VLT_norm", "mean"),
            VLT_norm_std=("VLT_norm", "std"),
            VLT_norm_median=("VLT_norm", "median"),
            VLT_norm_min=("VLT_norm", "min"),
            VLT_norm_max=("VLT_norm", "max"),
            # FAR is already a rate in [0, 100] — comparable across runs without rescaling.
            FAR_pct_mean=("FAR_pct", "mean"),
            FAR_pct_std=("FAR_pct", "std"),
            FAR_pct_median=("FAR_pct", "median"),
            n_runs=("run", "nunique"),
        )
        .sort_values(["mode", "method", "factor"])
    )
    # std is NaN when a single run contributes — report 0 for clarity.
    std_cols = ["VLT_hours_std", "VLT_norm_std", "FAR_pct_std"]
    agg[std_cols] = agg[std_cols].fillna(0.0)

    if save:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        all_out = os.path.join(PATHS["results_tables"], "sampling_sweep_all.csv")
        agg_out = os.path.join(PATHS["results_tables"], "sampling_sweep_aggregate.csv")
        all_df.to_csv(all_out, index=False)
        agg.to_csv(agg_out, index=False)
        logger.info(f"Saved combined sweep → {all_out}")
        logger.info(f"Saved aggregate stats → {agg_out}")

    return all_df, agg
