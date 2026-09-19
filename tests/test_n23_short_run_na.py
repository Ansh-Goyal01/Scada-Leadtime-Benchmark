"""N-23 regression: too-few-window cells are explicit N/A, never silent drops.

Before this fix, evaluate_all_methods() caught ShortRunError in a bare
``except Exception`` that logged and dropped the cell. training_sweep's na_count
could therefore only ever be 0, and n_bearings fell below the full n=6 whenever a
deep sequence model could not form a length-30 sequence -- contradicting the
explicit N/A promise in Section 4.5.
"""

import numpy as np
import pandas as pd
import pytest

from src.deep_baselines import ShortRunError
from src.lead_time import evaluate_all_methods


class _ShortRunDetector:
    """Stands in for a seq-len-30 deep model on a run with too few windows."""
    name = "LSTM Autoencoder"
    short_name = "lstm_ae"

    def fit(self, X):
        raise ShortRunError(f"LSTM-AE needs >= 30 windows; run has {len(X)}.")

    def score(self, X):  # pragma: no cover - never reached
        raise AssertionError("score() must not run after a ShortRunError")


def _args():
    ts = pd.date_range("2024-01-01", periods=12, freq="10min")
    return dict(
        detectors=[_ShortRunDetector()],
        X_train=np.random.RandomState(0).normal(size=(20, 4)),
        X_test=np.random.RandomState(1).normal(size=(12, 4)),
        timestamps_test=ts,
        failure_time=str(ts[-1]),
    )


def test_short_run_cell_is_recorded_as_na():
    _, results = evaluate_all_methods(record_short_run_na=True, **_args())

    assert len(results) == 1, "the too-short cell must be recorded, not dropped"
    r = results[0]
    assert r["na"] is True
    assert r["short_name"] == "lstm_ae"
    assert r["valid_alarm"] is False, "an N/A must never count as a detection"
    assert r["alarm_raised"] is False
    assert r["FAT"] is None
    assert not np.isfinite(r["lead_time_hours"])
    assert not np.isfinite(r["far_preonset_pct"])


def test_na_record_carries_the_full_result_schema():
    """Downstream consumers index these keys directly; a missing one is a KeyError."""
    _, results = evaluate_all_methods(record_short_run_na=True, **_args())
    for key in ("method", "short_name", "threshold", "FAT", "lead_time_hours",
                "detection_delay_hours", "far_preonset_pct", "max_lead_hours",
                "lead_norm", "t_onset", "VLT_hours", "FAR_pct", "alarm_raised",
                "valid_alarm", "timestamps", "failure_time"):
        assert key in results[0], f"N/A record is missing {key!r}"


def test_default_is_unchanged_so_published_artifacts_are_stable():
    """record_short_run_na defaults False: every already-published artifact produced
    through evaluate_all_methods keeps its exact previous contents (see N-24)."""
    _, results = evaluate_all_methods(**_args())
    assert results == []


def test_training_sweep_is_na_trusts_the_explicit_flag():
    from src.training_sweep import _is_na
    assert _is_na({"na": True, "lead_time_hours": 0.0, "FAT": "2024-01-01"}) is True
    assert _is_na({"na": False, "lead_time_hours": 3.5, "FAT": "2024-01-01"}) is False
