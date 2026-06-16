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
    noise_runlevel,
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


# ───────────────────── run-level collapse (W2 pseudoreplication fix) ────────────

def _noise_long_toy(spec=None):
    """Two magnitude charts x three runs x two modes at one SNR, from a per-run
    spec of (aggregate, decimate) lead-time pairs. Default per-run mean
    (aggregate-decimate) diffs are run A = +2, run B = +1, run C = -1."""
    spec = spec or {
        "runA": {"aggregate": (10.0, 12.0), "decimate": (8.0, 10.0)},   # mean diff +2
        "runB": {"aggregate": (5.0, 7.0),   "decimate": (4.0, 6.0)},    # mean diff +1
        "runC": {"aggregate": (3.0, 3.0),   "decimate": (4.0, 4.0)},    # mean diff -1
    }
    rows = []
    for run, modes in spec.items():
        for mode, (m_3s, m_ewma) in modes.items():
            for short, val in (("three_sigma", m_3s), ("ewma", m_ewma)):
                rows.append({"run": run, "snr_db": 10.0, "mode": mode,
                             "short_name": short, "lead_time_hours": val})
    return pd.DataFrame(rows)


def test_noise_runlevel_collapses_to_runs_not_detectors():
    rl = noise_runlevel(_noise_long_toy(), methods=("three_sigma", "ewma"))
    assert len(rl) == 1
    row = rl.iloc[0]
    # unit of inference is the run: n=3, NOT 6 (3 runs x 2 charts)
    assert row["n_runs"] == 3
    assert row["run_diffs"] == "+2.00, +1.00, -1.00"   # ordered runA, runB, runC
    assert abs(row["mean_diff"] - (2.0 / 3.0)) < 1e-9
    assert row["n_pos"] == 2 and row["n_neg"] == 1
    assert not row["all_same_sign"]


def test_noise_runlevel_detects_unanimous_sign():
    # all three runs positive -> all_same_sign True
    spec = {
        "runA": {"aggregate": (10.0, 12.0), "decimate": (8.0, 10.0)},   # +2
        "runB": {"aggregate": (5.0, 7.0),   "decimate": (4.0, 6.0)},    # +1
        "runC": {"aggregate": (8.0, 8.0),   "decimate": (4.0, 4.0)},    # +4
    }
    rl = noise_runlevel(_noise_long_toy(spec), methods=("three_sigma", "ewma"))
    row = rl.iloc[0]
    assert row["n_pos"] == 3 and row["all_same_sign"]


def test_noise_runlevel_empty_is_safe():
    assert noise_runlevel(pd.DataFrame()).empty
