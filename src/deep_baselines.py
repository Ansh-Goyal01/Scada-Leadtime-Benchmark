# src/deep_baselines.py
"""
Deep reconstruction baselines for sequence-level anomaly detection — added to
meet the 2025-venue expectation of modern deep baselines alongside the SPC
charts (reviewer W5/M1). Two detectors are provided, both reusing the LSTM-AE
template from src/models.py (overlapping feature-window sequences, MinMax
scaling, train-on-normal, score = per-window reconstruction error, front-padded
to the original length):

  1. TCNDetector           — a dilated causal 1-D convolutional autoencoder
                             (Temporal Convolutional Network). Stacked residual
                             blocks with dilations 1,2,4,8 give a wide receptive
                             field at low parameter count; CPU-friendly.
  2. TransformerADDetector — a lightweight reconstruction Transformer
                             (positional encoding + a few self-attention encoder
                             blocks) that reconstructs the input window. Small
                             d_model / few heads / few layers, sized for the tiny
                             (~100-window) normal training sets in this study.

HONEST CAVEAT (stated in the paper): with on the order of 100 normal training
windows these sequence models are data-starved. We report them for completeness
and modern-baseline coverage, NOT as favored methods, and we do not tune them
per-dataset — the same fixed-protocol fairness applied to the SPC charts. On
short runs (XJTU/ONGC), where the number of feature windows is below the
sequence length, fitting is impossible; rather than crash or silently drop the
cell we raise :class:`ShortRunError`, which the benchmark records as an explicit
N/A so the limitation is reported, not hidden.

PyTorch is an OPTIONAL dependency, imported lazily inside fit() — the same
pattern as LSTMAEDetector / DeepSVDDDetector.
"""

import logging

import numpy as np
from sklearn.preprocessing import MinMaxScaler

from src.models import BaseDetector, _make_sequences

logger = logging.getLogger(__name__)


class ShortRunError(RuntimeError):
    """Raised when a run has too few feature windows to form even one sequence.

    The benchmark catches this to emit an explicit N/A result for the
    (run, detector) cell instead of crashing or silently dropping it.
    """


def _device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _scores_from_recon(seqs: np.ndarray, recon: np.ndarray,
                       n_rows: int, seq_len: int) -> np.ndarray:
    """Per-sequence MSE, front-padded to the original row count (the first
    seq_len-1 rows have no sequence ending on them)."""
    mse = np.mean((seqs - recon) ** 2, axis=(1, 2))
    scores = np.full(n_rows, float(mse.min()))
    scores[seq_len - 1:] = mse
    return scores


# ──────────────────────────────────────────────────────────────────────────────
# 1. Temporal Convolutional Network autoencoder
# ──────────────────────────────────────────────────────────────────────────────
class TCNDetector(BaseDetector):
    """Dilated causal 1-D convolutional autoencoder; reconstruction-error score.

    A stack of residual temporal blocks (Conv1d → ReLU → Conv1d, with a 1×1
    residual projection) at exponentially increasing dilations encodes the
    windowed sequence; a symmetric 1×1 conv head reconstructs it. Trained on
    normal sequences only, so degraded windows reconstruct poorly → high score.
    """

    def __init__(self,
                 seq_len: int = 30,
                 channels: int = 32,
                 kernel_size: int = 3,
                 levels: int = 4,
                 epochs: int = 40,
                 batch_size: int = 32,
                 learning_rate: float = 1e-3,
                 dropout: float = 0.1,
                 random_state: int = 42,
                 device: str = "auto"):
        self.seq_len = seq_len
        self.channels = channels
        self.kernel_size = kernel_size
        self.levels = levels
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.dropout = dropout
        self.random_state = random_state
        self.device = _device(device)
        self._model = None
        self._n_features = None
        self._scaler = MinMaxScaler()

    @property
    def name(self):
        return "TCN-Autoencoder"

    @property
    def short_name(self):
        return "tcn"

    def fit(self, X: np.ndarray) -> "TCNDetector":
        try:
            import torch
            import torch.nn as nn  # noqa: F401
            from torch.utils.data import DataLoader, TensorDataset
        except ImportError:
            raise ImportError("PyTorch is required for TCNDetector. "
                              "Install with: pip install torch")

        if len(X) < self.seq_len:
            raise ShortRunError(
                f"TCN needs >= {self.seq_len} windows; run has {len(X)}.")

        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        X_scaled = self._scaler.fit_transform(X)
        self._n_features = X.shape[1]
        seqs = _make_sequences(X_scaled, self.seq_len)         # (N, seq_len, n_feat)
        data = torch.FloatTensor(seqs)
        loader = DataLoader(TensorDataset(data),
                            batch_size=self.batch_size, shuffle=True)

        self._model = _TCNAutoencoder(
            n_features=self._n_features, channels=self.channels,
            kernel_size=self.kernel_size, levels=self.levels,
            dropout=self.dropout,
        ).to(self.device)

        opt = torch.optim.Adam(self._model.parameters(), lr=self.learning_rate)
        crit = torch.nn.MSELoss()
        self._model.train()
        logger.info("Training TCN-AE on %s for %d epochs ...", self.device, self.epochs)
        for epoch in range(self.epochs):
            ep = 0.0
            for (batch,) in loader:
                batch = batch.to(self.device)
                recon = self._model(batch)
                loss = crit(recon, batch)
                opt.zero_grad(); loss.backward(); opt.step()
                ep += loss.item()
            if (epoch + 1) % 10 == 0:
                logger.info("  Epoch [%d/%d] loss: %.6f", epoch + 1, self.epochs, ep / len(loader))
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Call fit() before score().")
        import torch
        X_scaled = self._scaler.transform(X)
        seqs = _make_sequences(X_scaled, self.seq_len)
        data = torch.FloatTensor(seqs).to(self.device)
        self._model.eval()
        with torch.no_grad():
            recon = self._model(data).cpu().numpy()
        return _scores_from_recon(seqs, recon, len(X), self.seq_len)


class _TCNAutoencoder:
    """Internal PyTorch module — instantiated only when torch is available."""

    def __new__(cls, n_features, channels, kernel_size, levels, dropout):
        import torch.nn as nn

        class _Chomp(nn.Module):
            """Trim the right padding so the convolution stays causal."""
            def __init__(self, chomp):
                super().__init__()
                self.chomp = chomp

            def forward(self, x):
                return x[:, :, :-self.chomp].contiguous() if self.chomp > 0 else x

        class _TempBlock(nn.Module):
            def __init__(self, c_in, c_out, k, dilation):
                super().__init__()
                pad = (k - 1) * dilation
                self.conv1 = nn.Conv1d(c_in, c_out, k, padding=pad, dilation=dilation)
                self.chomp1 = _Chomp(pad)
                self.conv2 = nn.Conv1d(c_out, c_out, k, padding=pad, dilation=dilation)
                self.chomp2 = _Chomp(pad)
                self.relu = nn.ReLU()
                self.drop = nn.Dropout(dropout)
                self.down = nn.Conv1d(c_in, c_out, 1) if c_in != c_out else None

            def forward(self, x):
                y = self.drop(self.relu(self.chomp1(self.conv1(x))))
                y = self.drop(self.relu(self.chomp2(self.conv2(y))))
                res = x if self.down is None else self.down(x)
                return self.relu(y + res)

        class _Model(nn.Module):
            def __init__(self):
                super().__init__()
                blocks = []
                c_in = n_features
                for i in range(levels):
                    blocks.append(_TempBlock(c_in, channels, kernel_size, dilation=2 ** i))
                    c_in = channels
                self.tcn = nn.Sequential(*blocks)
                self.head = nn.Conv1d(channels, n_features, 1)

            def forward(self, x):
                # x: (batch, seq_len, n_features) → conv wants (batch, channels, seq_len)
                h = x.transpose(1, 2)
                h = self.tcn(h)
                out = self.head(h)
                return out.transpose(1, 2)

        return _Model()


# ──────────────────────────────────────────────────────────────────────────────
# 2. Reconstruction Transformer
# ──────────────────────────────────────────────────────────────────────────────
class TransformerADDetector(BaseDetector):
    """Lightweight reconstruction Transformer; per-window MSE anomaly score.

    A linear input projection + sinusoidal positional encoding feed a small
    stack of TransformerEncoder layers; a linear head reconstructs the window.
    Trained on normal sequences only. Kept deliberately small (d_model=32,
    2 heads, 2 layers) so it does not over-fit the ~100-window training sets.
    """

    def __init__(self,
                 seq_len: int = 30,
                 d_model: int = 32,
                 nhead: int = 2,
                 num_layers: int = 2,
                 dim_feedforward: int = 64,
                 epochs: int = 40,
                 batch_size: int = 32,
                 learning_rate: float = 1e-3,
                 dropout: float = 0.1,
                 random_state: int = 42,
                 device: str = "auto"):
        self.seq_len = seq_len
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers
        self.dim_feedforward = dim_feedforward
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.dropout = dropout
        self.random_state = random_state
        self.device = _device(device)
        self._model = None
        self._n_features = None
        self._scaler = MinMaxScaler()

    @property
    def name(self):
        return "Transformer-AD"

    @property
    def short_name(self):
        return "transformer_ad"

    def fit(self, X: np.ndarray) -> "TransformerADDetector":
        try:
            import torch
            import torch.nn as nn  # noqa: F401
            from torch.utils.data import DataLoader, TensorDataset
        except ImportError:
            raise ImportError("PyTorch is required for TransformerADDetector. "
                              "Install with: pip install torch")

        if len(X) < self.seq_len:
            raise ShortRunError(
                f"Transformer-AD needs >= {self.seq_len} windows; run has {len(X)}.")

        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        X_scaled = self._scaler.fit_transform(X)
        self._n_features = X.shape[1]
        seqs = _make_sequences(X_scaled, self.seq_len)
        data = torch.FloatTensor(seqs)
        loader = DataLoader(TensorDataset(data),
                            batch_size=self.batch_size, shuffle=True)

        self._model = _TransformerAE(
            n_features=self._n_features, d_model=self.d_model, nhead=self.nhead,
            num_layers=self.num_layers, dim_feedforward=self.dim_feedforward,
            dropout=self.dropout, seq_len=self.seq_len,
        ).to(self.device)

        opt = torch.optim.Adam(self._model.parameters(), lr=self.learning_rate)
        crit = torch.nn.MSELoss()
        self._model.train()
        logger.info("Training Transformer-AD on %s for %d epochs ...", self.device, self.epochs)
        for epoch in range(self.epochs):
            ep = 0.0
            for (batch,) in loader:
                batch = batch.to(self.device)
                recon = self._model(batch)
                loss = crit(recon, batch)
                opt.zero_grad(); loss.backward(); opt.step()
                ep += loss.item()
            if (epoch + 1) % 10 == 0:
                logger.info("  Epoch [%d/%d] loss: %.6f", epoch + 1, self.epochs, ep / len(loader))
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Call fit() before score().")
        import torch
        X_scaled = self._scaler.transform(X)
        seqs = _make_sequences(X_scaled, self.seq_len)
        data = torch.FloatTensor(seqs).to(self.device)
        self._model.eval()
        with torch.no_grad():
            recon = self._model(data).cpu().numpy()
        return _scores_from_recon(seqs, recon, len(X), self.seq_len)


class _TransformerAE:
    """Internal PyTorch module — instantiated only when torch is available."""

    def __new__(cls, n_features, d_model, nhead, num_layers,
                dim_feedforward, dropout, seq_len):
        import torch
        import torch.nn as nn

        class _Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.in_proj = nn.Linear(n_features, d_model)
                pe = torch.zeros(seq_len, d_model)
                pos = torch.arange(0, seq_len, dtype=torch.float).unsqueeze(1)
                div = torch.exp(torch.arange(0, d_model, 2).float()
                                * (-np.log(10000.0) / d_model))
                pe[:, 0::2] = torch.sin(pos * div)
                pe[:, 1::2] = torch.cos(pos * div[: pe[:, 1::2].shape[1]])
                self.register_buffer("pe", pe.unsqueeze(0))   # (1, seq_len, d_model)
                layer = nn.TransformerEncoderLayer(
                    d_model=d_model, nhead=nhead, dim_feedforward=dim_feedforward,
                    dropout=dropout, batch_first=True,
                )
                self.encoder = nn.TransformerEncoder(layer, num_layers=num_layers)
                self.out_proj = nn.Linear(d_model, n_features)

            def forward(self, x):
                # x: (batch, seq_len, n_features)
                h = self.in_proj(x) + self.pe[:, : x.shape[1], :]
                h = self.encoder(h)
                return self.out_proj(h)

        return _Model()
