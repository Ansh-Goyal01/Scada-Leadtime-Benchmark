# src/config.py
# Central configuration for the SCADA Lead-Time-Aware Anomaly Detection Framework
# All experiments pull from here — change once, affects everything

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    "raw_ims":        os.path.join(BASE_DIR, "data", "raw", "IMS"),
    "raw_ongc":       os.path.join(BASE_DIR, "data", "raw", "ONGC"),
    "raw_xjtu":       os.path.join(BASE_DIR, "data", "raw", "XJTU-SY"),
    "raw_femto":      os.path.join(BASE_DIR, "data", "raw", "FEMTO"),
    "processed":      os.path.join(BASE_DIR, "data", "processed"),
    "results_figures":os.path.join(BASE_DIR, "results", "figures"),
    "results_tables": os.path.join(BASE_DIR, "results", "tables"),
    "paper":          os.path.join(BASE_DIR, "paper"),
}

# ─── Dataset ──────────────────────────────────────────────────────────────────
DATASET = {
    "name": "IMS",
    "runs": ["1st_test", "2nd_test", "3rd_test"],

    # Channel layout: 4 bearings × 2 sensors (ch0..ch7)
    # ch0,ch1 = Bearing 1 | ch2,ch3 = Bearing 2
    # ch4,ch5 = Bearing 3 | ch6,ch7 = Bearing 4
    "n_channels": 8,
    "sampling_rate_hz": 20480,      # raw acquisition rate
    "samples_per_file": 20480,      # one second of data per snapshot file

    # Known failure channels. NOTE channel layout differs by set:
    #   Set 1 (1st_test): 8 channels — 2 accelerometers per bearing
    #       Bearing1=ch0,1  Bearing2=ch2,3  Bearing3=ch4,5  Bearing4=ch6,7
    #   Set 2/3 (2nd/3rd_test): 4 channels — 1 accelerometer per bearing
    #       Bearing1=ch0  Bearing2=ch1  Bearing3=ch2  Bearing4=ch3
    # Documented failures (Qiu et al. 2006, NASA IMS readme):
    #   Run 1: Bearing 3 (inner race) + Bearing 4 (rolling element) → ch4,5,6,7
    #   Run 2: Bearing 1 (outer race)                                → ch0
    #   Run 3: Bearing 3 (outer race)                                → ch2
    # (Used for documentation/diagnostics only; the pipeline uses all channels.)
    "failure_channels": {
        "1st_test": [4, 5, 6, 7],
        "2nd_test": [0],
        "3rd_test": [2],
    },

    # Known failure times.
    #   1st/2nd: last recording before test stop (matches data span).
    #   3rd_test: CORRECTED. The prior label "2004-04-08 09:16" placed the failure
    #     ~10 days before the end of the run — 1,359 rows (21.5%) lay *after* it,
    #     impossible for a run-to-failure series. Verified empirically: the mean-RMS
    #     health indicator is flat (~0.068) for weeks, then ramps to ~0.228 by
    #     2004-04-18 02:32; the final 02:42 row drops to ~0.004 (machine off). The
    #     bearing-3 outer-race failure is at the END of the run, near 2004-04-18.
    "failure_times": {
        "1st_test": "2003-11-25 23:39:56",
        "2nd_test": "2004-02-19 06:22:00",
        "3rd_test": "2004-04-18 02:42:00",
    },
}

# ─── Bearing Geometry (for spectral defect frequencies, src/spectral_features.py) ─
# Stored as plain dicts; the loader constructs BearingGeometry(**geom) at use time
# (keeps config import-light — no dependency on the spectral module).
DATASETS_GEOMETRY = {
    "IMS": {   # Rexnord ZA-2115 double-row, shaft 2000 RPM
        "geom": {"n_balls": 16, "ball_diameter_mm": 8.4,
                 "pitch_diameter_mm": 71.5, "contact_angle_deg": 15.17},
        "shaft_speed_hz": 2000.0 / 60.0,        # 33.333 Hz
        "fs": 20480.0,
    },
    "XJTU-SY": {  # LDK UER204; shaft speed varies per operating condition
        "geom": {"n_balls": 8, "ball_diameter_mm": 7.92,
                 "pitch_diameter_mm": 34.55, "contact_angle_deg": 0.0},
        "shaft_speed_hz": {"35Hz": 35.0, "37.5Hz": 37.5, "40Hz": 40.0},
        "fs": 25600.0,
    },
    "FEMTO": {  # PRONOSTIA; shaft speed per condition
        "geom": {"n_balls": 13, "ball_diameter_mm": 3.5,
                 "pitch_diameter_mm": 25.6, "contact_angle_deg": 0.0},
        "shaft_speed_hz": {"cond1": 30.0, "cond2": 27.5, "cond3": 25.0},
        "fs": 25600.0,
    },
}

# ─── Feature Extraction ───────────────────────────────────────────────────────
FEATURES = {
    "window_size": 10,         # samples per rolling window
    "overlap": 0.5,             # 50% overlap between consecutive windows
    "feature_list": [           # which features to compute
        "rms",
        "kurtosis",
        "crest_factor",
        "skewness",
        "peak_to_peak",
        "shape_factor",
        "variance",
    ],
    "include_cross_channel": True,   # correlation between channel pairs
    "channels_to_use": [0, 1, 2, 3, 4, 5, 6, 7],   # use all 8
    "use_spectral": False,           # augment snapshots with spectral/envelope features
                                     # (raw-waveform datasets only; cached to *_spectral.parquet)

    # Feature schema (W4 fix). "invariant" = channel-count-invariant aggregation →
    # fixed, low-dim, cross-dataset-comparable feature space (default). "legacy" = the
    # original stats-of-stats + all-pairs correlations (445/1465 dims; p≫n — kept for
    # back-compat and the appendix comparison only).
    "mode": "invariant",
    "select_top_k": 50,              # train-fit feature cap (guarantees p<n)
    "select_strategy": "stratified", # "stratified" (per-family quota) | "variance" (global)
    "invariant_channel_aggs":     ["mean", "max"],
    "invariant_window_summaries": ["mean", "std", "max", "slope"],
}

# ─── Train / Test Split ───────────────────────────────────────────────────────
SPLIT = {
    "train_fraction": 0.50,         # first 50% of run = training (normal data)
    "calibration_fraction": 0.10,   # next 10% = calibration (for conformal)
    "test_fraction": 0.40,          # last 400% = test (contains failure)
    "normal_period_fraction": 0.05, # first 5% of TEST used to measure FAR
}

# ─── Degradation-Onset Detection ──────────────────────────────────────────────
# The onset is a data-anchored, detector-independent change point that replaces the
# old arbitrary "first 5% of test" normal-period marker. It is computed ONCE per run
# on a health indicator (mean RMS trend), using ONLY the training-baseline statistics
# (leakage-free). All onset-relative metrics (detection delay, pre-onset FAR) anchor
# to it. See src/onset.py.
ONSET = {
    "health_indicator": "rms_kurt",   # amplitude-OR-impulsiveness HI (rms & kurt z-max);
                                      # leads pure rms when kurtosis rises early. Other:
                                      # "rms_mean" | "rms_max" | "pca1"
    "method": "terminal",             # "terminal" | "sigma" | "cusum" | "pelt"
    "sigma_k": 4.0,                    # band = train_mean + k*train_std (defines excursion)
    "cusum_k": 0.5,                    # CUSUM slack (in train-std units)
    "cusum_h": 5.0,                    # CUSUM decision threshold (in train-std units)
    "persistence": 5,                 # min sustained samples for a valid excursion
    "gap_tol": 10,                    # merge excursions separated by < this many samples
    "baseline_fraction": 0.2,         # early fraction of run treated as the normal baseline
}

# ─── Thresholding ─────────────────────────────────────────────────────────────
THRESHOLD = {
    "strategy": "percentile",   # "percentile" | "ewma" | "evt"
    "percentile": 97.5,         # used when strategy = "percentile"
    "ewma_lambda": 0.2,         # EWMA smoothing factor
    "ewma_k": 3.0,              # number of std devs for EWMA UCL
    "alarm_persistence": 3,     # consecutive windows above threshold = alarm
    # For sweep experiments
    "sweep_percentiles": [90, 92.5, 95, 97.5, 99, 99.5],
}

# ─── Models ───────────────────────────────────────────────────────────────────
MODELS = {
    "isolation_forest": {
        "n_estimators": 200,
        "contamination": "auto",
        "random_state": 42,
        "max_samples": "auto",
    },
    "one_class_svm": {
        "kernel": "rbf",
        "nu": 0.05,
        "gamma": "scale",
    },
    "three_sigma": {
        "n_sigma": 3.0,
    },
    "ewma": {
        "lambda_": 0.2,
        "k": 3.0,
    },
    "cusum": {                   # two-sided tabular CUSUM control chart (deterministic)
        "k": 0.5,                # reference value / slack (sigma units; half the shift to detect)
        "h": 5.0,                # decision interval (natural alarm level)
    },
    "hotelling_t2": {
        "alpha": 0.01,           # significance level for chi2 threshold
        "n_components": 10,      # PCA rank for the T² subspace (k << n; avoids singular cov when p >> n)
    },
    "lstm_ae": {
        "seq_len": 30,           # number of feature-windows per sequence
        "latent_dim": 16,
        "hidden_dim": 64,
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 1e-3,
        "dropout": 0.1,
    },
    # ─ Extra baselines (src/baselines_extra.py) ─
    "rms_trend": {                 # naive "RMS > kσ" floor baseline
        "n_sigma": 3.0,
    },
    "spectral_kurtosis": {         # alarm on spectral-kurtosis features (sk_* cols)
        "key": "sk_",              # select spectral-kurtosis cols by name substring
        "n_sigma": 3.0,
        # feature_names injected at call time so it becomes a true spectral alarm
    },
    "deep_svdd": {                 # one-class deep model (requires torch)
        "hidden_dim": 32,
        "latent_dim": 8,
        "epochs": 40,              # CPU-friendly
        "batch_size": 32,
        "learning_rate": 1e-3,
        "random_state": 42,
        "device": "auto",
    },
    "tcn": {                       # dilated causal conv autoencoder (requires torch)
        "seq_len": 30,
        "channels": 32,
        "kernel_size": 3,
        "levels": 4,               # dilations 1,2,4,8
        "epochs": 40,              # CPU-friendly; not tuned per-dataset (fixed-protocol fairness)
        "batch_size": 32,
        "learning_rate": 1e-3,
        "dropout": 0.1,
        "random_state": 42,
        "device": "auto",
    },
    "transformer_ad": {            # lightweight reconstruction Transformer (requires torch)
        "seq_len": 30,
        "d_model": 32,             # small — sized for ~100-window training sets
        "nhead": 2,
        "num_layers": 2,
        "dim_feedforward": 64,
        "epochs": 40,
        "batch_size": 32,
        "learning_rate": 1e-3,
        "dropout": 0.1,
        "random_state": 42,
        "device": "auto",
    },
    "conformal_if": {              # distribution-free Isolation Forest (FAR ≤ alpha)
        "n_estimators": 200,
        "contamination": "auto",
        "random_state": 42,
        "max_samples": "auto",
        "alpha": 0.05,             # target false-alarm rate (conformal guarantee)
    },
}

# ─── Uncertainty ──────────────────────────────────────────────────────────────
UNCERTAINTY = {
    "bootstrap_n": 30,
    "bootstrap_alpha": 0.10,     # CI width: 10minh–90th percentile
    "conformal_alpha": 0.05,     # target FAR for conformal detector
}

# ─── Experiment Control ───────────────────────────────────────────────────────
EXPERIMENT = {
    "random_seed": 42,
    "runs_to_evaluate": ["1st_test", "2nd_test", "3rd_test"],
    "methods_to_run": [
        "rms_trend",       # naive RMS>kσ floor baseline (reviewer-requested)
        "three_sigma",
        "ewma",
        "cusum",           # CUSUM control chart (reviewer-requested SPC baseline)
        "hotelling_t2",
        "isolation_forest",
        "deep_svdd",       # one-class deep model (torch)
        "lstm_ae",         # deep recon AE (torch); short-run N/A guard
        "tcn",             # dilated conv AE (torch); short-run N/A guard
        "transformer_ad",  # recon Transformer (torch); short-run N/A guard
    ],
    "run_threshold_sweep": True,
    "run_feature_ablation": True,
    "run_window_ablation": True,
    "run_sampling_robustness": False,   # slow — enable for final results
    "window_sizes_ablation": [64, 128, 256, 512],
    "sampling_downsample_factors": [1, 2, 5, 10, 20],  # 1 = no downsampling
}

# ─── SCADA-Rate Sampling Sweep ────────────────────────────────────────────────
# The core experiment behind the paper title: progressively coarsen the logging
# rate (simulating a SCADA historian that records less often) and measure how
# detection lead time degrades.
SAMPLING = {
    # Effective sampling interval at each step = base_grid_spacing × factor.
    "factors": EXPERIMENT["sampling_downsample_factors"],   # [1, 2, 5, 10, 20]

    # Two constraint mechanisms, compared:
    #   "aggregate" — mean over each coarser bin (what real SCADA historians store;
    #                 smooths away transient kurtosis/crest spikes → realistic worst case)
    #   "decimate"  — keep every k-th sample (lower logging frequency, values intact)
    "modes": ["aggregate", "decimate"],

    # Window + persistence are held constant in WALL-CLOCK time across all rates so
    # lead-time differences reflect information loss, not a window-counting artifact.
    # Both default to None → derived from the base grid so that factor=1 exactly
    # reproduces the standard pipeline (FEATURES window_size, THRESHOLD persistence),
    # giving a clean regression anchor. Override with explicit minutes if desired.
    "window_minutes":      None,   # None → FEATURES["window_size"] × base spacing
    "persistence_minutes": None,   # None → THRESHOLD["alarm_persistence"] × base window-stride
    "min_window_rows":     3,      # floor so higher-order features stay defined (logged if hit)
}

# ─── Plotting ─────────────────────────────────────────────────────────────────
PLOT = {
    "dpi": 150,
    "figsize_single": (10, 4),
    "figsize_double": (14, 5),
    "figsize_grid": (14, 10),
    "style": "seaborn-v0_8-whitegrid",
    "color_palette": [
        "#2196F3",   # blue     — 3σ
        "#4CAF50",   # green    — EWMA
        "#FF9800",   # orange   — Hotelling T²
        "#E91E63",   # pink     — Isolation Forest
        "#9C27B0",   # purple   — LSTM-AE
        "#00BCD4",   # cyan     — Conformal IF
    ],
    "method_colors": {
        "three_sigma":       "#2196F3",
        "ewma":              "#4CAF50",
        "hotelling_t2":      "#FF9800",
        "isolation_forest":  "#E91E63",
        "lstm_ae":           "#9C27B0",
        "conformal_if":      "#00BCD4",
    },
}
