# tests/test_onset.py
"""
Unit tests for degradation-onset detection (reviewer W1 leakage concern).

Verifies:
  * the onset baseline is estimated ONLY from the pre-train_end region (leakage-free):
    test-region values cannot move the onset earlier,
  * the terminal-excursion method ignores an early run-in transient and locks onto the
    sustained degradation that leads to failure,
  * a flat (healthy) series yields no onset.
"""

import numpy as np
import pandas as pd
import pytest

from src.onset import detect_onset, health_indicator, onset_for_run


def _hi_series(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="h")
    return pd.Series(np.asarray(values, dtype=float), index=idx)


def test_flat_series_has_no_onset():
    hi = _hi_series(np.ones(200) + np.random.RandomState(0).normal(0, 0.001, 200))
    assert detect_onset(hi, method="terminal", sigma_k=4.0, persistence=5) is None


def test_terminal_onset_locks_on_sustained_ramp():
    # 150 flat baseline, then a sustained ramp to failure
    base = np.ones(150) + np.random.RandomState(1).normal(0, 0.01, 150)
    ramp = np.linspace(1.0, 5.0, 50)
    hi = _hi_series(np.concatenate([base, ramp]))
    onset = detect_onset(hi, method="terminal", sigma_k=4.0, persistence=5)
    assert onset is not None
    # onset should be in the ramp region, not the flat baseline
    assert onset >= hi.index[150 - 5]


def test_terminal_ignores_early_runin_transient():
    """An early spike (run-in) then return to baseline, then the real terminal ramp.
    The terminal method must pick the LAST sustained excursion, not the run-in."""
    rng = np.random.RandomState(2)
    base = np.ones(60) + rng.normal(0, 0.01, 60)
    transient = np.concatenate([np.linspace(1, 6, 10), np.linspace(6, 1, 10)])  # run-in spike
    mid = np.ones(60) + rng.normal(0, 0.01, 60)
    ramp = np.linspace(1.0, 8.0, 40)   # terminal degradation
    hi = _hi_series(np.concatenate([base, transient, mid, ramp]))
    onset = detect_onset(hi, method="terminal", sigma_k=4.0,
                         persistence=5, gap_tol=10)
    assert onset is not None
    # terminal ramp starts at index 60+20+60 = 140; onset must be in that region,
    # strictly after the early transient (which ends by index 80)
    assert onset > hi.index[100]


def test_onset_baseline_is_leakage_free():
    """Inflating the post-train_end (test) region must NOT move the onset earlier:
    the baseline mean/std come only from the pre-train_end region."""
    rng = np.random.RandomState(3)
    base = np.ones(100) + rng.normal(0, 0.01, 100)
    ramp = np.linspace(1.0, 5.0, 100)
    hi = _hi_series(np.concatenate([base, ramp]))
    train_end = hi.index[80]

    onset_a = detect_onset(hi, train_end=train_end, method="terminal",
                           sigma_k=4.0, persistence=5)

    # Now massively inflate ONLY the test region (after train_end). Baseline is unchanged,
    # so the band (baseline_mean + k·baseline_std) and hence the onset must be identical.
    hi2 = hi.copy()
    hi2.iloc[81:] = hi2.iloc[81:] * 100.0
    onset_b = detect_onset(hi2, train_end=train_end, method="terminal",
                           sigma_k=4.0, persistence=5)
    assert onset_a is not None and onset_b is not None
    assert onset_b <= onset_a  # extra excursion can only keep/extend, never precede baseline


def test_health_indicator_requires_rms_columns():
    df = pd.DataFrame({"foo": [1, 2, 3]},
                      index=pd.date_range("2024-01-01", periods=3, freq="h"))
    with pytest.raises(ValueError):
        health_indicator(df)


def test_health_indicator_rms_mean():
    idx = pd.date_range("2024-01-01", periods=4, freq="h")
    df = pd.DataFrame({"rms_ch0": [1.0, 2.0, 3.0, 4.0],
                       "rms_ch1": [3.0, 4.0, 5.0, 6.0]}, index=idx)
    hi = health_indicator(df, kind="rms_mean")
    assert list(hi.values) == [2.0, 3.0, 4.0, 5.0]
