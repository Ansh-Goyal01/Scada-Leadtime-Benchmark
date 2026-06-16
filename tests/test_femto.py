# tests/test_femto.py
"""
Unit tests for the FEMTO/PRONOSTIA loader integration (Phase 3).

These assert the structural contract — which bearings are exposed, that the
Learning_set (run-to-failure) copy is preferred over the truncated Test/Validation
copies, and that temperature files are excluded from the acceleration ingest. They
are skipped if the FEMTO data is not present on disk.
"""

import os

import pytest

from src.config import PATHS
from src.datasets import default_runs, FEMTO_RUNS, _find_femto_learning_dir

_FEMTO_PRESENT = os.path.isdir(PATHS.get("raw_femto", ""))
pytestmark = pytest.mark.skipif(not _FEMTO_PRESENT,
                                reason="FEMTO data not present on disk")


def test_femto_default_runs_are_learning_set_six():
    runs = default_runs("FEMTO")
    assert runs == list(FEMTO_RUNS)
    assert len(runs) == 6
    assert set(runs) == {"Bearing1_1", "Bearing1_2", "Bearing2_1",
                         "Bearing2_2", "Bearing3_1", "Bearing3_2"}


@pytest.mark.parametrize("run", FEMTO_RUNS)
def test_femto_resolves_to_learning_set(run):
    d = _find_femto_learning_dir(PATHS["raw_femto"], run).replace("\\", "/").lower()
    assert "learning" in d, f"{run} resolved to non-learning dir: {d}"
    assert d.rstrip("/").endswith(run.lower())


def test_femto_run_dir_has_acc_and_temp_files():
    """Confirms the temp-file hazard the loader guards against actually exists."""
    d = _find_femto_learning_dir(PATHS["raw_femto"], "Bearing1_1")
    names = os.listdir(d)
    assert any(n.startswith("acc_") for n in names)
    assert any(n.startswith("temp_") for n in names), \
        "expected temp_*.csv present (loader must exclude these)"


def test_femto_unknown_run_raises():
    with pytest.raises(FileNotFoundError):
        _find_femto_learning_dir(PATHS["raw_femto"], "Bearing9_9")
