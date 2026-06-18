# tests/test_diagnostic_console.py
"""
Tests for the diagnostic console stack (loaders → alarms → diagnosis → app),
run entirely on the synthetic fixtures so no large downloads are required.
"""

import os
import importlib.util

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(BASE, "data", "raw", "_fixtures")


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures():
    """Generate the synthetic fixtures once if they are not already present."""
    metropt = os.path.join(FIX, "MetroPT3.csv")
    cmapss = os.path.join(FIX, "CMAPSS", "train_FD001.txt")
    if not (os.path.exists(metropt) and os.path.exists(cmapss)):
        path = os.path.join(BASE, "scripts", "make_demo_fixtures.py")
        spec = importlib.util.spec_from_file_location("make_demo_fixtures", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
    yield


# ── Loaders ───────────────────────────────────────────────────────────────────

def test_metropt_loads_with_expected_parameters():
    from src.metropt_preprocessing import load_metropt
    b = load_metropt()
    assert b.source == "fixture"
    assert len(b.df) > 100
    # core physical parameters present
    for col in ["Oil_temperature", "Motor_current", "TP3", "Reservoirs"]:
        assert col in b.parameters
    assert "Temperature" in b.groups() and "Pressure" in b.groups()
    assert b.health_params, "health params must be non-empty"
    # every parameter has a colour assigned (deterministic theme)
    assert all(b.parameters[c]["color"].startswith("#") for c in b.param_cols())


def test_cmapss_loads_one_unit():
    from src.cmapss_preprocessing import load_cmapss
    b = load_cmapss(unit=1)
    assert b.time_kind == "cycle"
    assert b.meta["failure_cycle"] == int(b.df["cycle"].max())
    assert len(b.meta["units_available"]) >= 1
    # full gas-path spread
    for g in ["Temperature", "Pressure", "Speed", "Flow"]:
        assert g in b.groups()


def test_metropt_missing_file_raises_clear_error():
    from src.metropt_preprocessing import load_metropt
    with pytest.raises(FileNotFoundError):
        load_metropt(path=os.path.join(BASE, "data", "raw", "MetroPT3", "does_not_exist.csv"))


# ── Alarms ────────────────────────────────────────────────────────────────────

def test_metropt_alarms_detect_injected_failure():
    from src.metropt_preprocessing import load_metropt
    from src.diagnosis import extract_alarms
    b = load_metropt()
    res = extract_alarms(b, percentile=99, persistence=3)
    assert res["threshold"] > 0
    assert len(res["events"]) >= 1
    # events are ordered and within range
    for e in res["events"]:
        assert 0 <= e.index < len(b.df)
        assert e.severity in ("warning", "critical")


# ── Diagnosis ─────────────────────────────────────────────────────────────────

def test_diagnosis_ranks_contributions_and_matches_signature():
    from src.metropt_preprocessing import load_metropt
    from src.diagnosis import extract_alarms, diagnose
    b = load_metropt()
    res = extract_alarms(b, percentile=99, persistence=3)
    diag = diagnose(b, res["events"][0])
    # contributions sorted by |z| descending
    zs = [abs(c.z) for c in diag.contributions]
    assert zs == sorted(zs, reverse=True)
    # percentages are a valid share
    assert all(0 <= c.pct <= 100 for c in diag.contributions)
    # the air-leak signature should fire near the injected event (pressure↓, temp/current↑)
    assert diag.cause and diag.recommendation
    assert diag.signature is not None


def test_diagnosis_handles_no_signature_gracefully():
    """A flat/odd pattern still yields a generic, non-empty diagnosis."""
    from src.cmapss_preprocessing import load_cmapss
    from src.diagnosis import extract_alarms, diagnose
    b = load_cmapss(unit=1)
    res = extract_alarms(b, percentile=95, persistence=3)
    if res["events"]:
        diag = diagnose(b, res["events"][0])
        assert diag.cause and diag.recommendation
        assert isinstance(diag.confidence, str)


# ── App + figures ─────────────────────────────────────────────────────────────

def test_app_builds_with_callbacks():
    pytest.importorskip("dash")
    from src.diagnostic_console import build_app
    app = build_app()
    assert len(app.callback_map) >= 6


def test_figure_builders_return_figures_for_both_datasets():
    pytest.importorskip("plotly")
    import src.diagnostic_console as dc
    from src.diagnosis import diagnose
    dc.build_app()
    for ds, unit, pct in [("MetroPT-3", "APU", 99), ("C-MAPSS", 1, 95)]:
        b = dc.SERVICE.bundle(ds, unit)
        res = dc.SERVICE.alarms(ds, unit, pct)
        assert res["events"], f"{ds}: expected at least one alarm"
        alarm = res["events"][-1]
        diag = diagnose(b, alarm)
        params = b.health_params[:5]
        assert len(dc.build_overlay(b, params, alarm, normalize=True).data) >= 1
        assert len(dc.build_health_fig(b, res, alarm).data) >= 1
        assert len(dc.build_contrib(diag).data) == 1
        assert dc.build_relationship(b, params, alarm).data[0].type == "heatmap"
        assert len(dc.build_scatter(b, diag).data) == 2


def test_pill_toggle_logic():
    from src.diagnostic_console import _apply_toggle
    cols = ["a", "b", "c", "d"]
    default = ["a", "b"]
    # non-pill trigger (dataset change) resets to default, preserving column order
    assert _apply_toggle(["c"], "dataset", default, cols) == ["a", "b"]
    # clicking an inactive pill adds it
    assert _apply_toggle(["a"], {"type": "trends-pill", "name": "c"}, default, cols) == ["a", "c"]
    # clicking an active pill removes it
    assert _apply_toggle(["a", "c"], {"type": "trends-pill", "name": "a"}, default, cols) == ["c"]


def test_render_pills_marks_active_state():
    import src.diagnostic_console as dc
    dc.build_app()
    b = dc.SERVICE.bundle("MetroPT-3", "APU")
    active = b.health_params[:3]
    wrap = dc._render_pills("trends", b, active)
    buttons = wrap.children
    assert len(buttons) == len(dc._ordered_cols(b))
    on = [btn for btn in buttons if "on" in btn.className]
    assert len(on) == len(active)


def test_pdf_report_is_generated():
    pytest.importorskip("matplotlib")
    import src.diagnostic_console as dc
    from src.diagnosis import diagnose
    dc.build_app()
    b = dc.SERVICE.bundle("MetroPT-3", "APU")
    res = dc.SERVICE.alarms("MetroPT-3", "APU", 99)
    diag = diagnose(b, res["events"][0])
    pdf = dc.build_pdf(b, diag)
    assert isinstance(pdf, (bytes, bytearray)) and pdf[:4] == b"%PDF"
