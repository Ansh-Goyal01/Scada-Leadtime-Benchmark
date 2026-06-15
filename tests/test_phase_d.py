# tests/test_phase_d.py
"""
Unit tests for the Phase D additions: conformal detector mechanics, the conformal_if
factory branch, and the feature-group ablation column selector.
"""

import numpy as np
import pytest

from src.models import get_all_models, IsolationForestDetector
from src.uncertainty import ConformalDetector
from src.ablation import _family_of, _select_columns, GROUPS


# ─────────────────────────── conformal factory + guarantee ─────────────────────

def test_conformal_if_factory_branch():
    dets = get_all_models({"methods_to_run": ["conformal_if"],
                           "model_params": {"conformal_if": {"alpha": 0.05,
                                                             "random_state": 7}}})
    assert len(dets) == 1
    d = dets[0]
    assert d.short_name == "conformal_if"
    assert hasattr(d, "calibrate") and hasattr(d, "alarm")


def test_conformal_pvalues_in_unit_interval():
    rng = np.random.RandomState(0)
    X_train = rng.normal(size=(200, 5))
    X_cal = rng.normal(size=(100, 5))
    X_test = rng.normal(size=(50, 5))
    cdet = ConformalDetector(IsolationForestDetector(random_state=0), alpha=0.05)
    cdet.calibrate(X_train, X_cal)
    p = cdet.predict_pvalue(X_test)
    assert p.shape == (50,)
    assert np.all((p >= 0) & (p <= 1))


def test_conformal_far_controlled_on_exchangeable_normal():
    """On exchangeable normal data the empirical FAR should be close to α (≤ small slack)."""
    rng = np.random.RandomState(1)
    X_train = rng.normal(size=(400, 6))
    X_cal = rng.normal(size=(300, 6))
    X_eval = rng.normal(size=(300, 6))   # same distribution → exchangeable
    alpha = 0.10
    cdet = ConformalDetector(IsolationForestDetector(random_state=1), alpha=alpha)
    cdet.calibrate(X_train, X_cal)
    p = cdet.predict_pvalue(X_eval)
    far = float(np.mean(p < alpha))
    # conformal guarantee: FAR ≤ α up to finite-sample noise
    assert far <= alpha + 0.07


# ─────────────────────────── ablation family selector ──────────────────────────

@pytest.mark.parametrize("name,expected", [
    ("rms_chmean_wmean", "rms"),
    ("kurt_chmax_wslope", "kurt"),
    ("crest_chmean_wstd", "crest"),
    ("band_lo_chmean_wmean", "band"),
    ("sk_max_chmax_wmean", "sk"),
    ("env_BPFO_chmean_wmax", "env"),
    ("rms_coherence", "rms"),       # starts with 'rms'
    ("totally_unknown", ""),
])
def test_family_of(name, expected):
    assert _family_of(name) == expected


def test_select_columns_time_only_excludes_spectral():
    names = ["rms_chmean_wmean", "kurt_chmax_wmean",
             "band_lo_chmean_wmean", "sk_max_chmean_wmean", "env_BPFO_chmean_wmax"]
    sel = _select_columns(names, GROUPS["time_only"])
    chosen = [names[i] for i in sel]
    assert "rms_chmean_wmean" in chosen and "kurt_chmax_wmean" in chosen
    assert "band_lo_chmean_wmean" not in chosen
    assert "sk_max_chmean_wmean" not in chosen
    assert "env_BPFO_chmean_wmax" not in chosen


def test_select_columns_all_keeps_everything():
    names = ["rms_a", "band_lo_b", "env_BPFO_c"]
    assert _select_columns(names, None) == [0, 1, 2]


def test_spectral_only_selects_spectral_and_envelope():
    names = ["rms_chmean_wmean", "band_lo_chmean_wmean",
             "sk_max_chmean_wmean", "env_BPFO_chmean_wmax"]
    sel = _select_columns(names, GROUPS["spectral_only"])
    chosen = set(names[i] for i in sel)
    assert chosen == {"band_lo_chmean_wmean", "sk_max_chmean_wmean", "env_BPFO_chmean_wmax"}
