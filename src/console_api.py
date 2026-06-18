# src/console_api.py
"""
JSON API for the React + Recharts SCADA Diagnostic Console.
===========================================================

This is a thin Flask layer over the EXISTING, UNCHANGED data + diagnosis pipeline
(``src/console_data.py``, ``src/diagnosis.py``, ``src/*_preprocessing.py``). It does
**not** re-implement any analytics: it imports ``extract_alarms``, ``diagnose`` and
``build_pdf`` and serializes their outputs to JSON for the browser app in
``frontend/``.

The legacy Dash app (``src/diagnostic_console.py``) is left fully intact — this module
is additive. Run:

    python -m src.console_api            # http://127.0.0.1:8051

then in another shell:

    cd frontend && npm install && npm run dev   # http://127.0.0.1:5173

The Vite dev server proxies ``/api`` to this server (see frontend/vite.config.js), so
there are no CORS issues in development; permissive CORS headers are added anyway for
flexibility.
"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.console_data import MachineBundle, GROUP_ORDER
from src.diagnosis import (
    extract_alarms, diagnose, evaluate_detection, lead_time_for_alarm,
)

# Reuse the legacy app's helpers verbatim — no analytics are duplicated here.
from src.diagnostic_console import (
    _Service, _decimate, _alarm_spans, _ordered_cols, build_pdf,
)

logger = logging.getLogger(__name__)

SERVICE: Optional[_Service] = None


# ── serialization helpers ──────────────────────────────────────────────────────

def _t(x) -> Any:
    """Time value -> JSON-friendly: ISO string for datetimes, float for cycles."""
    if hasattr(x, "isoformat"):
        return x.isoformat()
    try:
        return float(x)
    except (TypeError, ValueError):
        return str(x)


def _tstr(x) -> str:
    return x.strftime("%Y-%m-%d %H:%M") if hasattr(x, "strftime") else f"cycle {int(x)}"


def _num(x) -> Optional[float]:
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _event_json(e) -> dict:
    return {
        "index": int(e.index),
        "time": _t(e.time),
        "timeLabel": _tstr(e.time),
        "score": float(e.score),
        "threshold": float(e.threshold),
        "severity": e.severity,
        "topParam": e.top_param,
        "topParamLabel": e.top_param_label,
    }


def _registry_json(b: MachineBundle) -> List[dict]:
    out = []
    for col in _ordered_cols(b):
        m = b.parameters[col]
        out.append({
            "col": col,
            "label": m["label"],
            "unit": m.get("unit", ""),
            "color": m["color"],
            "group": m["group"],
            "important": bool(m.get("important", True)),
        })
    return out


def _series_payload(dataset: str, unit, percentile: float) -> dict:
    b = SERVICE.bundle(dataset, unit)
    res = SERVICE.alarms(dataset, unit, percentile)

    df = _decimate(b.df)
    keep_idx = df.index.to_numpy()
    t = [_t(v) for v in df[b.time_col]]

    cols = _ordered_cols(b)
    samples: Dict[str, List[Optional[float]]] = {}
    for c in cols:
        y = pd.to_numeric(df[c], errors="coerce")
        samples[c] = [_num(v) for v in y]

    # health score (decimated to match the same time axis used by the overview chart)
    score = res["score"]
    sidx = np.arange(len(score))
    skeep = sidx[:: int(np.ceil(len(sidx) / 6000))] if len(sidx) > 6000 else sidx
    health_t = [_t(v) for v in b.df[b.time_col].iloc[skeep]]
    health_v = [_num(v) for v in score[skeep]]

    spans = [{"start": _t(ws), "end": _t(we)} for ws, we in _alarm_spans(b, res)]
    fwins = [{"start": _t(ws), "end": _t(we), "point": ws == we}
             for ws, we in b.failure_windows]

    # baseline stats per parameter (first 20%) so the UI can show σ + % deviation badges
    k = max(5, int(len(b.df) * 0.2))
    base = b.df.iloc[:k]
    baseline: Dict[str, dict] = {}
    for c in cols:
        x = pd.to_numeric(base[c], errors="coerce").to_numpy()
        x = x[np.isfinite(x)]
        mu = float(np.mean(x)) if len(x) else 0.0
        sd = float(np.std(x)) if len(x) else 0.0
        baseline[c] = {"mean": mu, "std": sd}

    # healthy-baseline window span (for chart shading + threshold provenance)
    baseline_window = {
        "start": _t(b.df[b.time_col].iloc[0]),
        "end": _t(b.df[b.time_col].iloc[min(k, len(b.df)) - 1]),
        "nSamples": int(k),
        "frac": 0.2,
    }

    # detection quality vs ground-truth failure windows. Paper datasets report the
    # FAR-gated lead-time metric (matching the paper); MetroPT/C-MAPSS keep the
    # legacy precision/recall evaluator.
    from src.diagnostic_console import PAPER_DATASETS
    if dataset in PAPER_DATASETS:
        from src.console_paper_metric import evaluate_paper_run
        from src.datasets import default_runs
        run = unit if unit not in (None, "", "APU") else default_runs(dataset)[0]
        detection = {"metric": "far_gated_lead_time",
                     "paper": evaluate_paper_run(dataset, run, percentile=percentile)}
    else:
        detection = evaluate_detection(b, res)

    return {
        "dataset": dataset,
        "unitLabel": b.unit_label,
        "source": b.source,
        "isSimulated": b.source == "fixture",
        "timeKind": b.time_kind,
        "nSamples": int(len(b.df)),
        "time": t,
        "samples": samples,
        "parameters": _registry_json(b),
        "healthParams": list(b.health_params),
        "baseline": baseline,
        "baselineWindow": baseline_window,
        "health": {"time": health_t, "value": health_v,
                   "threshold": float(res["threshold"]),
                   "thresholdMeta": {
                       "strategy": "percentile",
                       "percentile": float(percentile),
                       "baselineN": int(k),
                       "totalN": int(len(b.df)),
                   }},
        "alarmSpans": spans,
        "failureWindows": fwins,
        "detection": detection,
        "events": [_event_json(e) for e in res["events"]],
        "percentile": float(percentile),
    }


def _diagnosis_payload(dataset: str, unit, percentile: float, alarm_idx: int) -> dict:
    b = SERVICE.bundle(dataset, unit)
    res = SERVICE.alarms(dataset, unit, percentile)
    alarm = next((e for e in res["events"] if e.index == alarm_idx), None)
    if alarm is None:
        return {"hasAlarm": False}
    diag = diagnose(b, alarm)

    contribs = [{
        "col": c.col, "label": c.label, "group": c.group, "unit": c.unit,
        "baseline": float(c.baseline), "value": float(c.value),
        "z": float(c.z), "direction": c.direction, "pct": float(c.pct),
    } for c in diag.contributions]

    # correlation matrix around the alarm (mirrors build_relationship)
    sel = [c.col for c in diag.contributions if c.col in b.df.columns]
    corr_payload = None
    if len(sel) >= 2:
        half = max(10, int(len(b.df) * 0.04))
        sub = b.df.iloc[max(0, alarm.index - half):min(len(b.df), alarm.index + half)]
        corr = sub[sel].apply(pd.to_numeric, errors="coerce").corr()
        labels = [b.parameters[c]["label"] for c in sel]
        corr_payload = {
            "labels": labels,
            "cols": sel,
            "matrix": [[_num(v) for v in row] for row in corr.values],
        }

    # scatter of the two strongest signals, phase-colored (mirrors build_scatter)
    scatter_payload = None
    if len(diag.contributions) >= 2:
        cx, cy = diag.contributions[0], diag.contributions[1]
        sdf = _decimate(b.df, max_points=2500)
        xs = pd.to_numeric(sdf[cx.col], errors="coerce")
        ys = pd.to_numeric(sdf[cy.col], errors="coerce")
        ai = alarm.index
        half = max(10, int(len(b.df) * 0.03))
        pts = []
        for orig_i, xv, yv in zip(sdf.index.to_numpy(), xs, ys):
            xn, yn = _num(xv), _num(yv)
            if xn is None or yn is None:
                continue
            phase = ("before" if orig_i < ai - half
                     else ("after" if orig_i > ai + half else "at"))
            pts.append({"x": xn, "y": yn, "phase": phase})
        alarm_pt = {
            "x": _num(b.df[cx.col].iloc[ai]),
            "y": _num(b.df[cy.col].iloc[ai]),
        }
        scatter_payload = {
            "xLabel": b.label(cx.col), "yLabel": b.label(cy.col),
            "points": pts, "alarm": alarm_pt,
        }

    lead = lead_time_for_alarm(b, alarm)

    return {
        "hasAlarm": True,
        "alarm": _event_json(alarm),
        "cause": diag.cause,
        "explanation": diag.explanation,
        "recommendation": diag.recommendation,
        "signature": diag.signature,
        "confidence": diag.confidence,
        "confidenceDetail": {
            "matched": diag.matched_count,
            "total": diag.pattern_count,
            "matchedLabels": diag.matched_labels,
            "ambiguousLabels": diag.ambiguous_labels,
        },
        "leadTime": lead,
        "contributions": contribs,
        "correlation": corr_payload,
        "scatter": scatter_payload,
        "unitLabel": b.unit_label,
        "isSimulated": b.source == "fixture",
    }


_SWEEP_PERCENTILES = [95.0, 96.0, 97.0, 98.0, 99.0, 99.5, 99.9]
_EVAL_CACHE: Dict[tuple, dict] = {}


def _paper_evaluation_payload(dataset: str, unit, percentile: float) -> dict:
    """FAR-gated lead-time metric (paper-faithful) for IMS/ONGC/XJTU/FEMTO."""
    from src.console_paper_metric import evaluate_paper_run
    from src.datasets import default_runs
    run = unit if unit not in (None, "", "APU") else default_runs(dataset)[0]
    paper = evaluate_paper_run(dataset, run, percentile=percentile)
    b = SERVICE.bundle(dataset, unit)
    return {
        "dataset": dataset,
        "unitLabel": b.unit_label,
        "metric": "far_gated_lead_time",
        "hasGroundTruth": paper["hasGroundTruth"],
        "paper": paper,
        "currentPercentile": float(percentile),
    }


def _evaluation_payload(dataset: str, unit, percentile: float) -> dict:
    """Sensitivity sweep: detection quality across alarm percentiles."""
    from src.diagnostic_console import PAPER_DATASETS
    if dataset in PAPER_DATASETS:
        return _paper_evaluation_payload(dataset, unit, percentile)
    key = (dataset, str(unit))
    if key in _EVAL_CACHE:
        sweep = _EVAL_CACHE[key]
    else:
        b = SERVICE.bundle(dataset, unit)
        sweep = []
        for p in _SWEEP_PERCENTILES:
            res = SERVICE.alarms(dataset, unit, p)
            det = evaluate_detection(b, res)
            sweep.append({
                "percentile": p,
                "nAlarms": det["nAlarms"],
                "precision": det["precision"],
                "recall": det["recall"],
                "f1": det["f1"],
                "medianLead": det["medianLead"],
                "leadUnit": det["leadUnit"],
            })
        _EVAL_CACHE[key] = sweep

    b = SERVICE.bundle(dataset, unit)
    current = evaluate_detection(b, SERVICE.alarms(dataset, unit, percentile))
    return {
        "dataset": dataset,
        "unitLabel": b.unit_label,
        "hasGroundTruth": current["hasGroundTruth"],
        "nFailures": current["nFailures"],
        "horizon": current["horizon"],
        "horizonUnit": current["horizonUnit"],
        "current": current,
        "currentPercentile": float(percentile),
        "sweep": sweep,
    }


# ── Flask app ───────────────────────────────────────────────────────────────────

def build_api(metropt_kw=None, cmapss_kw=None):
    from flask import Flask, jsonify, request, Response, send_from_directory
    import os

    global SERVICE
    SERVICE = _Service(metropt_kw=metropt_kw, cmapss_kw=cmapss_kw)

    dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
    app = Flask(__name__, static_folder=dist_dir if os.path.isdir(dist_dir) else None)

    @app.after_request
    def _cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    def _arg(name, default=None):
        v = request.args.get(name, default)
        return v

    @app.get("/api/datasets")
    def datasets():
        from src.diagnostic_console import DATASETS
        out = []
        for d in DATASETS:
            try:
                units = SERVICE.units(d)
            except Exception as e:  # pragma: no cover - defensive
                logger.warning("units(%s) failed: %s", d, e)
                units = []
            out.append({"dataset": d, "units": units})
        return jsonify({"datasets": out})

    @app.get("/api/series")
    def series():
        dataset = _arg("dataset", "MetroPT-3")
        unit = _arg("unit", "APU")
        percentile = float(_arg("percentile", 99))
        try:
            return jsonify(_series_payload(dataset, unit, percentile))
        except Exception as e:
            logger.exception("series failed")
            return jsonify({"error": str(e)}), 500

    @app.get("/api/diagnosis")
    def diagnosis():
        dataset = _arg("dataset", "MetroPT-3")
        unit = _arg("unit", "APU")
        percentile = float(_arg("percentile", 99))
        alarm_raw = _arg("alarm")
        if alarm_raw in (None, "", "null"):
            return jsonify({"hasAlarm": False})
        try:
            return jsonify(_diagnosis_payload(dataset, unit, percentile, int(float(alarm_raw))))
        except Exception as e:
            logger.exception("diagnosis failed")
            return jsonify({"error": str(e)}), 500

    @app.get("/api/evaluation")
    def evaluation():
        dataset = _arg("dataset", "MetroPT-3")
        unit = _arg("unit", "APU")
        percentile = float(_arg("percentile", 99))
        try:
            return jsonify(_evaluation_payload(dataset, unit, percentile))
        except Exception as e:
            logger.exception("evaluation failed")
            return jsonify({"error": str(e)}), 500

    @app.get("/api/report.pdf")
    def report_pdf():
        dataset = _arg("dataset", "MetroPT-3")
        unit = _arg("unit", "APU")
        percentile = float(_arg("percentile", 99))
        alarm_raw = _arg("alarm")
        if alarm_raw in (None, "", "null"):
            return jsonify({"error": "no alarm selected"}), 400
        try:
            b = SERVICE.bundle(dataset, unit)
            res = SERVICE.alarms(dataset, unit, percentile)
            alarm = next((e for e in res["events"] if e.index == int(float(alarm_raw))), None)
            if alarm is None:
                return jsonify({"error": "alarm not found"}), 404
            diag = diagnose(b, alarm)
            pdf = build_pdf(b, diag)
            tag = (alarm.time.strftime("%Y%m%d_%H%M") if hasattr(alarm.time, "strftime")
                   else f"cycle{int(alarm.time)}")
            fname = f"diagnostic_report_{dataset.replace('-', '')}_{tag}.pdf"
            return Response(pdf, mimetype="application/pdf",
                            headers={"Content-Disposition": f"attachment; filename={fname}"})
        except Exception as e:
            logger.exception("report failed")
            return jsonify({"error": str(e)}), 500

    # Serve the built SPA in production (after `npm run build`).
    @app.get("/")
    def index():
        if app.static_folder:
            return send_from_directory(app.static_folder, "index.html")
        return ("<h1>SCADA Diagnostic Console API</h1>"
                "<p>API is running. Build the frontend with "
                "<code>cd frontend &amp;&amp; npm install &amp;&amp; npm run dev</code> "
                "for development, or <code>npm run build</code> for production.</p>")

    @app.get("/<path:path>")
    def assets(path):
        if app.static_folder:
            full = os.path.join(app.static_folder, path)
            if os.path.isfile(full):
                return send_from_directory(app.static_folder, path)
            return send_from_directory(app.static_folder, "index.html")
        return jsonify({"error": "not found"}), 404

    return app


def launch_api(port=8051, debug=False, metropt_kw=None, cmapss_kw=None):
    app = build_api(metropt_kw=metropt_kw, cmapss_kw=cmapss_kw)
    print(f"\n{'='*64}\n  SCADA Console API  ->  http://127.0.0.1:{port}\n"
          f"  Frontend dev: cd frontend && npm install && npm run dev\n{'='*64}\n")
    app.run(debug=debug, port=port, use_reloader=False)


if __name__ == "__main__":
    launch_api()
