"""The released ONGC artifacts must let a reader reproduce the paper's onset WITHOUT
the proprietary data, and must not leak anything the NDA covers.

The ONGC record is proprietary, so a reader cannot rerun the case study from the raw data.
These tests are the standing check that the released substitute
actually works and stays within the disclosure boundary.
"""

import os
import re

import pandas as pd
import pytest

from src.onset import detect_onset

HI = os.path.join("results", "tables", "ongc_health_indicator.csv")
MARKERS = os.path.join("results", "tables", "ongc_onset_markers.csv")

pytestmark = pytest.mark.skipif(not os.path.exists(HI), reason="ONGC export not built")


def _hi():
    d = pd.read_csv(HI, parse_dates=["timestamp"])
    return pd.Series(d["health_indicator"].to_numpy(), index=pd.DatetimeIndex(d["timestamp"]))


def _markers():
    return pd.read_csv(MARKERS, parse_dates=["t_start", "t_train_end", "t_onset", "t_fail"]).iloc[0]


def test_reader_can_reproduce_the_published_onset_from_the_release_alone():
    """The whole point of the release: no proprietary input is touched here."""
    m = _markers()
    onset = detect_onset(
        _hi(), train_end=m["t_train_end"], t_fail=m["t_fail"],
        method=m["onset_method"], sigma_k=float(m["sigma_k"]),
        persistence=int(m["persistence"]), gap_tol=int(m["gap_tol"]),
    )
    assert pd.Timestamp(onset) == pd.Timestamp("2023-11-13 03:44:01")
    assert pd.Timestamp(onset) == m["t_onset"]


def test_markers_agree_with_the_already_released_benchmark_rows():
    m = _markers()
    b = pd.read_csv(os.path.join("results", "tables", "benchmark_ONGC_long.csv"))
    assert pd.Timestamp(b["t_onset"].iloc[0]) == m["t_onset"]
    assert pd.Timestamp(b["t_fail"].iloc[0]) == m["t_fail"]


def test_appendix_d2_facts_hold():
    m = _markers()
    assert int(m["n_samples"]) == 42698           # "42,698 rows"
    assert float(m["interval_s"]) == 10.0         # "10 s SCADA rate"
    assert 4.5 < (m["t_fail"] - m["t_start"]).total_seconds() / 86400 < 5.5   # "~5 days"
    lead = (m["t_fail"] - m["t_onset"]).total_seconds() / 3600
    assert 5.5 < lead < 6.5                       # "roughly six hours"


def test_release_contains_no_channel_level_measurements():
    forbidden = re.compile(r"^(rms|kurt|skew|p2p|crest|std|mean|max|min)_ch\d+$", re.I)
    for path in (HI, MARKERS):
        cols = list(pd.read_csv(path, nrows=1).columns)
        leaked = [c for c in cols if forbidden.match(c)]
        assert not leaked, f"{path} leaks per-channel measurements: {leaked}"


def test_health_indicator_is_a_single_dimensionless_aggregate():
    """One scalar per timestamp, baseline-standardized: the four channel values cannot
    be recovered from it, and no physical vibration amplitude is disclosed."""
    d = pd.read_csv(HI)
    assert list(d.columns) == ["timestamp", "hours_from_start", "health_indicator"]
    assert d["timestamp"].is_unique
    assert d["health_indicator"].min() < 0, "a z-scored indicator should go negative"
