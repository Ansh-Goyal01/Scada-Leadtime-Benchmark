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

# The ML detectors (sklearn / torch) are an OPTIONAL backend. Lightweight consumers
# — the diagnostic console, threshold utilities, plain data loaders — must remain
# importable even when those compiled deps are unavailable (missing install, blocked
# DLL on a locked-down host, etc.). Guard the heavy import groups so a backend that
# can't load degrades to "feature unavailable" instead of breaking the whole package.
import warnings as _warnings

try:
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
except ImportError as _e:   # pragma: no cover - environment-dependent
    _warnings.warn(f"src.models unavailable ({_e}); detector API disabled, "
                   "lightweight modules (console, thresholds) still work.")

from src.thresholds import (
    compute_threshold,
    generate_alarm_signal,
    apply_persistence_filter,
    threshold_sweep,
    dynamic_ewma_threshold,
)

try:
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
except ImportError as _e:   # pragma: no cover - environment-dependent
    _warnings.warn(f"src.lead_time unavailable ({_e}); lead-time metrics disabled.")

try:
    from src.uncertainty import (
        BootstrapEnsemble,
        ConformalDetector,
        compute_shap_values,
        plot_shap_summary,
        plot_calibration_curve,
        plot_score_with_uncertainty,
    )
except ImportError as _e:   # pragma: no cover - environment-dependent
    _warnings.warn(f"src.uncertainty unavailable ({_e}); uncertainty API disabled.")



# Convenience pipeline wrappers

def _median_spacing_minutes(index) -> float:
    """Median spacing of a DatetimeIndex in minutes (robust to gaps)."""
    import numpy as np
    if len(index) < 2:
        return float("nan")
    diffs = index.to_series().diff().dropna().dt.total_seconds() / 60.0
    return float(np.median(diffs)) if len(diffs) else float("nan")


def ensure_spectral_cache(run_name: str):
    """
    Build (or load) the spectral-augmented snapshot parquet for an IMS run: join the
    cached time-domain snapshot stats with frequency-domain features (spectral kurtosis,
    envelope defect-band amplitudes, FFT band energies) computed from the raw 20.48 kHz
    waveforms, resampled onto the same 10-min grid. Cached to *_features_spectral.parquet.
    Addresses reviewer W10 (spectral information discarded).
    """
    import os
    import pandas as pd
    from src.config import PATHS, DATASETS_GEOMETRY
    from src.preprocessing import load_processed, save_processed

    spec_path = os.path.join(PATHS["processed"], f"{run_name}_features_spectral.parquet")
    if os.path.exists(spec_path):
        return load_processed(spec_path)

    base = load_processed(os.path.join(PATHS["processed"], f"{run_name}_features.parquet"))
    n_ch = sum(1 for c in base.columns if c.startswith("rms_ch"))

    # Cache the (slow) raw spectral computation separately so a re-join is cheap.
    raw_spec_path = os.path.join(PATHS["processed"], f"{run_name}_spectral_raw.parquet")
    if os.path.exists(raw_spec_path):
        spec = load_processed(raw_spec_path)
    else:
        from src.spectral_features import compute_spectral_for_run, BearingGeometry
        g = DATASETS_GEOMETRY["IMS"]
        run_dir = os.path.join(PATHS["raw_ims"], run_name)
        spec = compute_spectral_for_run(run_dir, BearingGeometry(**g["geom"]),
                                        g["shaft_speed_hz"], n_channels=n_ch, fs=g["fs"])
        save_processed(spec, raw_spec_path)

    # Align spectral rows (same raw-file timestamps) to the base snapshot grid by NEAREST
    # within tolerance. Use merge_asof (not reindex) because IMS timestamps can contain
    # duplicates (minute-truncated collisions), which reindex rejects. The base index and
    # spec index derive from the same files but may differ by seconds.
    spec_cols = list(spec.columns)
    b = base.reset_index()
    ts_b = b.columns[0]
    s = spec.reset_index()
    ts_s = s.columns[0]
    b = b.sort_values(ts_b)
    s = s.sort_values(ts_s)
    merged = pd.merge_asof(b, s, left_on=ts_b, right_on=ts_s,
                           direction="nearest", tolerance=pd.Timedelta("5min"),
                           suffixes=("", "_specidx"))
    merged = merged.set_index(ts_b)
    joined = merged[list(base.columns) + spec_cols].copy()
    joined[spec_cols] = joined[spec_cols].ffill().bfill()
    save_processed(joined, spec_path)
    return joined


def load_pipeline(run_name: str = "2nd_test",
                  window_size: int = None,
                  overlap: float = None,
                  resample_freq: str = "10min",
                  downsample_factor: int = 1,
                  downsample_mode: str = "none",
                  use_spectral: bool = None,
                  dataset: str = "IMS",
                  signal_transform=None) -> dict:
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
    if use_spectral is None:
        use_spectral = FEATURES.get("use_spectral", False)

    # Load the run via the dataset registry (IMS / ONGC / XJTU-SY / FEMTO). Every loader
    # yields a RunBundle whose snapshot_df carries rms_ch* signal columns, so the rest of
    # the pipeline is dataset-agnostic. ONGC etc. have no raw waveform → use_spectral off.
    from src.datasets import load_run
    bundle = load_run(dataset, run_name, use_spectral=bool(use_spectral))
    df = bundle.snapshot_df
    failure_time = bundle.failure_time
    train_fraction = bundle.train_fraction

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

    # Optional mechanism-test hook (src/robustness.py): an arbitrary transform of
    # the snapshot signal grid AFTER any downsampling but BEFORE feature extraction.
    # Used to inject noise and to compare alternative denoisers (median / moving-
    # average / Kalman / wavelet) against historian bin-averaging. signal_transform
    # is a callable df -> df operating on the rms_ch*/kurt_ch* columns; None is a
    # no-op so all existing call sites are unchanged.
    if signal_transform is not None:
        df = signal_transform(df)

    # Feature extraction — channel-count-invariant schema (W4 fix) or legacy.
    if FEATURES.get("mode", "invariant") == "invariant":
        from src.features import extract_invariant_features
        feat_df = extract_invariant_features(
            df,
            window_size=ws,
            overlap=ovl,
            channel_aggs=tuple(FEATURES.get("invariant_channel_aggs", ("mean", "max"))),
            window_summaries=tuple(FEATURES.get("invariant_window_summaries",
                                                ("mean", "std", "max", "slope"))),
        )
    else:
        feat_df = extract_rolling_features(
            df,
            window_size=ws,
            overlap=ovl,
            feature_list=FEATURES["feature_list"],
            include_cross_channel=FEATURES["include_cross_channel"],
        )

    # Temporal split on feature DataFrame (train fraction is per-dataset, from the bundle)
    df_train, df_cal, df_test = temporal_split(
        feat_df,
        train_frac=train_fraction,
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
    feature_names = list(feat_cols)

    # Train-fit feature selection (variance top-k) — guarantees p < n even after the
    # invariant schema, removing the residual p≫n degeneracy. Leakage-free (fit on train).
    top_k = FEATURES.get("select_top_k")
    if top_k and X_train.shape[1] > top_k:
        strategy = FEATURES.get("select_strategy", "stratified")
        if strategy == "stratified":
            from src.features import select_stratified_features
            sel = select_stratified_features(X_train, feature_names, k=top_k)
        else:
            from src.features import select_top_k_features
            sel = select_top_k_features(X_train, feature_names, k=top_k)
        X_train, X_cal, X_test = X_train[:, sel], X_cal[:, sel], X_test[:, sel]
        feature_names = [feature_names[i] for i in sel]

    # Failure reference timestamps (failure_time comes from the bundle)
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
        "dataset":       dataset,
        "train_fraction": train_fraction,
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
