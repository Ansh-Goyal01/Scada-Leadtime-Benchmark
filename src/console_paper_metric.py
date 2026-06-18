# src/console_paper_metric.py
"""
Paper-faithful evaluation for the console (FAR-gated lead time).
====================================================================================

The legacy console metric (``src.diagnosis.evaluate_detection``) reports
precision/recall/F1 over a fixed time horizon. The PAPER reports a different,
deliberately ungameable metric: an onset-anchored ``lead_time_hours`` that is
**FAR-gated** — an alarm only counts as a valid early warning if it fires after
the degradation onset AND keeps the pre-onset false-alarm rate within budget
(``src.lead_time.evaluate_method``). A latch-on / always-on detector floods the
pre-onset region and is scored invalid.

To keep the dashboard and the paper telling the SAME story, this module runs the
paper's canonical evaluation path for a single run and returns a JSON-friendly
summary:

    compute_run_onset  →  load_pipeline  →  make_detectors  →  evaluate_method

i.e. the exact pipeline ``src/benchmark.py`` uses, so the numbers reconcile by
construction. Results are cached per (dataset, run, detector, percentile).

Only the paper's four datasets (IMS/ONGC/XJTU-SY/FEMTO) flow through here;
MetroPT-3 / C-MAPSS keep the legacy ``evaluate_detection`` path.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# A single interpretable detector drives the console headline number. CUSUM is a
# standard SPC control chart (reviewer-requested), cheap, deterministic, and a
# faithful stand-in for the "simple monitor" the dashboard presents.
DEFAULT_DETECTOR = "cusum"

_CACHE: Dict[tuple, dict] = {}


def _natural_lead(lead_hours: float, meta: dict) -> Dict[str, Any]:
    """
    Re-express a lead time (in hours, on the run's possibly-synthetic clock) in
    units honest for the dataset.

    Run-to-failure sets (XJTU/FEMTO) use a synthetic uniform clock whose snapshot
    spacing (e.g. 1 min) compresses real elapsed time, so raw "hours" understate
    the warning. ``lead_norm`` (lead ÷ max-achievable-lead) is the clock-invariant
    figure; we surface both plus a fraction-of-life value.
    """
    out = {"hours": (float(lead_hours) if lead_hours == lead_hours else None)}
    interval = meta.get("interval") or meta.get("sampling")
    out["clockNote"] = None
    if interval and meta.get("dataset") in ("XJTU-SY", "FEMTO"):
        out["clockNote"] = (
            f"synthetic {interval} snapshot clock — see normalized lead "
            f"(fraction of degradation window) for the clock-invariant figure"
        )
    return out


def evaluate_paper_run(dataset: str, run_name: str,
                       detector: str = DEFAULT_DETECTOR,
                       percentile: Optional[float] = None,
                       far_budget: float = 0.10) -> Dict[str, Any]:
    """
    Run the paper's FAR-gated lead-time evaluation for one run and return a
    JSON-friendly dict. Cached per (dataset, run, detector, percentile).
    """
    from src.config import THRESHOLD, SPLIT, EXPERIMENT
    pct = float(THRESHOLD["percentile"] if percentile is None else percentile)
    key = (dataset, run_name, detector, round(pct, 2), round(far_budget, 4))
    if key in _CACHE:
        return _CACHE[key]

    from src.benchmark import compute_run_onset, make_detectors
    from src.lead_time import evaluate_method

    info = compute_run_onset(run_name, dataset=dataset)
    onset = info["t_onset"]

    pipe = _load_pipeline_cached(dataset, run_name)
    dets = make_detectors([detector], EXPERIMENT["random_seed"])
    if not dets:
        raise ValueError(f"detector {detector!r} not available")

    res = evaluate_method(
        detector=dets[0],
        X_train=pipe["X_train"], X_test=pipe["X_test"],
        timestamps_test=pipe["ts_test"], failure_time=pipe["failure_time"],
        normal_period_fraction=SPLIT["normal_period_fraction"],
        threshold_strategy=THRESHOLD["strategy"],
        threshold_percentile=pct,
        alarm_persistence=THRESHOLD["alarm_persistence"],
        t_onset=onset, far_budget=far_budget,
        X_cal=pipe.get("X_cal"),
    )

    meta = {"dataset": dataset, "interval": (pipe.get("meta") or {}).get("interval")}
    # carry the run's native sampling for the unit note
    rb_meta = pipe.get("bundle_meta") or {}
    meta["interval"] = rb_meta.get("interval") or rb_meta.get("sampling")

    lead_h = res["lead_time_hours"]
    max_lead = res["max_lead_hours"]
    payload = {
        "dataset": dataset,
        "run": run_name,
        "detector": dets[0].name,
        "detectorShort": dets[0].short_name,
        "metric": "far_gated_lead_time",
        "percentile": pct,
        "farBudget": far_budget,
        # headline, paper-faithful fields
        "validAlarm": bool(res["valid_alarm"]),
        "leadTimeHours": (float(lead_h) if lead_h == lead_h else None),
        "detectionDelayHours": (float(res["detection_delay_hours"])
                                if res["detection_delay_hours"] is not None else None),
        "farPreonsetPct": (float(res["far_preonset_pct"])
                           if res["far_preonset_pct"] == res["far_preonset_pct"] else None),
        "leadNorm": (float(res["lead_norm"]) if res["lead_norm"] == res["lead_norm"] else None),
        "maxLeadHours": (float(max_lead) if max_lead == max_lead else None),
        "alarmRaised": bool(res["alarm_raised"]),
        "tOnset": (str(onset) if onset is not None else None),
        "tFail": str(res["failure_time"]),
        "lead": _natural_lead(lead_h, meta),
        "hasGroundTruth": onset is not None,
    }
    _CACHE[key] = payload
    return payload


_PIPE_CACHE: Dict[tuple, dict] = {}


def _load_pipeline_cached(dataset: str, run_name: str) -> dict:
    key = (dataset, run_name)
    if key in _PIPE_CACHE:
        return _PIPE_CACHE[key]
    from src.datasets import load_run
    from src import load_pipeline
    pipe = load_pipeline(run_name, dataset=dataset)
    # stash the source RunBundle meta (sampling interval) for unit presentation
    try:
        pipe["bundle_meta"] = load_run(dataset, run_name).meta or {}
    except Exception:
        pipe["bundle_meta"] = {}
    _PIPE_CACHE[key] = pipe
    return pipe
