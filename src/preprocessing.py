# src/preprocessing.py
"""
Data ingestion, cleaning, timestamp alignment, and normalization.

All functions are stateless and pipeline-friendly:
  - fit functions return (transformed_data, fitted_object)
  - transform functions accept the fitted object
  - No global state — safe to call from notebooks and scripts
"""

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import signal as scipy_signal
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")



# IMS Dataset Loader


def load_ims_run(run_dir: str, n_channels: int = 8, verbose: bool = True) -> pd.DataFrame:
    """
    Load one IMS bearing run from its folder of snapshot files.

    Each file in the folder:
      - Filename = Unix timestamp (integer seconds)
      - Content   = space/tab-delimited matrix of shape (20480, 8)
                    representing 1 second of 8-channel vibration data at 20480 Hz

    Returns a DataFrame indexed by datetime, one row per snapshot file.
    Columns: rms_ch0..rms_ch7, kurt_ch0..kurt_ch7, peak_ch0..peak_ch7,
             skew_ch0..skew_ch7, crest_ch0..crest_ch7, p2p_ch0..p2p_ch7
    """
    run_dir = Path(run_dir)
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    files = sorted([f for f in run_dir.iterdir() if f.is_file()])
    if len(files) == 0:
        raise ValueError(f"No files found in {run_dir}")

    if verbose:
        logger.info(f"Loading {len(files)} snapshot files from {run_dir.name} ...")

    records = []
    for i, filepath in enumerate(files):
        try:
            raw = np.loadtxt(filepath)                       # (20480, 8) or (20480, 4)
        except Exception:
            try:
                raw = np.loadtxt(filepath, delimiter='\t')
            except Exception as e:
                logger.warning(f"Skipping {filepath.name}: {e}")
                continue

        if raw.ndim == 1:
            raw = raw.reshape(-1, 1)

        actual_channels = min(raw.shape[1], n_channels)

        # Parse timestamp from filename
        try:
            # Date-formatted: 2004.02.12.10.32.39 → 2004-02-12 10:32:39
            parts = filepath.stem.split(".")
            ts = pd.Timestamp(
                year=int(parts[0]), month=int(parts[1]), day=int(parts[2]),
                hour=int(parts[3]), minute=int(parts[4]),
                second=int(parts[5]) if len(parts) > 5 else 0
            )
        except Exception:
            try:
                ts = pd.Timestamp(float(filepath.stem), unit='s')
            except Exception:
                ts = pd.Timestamp("2003-10-22") + pd.Timedelta(minutes=i)

        row = {"timestamp": ts}

        for ch in range(actual_channels):
            x = raw[:, ch].astype(np.float64)
            rms_val = float(np.sqrt(np.mean(x ** 2)))
            row[f"rms_ch{ch}"]   = rms_val
            row[f"kurt_ch{ch}"]  = float(_kurtosis(x))
            row[f"skew_ch{ch}"]  = float(_skewness(x))
            row[f"p2p_ch{ch}"]   = float(np.max(x) - np.min(x))
            row[f"crest_ch{ch}"] = float(np.max(np.abs(x)) / (rms_val + 1e-12))
            row[f"var_ch{ch}"]   = float(np.var(x))

        records.append(row)

        if verbose and (i + 1) % 500 == 0:
            logger.info(f"  Processed {i+1}/{len(files)} files ...")

    df = pd.DataFrame(records).set_index("timestamp").sort_index()

    if verbose:
        logger.info(f"Loaded {len(df)} snapshots, {df.shape[1]} features per snapshot.")

    return df


def load_all_runs(raw_ims_dir: str, run_names: list, n_channels: int = 8) -> dict:
    """
    Load all IMS runs into a dictionary of DataFrames.

    Returns: {"1st_test": df1, "2nd_test": df2, "3rd_test": df3}
    """
    runs = {}
    for run_name in run_names:
        run_path = os.path.join(raw_ims_dir, run_name)
        if os.path.exists(run_path):
            runs[run_name] = load_ims_run(run_path, n_channels=n_channels)
        else:
            logger.warning(f"Run directory not found, skipping: {run_path}")
    return runs



# Cleaning


def handle_missing(df: pd.DataFrame, method: str = "ffill", max_gap: int = 5) -> pd.DataFrame:
    """
    Fill missing values.
    method: "ffill" | "interpolate" | "drop"
    max_gap: max consecutive NaN rows to fill (beyond this, drop row)
    """
    df = df.copy()
    if method == "ffill":
        df = df.ffill(limit=max_gap)
        df = df.bfill(limit=max_gap)
    elif method == "interpolate":
        df = df.interpolate(method="time", limit=max_gap)
    elif method == "drop":
        df = df.dropna()

    remaining_nans = df.isna().sum().sum()
    if remaining_nans > 0:
        logger.warning(f"Still {remaining_nans} NaN values after fill — dropping rows.")
        df = df.dropna()

    return df


def detect_stuck_sensors(df: pd.DataFrame, window: int = 20, tol: float = 1e-9) -> pd.DataFrame:
    """
    Detect time windows where a sensor value doesn't change (sensor dropout / stuck).
    Returns a boolean DataFrame (True = stuck at that timestamp).
    """
    stuck = pd.DataFrame(False, index=df.index, columns=df.columns)
    for col in df.columns:
        roll_std = df[col].rolling(window=window, min_periods=window).std()
        stuck[col] = roll_std < tol
    return stuck


def remove_outlier_spikes(df: pd.DataFrame, z_thresh: float = 10.0) -> pd.DataFrame:
    """
    Remove extreme single-point spikes using z-score clipping.
    Values beyond z_thresh standard deviations are clipped to the boundary.
    (We clip, not drop — preserving the time index.)
    """
    df = df.copy()
    for col in df.columns:
        mu = df[col].mean()
        sigma = df[col].std()
        lower = mu - z_thresh * sigma
        upper = mu + z_thresh * sigma
        df[col] = df[col].clip(lower=lower, upper=upper)
    return df



# Resampling & Alignment


def resample_uniform(df: pd.DataFrame, freq: str = "10min") -> pd.DataFrame:
    """
    Resample to a uniform time grid using mean aggregation.
    freq: pandas offset alias — "10min" = 10 minutes, "1H" = 1 hour, etc.
    IMS snapshots are typically ~1/min; resampling to 10-min smooths noise.
    """
    return df.resample(freq).mean().dropna(how="all")


def align_to_failure(df: pd.DataFrame, failure_time: str) -> pd.DataFrame:
    """
    Add a 'hours_to_failure' column (negative = time before failure).
    Useful for plotting and for failure-relative lead time analysis.
    """
    df = df.copy()
    t_fail = pd.Timestamp(failure_time)
    df["hours_to_failure"] = (df.index - t_fail).total_seconds() / 3600.0
    return df



# Normalization


def fit_scaler(df_train: pd.DataFrame, scaler_type: str = "robust"):
    """
    Fit a scaler on training data only.
    Returns (fitted_scaler, feature_columns)
    """
    feature_cols = [c for c in df_train.columns if c != "hours_to_failure"]
    if scaler_type == "robust":
        scaler = RobustScaler()
    elif scaler_type == "standard":
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
    elif scaler_type == "minmax":
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
    else:
        raise ValueError(f"Unknown scaler: {scaler_type}")

    scaler.fit(df_train[feature_cols].values)
    return scaler, feature_cols


def apply_scaler(df: pd.DataFrame, scaler, feature_cols: list) -> pd.DataFrame:
    """
    Apply a pre-fitted scaler to a DataFrame.
    Non-feature columns (e.g. hours_to_failure) are preserved as-is.
    """
    df = df.copy()
    df[feature_cols] = scaler.transform(df[feature_cols].values)
    return df



# Train / Calibration / Test Split


def temporal_split(df: pd.DataFrame,
                   train_frac: float = 0.60,
                   cal_frac: float = 0.20) -> tuple:
    """
    Split a time-series DataFrame into train / calibration / test sets.
    NEVER shuffle — always split by time position.

    Returns: (df_train, df_cal, df_test)
      df_train : first train_frac of data (fit models here)
      df_cal   : next cal_frac of data (fit conformal / thresholds here)
      df_test  : remainder (evaluate lead time here — contains failure)
    """
    n = len(df)
    i_train = int(n * train_frac)
    i_cal   = int(n * (train_frac + cal_frac))

    df_train = df.iloc[:i_train].copy()
    df_cal   = df.iloc[i_train:i_cal].copy()
    df_test  = df.iloc[i_cal:].copy()

    logger.info(
        f"Split: train={len(df_train)}, cal={len(df_cal)}, test={len(df_test)} "
        f"(total={n})"
    )
    return df_train, df_cal, df_test



# Save / Load Processed Data


def save_processed(df: pd.DataFrame, path: str):
    """Save to parquet (preserves dtypes and DatetimeIndex)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path)
    logger.info(f"Saved processed data → {path}")


def load_processed(path: str) -> pd.DataFrame:
    """Load from parquet."""
    df = pd.read_parquet(path)
    logger.info(f"Loaded processed data ← {path} ({df.shape})")
    return df



# Internal helpers


def _kurtosis(x: np.ndarray) -> float:
    """Fisher kurtosis (excess kurtosis, normal = 0)."""
    n = len(x)
    if n < 4:
        return 0.0
    mu = np.mean(x)
    sigma = np.std(x)
    if sigma < 1e-12:
        return 0.0
    return float(np.mean(((x - mu) / sigma) ** 4) - 3.0)


def _skewness(x: np.ndarray) -> float:
    """Fisher skewness."""
    n = len(x)
    if n < 3:
        return 0.0
    mu = np.mean(x)
    sigma = np.std(x)
    if sigma < 1e-12:
        return 0.0
    return float(np.mean(((x - mu) / sigma) ** 3))



# Full Pipeline (convenience wrapper)


def run_preprocessing_pipeline(raw_ims_dir: str,
                                run_names: list,
                                processed_dir: str,
                                failure_times: dict,
                                n_channels: int = 8,
                                resample_freq: str = "10min") -> dict:
    """
    End-to-end preprocessing for all IMS runs.

    Steps:
      1. Load raw snapshot files
      2. Handle missing values
      3. Remove outlier spikes
      4. Resample to uniform grid
      5. Add hours_to_failure column
      6. Save to parquet

    Returns: {"1st_test": df, "2nd_test": df, "3rd_test": df}
    """
    os.makedirs(processed_dir, exist_ok=True)
    result = {}

    for run_name in run_names:
        out_path = os.path.join(processed_dir, f"{run_name}_features.parquet")

        if os.path.exists(out_path):
            logger.info(f"[{run_name}] Processed file exists, loading from cache.")
            result[run_name] = load_processed(out_path)
            continue

        run_dir = os.path.join(raw_ims_dir, run_name)
        if not os.path.exists(run_dir):
            logger.warning(f"[{run_name}] Raw directory not found: {run_dir}")
            continue

        logger.info(f"\n{'='*50}")
        logger.info(f"Processing run: {run_name}")

        df = load_ims_run(run_dir, n_channels=n_channels)
        df = handle_missing(df)
        df = remove_outlier_spikes(df)
        df = resample_uniform(df, freq=resample_freq)

        if run_name in failure_times:
            df = align_to_failure(df, failure_times[run_name])

        save_processed(df, out_path)
        result[run_name] = df

    return result

