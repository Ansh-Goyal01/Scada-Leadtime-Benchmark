# src/config.py
# Central configuration for the SCADA Lead-Time-Aware Anomaly Detection Framework
# All experiments pull from here — change once, affects everything

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    "raw_ims":        os.path.join(BASE_DIR, "data", "raw", "IMS"),
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

    # Known failure channels (from PRONOSTIA / original paper)
    # Run 1: Bearing 3 (ch4,ch5) and Bearing 4 (ch6,ch7)
    # Run 2: Bearing 1 (ch0,ch1)
    # Run 3: Bearing 3 (ch4,ch5)
    "failure_channels": {
        "1st_test": [4, 5, 6, 7],
        "2nd_test": [0, 1],
        "3rd_test": [4, 5],
    },

    # Known failure times (approximate, from literature)
    "failure_times": {
        "1st_test": "2003-11-25 23:39:56",
        "2nd_test": "2004-02-19 06:22:00",
        "3rd_test": "2004-04-08 09:16:00",
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
}

# ─── Train / Test Split ───────────────────────────────────────────────────────
SPLIT = {
    "train_fraction": 0.50,         # first 50% of run = training (normal data)
    "calibration_fraction": 0.10,   # next 10% = calibration (for conformal)
    "test_fraction": 0.40,          # last 400% = test (contains failure)
    "normal_period_fraction": 0.05, # first 5% of TEST used to measure FAR
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
        "three_sigma",
        "ewma",
        "hotelling_t2",
        "isolation_forest",
        # "lstm_ae",       # comment out for local CPU runs
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
