# src/lead_time.py
"""
Lead-time computation — the core scientific contribution of this framework.

Formal definitions implemented here:
  FAT  : First Alarm Time — timestamp of first sustained alarm
  VLT  : Valid Lead Time  — hours between FAT and failure (0 if missed/false)
  FAR  : False Alarm Rate — fraction of normal-period windows incorrectly flagged
  MissRate : fraction of test runs with no valid alarm before failure

All evaluation functions follow the same contract so results are directly comparable.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)



# Core Metric Functions


def compute_FAT(alarm_signal: np.ndarray,
                timestamps: pd.DatetimeIndex) -> Optional[pd.Timestamp]:
    """
    First Alarm Time: the timestamp of the first alarm that is sustained
    (first True value in the already-persistence-filtered alarm signal).

    Returns None if no alarm was raised.
    """
    alarm_signal = np.asarray(alarm_signal, dtype=bool)
    alarm_indices = np.where(alarm_signal)[0]
    if len(alarm_indices) == 0:
        return None
    return timestamps[alarm_indices[0]]


def compute_VLT(fat: Optional[pd.Timestamp],
                t_fail: pd.Timestamp,
                t_normal_end: Optional[pd.Timestamp] = None) -> float:
    """
    Valid Lead Time (hours).

    Rules:
      - If FAT is None (no alarm): VLT = 0  (missed failure)
      - If FAT >= t_fail: VLT = 0  (alarm too late)
      - If t_normal_end is given and FAT <= t_normal_end: VLT = 0  (false alarm in normal period)
      - Otherwise: VLT = (t_fail - FAT).total_seconds() / 3600

    A higher VLT is always better.
    """
    if fat is None:
        return 0.0
    if fat >= t_fail:
        return 0.0
    if t_normal_end is not None and fat <= t_normal_end:
        return 0.0   # alarm during normal period = false alarm, not a valid prediction

    vlt_hours = (t_fail - fat).total_seconds() / 3600.0
    return float(vlt_hours)


def compute_FAR(alarm_signal: np.ndarray,
                timestamps: pd.DatetimeIndex,
                normal_period_end: pd.Timestamp) -> float:
    """
    False Alarm Rate: fraction of time steps in the normal period where alarm = True.

    normal_period_end: timestamp marking the end of what we consider "definitely normal".
    Typically set to the first 20% of the test window.

    Returns float in [0, 1].
    """
    alarm_signal = np.asarray(alarm_signal, dtype=bool)
    normal_mask = timestamps <= normal_period_end
    n_normal = normal_mask.sum()
    if n_normal == 0:
        return 0.0
    n_false_alarms = alarm_signal[normal_mask].sum()
    return float(n_false_alarms) / float(n_normal)


def compute_detection_delay(fat: Optional[pd.Timestamp],
                            t_degradation_onset: pd.Timestamp) -> Optional[float]:
    """
    Detection Delay (hours): how long after degradation began before alarm fired.
    Requires knowledge of the true degradation onset time (from domain expert or RUL label).

    Returns None if FAT is None or FAT is before onset (early alarm).
    """
    if fat is None:
        return None
    delay = (fat - t_degradation_onset).total_seconds() / 3600.0
    return float(delay) if delay >= 0 else None



# Full Evaluation Loop

def evaluate_method(detector,
                    X_train: np.ndarray,
                    X_test: np.ndarray,
                    timestamps_test: pd.DatetimeIndex,
                    failure_time: str,
                    normal_period_fraction: float = 0.20,
                    threshold_strategy: str = "percentile",
                    threshold_percentile: float = 97.5,
                    alarm_persistence: int = 3) -> dict:
    """
    Full pipeline for a single detector on a single test run.

    Steps:
      1. Fit detector on X_train
      2. Score X_test
      3. Compute threshold from training scores
      4. Generate alarm signal
      5. Compute FAT, VLT, FAR

    Returns a result dict with all metrics.
    """
    from src.thresholds import compute_threshold, generate_alarm_signal

    # Fit
    detector.fit(X_train)

    # Score both sets
    scores_train = detector.score(X_train)
    scores_test  = detector.score(X_test)

    # Threshold
    threshold = compute_threshold(
        scores_train,
        strategy=threshold_strategy,
        percentile=threshold_percentile,
    )

    # Alarm
    alarm = generate_alarm_signal(scores_test, threshold, persistence=alarm_persistence)

    # Key timestamps
    t_fail = pd.Timestamp(failure_time)
    n_normal = int(len(timestamps_test) * normal_period_fraction)
    t_normal_end = timestamps_test[min(n_normal, len(timestamps_test) - 1)]

    # Metrics
    fat = compute_FAT(alarm, timestamps_test)
    vlt = compute_VLT(fat, t_fail, t_normal_end)
    far = compute_FAR(alarm, timestamps_test, t_normal_end)

    result = {
        "method":         detector.name,
        "short_name":     detector.short_name,
        "threshold":      threshold,
        "FAT":            fat,
        "VLT_hours":      vlt,
        "FAR_pct":        far * 100.0,
        "alarm_raised":   fat is not None,
        "valid_alarm":    vlt > 0,
        "scores_train":   scores_train,
        "scores_test":    scores_test,
        "alarm_signal":   alarm,
        "timestamps":     timestamps_test,
        "failure_time":   t_fail,
        "normal_end":     t_normal_end,
    }

    logger.info(
        f"[{detector.name}] FAT={fat} | VLT={vlt:.2f}h | "
        f"FAR={far*100:.1f}% | valid={vlt > 0}"
    )

    return result


def evaluate_all_methods(detectors: list,
                         X_train: np.ndarray,
                         X_test: np.ndarray,
                         timestamps_test: pd.DatetimeIndex,
                         failure_time: str,
                         normal_period_fraction: float = 0.20,
                         threshold_strategy: str = "percentile",
                         threshold_percentile: float = 97.5,
                         alarm_persistence: int = 3) -> pd.DataFrame:
    """
    Run evaluate_method() for all detectors, return summary DataFrame.
    """
    rows = []
    all_results = []

    for det in detectors:
        try:
            result = evaluate_method(
                detector=det,
                X_train=X_train,
                X_test=X_test,
                timestamps_test=timestamps_test,
                failure_time=failure_time,
                normal_period_fraction=normal_period_fraction,
                threshold_strategy=threshold_strategy,
                threshold_percentile=threshold_percentile,
                alarm_persistence=alarm_persistence,
            )
            all_results.append(result)
            rows.append({
                "Method":       result["method"],
                "VLT (hours)":  round(result["VLT_hours"], 2),
                "FAR (%)":      round(result["FAR_pct"], 2),
                "Valid Alarm":  result["valid_alarm"],
                "FAT":          result["FAT"],
                "Threshold":    round(result["threshold"], 4),
            })
        except Exception as e:
            logger.error(f"Method {det.name} failed: {e}")

    summary_df = pd.DataFrame(rows).sort_values("VLT (hours)", ascending=False)
    return summary_df, all_results


def compute_miss_rate(all_results: list) -> float:
    """
    Fraction of evaluation runs with no valid alarm before failure.
    """
    if len(all_results) == 0:
        return 1.0
    misses = sum(1 for r in all_results if not r["valid_alarm"])
    return misses / len(all_results)



# Plotting


def plot_alarm_timeline(result: dict,
                        save_path: Optional[str] = None,
                        figsize: tuple = (14, 5)) -> plt.Figure:
    """
    Figure 5 (paper): Anomaly score over time with threshold, alarm, and failure marker.

    Shows:
      - Anomaly score stream (blue line)
      - Threshold (red dashed)
      - Alarm region (red shading)
      - Failure time (vertical red line)
      - Lead time annotation (arrow)
    """
    scores     = result["scores_test"]
    alarm      = result["alarm_signal"]
    timestamps = result["timestamps"]
    t_fail     = result["failure_time"]
    threshold  = result["threshold"]
    fat        = result["FAT"]
    vlt        = result["VLT_hours"]
    method     = result["method"]

    fig, ax = plt.subplots(figsize=figsize)

    # Score stream
    ax.plot(timestamps, scores, color="#1976D2", linewidth=1.2,
            label="Anomaly Score", zorder=3)

    # Threshold line
    ax.axhline(threshold, color="#D32F2F", linewidth=1.5, linestyle="--",
               label=f"Threshold ({threshold:.3f})", zorder=4)

    # Alarm shading
    alarm_mask = alarm.astype(float)
    ax.fill_between(timestamps, 0, scores.max() * 1.05,
                    where=alarm.astype(bool),
                    alpha=0.18, color="#FF5722", label="Alarm Active")

    # Failure time
    ax.axvline(t_fail, color="#B71C1C", linewidth=2.5, linestyle="-",
               label=f"Failure: {t_fail.strftime('%Y-%m-%d %H:%M')}", zorder=5)

    # FAT and lead-time annotation
    if fat is not None and vlt > 0:
        ax.axvline(fat, color="#388E3C", linewidth=2.0, linestyle="-.",
                   label=f"First Alarm: {fat.strftime('%Y-%m-%d %H:%M')}", zorder=5)

        # Arrow annotation for lead time
        score_at_fat = float(np.interp(
            mdates.date2num(fat),
            mdates.date2num(timestamps.to_pydatetime()),
            scores
        ))
        mid_x = fat + pd.Timedelta(seconds=(t_fail - fat).total_seconds() / 2)
        ax.annotate(
            f"Lead Time\n{vlt:.1f} hrs",
            xy=(mid_x, threshold * 1.05),
            fontsize=10,
            ha="center",
            color="#1B5E20",
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#C8E6C9", alpha=0.8),
        )
        # Horizontal bracket
        ax.annotate("", xy=(t_fail, threshold * 1.02), xytext=(fat, threshold * 1.02),
                    arrowprops=dict(arrowstyle="<->", color="#1B5E20", lw=1.5))

    ax.set_title(f"{method} — Anomaly Score Timeline", fontsize=13, fontweight="bold")
    ax.set_xlabel("Time", fontsize=11)
    ax.set_ylabel("Anomaly Score", fontsize=11)
    ax.legend(loc="upper left", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved alarm timeline → {save_path}")

    return fig


def plot_lead_time_comparison(summary_df: pd.DataFrame,
                               save_path: Optional[str] = None,
                               figsize: tuple = (10, 5)) -> plt.Figure:
    """
    Figure 4 (paper): Bar chart of Valid Lead Time per method.
    Color-codes bars by validity.
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Left: VLT bar chart
    ax = axes[0]
    colors = ["#388E3C" if v else "#D32F2F" for v in summary_df["Valid Alarm"]]
    bars = ax.barh(summary_df["Method"], summary_df["VLT (hours)"],
                   color=colors, edgecolor="white", height=0.55)

    for bar, vlt in zip(bars, summary_df["VLT (hours)"]):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{vlt:.1f}h", va="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("Valid Lead Time (hours)", fontsize=11)
    ax.set_title("Lead Time by Method", fontsize=12, fontweight="bold")
    ax.set_xlim(0, summary_df["VLT (hours)"].max() * 1.25)
    ax.axvline(0, color="black", linewidth=0.8)

    # Right: FAR bar chart
    ax2 = axes[1]
    ax2.barh(summary_df["Method"], summary_df["FAR (%)"],
             color="#1976D2", edgecolor="white", height=0.55, alpha=0.8)
    ax2.axvline(5.0, color="#D32F2F", linewidth=1.5, linestyle="--",
                label="5% FAR target")
    ax2.set_xlabel("False Alarm Rate (%)", fontsize=11)
    ax2.set_title("False Alarm Rate by Method", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=9)

    plt.suptitle("Method Comparison: Lead Time vs False Alarm Rate",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved comparison chart → {save_path}")

    return fig


def plot_vlt_vs_far(sweep_df: pd.DataFrame,
                    method_name: str = "Isolation Forest",
                    save_path: Optional[str] = None,
                    figsize: tuple = (8, 5)) -> plt.Figure:
    """
    Figure 3 (paper): Lead-Time vs FAR tradeoff curve.
    This is the key novelty figure — analogous to ROC but for prognostics.
    """
    fig, ax = plt.subplots(figsize=figsize)

    valid = sweep_df[sweep_df["valid_alarm"]]
    invalid = sweep_df[~sweep_df["valid_alarm"]]

    ax.scatter(valid["FAR_pct"], valid["VLT_hours"],
               c="#388E3C", s=80, zorder=5, label="Valid alarm", edgecolors="white")
    ax.scatter(invalid["FAR_pct"], invalid["VLT_hours"],
               c="#D32F2F", s=80, marker="x", zorder=5, label="No valid alarm")

    # Annotate percentile values
    for _, row in sweep_df.iterrows():
        ax.annotate(f"p={row['percentile']:.0f}%",
                    (row["FAR_pct"], row["VLT_hours"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=7.5)

    if len(valid) > 1:
        ax.plot(valid["FAR_pct"], valid["VLT_hours"],
                color="#388E3C", linewidth=1.2, linestyle="--", alpha=0.6)

    ax.axvline(5.0, color="#FF9800", linewidth=1.5, linestyle=":",
               label="5% FAR target")
    ax.set_xlabel("False Alarm Rate (%)", fontsize=11)
    ax.set_ylabel("Valid Lead Time (hours)", fontsize=11)
    ax.set_title(f"Lead-Time vs FAR Tradeoff — {method_name}",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved VLT vs FAR curve → {save_path}")

    return fig


def plot_score_with_rms(result: dict,
                        rms_series: pd.Series,
                        save_path: Optional[str] = None,
                        figsize: tuple = (14, 6)) -> plt.Figure:
    """
    Dual-panel plot: top = raw RMS trend, bottom = anomaly score + alarm.
    Useful as Figure 2 in the paper (shows degradation visually alongside model output).
    """
    scores     = result["scores_test"]
    alarm      = result["alarm_signal"]
    timestamps = result["timestamps"]
    t_fail     = result["failure_time"]
    threshold  = result["threshold"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    # Top: RMS
    common_idx = rms_series.index.intersection(timestamps)
    if len(common_idx) > 0:
        ax1.plot(rms_series.loc[common_idx], color="#FF6F00", linewidth=1.2)
    ax1.axvline(t_fail, color="#B71C1C", linewidth=2, linestyle="--")
    ax1.set_ylabel("RMS Amplitude", fontsize=10)
    ax1.set_title("Raw RMS Signal", fontsize=11)

    # Bottom: Anomaly score
    ax2.plot(timestamps, scores, color="#1976D2", linewidth=1.0, label="Score")
    ax2.axhline(threshold, color="#D32F2F", linewidth=1.5, linestyle="--",
                label=f"Threshold")
    ax2.fill_between(timestamps, 0, scores.max(),
                     where=alarm, alpha=0.2, color="#FF5722", label="Alarm")
    ax2.axvline(t_fail, color="#B71C1C", linewidth=2, linestyle="--", label="Failure")
    ax2.set_ylabel("Anomaly Score", fontsize=10)
    ax2.set_xlabel("Time", fontsize=10)
    ax2.legend(fontsize=8, loc="upper left")

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig