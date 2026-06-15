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


def _median_spacing_minutes(index) -> float:
    """Median spacing of a DatetimeIndex in minutes (robust to gaps). Mirrors
    src.__init__._median_spacing_minutes so this module stays self-contained."""
    if len(index) < 2:
        return float("nan")
    diffs = index.to_series().diff().dropna().dt.total_seconds() / 60.0
    return float(np.median(diffs)) if len(diffs) else float("nan")


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


# ─────────────────────────────────────────────────────────────────────────────
# CONTROLLED feature-level sampling sweep  (reviewer W7 fix)
#
# The legacy path above (run_sampling_sweep / load_pipeline downsample_*) coarsens
# the SNAPSHOT grid BEFORE feature extraction, then floors the feature window to a
# minimum of `min_window_rows`. At factors 5/10/20 this floors the window, collapses
# alarm persistence to 1, and changes the number of test windows — so coarse-rate
# comparisons confound three nuisance variables at once.
#
# The controlled path below resamples at the FEATURE level instead: features are
# extracted ONCE at full resolution, then the feature-ROW stream is downsampled.
# The per-window feature definition is therefore IDENTICAL across factors, alarm
# persistence is constant in window-units, and the only thing that changes is the
# effective logging interval. (The number of test windows still shrinks because
# there are fewer feature rows after downsampling — that is intrinsic and
# acceptable; window CONTENT and persistence are no longer confounded.)
# ─────────────────────────────────────────────────────────────────────────────


def downsample_features(feat_df: pd.DataFrame,
                        factor: int,
                        mode: str) -> pd.DataFrame:
    """
    Downsample a FEATURE DataFrame's rows by an integer factor, preserving its
    DatetimeIndex. The per-window feature definition is untouched — only the stream
    of feature rows is thinned, so window content / persistence stay constant.

        mode "aggregate" — mean over each consecutive block of `factor` rows; the
                           block's LAST timestamp labels the aggregated row (the
                           latest information the block could have reported).
        mode "decimate"  — keep every `factor`-th feature row, values intact.
        mode "none"      — no-op (also returned for factor == 1).

    factor == 1 returns the input unchanged (any mode).
    """
    if factor is None or factor <= 1 or mode == "none":
        return feat_df
    if mode not in ("aggregate", "decimate"):
        raise ValueError(f"Unknown feature downsample mode '{mode}'")

    n = len(feat_df)
    if n == 0:
        return feat_df

    if mode == "decimate":
        return feat_df.iloc[::factor].copy()

    # aggregate: block-mean over consecutive groups of `factor` rows.
    # Group label = integer block id; block's LAST original timestamp is the new index.
    block_id = np.arange(n) // factor
    grouped = feat_df.groupby(block_id, sort=True)
    out = grouped.mean(numeric_only=True)
    # Use each block's last (center/last) timestamp as the representative index.
    last_ts = feat_df.index.to_series().groupby(block_id, sort=True).last()
    out.index = pd.DatetimeIndex(last_ts.values)
    return out


def load_pipeline_controlled(run_name: str = "2nd_test",
                             factor: int = 1,
                             mode: str = "none",
                             window_size: int = None,
                             overlap: float = None,
                             resample_freq: str = "10min") -> dict:
    """
    Controlled-sweep loader: preprocess → feature-extract ONCE at full resolution →
    downsample the FEATURE rows → split → scale.

    Same dict shape as src.load_pipeline, but the KEY difference is that the feature
    window stays full-resolution CONSTANT across factors; only the feature-row stream
    is thinned (mean-block or decimate). The reported ``effective_interval_min`` is
    recomputed from the DOWNSAMPLED feature index, and ``window_size_used`` is the
    constant full-res window (never floored).

    Returns a dict with keys:
        X_train, X_cal, X_test,
        feature_names, ts_train, ts_cal, ts_test,
        df_full, feat_df_full,
        failure_time, t_normal_end, scaler, run_name,
        effective_interval_min, window_size_used
    """
    import os
    from src.preprocessing import (
        load_processed, temporal_split, fit_scaler, apply_scaler,
        run_preprocessing_pipeline,
    )
    from src.features import extract_rolling_features, build_feature_matrix

    ws  = window_size or FEATURES["window_size"]
    ovl = overlap     or FEATURES["overlap"]

    # ── Load full-resolution snapshot df (reuse load_pipeline's cache-load logic) ──
    processed_path = os.path.join(
        PATHS["processed"], f"{run_name}_features.parquet"
    )
    if os.path.exists(processed_path):
        df = load_processed(processed_path)
    else:
        runs = run_preprocessing_pipeline(
            raw_ims_dir=PATHS["raw_ims"],
            run_names=[run_name],
            processed_dir=PATHS["processed"],
            failure_times=DATASET["failure_times"],
            resample_freq=resample_freq,
        )
        df = runs[run_name]

    # ── Extract features ONCE at FULL resolution (no snapshot-grid coarsening) ──
    feat_df = extract_rolling_features(
        df,
        window_size=ws,
        overlap=ovl,
        feature_list=FEATURES["feature_list"],
        include_cross_channel=FEATURES["include_cross_channel"],
    )

    # ── Downsample the FEATURE ROWS (the controlled coarsening) ──
    feat_df = downsample_features(feat_df, factor, mode)

    # Effective logging interval = spacing of the DOWNSAMPLED feature index.
    effective_interval_min = _median_spacing_minutes(feat_df.index)

    # ── Split / matrices / scale — EXACTLY as load_pipeline does ──
    df_train, df_cal, df_test = temporal_split(
        feat_df,
        train_frac=SPLIT["train_fraction"],
        cal_frac=SPLIT["calibration_fraction"],
    )

    X_train, feature_names, ts_train = build_feature_matrix(df_train)
    X_cal,   _,             ts_cal   = build_feature_matrix(df_cal)
    X_test,  _,             ts_test  = build_feature_matrix(df_test)

    scaler, feat_cols = fit_scaler(df_train, scaler_type="robust")
    X_train = apply_scaler(df_train, scaler, feat_cols)[feat_cols].values
    X_cal   = apply_scaler(df_cal,   scaler, feat_cols)[feat_cols].values
    X_test  = apply_scaler(df_test,  scaler, feat_cols)[feat_cols].values

    failure_time = DATASET["failure_times"].get(run_name)
    n_normal = int(len(ts_test) * SPLIT["normal_period_fraction"])
    t_normal_end = ts_test[min(n_normal, len(ts_test) - 1)]

    return {
        "X_train":       X_train,
        "X_cal":         X_cal,
        "X_test":        X_test,
        "feature_names": feature_names,
        "ts_train":      ts_train,
        "ts_cal":        ts_cal,
        "ts_test":       ts_test,
        "df_full":       df,
        "feat_df_full":  feat_df,
        "failure_time":  failure_time,
        "t_normal_end":  t_normal_end,
        "scaler":        scaler,
        "run_name":      run_name,
        "effective_interval_min": effective_interval_min,
        "window_size_used":       ws,
    }


def run_controlled_sweep(run_name: str = "2nd_test",
                         factors: list = None,
                         modes: list = None,
                         methods: list = None,
                         t_onset=None,
                         far_budget: float = 0.10,
                         save: bool = True) -> pd.DataFrame:
    """
    Controlled feature-level sampling sweep for one run.

    Analogous to ``run_sampling_sweep`` but built on ``load_pipeline_controlled``:
    features are extracted once at full resolution and the feature-row stream is
    downsampled, so the per-window feature definition and alarm persistence stay
    constant across factors. ``t_onset`` and ``far_budget`` are passed through to
    ``evaluate_all_methods`` for onset-relative, FAR-budget-gated metrics.

    Unlike the legacy sweep there is NO derive_counts flooring: alarm persistence is
    held at THRESHOLD['alarm_persistence'] CONSTANT (that is the whole point). The
    emitted ``n_test_windows`` lets callers confirm that, although the row count drops
    with factor, the per-window CONTENT is unchanged (window_size_used is constant and
    never floored).

    Returns a tidy DataFrame: one row per (mode × factor × method).
    """
    factors = factors or SAMPLING["factors"]
    modes   = modes   or SAMPLING["modes"]
    methods = methods or EXPERIMENT["methods_to_run"]

    persistence = THRESHOLD["alarm_persistence"]   # CONSTANT in window-units

    rows = []
    for mode in modes:
        for factor in factors:
            dmode = "none" if factor == 1 else mode
            pipe = load_pipeline_controlled(
                run_name,
                factor=factor,
                mode=dmode,
            )

            detectors = get_all_models({
                "methods_to_run": methods,
                "model_params":   MODELS,
            })

            summary_df, all_results = evaluate_all_methods(
                detectors=detectors,
                X_train=pipe["X_train"],
                X_test=pipe["X_test"],
                timestamps_test=pipe["ts_test"],
                failure_time=pipe["failure_time"],
                normal_period_fraction=SPLIT["normal_period_fraction"],
                threshold_strategy=THRESHOLD["strategy"],
                threshold_percentile=THRESHOLD["percentile"],
                alarm_persistence=persistence,
                t_onset=t_onset,
                far_budget=far_budget,
                X_cal=pipe.get("X_cal"),
            )

            for r in all_results:
                rows.append({
                    "run":                    run_name,
                    "mode":                   mode,
                    "factor":                 factor,
                    "effective_interval_min": round(pipe["effective_interval_min"], 2),
                    "method":                 r["method"],
                    "short_name":             r.get("short_name", r["method"]),
                    "lead_time_hours":        r["lead_time_hours"],
                    "detection_delay_hours":  r["detection_delay_hours"],
                    "far_preonset_pct":       r["far_preonset_pct"],
                    "lead_norm":              r.get("lead_norm", np.nan),
                    "vlt_legacy_hours":       r["VLT_hours"],
                    "far_legacy_pct":         r["FAR_pct"],
                    "valid_alarm":            r["valid_alarm"],
                    "n_test_windows":         len(pipe["ts_test"]),
                    "window_size_used":       pipe["window_size_used"],
                    "persistence_windows":    persistence,
                })

            logger.info(
                f"[{run_name}] CONTROLLED mode={mode} factor={factor} "
                f"(≈{pipe['effective_interval_min']:.0f} min) — done "
                f"({len(pipe['ts_test'])} test windows, "
                f"window={pipe['window_size_used']} rows constant)"
            )

    sweep_df = pd.DataFrame(rows)

    if save:
        out = os.path.join(
            PATHS["results_tables"], f"controlled_sweep_{run_name}.csv"
        )
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sweep_df.to_csv(out, index=False)
        logger.info(f"Saved controlled sweep → {out}")

    return sweep_df
