# tests/test_console_paper_alignment.py
"""
The console must tell the SAME story as the paper for the shared datasets.

These tests assert two contracts:
  1. The RunBundle→MachineBundle adapter produces a valid console bundle whose
     ground-truth failure window is anchored to the paper's degradation onset.
  2. The console's FAR-gated lead-time metric (src.console_paper_metric) is
     numerically IDENTICAL to the canonical benchmark path (src.benchmark), so a
     reviewer opening the dashboard sees the paper's exact numbers.

IMS 2nd_test is used: it ships as a cached feature parquet (no large download),
loads in well under a second, and is one of the paper's headline runs.
"""

import os

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMS_PARQUET = os.path.join(BASE, "data", "processed", "2nd_test_features.parquet")

pytestmark = pytest.mark.skipif(
    not os.path.exists(IMS_PARQUET),
    reason="IMS 2nd_test feature parquet not present (run preprocessing first)",
)

DATASET, RUN, DETECTOR = "IMS", "2nd_test", "cusum"


def test_adapter_produces_valid_bundle_with_onset_window():
    from src.console_paper_adapter import load_machine_bundle
    b = load_machine_bundle(DATASET, RUN)

    assert b.source == "real"
    assert b.time_kind == "datetime"
    assert b.health_params, "no health params exposed"
    assert all(c.startswith("rms_ch") for c in b.health_params)
    # every health param is a registered Vibration parameter
    for c in b.health_params:
        assert b.parameters[c]["group"] == "Vibration"

    # ground-truth window = [onset, failure], onset strictly before failure
    assert len(b.failure_windows) == 1
    ws, we = b.failure_windows[0]
    assert ws < we
    assert b.meta["t_onset"] is not None
    assert str(ws) == b.meta["t_onset"]
    assert str(we) == b.meta["failure_time"]


def test_console_metric_reconciles_with_benchmark():
    """Console FAR-gated lead time == canonical benchmark path, bit for bit."""
    from src.console_paper_metric import evaluate_paper_run
    from src.benchmark import run_benchmark

    console = evaluate_paper_run(DATASET, RUN, detector=DETECTOR)

    df = run_benchmark(dataset=DATASET, runs=[RUN], methods=[DETECTOR],
                       factors=[1], modes=["decimate"], save=False)
    row = df[df["short_name"] == DETECTOR].iloc[0]

    assert console["validAlarm"] == bool(row["valid_alarm"])
    assert console["leadTimeHours"] == pytest.approx(row["lead_time_hours"], abs=1e-6)
    assert console["farPreonsetPct"] == pytest.approx(row["far_preonset_pct"], abs=1e-6)
    assert console["tOnset"] == str(row["t_onset"])


def test_paper_datasets_use_far_gated_metric_in_api():
    """/api/evaluation routes paper datasets through the FAR-gated metric."""
    import src.console_api as api
    from src.diagnostic_console import _Service
    api.SERVICE = _Service()
    ev = api._evaluation_payload(DATASET, RUN, 97.5)
    assert ev["metric"] == "far_gated_lead_time"
    assert "paper" in ev
    assert ev["paper"]["detectorShort"] == DETECTOR
