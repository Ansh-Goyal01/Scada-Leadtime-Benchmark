# src/features.py
"""
Rolling-window feature extraction for anomaly detection.

Design principle:
  - All features computed over sliding windows on the preprocessed snapshot DataFrame
  - Output is a feature matrix X suitable for model training/inference
  - Feature names are tracked so SHAP explanations have readable labels
"""

import numpy as np
import pandas as pd
from itertools import combinations
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)



# Per-window statistical features


def _compute_window_features(window: np.ndarray,
                              feature_list: List[str],
                              channel_names: List[str]) -> dict:
    """
    Compute all requested features for a 2D window (n_timesteps × n_channels).
    Returns a flat dict: {"rms_ch0": ..., "kurt_ch1": ..., ...}
    """
    row = {}
    n_steps, n_ch = window.shape

    for ch_idx in range(n_ch):
        ch_name = channel_names[ch_idx]
        x = window[:, ch_idx].astype(np.float64)
        sigma = np.std(x) + 1e-12
        mu    = np.mean(x)

        for feat in feature_list:
            if feat == "rms":
                row[f"rms_{ch_name}"] = float(np.sqrt(np.mean(x ** 2)))

            elif feat == "kurtosis":
                row[f"kurt_{ch_name}"] = float(np.mean(((x - mu) / sigma) ** 4) - 3.0)

            elif feat == "skewness":
                row[f"skew_{ch_name}"] = float(np.mean(((x - mu) / sigma) ** 3))

            elif feat == "crest_factor":
                rms_val = float(np.sqrt(np.mean(x ** 2))) + 1e-12
                row[f"crest_{ch_name}"] = float(np.max(np.abs(x)) / rms_val)

            elif feat == "peak_to_peak":
                row[f"p2p_{ch_name}"] = float(np.max(x) - np.min(x))

            elif feat == "shape_factor":
                rms_val = float(np.sqrt(np.mean(x ** 2))) + 1e-12
                mean_abs = np.mean(np.abs(x)) + 1e-12
                row[f"shape_{ch_name}"] = float(rms_val / mean_abs)

            elif feat == "variance":
                row[f"var_{ch_name}"] = float(np.var(x))

            elif feat == "mean_abs":
                row[f"mabs_{ch_name}"] = float(np.mean(np.abs(x)))

    return row


def _compute_cross_channel_features(window: np.ndarray,
                                     channel_names: List[str]) -> dict:
    """
    Pairwise correlation between channels in a window.
    Correlation dropping away from 1.0 can indicate coupling breakdown (fault signature).
    """
    row = {}
    n_steps, n_ch = window.shape
    if n_ch < 2:
        return row

    for i, j in combinations(range(n_ch), 2):
        x_i = window[:, i]
        x_j = window[:, j]
        # Pearson correlation — robust even for short windows
        corr_matrix = np.corrcoef(x_i, x_j)
        corr = corr_matrix[0, 1]
        if np.isnan(corr):
            corr = 0.0
        row[f"corr_{channel_names[i]}_{channel_names[j]}"] = float(corr)

    # Trace of rolling covariance matrix (captures total multivariate variance)
    cov = np.cov(window.T)
    row["cov_trace"] = float(np.trace(cov)) if cov.ndim == 2 else float(cov)

    return row



# Rolling window feature extraction over a time-series DataFrame


def extract_rolling_features(df: pd.DataFrame,
                              window_size: int = 30,
                              overlap: float = 0.5,
                              feature_list: Optional[List[str]] = None,
                              include_cross_channel: bool = True,
                              channel_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Sliding-window feature extraction over a preprocessed snapshot DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Time-indexed DataFrame of per-snapshot statistics (rms_ch0, kurt_ch0, ...).
        Each ROW is one snapshot (one second of data, already summarized).
        This is the output of preprocessing.load_ims_run().

    window_size : int
        Number of snapshots per feature-extraction window.
        e.g. window_size=30 on 10-min resampled data = 5 hours per window

    overlap : float
        Fraction of overlap between consecutive windows (0 = no overlap, 0.9 = 90%).

    feature_list : list of str
        Which statistical features to compute.
        Options: "rms", "kurtosis", "skewness", "crest_factor",
                 "peak_to_peak", "shape_factor", "variance"

    include_cross_channel : bool
        Whether to include pairwise correlation features.

    channel_cols : list of str, optional
        Which columns to treat as channels. If None, uses all numeric columns
        that start with "rms_ch" (the primary health indicator per channel).

    Returns
    -------
    pd.DataFrame
        Feature matrix indexed by window center timestamp.
        Shape: (n_windows, n_features)
    """
    if feature_list is None:
        feature_list = ["rms", "kurtosis", "crest_factor", "skewness",
                        "peak_to_peak", "shape_factor", "variance"]

    # Determine which columns to build windows from
    if channel_cols is None:
        # Use the pre-computed per-snapshot stats as the "signal"
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        channel_cols = [c for c in numeric_cols if c != "hours_to_failure"]

    # Build a short name for each channel column
    channel_names = [c.replace("_", "").replace("ch", "ch") for c in channel_cols]

    values = df[channel_cols].values   # shape: (n_snapshots, n_channel_cols)
    timestamps = df.index

    step = max(1, int(window_size * (1.0 - overlap)))
    n_windows = (len(values) - window_size) // step + 1

    if n_windows <= 0:
        raise ValueError(
            f"Not enough data: {len(values)} rows with window_size={window_size}. "
            "Try reducing window_size or using a longer run."
        )

    records = []
    window_timestamps = []

    for w in range(n_windows):
        start = w * step
        end   = start + window_size
        window = values[start:end, :]                   # (window_size, n_cols)
        center_ts = timestamps[start + window_size // 2]

        row = _compute_window_features(window, feature_list, channel_names)

        if include_cross_channel and values.shape[1] > 1:
            cross = _compute_cross_channel_features(window, channel_names)
            row.update(cross)

        records.append(row)
        window_timestamps.append(center_ts)

    feat_df = pd.DataFrame(records, index=pd.DatetimeIndex(window_timestamps))

    # Preserve hours_to_failure if present
    if "hours_to_failure" in df.columns:
        # Map each window center to the nearest hours_to_failure
        htf = df["hours_to_failure"].reindex(feat_df.index, method="nearest")
        feat_df["hours_to_failure"] = htf.values

    logger.info(
        f"Feature extraction: {n_windows} windows × {feat_df.shape[1]} features "
        f"(window_size={window_size}, overlap={overlap})"
    )

    return feat_df



# Build design matrix for model training


def build_feature_matrix(feat_df: pd.DataFrame,
                          exclude_cols: Optional[List[str]] = None) -> tuple:
    """
    Extract the numeric feature matrix X and corresponding timestamps.

    Parameters
    ----------
    feat_df : pd.DataFrame
        Output of extract_rolling_features().
    exclude_cols : list, optional
        Columns to exclude from X (e.g. ["hours_to_failure"]).

    Returns
    -------
    X : np.ndarray, shape (n_windows, n_features)
    feature_names : list of str
    timestamps : pd.DatetimeIndex
    """
    if exclude_cols is None:
        exclude_cols = ["hours_to_failure"]

    feature_names = [c for c in feat_df.columns if c not in exclude_cols]
    X = feat_df[feature_names].values.astype(np.float64)

    # Replace any remaining NaN/inf with column mean (shouldn't happen after preprocessing)
    col_means = np.nanmean(X, axis=0)
    nan_mask = ~np.isfinite(X)
    X[nan_mask] = np.take(col_means, np.where(nan_mask)[1])

    return X, feature_names, feat_df.index


def get_feature_subset(X: np.ndarray,
                       feature_names: List[str],
                       prefix: str) -> tuple:
    """
    Filter features by name prefix for ablation studies.

    Example:
        X_rms, names_rms = get_feature_subset(X, feature_names, "rms")
        X_kurt, names_kurt = get_feature_subset(X, feature_names, "kurt")
    """
    mask = [i for i, name in enumerate(feature_names) if name.startswith(prefix)]
    return X[:, mask], [feature_names[i] for i in mask]



# Feature ablation helper


FEATURE_GROUPS = {
    "rms_only":        ["rms"],
    "kurtosis_only":   ["kurtosis"],
    "time_domain":     ["rms", "kurtosis", "skewness", "crest_factor",
                        "peak_to_peak", "shape_factor", "variance"],
    "health_core":     ["rms", "kurtosis", "crest_factor"],
    "all":             ["rms", "kurtosis", "skewness", "crest_factor",
                        "peak_to_peak", "shape_factor", "variance"],
}


def build_ablation_matrices(df: pd.DataFrame,
                             window_size: int = 30,
                             overlap: float = 0.5) -> dict:
    """
    Build one feature matrix per ablation group.
    Returns dict: {"rms_only": (X, names, ts), "all": (X, names, ts), ...}
    """
    results = {}
    for group_name, feat_list in FEATURE_GROUPS.items():
        feat_df = extract_rolling_features(
            df,
            window_size=window_size,
            overlap=overlap,
            feature_list=feat_list,
            include_cross_channel=(group_name == "all"),
        )
        X, names, ts = build_feature_matrix(feat_df)
        results[group_name] = (X, names, ts)
        logger.info(f"  Ablation group '{group_name}': X shape = {X.shape}")

    return results

def extract_multiscale_features(df,
                                 window_sizes,
                                 overlap=0.5,
                                 feature_list=None,
                                 channel_cols=None):
    """
    Multi-scale feature fusion (C2 contribution).

    Runs extract_rolling_features() at each window size, aligns all outputs
    to the coarsest window time grid, and concatenates column-wise.
    Each feature column is suffixed with its window size to avoid collisions:
    e.g. rms_LPCDEXVib_w30, rms_LPCDEXVib_w180.

    Why multi-scale: small W captures transient spikes, large W captures slow
    drift trends. Neither alone is sufficient for bearing degradation detection.

    Alignment: finer-scale frames are reindexed to the coarse grid via
    nearest-neighbour with 5-minute tolerance, so the fused matrix has the
    same row count as the coarsest-scale extraction.

    Parameters
    ----------
    df           : time-indexed DataFrame (output of load_ongc_run or load_ims_run)
    window_sizes : list[int] e.g. [30, 60, 180] for ONGC or [5, 10, 30] for IMS
    overlap      : window overlap fraction (default 0.5)
    feature_list : list[str] features to compute (default: rms, kurtosis, crest_factor)
    channel_cols : list[str] columns to use as signal channels (default: all numeric)

    Returns
    -------
    pd.DataFrame  — fused feature matrix indexed by coarse-window center timestamps.
    Shape: (n_windows_coarsest, n_features_per_scale * n_scales [+ hours_to_failure])
    """
    if feature_list is None:
        feature_list = ["rms", "kurtosis", "crest_factor"]

    scale_dfs = []
    for W in window_sizes:
        feat_df = extract_rolling_features(
            df,
            window_size=W,
            overlap=overlap,
            feature_list=feature_list,
            include_cross_channel=False,
            channel_cols=channel_cols,
        )
        if "hours_to_failure" in feat_df.columns:
            feat_df = feat_df.drop(columns=["hours_to_failure"])
        feat_df = feat_df.add_suffix(f"_w{W}")
        scale_dfs.append((W, feat_df))

    # Coarsest scale = last entry (largest W) — used as reference grid
    _, coarsest_df = scale_dfs[-1]
    coarse_index   = coarsest_df.index

    aligned = [coarsest_df]
    for W, feat_df in scale_dfs[:-1]:
        reindexed = feat_df.reindex(
            coarse_index,
            method="nearest",
            tolerance=pd.Timedelta("5min"),
        )
        aligned.append(reindexed)

    fused = pd.concat(aligned, axis=1)

    # Re-attach hours_to_failure if present in original df
    if "hours_to_failure" in df.columns:
        htf = df["hours_to_failure"].reindex(fused.index, method="nearest")
        fused["hours_to_failure"] = htf.values

    logger.info(
        f"Multi-scale fusion: W={window_sizes} -> "
        f"{fused.shape[0]} windows x {fused.shape[1]} features"
    )
    return fused