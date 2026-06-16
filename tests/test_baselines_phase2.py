# tests/test_baselines_phase2.py
"""
Unit tests for the Phase 2 baselines: the deterministic CUSUM control chart and
the short-run N/A guard shared by the deep reconstruction baselines (LSTM-AE,
TCN, Transformer-AD).

The deep-model forward passes are exercised lightly (a few epochs) only to assert
the contract — output length, seed reproducibility, and that degradation raises
the reconstruction score — not to evaluate detection quality.
"""

import numpy as np
import pytest

from src.models import CUSUMDetector, get_all_models


# ──────────────────────────────── CUSUM ────────────────────────────────────────

def test_cusum_alarms_after_step_shift():
    """CUSUM must accumulate AFTER a sustained mean shift, not before it."""
    rng = np.random.RandomState(0)
    X_train = rng.normal(0, 1, size=(100, 5))
    X_test = np.vstack([rng.normal(0, 1, size=(50, 5)),
                        rng.normal(3, 1, size=(50, 5))])
    d = CUSUMDetector(k=0.5, h=5.0).fit(X_train)
    s = d.score(X_test)
    assert len(s) == len(X_test)
    # Post-shift accumulation dwarfs the in-control region.
    assert s[50:].max() > 10 * (s[:50].max() + 1e-9)
    assert s[:50].mean() < s[50:].mean()


def test_cusum_is_deterministic():
    rng = np.random.RandomState(1)
    X_train = rng.normal(size=(80, 4))
    X_test = rng.normal(size=(60, 4))
    s1 = CUSUMDetector().fit(X_train).score(X_test)
    s2 = CUSUMDetector().fit(X_train).score(X_test)
    assert np.array_equal(s1, s2)


def test_cusum_requires_fit():
    with pytest.raises(RuntimeError):
        CUSUMDetector().score(np.zeros((5, 3)))


def test_cusum_registered_in_factory():
    dets = get_all_models({"methods_to_run": ["cusum"],
                           "model_params": {"cusum": {"k": 0.5, "h": 5.0}}})
    assert len(dets) == 1 and dets[0].short_name == "cusum"


# ────────────────────────── short-run N/A guard ────────────────────────────────

torch = pytest.importorskip("torch")  # deep baselines need PyTorch


def test_short_run_error_on_tcn_and_transformer():
    from src.deep_baselines import TCNDetector, TransformerADDetector, ShortRunError
    short = np.random.RandomState(0).normal(size=(10, 6)).astype("float32")  # < seq_len=30
    for D in (TCNDetector, TransformerADDetector):
        with pytest.raises(ShortRunError):
            D(seq_len=30, epochs=1).fit(short)


def test_lstm_ae_short_run_error():
    from src.models import LSTMAEDetector
    from src.deep_baselines import ShortRunError
    short = np.random.RandomState(0).normal(size=(10, 6)).astype("float32")
    with pytest.raises(ShortRunError):
        LSTMAEDetector(seq_len=30, epochs=1).fit(short)


def test_deep_recon_score_length_and_degradation():
    from src.deep_baselines import TCNDetector, TransformerADDetector
    rng = np.random.RandomState(0)
    X_train = rng.normal(0, 1, size=(120, 8)).astype("float32")
    X_test = np.vstack([rng.normal(0, 1, size=(40, 8)),
                        rng.normal(2.5, 1, size=(40, 8))]).astype("float32")
    for D in (TCNDetector, TransformerADDetector):
        d = D(epochs=3).fit(X_train)
        s = d.score(X_test)
        assert len(s) == len(X_test)
        # Reconstruction error should rise on the degraded second half.
        assert np.mean(s[40:]) > np.mean(s[:40])


def test_tcn_seed_reproducible():
    from src.deep_baselines import TCNDetector
    rng = np.random.RandomState(0)
    X_train = rng.normal(size=(120, 8)).astype("float32")
    X_test = rng.normal(size=(60, 8)).astype("float32")
    s1 = TCNDetector(epochs=3, random_state=42).fit(X_train).score(X_test)
    s2 = TCNDetector(epochs=3, random_state=42).fit(X_train).score(X_test)
    assert np.allclose(s1, s2)
