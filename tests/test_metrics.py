# tests/test_metrics.py
"""
Unit tests for the lead-time metric layer (reviewer W1, W6 verification).

These tests pin the *contract* the revision is built on:
  * lead time / VLT credit only valid early warnings,
  * a latch-on detector is exposed by the pre-onset FAR (W1 fix),
  * FAR is measured over the FULL pre-onset region, not a positional 5% marker (W6 fix).
"""

import numpy as np
import pandas as pd
import pytest

from src.lead_time import (
    compute_FAT, compute_VLT, compute_FAR, compute_lead_time,
    compute_detection_delay, compute_FAR_preonset, evaluate_method,
)


@pytest.fixture
def timeline():
    """Hourly timestamps over 100 h; failure at the end, onset at hour 70."""
    ts = pd.date_range("2024-01-01", periods=100, freq="h")
    t_fail = ts[-1]
    t_onset = ts[70]
    return ts, t_fail, t_onset


# ─────────────────────────── core primitives ──────────────────────────────────

def test_fat_first_true(timeline):
    ts, _, _ = timeline
    alarm = np.zeros(100, dtype=bool)
    alarm[60:] = True
    assert compute_FAT(alarm, ts) == ts[60]


def test_fat_none_when_silent(timeline):
    ts, _, _ = timeline
    assert compute_FAT(np.zeros(100, dtype=bool), ts) is None


def test_lead_time_positive_before_failure(timeline):
    ts, t_fail, _ = timeline
    fat = ts[80]
    lead = compute_lead_time(fat, t_fail)
    assert lead == pytest.approx((t_fail - fat).total_seconds() / 3600.0)
    assert lead > 0


def test_lead_time_zero_when_no_alarm(timeline):
    _, t_fail, _ = timeline
    assert compute_lead_time(None, t_fail) == 0.0


def test_lead_time_zero_when_after_failure(timeline):
    ts, t_fail, _ = timeline
    late = t_fail + pd.Timedelta(hours=5)
    assert compute_lead_time(late, t_fail) == 0.0


def test_detection_delay_none_for_early_alarm(timeline):
    ts, _, t_onset = timeline
    # alarm before onset → delay is negative → returns None (early alarm)
    assert compute_detection_delay(ts[50], t_onset) is None
    # alarm after onset → positive delay
    assert compute_detection_delay(ts[80], t_onset) == pytest.approx(10.0)


# ─────────────────────────── FAR over full pre-onset region (W6) ───────────────

def test_far_preonset_spans_full_normal_region(timeline):
    ts, _, t_onset = timeline
    # one false alarm at hour 10 (well inside pre-onset region [0, 70))
    alarm = np.zeros(100, dtype=bool)
    alarm[10] = True
    far = compute_FAR_preonset(alarm, ts, t_onset)
    # 1 alarm / 70 pre-onset windows — NOT 1/5 as the old positional 5% marker gave
    assert far == pytest.approx(1.0 / 70.0)


def test_far_preonset_nan_when_no_preonset_window():
    ts = pd.date_range("2024-01-01", periods=10, freq="h")
    t_onset = ts[0]  # nothing strictly before onset
    assert np.isnan(compute_FAR_preonset(np.zeros(10, dtype=bool), ts, t_onset))


# ─────────────────────────── W1: latch-on detector is exposed ──────────────────

class _LatchOnDetector:
    """Adversarial detector that screams across the whole test window — the W1 exploit.
    Score = feature-row magnitude; with a near-zero train baseline the percentile
    threshold is tiny, so every (large-valued) test window alarms, including the entire
    pre-onset region. It earns large raw lead time but must be flagged invalid."""
    name = "Latch-On"
    short_name = "latch_on"

    def fit(self, X):
        return self

    def score(self, X):
        return np.linalg.norm(X, axis=1)


def test_latchon_detector_is_invalid(timeline):
    ts, t_fail, t_onset = timeline
    # train baseline ≈ 0 → threshold ≈ 0; test values large → alarm fires everywhere.
    rng = np.random.RandomState(0)
    X_train = rng.normal(scale=1e-3, size=(50, 4))
    X_test = np.full((100, 4), 100.0)

    res = evaluate_method(
        detector=_LatchOnDetector(),
        X_train=X_train, X_test=X_test,
        timestamps_test=ts, failure_time=str(t_fail),
        threshold_strategy="percentile", threshold_percentile=97.5,
        alarm_persistence=3, t_onset=t_onset, far_budget=0.10,
    )
    # It DOES earn a large raw lead time (latching from the start) ...
    assert res["lead_time_hours"] > 0
    # ... but pre-onset FAR is ~100%, so the budget gate marks it INVALID. This is W1 fixed.
    assert res["far_preonset_pct"] > 90.0
    assert res["valid_alarm"] is False


def test_genuine_detector_can_be_valid(timeline):
    """A detector that is quiet until just after onset passes the budget gate."""
    ts, t_fail, t_onset = timeline

    class _GenuineDetector:
        name = "Genuine"
        short_name = "genuine"

        def fit(self, X):
            return self

        def score(self, X):
            s = np.zeros(len(X))
            s[75:] = 1e6   # fires only well after onset (hour 70)
            return s

    rng = np.random.RandomState(1)
    res = evaluate_method(
        detector=_GenuineDetector(),
        X_train=rng.normal(size=(50, 4)),
        X_test=rng.normal(size=(100, 4)),
        timestamps_test=ts, failure_time=str(t_fail),
        threshold_strategy="percentile", threshold_percentile=97.5,
        alarm_persistence=3, t_onset=t_onset, far_budget=0.10,
    )
    assert res["lead_time_hours"] > 0
    assert res["far_preonset_pct"] == pytest.approx(0.0)
    assert res["valid_alarm"] is True


# ─────────────────────────── legacy VLT rules ──────────────────────────────────

def test_vlt_zero_for_false_alarm_in_normal_period(timeline):
    ts, t_fail, _ = timeline
    t_normal_end = ts[20]
    fat = ts[10]   # inside the declared normal period
    assert compute_VLT(fat, t_fail, t_normal_end) == 0.0


def test_compute_far_basic(timeline):
    ts, _, _ = timeline
    normal_end = ts[19]   # first 20 windows are "normal"
    alarm = np.zeros(100, dtype=bool)
    alarm[5] = True
    far = compute_FAR(alarm, ts, normal_end)
    assert far == pytest.approx(1.0 / 20.0)
