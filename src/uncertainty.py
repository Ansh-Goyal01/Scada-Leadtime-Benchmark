# src/uncertainty.py
"""
Uncertainty estimation and explainability.

Two uncertainty methods:
  1. Bootstrap Ensemble   — model-agnostic, gives CI on anomaly scores
  2. Conformal Detector   — distribution-free, guarantees FAR ≤ α

Explainability:
  - SHAP TreeExplainer for Isolation Forest
  - Feature importance from score variance across bootstrap
"""

import numpy as np
import pandas as pd
import logging
import os
from typing import Optional, List
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)



# Bootstrap Ensemble


class BootstrapEnsemble:
    """
    Trains N versions of a base detector on bootstrap samples.
    At inference, produces mean score + confidence interval.

    Usage:
        ensemble = BootstrapEnsemble(base_cls=IsolationForestDetector,
                                     base_kwargs={"n_estimators": 100},
                                     n_bootstraps=30)
        ensemble.fit(X_train)
        mean_score, lower, upper = ensemble.score_with_ci(X_test, alpha=0.10)
    """

    def __init__(self, base_cls, base_kwargs: dict = None,
                 n_bootstraps: int = 30, random_state: int = 42):
        self.base_cls = base_cls
        self.base_kwargs = base_kwargs or {}
        self.n_bootstraps = n_bootstraps
        self.random_state = random_state
        self._models = []

    def fit(self, X: np.ndarray) -> "BootstrapEnsemble":
        """Train N models on bootstrap resamples of X."""
        self._models = []
        rng = np.random.RandomState(self.random_state)
        n = len(X)

        logger.info(f"Bootstrap ensemble: fitting {self.n_bootstraps} models ...")
        for i in range(self.n_bootstraps):
            idx = rng.choice(n, size=n, replace=True)
            X_boot = X[idx]
            model = self.base_cls(**self.base_kwargs)
            model.fit(X_boot)
            self._models.append(model)

        logger.info("Bootstrap ensemble fitting complete.")
        return self

    def score_all(self, X: np.ndarray) -> np.ndarray:
        """
        Score X with all models.
        Returns array of shape (n_bootstraps, n_samples).
        """
        if not self._models:
            raise RuntimeError("Call fit() before score_all().")
        all_scores = np.stack([m.score(X) for m in self._models], axis=0)
        return all_scores

    def score_with_ci(self, X: np.ndarray,
                      alpha: float = 0.10) -> tuple:
        """
        Returns (mean_score, lower_ci, upper_ci).
        CI is at the (alpha/2, 1-alpha/2) percentile level.
        """
        all_scores = self.score_all(X)  # (n_bootstraps, n_samples)
        lo_pct = alpha / 2 * 100
        hi_pct = (1 - alpha / 2) * 100

        mean_score = np.mean(all_scores, axis=0)
        lower_ci   = np.percentile(all_scores, lo_pct, axis=0)
        upper_ci   = np.percentile(all_scores, hi_pct, axis=0)
        return mean_score, lower_ci, upper_ci

    @property
    def name(self) -> str:
        return f"Bootstrap-{self.base_cls.__name__}(n={self.n_bootstraps})"



# Conformal Anomaly Detector


class ConformalDetector:
    """
    Distribution-free anomaly detector with guaranteed false alarm control.

    Theory:
      Train a base detector on X_train (normal).
      Compute non-conformity scores on a calibration set X_cal (also normal).
      At test time, compute p-value:
          p_value(x_t) = |{x_cal : score(x_cal) >= score(x_t)}| / |X_cal|
      Alert when p_value(x_t) < alpha.

    Guarantee: if data is exchangeable (i.i.d. approximately), FAR ≤ alpha.

    Reference: Vovk et al. "Algorithmic Learning in a Random World", 2005.
    """

    def __init__(self, base_detector, alpha: float = 0.05):
        self.base_detector = base_detector
        self.alpha = alpha
        self._cal_scores = None

    def calibrate(self, X_train: np.ndarray, X_cal: np.ndarray) -> "ConformalDetector":
        """
        Fit base detector on X_train, store calibration scores from X_cal.
        Both X_train and X_cal should contain only NORMAL data.
        """
        self.base_detector.fit(X_train)
        self._cal_scores = self.base_detector.score(X_cal)
        logger.info(
            f"Conformal calibration: {len(self._cal_scores)} calibration scores. "
            f"α={self.alpha}"
        )
        return self

    def predict_pvalue(self, X_test: np.ndarray) -> np.ndarray:
        """
        Compute p-values for each test point.
        p_value near 0 = anomalous (does not conform with calibration set).
        """
        if self._cal_scores is None:
            raise RuntimeError("Call calibrate() before predict_pvalue().")

        test_scores = self.base_detector.score(X_test)
        n_cal = len(self._cal_scores)
        p_values = np.zeros(len(test_scores))

        for i, s in enumerate(test_scores):
            # Fraction of calibration scores that are >= this test score
            p_values[i] = float(np.sum(self._cal_scores >= s)) / (n_cal + 1)

        return p_values

    def alarm(self, X_test: np.ndarray,
              persistence: int = 3) -> tuple:
        """
        Generate alarm signal: True where p_value < alpha (sustained).

        Returns (alarm_signal, p_values, anomaly_scores)
        """
        from src.thresholds import apply_persistence_filter

        p_values = self.predict_pvalue(X_test)
        raw_alarm = p_values < self.alpha
        alarm_signal = apply_persistence_filter(raw_alarm, n_confirm=persistence)

        scores = self.base_detector.score(X_test)
        return alarm_signal, p_values, scores

    @property
    def name(self) -> str:
        return f"Conformal-{self.base_detector.name} (α={self.alpha})"

    @property
    def short_name(self) -> str:
        return "conformal_if"


# SHAP Explainability

def compute_shap_values(if_detector,
                        X: np.ndarray,
                        feature_names: List[str],
                        max_samples: int = 200) -> np.ndarray:
    """
    Compute SHAP values for Isolation Forest using TreeExplainer.

    Parameters
    ----------
    if_detector : IsolationForestDetector
        A fitted IsolationForestDetector (must have .model property).
    X : np.ndarray
        Samples to explain (e.g. windows around alarm time).
    feature_names : list of str
        Names of features (for labeling).
    max_samples : int
        Limit samples for speed (SHAP can be slow on large arrays).

    Returns
    -------
    shap_values : np.ndarray, shape (n_samples, n_features)
    """
    try:
        import shap
    except ImportError:
        raise ImportError("Install SHAP: pip install shap")

    if X.shape[0] > max_samples:
        idx = np.random.choice(X.shape[0], max_samples, replace=False)
        X_explain = X[idx]
    else:
        X_explain = X

    explainer = shap.TreeExplainer(if_detector.model)
    shap_values = explainer.shap_values(X_explain)

    logger.info(f"SHAP values computed: shape={shap_values.shape}")
    return shap_values


def plot_shap_summary(shap_values: np.ndarray,
                      X: np.ndarray,
                      feature_names: List[str],
                      save_path: Optional[str] = None,
                      max_display: int = 15) -> plt.Figure:
    """
    Figure 7 (paper): SHAP beeswarm / summary plot.
    Shows which features most influence the anomaly score.
    """
    try:
        import shap
    except ImportError:
        raise ImportError("Install SHAP: pip install shap")

    fig, ax = plt.subplots(figsize=(9, max(4, max_display * 0.4)))
    shap.summary_plot(
        shap_values, X,
        feature_names=feature_names,
        max_display=max_display,
        show=False,
        plot_size=None,
    )
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved SHAP summary → {save_path}")

    return fig


def plot_shap_waterfall_at_alarm(shap_values: np.ndarray,
                                  X: np.ndarray,
                                  feature_names: List[str],
                                  alarm_window_idx: int = -1,
                                  save_path: Optional[str] = None) -> plt.Figure:
    """
    Figure 7b (paper): SHAP waterfall for the specific window at alarm time.
    Shows exactly which features drove the first alarm.
    """
    try:
        import shap
    except ImportError:
        raise ImportError("Install SHAP: pip install shap")

    sv = shap_values[alarm_window_idx]     # (n_features,)
    x  = X[alarm_window_idx]

    # Sort by absolute contribution
    order = np.argsort(np.abs(sv))[::-1]
    sv_sorted = sv[order]
    names_sorted = [feature_names[i] for i in order]
    x_sorted   = x[order]

    fig, ax = plt.subplots(figsize=(9, max(4, len(names_sorted[:15]) * 0.45)))
    colors = ["#D32F2F" if v > 0 else "#1976D2" for v in sv_sorted[:15]]
    bars = ax.barh(names_sorted[:15][::-1], sv_sorted[:15][::-1],
                   color=colors[::-1], edgecolor="white")

    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("SHAP Value (contribution to anomaly score)", fontsize=10)
    ax.set_title("Feature Contribution at Alarm Time", fontsize=12, fontweight="bold")

    # Annotate with feature values
    for bar, val in zip(bars, sv_sorted[:15][::-1]):
        ax.text(bar.get_width() + 0.001,
                bar.get_y() + bar.get_height() / 2,
                f"{val:+.4f}", va="center", fontsize=8)

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved SHAP waterfall → {save_path}")

    return fig



# Calibration Curve (Figure 8)


def plot_calibration_curve(conformal_detector: ConformalDetector,
                           X_test_normal: np.ndarray,
                           alpha_range: list = None,
                           save_path: Optional[str] = None) -> plt.Figure:
    """
    Figure 8 (paper): Calibration curve for conformal detector.
    X-axis: target alpha (claimed FAR)
    Y-axis: actual FAR on normal test data

    A well-calibrated detector should lie on or below the diagonal.
    """
    if alpha_range is None:
        alpha_range = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20]

    p_values = conformal_detector.predict_pvalue(X_test_normal)
    actual_fars = []

    for alpha in alpha_range:
        actual_far = float(np.mean(p_values < alpha))
        actual_fars.append(actual_far)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, max(alpha_range)], [0, max(alpha_range)],
            "k--", linewidth=1.2, label="Perfect calibration")
    ax.plot(alpha_range, actual_fars,
            "o-", color="#1976D2", linewidth=2, markersize=8,
            label="Conformal detector")

    ax.fill_between(alpha_range, alpha_range, actual_fars,
                    alpha=0.15, color="#1976D2")

    ax.set_xlabel("Target FAR (α)", fontsize=11)
    ax.set_ylabel("Actual FAR on normal data", fontsize=11)
    ax.set_title("Conformal Calibration Curve", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved calibration curve → {save_path}")

    return fig



# Score Uncertainty Plot


def plot_score_with_uncertainty(timestamps: pd.DatetimeIndex,
                                 mean_score: np.ndarray,
                                 lower_ci: np.ndarray,
                                 upper_ci: np.ndarray,
                                 threshold: float,
                                 failure_time: Optional[str] = None,
                                 method_name: str = "Bootstrap Ensemble",
                                 save_path: Optional[str] = None,
                                 figsize: tuple = (13, 4)) -> plt.Figure:
    """
    Plot anomaly score with confidence interval band.
    Demonstrates that uncertainty-aware alarms are more trustworthy.
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.fill_between(timestamps, lower_ci, upper_ci,
                    alpha=0.25, color="#1976D2", label="90% CI")
    ax.plot(timestamps, mean_score,
            color="#1976D2", linewidth=1.5, label="Mean Score")
    ax.axhline(threshold, color="#D32F2F", linewidth=1.5, linestyle="--",
               label=f"Threshold ({threshold:.3f})")

    if failure_time:
        t_fail = pd.Timestamp(failure_time)
        ax.axvline(t_fail, color="#B71C1C", linewidth=2.5, linestyle="-",
                   label="Failure")

    ax.set_xlabel("Time", fontsize=11)
    ax.set_ylabel("Anomaly Score", fontsize=11)
    ax.set_title(f"{method_name} — Score with Uncertainty Bands",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, loc="upper left")
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved uncertainty plot → {save_path}")

    return fig