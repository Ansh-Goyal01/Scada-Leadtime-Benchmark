    # src/__init__.py
"""
SCADA Lead-Time-Aware Anomaly Detection Framework
==================================================
Public API — import from here for clean notebook usage.

Example:
    from src import load_pipeline, run_experiment
    from src.config import PATHS, DATASET, FEATURES, SPLIT, THRESHOLD, EXPERIMENT
"""

from src.config import (
    PATHS, DATASET, FEATURES, SPLIT,
    THRESHOLD, MODELS, UNCERTAINTY, EXPERIMENT, PLOT
)

from src.preprocessing import (
    load_ims_run,
    load_all_runs,
    run_preprocessing_pipeline,
    resample_uniform,
    temporal_split,
    fit_scaler,
    apply_scaler,
    align_to_failure,
)

from src.features import (
    extract_rolling_features,
    build_feature_matrix,
    get_feature_subset,
    build_ablation_matrices,
    FEATURE_GROUPS,
)

from src.models import (
    BaseDetector,
    ThreeSigmaDetector,
    EWMADetector,
    HotellingT2Detector,
    IsolationForestDetector,
    OneClassSVMDetector,
    LSTMAEDetector,
    get_all_models,
)

from src.thresholds import (
    compute_threshold,
    generate_alarm_signal,
    apply_persistence_filter,
    threshold_sweep,
    dynamic_ewma_threshold,
)

from src.lead_time import (
    compute_FAT,
    compute_VLT,
    compute_FAR,
    compute_miss_rate,
    evaluate_method,
    evaluate_all_methods,
    plot_alarm_timeline,
    plot_lead_time_comparison,
    plot_vlt_vs_far,
    plot_lead_time_vs_sampling,
)

from src.uncertainty import (
    BootstrapEnsemble,
    ConformalDetector,
    compute_shap_values,
    plot_shap_summary,
    plot_calibration_curve,
    plot_score_with_uncertainty,
)



# Convenience pipeline wrappers

def _median_spacing_minutes(index) -> float:
    """Median spacing of a DatetimeIndex in minutes (robust to gaps)."""
    import numpy as np
    if len(index) < 2:
        return float("nan")
    diffs = index.to_series().diff().dropna().dt.total_seconds() / 60.0
    return float(np.median(diffs)) if len(diffs) else float("nan")


def load_pipeline(run_name: str = "2nd_test",
                  window_size: int = None,
                  overlap: float = None,
                  resample_freq: str = "10min",
                  downsample_factor: int = 1,
                  downsample_mode: str = "none") -> dict:
    """
    One-call loader: preprocess → (SCADA-rate downsample) → feature extract → split → scale.

    downsample_factor / downsample_mode simulate a SCADA-rate sampling constraint by
    coarsening the time grid BEFORE feature extraction. The effective sampling interval
    becomes ``base_spacing × downsample_factor``.
        mode "none"      — no downsampling (default; baseline behavior unchanged)
        mode "aggregate" — mean over each coarser bin (realistic SCADA averaging)
        mode "decimate"  — keep every k-th sample (lower logging frequency)

    Returns a dict with keys:
        X_train, X_cal, X_test,
        feature_names, ts_train, ts_cal, ts_test,
        df_full, feat_df_full,
        failure_time, t_normal_end, scaler, run_name,
        effective_interval_min, window_size_used
    """
    import os

    ws  = window_size or FEATURES["window_size"]
    ovl = overlap     or FEATURES["overlap"]

    # Load and preprocess
    processed_path = os.path.join(
        PATHS["processed"], f"{run_name}_features.parquet"
    )

    if os.path.exists(processed_path):
        from src.preprocessing import load_processed
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

    # SCADA-rate sampling constraint: coarsen the grid before feature extraction.
    base_min = _median_spacing_minutes(df.index)
    if downsample_mode not in ("none", "aggregate", "decimate"):
        raise ValueError(f"Unknown downsample_mode '{downsample_mode}'")
    if downsample_mode != "none" and downsample_factor > 1:
        if downsample_mode == "aggregate":
            target_min = max(1, int(round(base_min * downsample_factor)))
            df = resample_uniform(df, f"{target_min}min")
        else:  # decimate — keep every k-th row of the uniform grid
            df = df.iloc[::downsample_factor].copy()
    effective_interval_min = _median_spacing_minutes(df.index)

    # Feature extraction
    feat_df = extract_rolling_features(
        df,
        window_size=ws,
        overlap=ovl,
        feature_list=FEATURES["feature_list"],
        include_cross_channel=FEATURES["include_cross_channel"],
    )

    # Temporal split on feature DataFrame
    df_train, df_cal, df_test = temporal_split(
        feat_df,
        train_frac=SPLIT["train_fraction"],
        cal_frac=SPLIT["calibration_fraction"],
    )

    # Build feature matrices
    X_train, feature_names, ts_train = build_feature_matrix(df_train)
    X_cal,   _,             ts_cal   = build_feature_matrix(df_cal)
    X_test,  _,             ts_test  = build_feature_matrix(df_test)

    # Scale (fit only on train)
    scaler, feat_cols = fit_scaler(df_train, scaler_type="robust")
    # Re-extract raw arrays after scaling for model input
    X_train = apply_scaler(df_train, scaler, feat_cols)[feat_cols].values
    X_cal   = apply_scaler(df_cal,   scaler, feat_cols)[feat_cols].values
    X_test  = apply_scaler(df_test,  scaler, feat_cols)[feat_cols].values

    # Failure reference timestamps
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


def run_experiment(run_name: str = "2nd_test") -> tuple:
    """
    Full experiment: load data → run all configured methods → return summary + results.
    """
    pipe = load_pipeline(run_name)

    detectors = get_all_models({
        "methods_to_run": EXPERIMENT["methods_to_run"],
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
        alarm_persistence=THRESHOLD["alarm_persistence"],
    )

    return summary_df, all_results, pipe
