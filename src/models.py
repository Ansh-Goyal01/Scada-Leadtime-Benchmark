# src/models.py
"""
Anomaly detection models — all share a common BaseDetector interface.

Interface contract (all models must implement):
    detector.fit(X_train)             -> self
    detector.score(X)                 -> np.ndarray of anomaly scores (higher = more anomalous)
    detector.name                     -> str (display name)
    detector.short_name               -> str (used for filenames / dict keys)

Scores are normalized to [0, 1] range where possible so thresholds are comparable.
"""

import numpy as np
import logging
from abc import ABC, abstractmethod
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import chi2

logger = logging.getLogger(__name__)



# Abstract Base


class BaseDetector(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def short_name(self) -> str:
        ...

    @abstractmethod
    def fit(self, X: np.ndarray) -> "BaseDetector":
        ...

    @abstractmethod
    def score(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores. Higher = more anomalous."""
        ...

    def fit_score(self, X_train: np.ndarray, X_test: np.ndarray) -> np.ndarray:
        """Convenience: fit on train, score test."""
        self.fit(X_train)
        return self.score(X_test)

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Min-max normalize to [0, 1] for cross-method comparability."""
        lo, hi = scores.min(), scores.max()
        if hi - lo < 1e-12:
            return np.zeros_like(scores)
        return (scores - lo) / (hi - lo)

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"



# 1. Three-Sigma (3σ)


class ThreeSigmaDetector(BaseDetector):
    """
    Univariate 3σ rule applied to the L2-norm of the feature vector.
    Anomaly score = max z-score across all features (worst-channel logic).

    Pro: Fully interpretable, SCADA operators know this.
    Con: Assumes Gaussian, no multivariate structure.
    """

    def __init__(self, n_sigma: float = 3.0):
        self.n_sigma = n_sigma
        self._mu = None
        self._sigma = None

    @property
    def name(self):
        return f"3σ Rule (σ={self.n_sigma})"

    @property
    def short_name(self):
        return "three_sigma"

    def fit(self, X: np.ndarray) -> "ThreeSigmaDetector":
        self._mu    = np.mean(X, axis=0)
        self._sigma = np.std(X, axis=0) + 1e-12
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._mu is None:
            raise RuntimeError("Call fit() before score().")
        z_scores = np.abs((X - self._mu) / self._sigma)   # (n, n_feat)
        # Return maximum z-score across features per sample (most anomalous feature)
        return z_scores.max(axis=1)



# 2. EWMA (Exponentially Weighted Moving Average)


class EWMADetector(BaseDetector):
    """
    EWMA control chart applied to the RMS of the feature vector.
    Anomaly score = deviation of EWMA from training mean, in sigma units.

    This captures gradual drift — ideal for slow bearing degradation.
    """

    def __init__(self, lambda_: float = 0.2, k: float = 3.0):
        self.lambda_ = lambda_
        self.k = k
        self._mu_train = None
        self._sigma_train = None
        self._ucl = None

    @property
    def name(self):
        return f"EWMA (λ={self.lambda_}, k={self.k})"

    @property
    def short_name(self):
        return "ewma"

    def fit(self, X: np.ndarray) -> "EWMADetector":
        # Use the mean feature magnitude as the monitored statistic
        magnitudes = np.mean(np.abs(X), axis=1)
        self._mu_train    = float(np.mean(magnitudes))
        self._sigma_train = float(np.std(magnitudes)) + 1e-12
        # Upper Control Limit
        self._ucl = self._mu_train + self.k * self._sigma_train * np.sqrt(
            self.lambda_ / (2.0 - self.lambda_)
        )
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._mu_train is None:
            raise RuntimeError("Call fit() before score().")

        magnitudes = np.mean(np.abs(X), axis=1)
        n = len(magnitudes)
        ewma_vals = np.zeros(n)
        ewma_t = self._mu_train   # start EWMA at training mean

        for t in range(n):
            ewma_t = self.lambda_ * magnitudes[t] + (1 - self.lambda_) * ewma_t
            ewma_vals[t] = ewma_t

        # Anomaly score = deviation from training mean in sigma units
        scores = np.abs(ewma_vals - self._mu_train) / self._sigma_train
        return scores



# 3. Hotelling's T² (multivariate Gaussian)


class HotellingT2Detector(BaseDetector):
    """
    Multivariate Hotelling T² statistic.
    Score = Mahalanobis distance from training mean.
    Follows chi² distribution → principled threshold via chi² quantile.

    Better than 3σ because it captures covariance structure.
    """

    def __init__(self, alpha: float = 0.01):
        self.alpha = alpha
        self._mu = None
        self._cov_inv = None

    @property
    def name(self):
        return "Hotelling T²"

    @property
    def short_name(self):
        return "hotelling_t2"

    def fit(self, X: np.ndarray) -> "HotellingT2Detector":
        self._mu = np.mean(X, axis=0)
        cov = np.cov(X.T) + np.eye(X.shape[1]) * 1e-6  # regularize
        try:
            self._cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            self._cov_inv = np.linalg.pinv(cov)
        self._n_features = X.shape[1]
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._mu is None:
            raise RuntimeError("Call fit() before score().")
        diff = X - self._mu                              # (n, p)
        # T² = (x - μ)^T * Σ^{-1} * (x - μ)
        scores = np.array([
            float(d @ self._cov_inv @ d) for d in diff
        ])
        return scores

    def chi2_threshold(self) -> float:
        """Chi-squared threshold at the given significance level."""
        return chi2.ppf(1.0 - self.alpha, df=self._n_features)



# 4. Isolation Forest


class IsolationForestDetector(BaseDetector):
    """
    Isolation Forest anomaly detector.
    Scores are negated decision_function output (higher = more anomalous).

    Best all-around method in this benchmark:
    - No distributional assumptions
    - Handles multivariate data natively
    - Fast training and inference
    - Compatible with SHAP TreeExplainer
    """

    def __init__(self, n_estimators: int = 200,
                 contamination: str = "auto",
                 random_state: int = 42,
                 max_samples: str = "auto"):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.max_samples = max_samples
        self._model = None

    @property
    def name(self):
        return "Isolation Forest"

    @property
    def short_name(self):
        return "isolation_forest"

    def fit(self, X: np.ndarray) -> "IsolationForestDetector":
        self._model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            max_samples=self.max_samples,
            n_jobs=-1,
        )
        self._model.fit(X)
        logger.info(f"IsolationForest fitted on X={X.shape}")
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Call fit() before score().")
        # decision_function returns: positive = normal, negative = anomalous
        # Negate so higher = more anomalous
        raw = -self._model.decision_function(X)
        return raw

    @property
    def model(self):
        """Direct access to the sklearn model (needed for SHAP)."""
        return self._model


# 5. One-Class SVM

class OneClassSVMDetector(BaseDetector):
    """
    One-Class SVM with RBF kernel.
    Good for small datasets and non-Gaussian distributions.
    Slower than IF for large data — use with caution on full IMS runs.
    """

    def __init__(self, nu: float = 0.05, kernel: str = "rbf", gamma: str = "scale"):
        self.nu = nu
        self.kernel = kernel
        self.gamma = gamma
        self._model = None

    @property
    def name(self):
        return f"One-Class SVM (nu={self.nu})"

    @property
    def short_name(self):
        return "one_class_svm"

    def fit(self, X: np.ndarray) -> "OneClassSVMDetector":
        from sklearn.svm import OneClassSVM
        self._model = OneClassSVM(nu=self.nu, kernel=self.kernel, gamma=self.gamma)
        self._model.fit(X)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Call fit() before score().")
        return -self._model.decision_function(X)



# 6. LSTM Autoencoder (PyTorch — optional, for Colab/GPU)


class LSTMAEDetector(BaseDetector):
    """
    LSTM Autoencoder for sequence-level anomaly detection.

    Input: sequences of feature windows (shape: seq_len × n_features)
    Score: mean reconstruction error (MSE) per sequence

    Train on NORMAL sequences only.
    At test time: degraded sequences reconstruct poorly → high score.

    Requires PyTorch. Will raise ImportError if not installed.
    """

    def __init__(self,
                 seq_len: int = 30,
                 hidden_dim: int = 64,
                 latent_dim: int = 16,
                 epochs: int = 50,
                 batch_size: int = 32,
                 learning_rate: float = 1e-3,
                 dropout: float = 0.1,
                 device: str = "auto"):
        self.seq_len = seq_len
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.dropout = dropout
        self._model = None
        self._n_features = None
        self._scaler = MinMaxScaler()

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
        return "LSTM-Autoencoder"

    @property
    def short_name(self):
        return "lstm_ae"

    def fit(self, X: np.ndarray) -> "LSTMAEDetector":
        try:
            import torch
            import torch.nn as nn
            from torch.utils.data import DataLoader, TensorDataset
        except ImportError:
            raise ImportError("PyTorch is required for LSTMAEDetector. "
                              "Install with: pip install torch")

        X_scaled = self._scaler.fit_transform(X)
        self._n_features = X.shape[1]

        # Build sequences
        seqs = _make_sequences(X_scaled, self.seq_len)   # (N, seq_len, n_feat)
        tensor_data = torch.FloatTensor(seqs)
        loader = DataLoader(
            TensorDataset(tensor_data),
            batch_size=self.batch_size,
            shuffle=True
        )

        self._model = _LSTMAutoencoder(
            n_features=self._n_features,
            hidden_dim=self.hidden_dim,
            latent_dim=self.latent_dim,
            dropout=self.dropout,
        ).to(self.device)

        optimizer = torch.optim.Adam(self._model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()

        self._model.train()
        logger.info(f"Training LSTM-AE on {self.device} for {self.epochs} epochs ...")

        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for (batch,) in loader:
                batch = batch.to(self.device)
                recon = self._model(batch)
                loss  = criterion(recon, batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            if (epoch + 1) % 10 == 0:
                avg = epoch_loss / len(loader)
                logger.info(f"  Epoch [{epoch+1}/{self.epochs}] loss: {avg:.6f}")

        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Call fit() before score().")
        import torch

        X_scaled = self._scaler.transform(X)
        seqs = _make_sequences(X_scaled, self.seq_len)     # (N, seq_len, n_feat)
        tensor_data = torch.FloatTensor(seqs).to(self.device)

        self._model.eval()
        with torch.no_grad():
            recon = self._model(tensor_data).cpu().numpy()

        # MSE per sequence
        mse = np.mean((seqs - recon) ** 2, axis=(1, 2))

        # Pad front to match original length (first seq_len-1 points have no score)
        scores = np.full(len(X), float(mse.min()))
        scores[self.seq_len - 1:] = mse

        return scores



# LSTM-AE internal architecture


def _make_sequences(X: np.ndarray, seq_len: int) -> np.ndarray:
    """Convert a (T, n_feat) array into overlapping sequences (T-seq_len+1, seq_len, n_feat)."""
    n = len(X)
    seqs = np.stack([X[i:i + seq_len] for i in range(n - seq_len + 1)])
    return seqs


class _LSTMAutoencoder:
    """Internal PyTorch module — only instantiated when PyTorch is available."""

    def __new__(cls, n_features, hidden_dim, latent_dim, dropout):
        try:
            import torch.nn as nn
        except ImportError:
            raise ImportError("PyTorch required.")

        class _Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = nn.LSTM(
                    n_features, hidden_dim, batch_first=True, dropout=dropout
                )
                self.enc_proj = nn.Linear(hidden_dim, latent_dim)

                self.decoder = nn.LSTM(
                    latent_dim, hidden_dim, batch_first=True, dropout=dropout
                )
                self.dec_proj = nn.Linear(hidden_dim, n_features)

            def forward(self, x):
                # x: (batch, seq_len, n_features)
                enc_out, _ = self.encoder(x)
                latent = self.enc_proj(enc_out)

                dec_out, _ = self.decoder(latent)
                recon = self.dec_proj(dec_out)
                return recon

        return _Model()



# Factory function


def get_all_models(config: dict) -> list:
    """
    Instantiate all models listed in config["methods_to_run"].

    Usage:
        from src.config import EXPERIMENT, MODELS
        detectors = get_all_models({"methods_to_run": EXPERIMENT["methods_to_run"],
                                    "model_params": MODELS})
    """
    methods = config.get("methods_to_run", ["three_sigma", "ewma", "isolation_forest"])
    params  = config.get("model_params", {})

    detectors = []
    for method in methods:
        p = params.get(method, {})
        if method == "three_sigma":
            detectors.append(ThreeSigmaDetector(**p))
        elif method == "ewma":
            detectors.append(EWMADetector(**p))
        elif method == "hotelling_t2":
            detectors.append(HotellingT2Detector(**p))
        elif method == "isolation_forest":
            detectors.append(IsolationForestDetector(**p))
        elif method == "one_class_svm":
            detectors.append(OneClassSVMDetector(**p))
        elif method == "lstm_ae":
            detectors.append(LSTMAEDetector(**p))
        else:
            logger.warning(f"Unknown method '{method}' — skipping.")

    return detectors