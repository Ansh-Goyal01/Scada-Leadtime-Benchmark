"""
Feature-schema contract for the IMS controlled-sweep loader (decision D-2).

D-2 re-baselined IMS onto the 49-dim invariant schema, so `load_pipeline_controlled`
now defaults to `feature_mode="config"` -> `FEATURES["mode"]`. The legacy 445-dim
schema must remain reachable and bit-reproducible: the originally published
`benchmark_IMS_long.csv` was produced under it and the response letter cites it.

These tests pin both halves of that contract. There were previously no tests over
`load_pipeline_controlled` at all.
"""

import inspect
import os

import pytest

from src.config import FEATURES, PATHS
from src.sampling import load_pipeline_controlled

RUN = "2nd_test"
PARQUET = os.path.join(PATHS["processed"], f"{RUN}_features.parquet")
needs_data = pytest.mark.skipif(not os.path.exists(PARQUET),
                                reason=f"{PARQUET} not present")

LEGACY_DIMS = 445          # stats-of-stats + all-pairs correlations on IMS's 8 channels


def test_default_feature_mode_is_config():
    """The default must be 'config' so FEATURES['mode'] governs -- not a hardcoded schema."""
    sig = inspect.signature(load_pipeline_controlled)
    assert sig.parameters["feature_mode"].default == "config"


def test_run_benchmark_default_feature_mode_is_config():
    from src.benchmark import run_benchmark
    sig = inspect.signature(run_benchmark)
    assert sig.parameters["feature_mode"].default == "config"


def test_unknown_feature_mode_raises():
    with pytest.raises(ValueError, match="Unknown feature_mode"):
        load_pipeline_controlled(RUN, feature_mode="not_a_schema")


@needs_data
def test_config_resolves_to_the_configured_schema():
    pipe = load_pipeline_controlled(RUN, factor=1, mode="none")
    assert pipe["feature_mode"] == FEATURES["mode"] == "invariant"
    top_k = FEATURES.get("select_top_k")
    assert pipe["n_features"] <= top_k, "top-k selection must keep p < n on the invariant path"
    assert pipe["n_features"] < pipe["X_train"].shape[0], "p >= n defeats the point of D-2"


@needs_data
def test_legacy_schema_still_reachable_and_unchanged():
    """The published 445-dim path must survive D-2 so the old numbers reproduce."""
    pipe = load_pipeline_controlled(RUN, factor=1, mode="none", feature_mode="legacy")
    assert pipe["feature_mode"] == "legacy"
    assert pipe["n_features"] == LEGACY_DIMS
    # The defect the paper's Section 4.2 names: p >> n on the published IMS path.
    assert pipe["n_features"] > pipe["X_train"].shape[0]


@needs_data
def test_explicit_invariant_matches_config_default():
    a = load_pipeline_controlled(RUN, factor=1, mode="none", feature_mode="invariant")
    b = load_pipeline_controlled(RUN, factor=1, mode="none")
    assert a["n_features"] == b["n_features"]
    assert a["feature_names"] == b["feature_names"]


@needs_data
def test_downsampling_geometry_is_schema_independent():
    """Window content and test-window counts must not depend on the feature schema."""
    leg = load_pipeline_controlled(RUN, factor=5, mode="aggregate", feature_mode="legacy")
    inv = load_pipeline_controlled(RUN, factor=5, mode="aggregate", feature_mode="invariant")
    assert leg["X_test"].shape[0] == inv["X_test"].shape[0]
    assert leg["window_size_used"] == inv["window_size_used"]
    assert leg["effective_interval_min"] == inv["effective_interval_min"]
