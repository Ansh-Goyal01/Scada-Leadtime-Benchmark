# src/baselines_extra.py
"""
Extra baseline detectors — added to address reviewer weakness W (baseline
selection). These complement the detectors in src/models.py and follow the exact
same BaseDetector contract (fit -> self, score -> np.ndarray with higher = more
anomalous, plus `name` / `short_name` properties).

Three detectors are provided:

  1. RMSTrendDetector       — the "naive RMS > kσ" health-index baseline. The
                              simplest transparent reference a SCADA operator
                              would reach for.
  2. SpectralKurtosisDetector — a spectral-kurtosis alarm that watches the
                              'sk_'-prefixed spectral features (see
                              src/spectral_features.py). Most meaningful when
                              those features are present in X.
  3. DeepSVDDDetector       — Deep Support Vector Data Description (Ruff et al.,
                              ICML 2018). A one-class deep model: an MLP encoder
                              f(x)->z, objective min ||f(x) - c||² where c is the
                              fixed mean latent of an initial forward pass.
                              Anomaly score = squared distance to the center c.
                              PyTorch is imported LAZILY (optional dependency),
                              mirroring LSTMAEDetector in src/models.py.

All scores are mapped to [0, 1] via BaseDetector._normalize_scores where that is
sensible, so thresholds stay comparable across the benchmark.
"""

import numpy as np
import logging

from src.models import BaseDetector

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 1. RMS-Trend (naive kσ health-index baseline)
# ──────────────────────────────────────────────────────────────────────────────
class RMSTrendDetector(BaseDetector):
    """
    The simplest possible health-index baseline — the "naive RMS > kσ" rule the
    reviewer asked for.

    Health index per sample = mean across features (the average standardized
    magnitude of the feature vector). The training mean/std of that index are
    stored at fit time. The anomaly score is the one-sided, upper standardized
    exceedance:

        score_raw = max(0, (health - mu_train) / sigma_train)

    Only *increases* in the health index count (one-sided): degradation raises
    vibration energy, so a drop below baseline is not an anomaly here. The raw
    z-exceedance is then min-max normalized to [0, 1] for comparability with the
    other detectors; the natural alarm level (n_sigma) is retained as `n_sigma`
    for any caller that wants a pre-normalization threshold.

    Deliberately minimal and fully transparent — no covariance, no PCA, no
    learning. This is the floor that more sophisticated detectors must beat.
    """

    def __init__(self, n_sigma: float = 3.0):
        self.n_sigma = n_sigma
        self._mu = None       # training mean of the health index
        self._sigma = None    # training std of the health index

    @property
    def name(self):
        return "RMS-Trend (kσ)"

    @property
    def short_name(self):
        return "rms_trend"

    @staticmethod
    def _health_index(X: np.ndarray) -> np.ndarray:
        """Univariate health index: mean across features per sample."""
        return np.mean(X, axis=1)

    def fit(self, X: np.ndarray) -> "RMSTrendDetector":
        h = self._health_index(X)
        self._mu = float(np.mean(h))
        self._sigma = float(np.std(h)) + 1e-12
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._mu is None:
            raise RuntimeError("Call fit() before score().")
        h = self._health_index(X)
        # One-sided upper exceedance in sigma units (only increases matter).
        z = (h - self._mu) / self._sigma
        raw = np.clip(z, 0.0, None)
        return self._normalize_scores(raw)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Spectral-Kurtosis Alarm
# ──────────────────────────────────────────────────────────────────────────────
class SpectralKurtosisDetector(BaseDetector):
    """
    Spectral-kurtosis alarm.

    Spectral kurtosis is a classic bearing-fault sensitive statistic: it spikes
    when impulsive, non-stationary energy (characteristic of incipient bearing
    defects) appears in the signal. This detector monitors the 'sk_'-prefixed
    spectral-kurtosis features produced by src/spectral_features.py.

    Column selection:
      * If `feature_names` is given, the columns whose name *contains* `key`
        (default "sk_") are selected. This is the intended path.
      * If `feature_names` is given but no column matches `key`, the detector
        falls back to ALL columns and logs a warning — it stays functional but is
        no longer a pure spectral alarm.
      * If `feature_names` is None, ALL columns are used.

    Health index per sample = MAX over the selected columns (worst spectral-
    kurtosis channel). Training mean/std of that index are stored at fit time.
    The score is the one-sided upper standardized exceedance, min-max normalized
    to [0, 1].

    NOTE: this detector is most meaningful when spectral-kurtosis features are
    actually present in X. On a purely time-domain feature matrix it degrades to
    a "max-feature kσ" alarm (and the fallback warning will fire).
    """

    def __init__(self, feature_names=None, key: str = "sk_", n_sigma: float = 3.0):
        self.feature_names = feature_names
        self.key = key
        self.n_sigma = n_sigma
        self._cols = None     # selected column indices
        self._mu = None
        self._sigma = None

    @property
    def name(self):
        return "Spectral-Kurtosis Alarm"

    @property
    def short_name(self):
        return "spectral_kurtosis"

    def _resolve_columns(self, n_features: int):
        """Pick the columns this detector monitors, given the feature count."""
        if self.feature_names is not None:
            names = list(self.feature_names)
            cols = [i for i, nm in enumerate(names) if self.key in str(nm)]
            if cols:
                return np.asarray(cols, dtype=int)
            logger.warning(
                "SpectralKurtosisDetector: no feature name contains key '%s' — "
                "falling back to ALL %d columns (no longer a pure spectral alarm).",
                self.key, n_features,
            )
        # No names provided, or none matched → use everything.
        return np.arange(n_features, dtype=int)

    def _health_index(self, X: np.ndarray) -> np.ndarray:
        """Worst (max) value over the selected spectral columns, per sample."""
        return np.max(X[:, self._cols], axis=1)

    def fit(self, X: np.ndarray) -> "SpectralKurtosisDetector":
        self._cols = self._resolve_columns(X.shape[1])
        h = self._health_index(X)
        self._mu = float(np.mean(h))
        self._sigma = float(np.std(h)) + 1e-12
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._mu is None:
            raise RuntimeError("Call fit() before score().")
        h = self._health_index(X)
        # One-sided upper standardized exceedance (impulsive energy → high SK).
        z = (h - self._mu) / self._sigma
        raw = np.clip(z, 0.0, None)
        return self._normalize_scores(raw)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Deep SVDD (Ruff et al., ICML 2018) — optional PyTorch dependency
# ──────────────────────────────────────────────────────────────────────────────
class DeepSVDDDetector(BaseDetector):
    """
    Deep Support Vector Data Description (Deep SVDD).

    One-class deep model. An MLP encoder f(x) -> z maps each sample into a small
    latent space. The center c is fixed as the mean latent of an initial forward
    pass over the (untrained) network on the training data; training then
    minimizes the mean squared distance of the latents to that center:

        L = (1/N) Σ_i ||f(x_i) - c||²

    so normal data collapses toward c. At test time the anomaly score is the
    squared distance to the center, ||f(x) - c||², which is large for points the
    encoder cannot pull in — i.e. anomalies. Reference: Ruff et al., "Deep
    One-Class Classification", ICML 2018.

    PyTorch is an OPTIONAL dependency and is imported lazily inside fit() (the
    same pattern LSTMAEDetector uses in src/models.py). If torch is missing, a
    clear ImportError with an install hint is raised. CPU-friendly defaults keep
    epochs small.
    """

    def __init__(self,
                 hidden_dim: int = 32,
                 latent_dim: int = 8,
                 epochs: int = 40,
                 batch_size: int = 32,
                 learning_rate: float = 1e-3,
                 random_state: int = 42,
                 device: str = "auto"):
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.random_state = random_state
        self._model = None
        self._center = None        # torch tensor c (fixed after init)
        self._n_features = None

        if device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device

    @property
    def name(self):
        return "Deep SVDD"

    @property
    def short_name(self):
        return "deep_svdd"

    def _build_encoder(self, n_features: int):
        """Build the MLP encoder. Imports torch.nn lazily."""
        import torch.nn as nn

        # Bias-free linear layers are standard in Deep SVDD: a bias term would let
        # the network trivially map everything onto the center, collapsing the
        # objective. Ruff et al. drop biases for exactly this reason.
        return nn.Sequential(
            nn.Linear(n_features, self.hidden_dim, bias=False),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.latent_dim, bias=False),
        )

    def fit(self, X: np.ndarray) -> "DeepSVDDDetector":
        try:
            import torch
            import torch.nn as nn  # noqa: F401  (used indirectly via _build_encoder)
            from torch.utils.data import DataLoader, TensorDataset
        except ImportError:
            raise ImportError(
                "PyTorch is required for DeepSVDDDetector. "
                "Install with: pip install torch"
            )

        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        self._n_features = X.shape[1]
        X_t = torch.FloatTensor(np.asarray(X, dtype=np.float32))

        self._model = self._build_encoder(self._n_features).to(self.device)

        # Center c = mean latent of an initial forward pass (network as-initialized).
        self._model.eval()
        with torch.no_grad():
            z0 = self._model(X_t.to(self.device))
            c = z0.mean(dim=0)
            # Guard against a near-zero center coordinate, which can drive a
            # degenerate solution (standard Deep SVDD epsilon nudge).
            eps = 1e-6
            c[(abs(c) < eps) & (c < 0)] = -eps
            c[(abs(c) < eps) & (c >= 0)] = eps
            self._center = c

        loader = DataLoader(
            TensorDataset(X_t),
            batch_size=self.batch_size,
            shuffle=True,
        )
        optimizer = torch.optim.Adam(
            self._model.parameters(), lr=self.learning_rate
        )

        self._model.train()
        logger.info(
            "Training Deep SVDD on %s for %d epochs ...", self.device, self.epochs
        )
        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for (batch,) in loader:
                batch = batch.to(self.device)
                z = self._model(batch)
                loss = torch.mean(torch.sum((z - self._center) ** 2, dim=1))
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            if (epoch + 1) % 10 == 0:
                logger.info(
                    "  Epoch [%d/%d] loss: %.6f",
                    epoch + 1, self.epochs, epoch_loss / len(loader),
                )
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Call fit() before score().")
        import torch

        X_t = torch.FloatTensor(np.asarray(X, dtype=np.float32)).to(self.device)
        self._model.eval()
        with torch.no_grad():
            z = self._model(X_t)
            dist = torch.sum((z - self._center) ** 2, dim=1).cpu().numpy()

        # Squared distance to center → higher = more anomalous. Normalize to [0,1].
        return self._normalize_scores(dist)
