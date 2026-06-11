# src/thresholds.py
"""
Threshold computation, alarm generation, and persistence filtering.

Three threshold strategies:
  1. Percentile  — static, fit on training scores
  2. EWMA        — dynamic, tracks score stream mean/std
  3. EVT         — Extreme Value Theory (Generalized Pareto on tail)

All return a scalar threshold. generate_alarm_signal() applies it with persistence.
"""

import numpy as np
import pandas as pd
import logging
from typing import Union, Optional

logger = logging.getLogger(__name__)



# Threshold Computation


def compute_threshold(scores_train: np.ndarray,
                      strategy: str = "percentile",
                      percentile: float = 97.5,
                      ewma_lambda: float = 0.2,
                      ewma_k: float = 3.0,
                      evt_quantile: float = 0.95) -> float:
    """
    Compute a scalar decision threshold from training-set anomaly scores.

    Parameters
    ----------
    scores_train : np.ndarray
        Anomaly scores on the TRAINING set (normal data only).
    strategy : str
        "percentile" | "ewma" | "evt"
    percentile : float
        Used when strategy="percentile". e.g. 97.5 → 97.5th percentile.
    ewma_lambda : float
        EWMA smoothing parameter (used for strategy="ewma").
    ewma_k : float
        Number of std devs above EWMA mean (used for strategy="ewma").
    evt_quantile : float
        Tail quantile for GPD fitting (used for strategy="evt").

    Returns
    -------
    float : scalar threshold
    """
    scores_train = np.asarray(scores_train, dtype=np.float64)
    scores_train = scores_train[np.isfinite(scores_train)]

    if strategy == "percentile":
        threshold = float(np.percentile(scores_train, percentile))

    elif strategy == "ewma":
        # Compute EWMA of training scores, use its UCL as threshold
        ewma = _compute_ewma(scores_train, lambda_=ewma_lambda)
        mu_ewma    = float(np.mean(ewma))
        sigma_ewma = float(np.std(ewma)) + 1e-12
        ucl_factor = np.sqrt(ewma_lambda / (2.0 - ewma_lambda))
        threshold  = mu_ewma + ewma_k * sigma_ewma * ucl_factor

    elif strategy == "evt":
        # Extreme Value Theory: fit Generalized Pareto Distribution to tail
        threshold = _evt_threshold(scores_train, tail_quantile=evt_quantile)

    else:
        raise ValueError(f"Unknown threshold strategy: '{strategy}'. "
                         "Choose 'percentile', 'ewma', or 'evt'.")

    logger.info(f"Threshold [{strategy}]: {threshold:.6f}")
    return threshold


def _compute_ewma(x: np.ndarray, lambda_: float = 0.2) -> np.ndarray:
    """Apply EWMA smoothing to a 1D array."""
    ewma = np.zeros_like(x)
    ewma[0] = x[0]
    for t in range(1, len(x)):
        ewma[t] = lambda_ * x[t] + (1 - lambda_) * ewma[t - 1]
    return ewma


def _evt_threshold(scores: np.ndarray, tail_quantile: float = 0.95) -> float:
    """
    Fit a Generalized Pareto Distribution (GPD) to the tail of the score distribution.
    Returns the 99th percentile of the GPD fit as the anomaly threshold.

    Uses scipy's genpareto if available, falls back to percentile otherwise.
    """
    try:
        from scipy.stats import genpareto
        u = float(np.percentile(scores, tail_quantile * 100))
        tail = scores[scores > u] - u
        if len(tail) < 10:
            logger.warning("EVT: Too few tail samples, falling back to percentile.")
            return float(np.percentile(scores, 99.0))
        c, loc, scale = genpareto.fit(tail, floc=0)
        # Threshold at 99% quantile of GPD
        threshold = u + genpareto.ppf(0.99, c, loc=loc, scale=scale)
        return float(threshold)
    except Exception as e:
        logger.warning(f"EVT fitting failed ({e}), falling back to 99th percentile.")
        return float(np.percentile(scores, 99.0))



# Alarm Signal Generation


def generate_alarm_signal(scores: np.ndarray,
                          threshold: float,
                          persistence: int = 3) -> np.ndarray:
    """
    Convert a score stream into a binary alarm signal with persistence filtering.

    Persistence filter: an alarm is raised at time t only if scores[t:t+persistence]
    are ALL above the threshold. This eliminates single-point false alarms.

    Parameters
    ----------
    scores : np.ndarray, shape (n,)
    threshold : float
    persistence : int
        Number of consecutive windows that must exceed threshold before alarm fires.

    Returns
    -------
    np.ndarray of bool, shape (n,) — True where alarm is active.
    """
    scores = np.asarray(scores, dtype=np.float64)
    n = len(scores)
    raw_alarm = scores > threshold            # (n,) bool

    if persistence <= 1:
        return raw_alarm

    # Apply persistence: alarm only if a run of `persistence` consecutive hits exists
    alarm = np.zeros(n, dtype=bool)
    for t in range(n - persistence + 1):
        if np.all(raw_alarm[t:t + persistence]):
            alarm[t:t + persistence] = True

    return alarm


def apply_persistence_filter(alarm_raw: np.ndarray,
                              n_confirm: int = 3) -> np.ndarray:
    """
    Post-hoc persistence filter on an already-computed binary alarm array.
    Clears isolated alarm bursts shorter than n_confirm steps.
    """
    alarm_raw = np.asarray(alarm_raw, dtype=bool)
    filtered  = np.zeros_like(alarm_raw)
    n = len(alarm_raw)

    i = 0
    while i < n:
        if alarm_raw[i]:
            # Find run length
            j = i
            while j < n and alarm_raw[j]:
                j += 1
            run_len = j - i
            if run_len >= n_confirm:
                filtered[i:j] = True
            i = j
        else:
            i += 1

    return filtered



# Threshold Sensitivity Sweep (for Experiment 2 / Figure 3)


def threshold_sweep(scores_train: np.ndarray,
                    scores_test: np.ndarray,
                    timestamps_test: pd.DatetimeIndex,
                    failure_time: str,
                    normal_period_end: str,
                    percentile_range: list = None,
                    persistence: int = 3) -> pd.DataFrame:
    """
    Sweep over a range of threshold percentiles.
    For each, compute: threshold, FAT, VLT, FAR.

    Returns a DataFrame with one row per percentile value.
    Used to generate the Lead-Time vs FAR curve (key novelty figure).
    """
    from src.lead_time import compute_VLT, compute_FAT, compute_FAR

    if percentile_range is None:
        percentile_range = [80, 85, 90, 92.5, 95, 97.5, 99, 99.5]

    t_fail = pd.Timestamp(failure_time)
    t_normal_end = pd.Timestamp(normal_period_end)

    results = []
    for p in percentile_range:
        thresh = compute_threshold(scores_train, strategy="percentile", percentile=p)
        alarm  = generate_alarm_signal(scores_test, thresh, persistence=persistence)

        fat = compute_FAT(alarm, timestamps_test)
        vlt = compute_VLT(fat, t_fail)
        far = compute_FAR(alarm, timestamps_test, t_normal_end)

        results.append({
            "percentile":  p,
            "threshold":   thresh,
            "FAT":         fat,
            "VLT_hours":   vlt,
            "FAR_pct":     far * 100.0,
            "valid_alarm": (fat is not None) and (fat < t_fail),
        })

        logger.info(
            f"  p={p:5.1f}% | thresh={thresh:.4f} | "
            f"VLT={vlt:.2f}h | FAR={far*100:.1f}%"
        )

    return pd.DataFrame(results)



# Dynamic EWMA Threshold (for online / streaming use)


def dynamic_ewma_threshold(scores: np.ndarray,
                           lambda_: float = 0.2,
                           k: float = 3.0,
                           warmup: int = 50) -> np.ndarray:
    """
    Compute a time-varying EWMA threshold for each time step.
    Useful for streaming / online scenarios where a fixed threshold may drift.

    Parameters
    ----------
    scores : np.ndarray
        Full score stream (train + test concatenated).
    lambda_ : float
        EWMA smoothing factor.
    k : float
        UCL multiplier.
    warmup : int
        Number of initial steps to use for baseline estimation.

    Returns
    -------
    thresholds : np.ndarray, same length as scores.
    """
    n = len(scores)
    ewma_mean = np.zeros(n)
    ewma_var  = np.zeros(n)

    # Warmup: estimate mean and variance from first `warmup` points
    mu0    = float(np.mean(scores[:warmup]))
    sigma0 = float(np.std(scores[:warmup])) + 1e-12

    ewma_mean[0] = mu0
    ewma_var[0]  = sigma0 ** 2

    for t in range(1, n):
        ewma_mean[t] = lambda_ * scores[t] + (1 - lambda_) * ewma_mean[t - 1]
        ewma_var[t]  = (lambda_ * (scores[t] - ewma_mean[t]) ** 2
                        + (1 - lambda_) * ewma_var[t - 1])

    ewma_std = np.sqrt(ewma_var) + 1e-12
    ucl_factor = np.sqrt(lambda_ / (2.0 - lambda_))
    thresholds = ewma_mean + k * ewma_std * ucl_factor

    return thresholds