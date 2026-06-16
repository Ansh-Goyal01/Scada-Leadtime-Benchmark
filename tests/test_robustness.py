# tests/test_robustness.py
"""
Unit tests for the Phase 2.5 noise/denoising mechanism test (src/robustness.py).

These exercise the signal transforms (contract + correctness), not the full
lead-time evaluation, which is integration-tested by running the CLI.
"""

import numpy as np
import pandas as pd
import pytest

from src.robustness import (
    make_noise_transform,
    make_denoise_transform,
    _kalman_cv_smooth,
    _signal_columns,
)


def _toy_df(n=200, seed=0):
    rng = np.random.RandomState(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="10min")
    base = np.sin(np.linspace(0, 12, n)) + 2.0
    return pd.DataFrame({
        "rms_ch0": base + rng.normal(0, 0.02, n),
        "rms_ch1": 0.8 * base + rng.normal(0, 0.02, n),
        "kurt_ch0": np.full(n, 3.0),
        "other_col": rng.normal(size=n),   # must be left untouched
    }, index=idx)


# ──────────────────────────── noise injection ──────────────────────────────────

def test_noise_hits_target_snr():
    df = _toy_df()
    for target in (10.0, 20.0, 30.0):
        noisy = make_noise_transform(target, seed=1)(df)
        x = df["rms_ch0"].to_numpy()
        e = noisy["rms_ch0"].to_numpy() - x
        snr = 10 * np.log10(np.mean(x ** 2) / np.mean(e ** 2))
        assert abs(snr - target) < 1.5, f"SNR {snr:.1f} far from {target}"


def test_noise_is_seed_reproducible():
    df = _toy_df()
    a = make_noise_transform(20.0, seed=7)(df)
    b = make_noise_transform(20.0, seed=7)(df)
    pd.testing.assert_frame_equal(a, b)


def test_noise_leaves_non_signal_columns_untouched():
    df = _toy_df()
    noisy = make_noise_transform(20.0, seed=1)(df)
    assert np.array_equal(noisy["other_col"].to_numpy(), df["other_col"].to_numpy())
    assert _signal_columns(df) == ["rms_ch0", "rms_ch1", "kurt_ch0"]


def test_more_noise_means_lower_snr():
    df = _toy_df()
    x = df["rms_ch0"].to_numpy()
    errs = []
    for target in (30.0, 20.0, 10.0):
        e = make_noise_transform(target, seed=2)(df)["rms_ch0"].to_numpy() - x
        errs.append(np.mean(e ** 2))
    assert errs[0] < errs[1] < errs[2]   # 30 dB cleaner than 10 dB


# ─────────────────────────────── denoisers ─────────────────────────────────────

@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.parametrize("kind", ["median", "moving_average", "kalman", "wavelet"])
def test_denoiser_contract(kind):
    df = _toy_df()
    tf = make_denoise_transform(kind)
    if tf is None:           # wavelet may be unavailable (pywt not installed)
        pytest.skip(f"{kind} denoiser unavailable")
    out = tf(df)
    for c in _signal_columns(df):
        assert len(out[c]) == len(df[c])
        assert np.isfinite(out[c].to_numpy()).all()
    # non-signal column untouched
    assert np.array_equal(out["other_col"].to_numpy(), df["other_col"].to_numpy())


def test_denoiser_reduces_noise_variance():
    """A smoother applied to a noisy signal should bring it closer to the clean
    signal than the noisy input itself (residual variance drops)."""
    df = _toy_df()
    clean = df["rms_ch0"].to_numpy()
    noisy_df = make_noise_transform(10.0, seed=3)(df)
    noisy = noisy_df["rms_ch0"].to_numpy()
    base_err = np.mean((noisy - clean) ** 2)
    for kind in ("median", "moving_average", "kalman"):
        sm = make_denoise_transform(kind)(noisy_df)["rms_ch0"].to_numpy()
        assert np.mean((sm - clean) ** 2) < base_err, f"{kind} did not denoise"


def test_kalman_smooth_basic():
    x = np.linspace(0, 1, 50) + np.random.RandomState(0).normal(0, 0.1, 50)
    y = _kalman_cv_smooth(x)
    assert len(y) == len(x)
    assert np.isfinite(y).all()
    # smoother output should have lower step-to-step variance than the raw input
    assert np.var(np.diff(y)) < np.var(np.diff(x))


def test_unknown_denoiser_raises():
    with pytest.raises(ValueError):
        make_denoise_transform("nope")
