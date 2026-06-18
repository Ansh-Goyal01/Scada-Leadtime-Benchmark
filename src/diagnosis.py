# src/diagnosis.py
"""
Alarm extraction + explainable root-cause diagnosis for the diagnostic console.
==============================================================================

This is the layer the mentor actually asked for: when an alarm fires, the
engineer should see *which parameters drove it* and *what to do about it* —
without driving to the site.

Pipeline
--------
1. ``compute_health_score`` — collapse the machine's health parameters into one
   multivariate deviation score (RMS of per-parameter z-scores vs a healthy
   baseline). Direction-agnostic: an abnormal rise OR drop both raise it.
2. ``extract_alarms`` — threshold that score (reusing src/thresholds.py, the same
   machinery as the lead-time benchmark) with persistence, and return the onset of
   each alarm episode as a clickable event.
3. ``diagnose`` — at a chosen alarm, rank every parameter by how far it deviated
   from baseline (a transparent contribution score — NOT a black box), then match
   the deviation pattern against a curated failure-signature library to produce a
   plain-language probable cause and recommended fix.

The contribution scores are standardized deviations, fully inspectable; the
signature library is explicit rules. Nothing here is opaque — by design, because
the whole point is explainability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

import numpy as np
import pandas as pd

from src.thresholds import compute_threshold, generate_alarm_signal
from src.console_data import MachineBundle

logger = logging.getLogger(__name__)

_EPS = 1e-9


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class AlarmEvent:
    index: int                 # row index of the alarm onset
    time: Any                  # timestamp or cycle of onset
    score: float               # health score at onset
    threshold: float           # decision threshold
    severity: str              # "warning" | "critical"
    top_param: str             # parameter with the largest deviation at onset
    top_param_label: str


@dataclass
class ParamContribution:
    col: str
    label: str
    group: str
    unit: str
    baseline: float            # healthy-baseline mean
    value: float               # value at alarm
    z: float                   # standardized deviation (signed)
    direction: str             # "up" | "down" | "flat"
    pct: float                 # share of total deviation (0..100)


@dataclass
class Diagnosis:
    alarm: AlarmEvent
    contributions: List[ParamContribution]
    cause: str                 # probable-cause headline
    explanation: str           # plain-language reasoning
    recommendation: str        # recommended fix / next action
    signature: Optional[str]   # matched signature name, or None (generic)
    confidence: str            # "high" | "moderate" | "low"
    matched_count: int = 0     # signature patterns satisfied (0 if generic)
    pattern_count: int = 0     # signature patterns required (0 if generic)
    matched_labels: List[str] = field(default_factory=list)   # contributors that matched
    ambiguous_labels: List[str] = field(default_factory=list)  # required-but-weak contributors


# ── Health score + alarm extraction ───────────────────────────────────────────

def _baseline_stats(bundle: MachineBundle, cols: List[str],
                    baseline_frac: float) -> Dict[str, tuple]:
    n = len(bundle.df)
    k = max(5, int(n * baseline_frac))
    base = bundle.df.iloc[:k]
    stats = {}
    for c in cols:
        x = pd.to_numeric(base[c], errors="coerce").to_numpy()
        x = x[np.isfinite(x)]
        if len(x) == 0:
            stats[c] = (0.0, 0.0)
        else:
            stats[c] = (float(np.mean(x)), float(np.std(x)))
    return stats


def compute_health_score(bundle: MachineBundle,
                         baseline_frac: float = 0.2) -> Dict[str, Any]:
    """
    Multivariate health score = RMS of per-parameter z-scores vs healthy baseline.

    Returns dict: {score (np.ndarray), stats (per-col mean/std), cols, baseline_n}.
    """
    cols = [c for c in bundle.health_params if c in bundle.df.columns]
    if not cols:
        cols = bundle.param_cols(important_only=True) or bundle.param_cols()
    stats = _baseline_stats(bundle, cols, baseline_frac)

    zmat = []
    for c in cols:
        mu, sd = stats[c]
        x = pd.to_numeric(bundle.df[c], errors="coerce").to_numpy()
        if sd < _EPS:
            z = np.zeros(len(x))
        else:
            z = (x - mu) / sd
        zmat.append(z)
    zmat = np.vstack(zmat) if zmat else np.zeros((1, len(bundle.df)))
    score = np.sqrt(np.nanmean(zmat ** 2, axis=0))
    score = np.nan_to_num(score, nan=0.0)
    return {"score": score, "stats": stats, "cols": cols,
            "baseline_n": max(5, int(len(bundle.df) * baseline_frac))}


def extract_alarms(bundle: MachineBundle,
                   percentile: float = 99.0,
                   persistence: int = 3,
                   baseline_frac: float = 0.2,
                   min_separation: int = 5) -> Dict[str, Any]:
    """
    Detect alarm episodes on the health score. Returns dict with the score, the
    threshold, and a list[AlarmEvent] (one per episode onset).
    """
    hs = compute_health_score(bundle, baseline_frac=baseline_frac)
    score = hs["score"]
    base_n = hs["baseline_n"]
    base_scores = score[:base_n]
    if len(base_scores) < 3 or np.allclose(base_scores, base_scores[0]):
        # Degenerate baseline → fall back to a global percentile so we still alarm.
        threshold = float(np.percentile(score, percentile))
    else:
        threshold = compute_threshold(base_scores, strategy="percentile",
                                      percentile=percentile)
    # Guard: threshold must exceed baseline noise floor.
    threshold = max(threshold, float(np.percentile(score[:base_n], 95)) + _EPS)

    alarm = generate_alarm_signal(score, threshold, persistence=persistence)

    events: List[AlarmEvent] = []
    last_onset = -10 ** 9
    for i in range(len(alarm)):
        if alarm[i] and (i == 0 or not alarm[i - 1]):
            if i - last_onset < min_separation:
                continue
            last_onset = i
            top_col, top_lbl = _top_param_at(bundle, hs, i)
            sev = "critical" if score[i] >= 2.0 * threshold else "warning"
            events.append(AlarmEvent(
                index=i, time=bundle.df[bundle.time_col].iloc[i],
                score=float(score[i]), threshold=float(threshold),
                severity=sev, top_param=top_col, top_param_label=top_lbl,
            ))
    logger.info("%s: %d alarm episode(s) at percentile %.1f",
                bundle.dataset, len(events), percentile)
    return {"score": score, "threshold": threshold, "events": events,
            "alarm": alarm, "stats": hs["stats"], "cols": hs["cols"]}


def _top_param_at(bundle: MachineBundle, hs: Dict[str, Any], idx: int):
    stats = hs["stats"]
    best_col, best_z = None, -1.0
    for c in hs["cols"]:
        mu, sd = stats[c]
        if sd < _EPS:
            continue
        z = abs((float(bundle.df[c].iloc[idx]) - mu) / sd)
        if z > best_z:
            best_z, best_col = z, c
    if best_col is None:
        best_col = hs["cols"][0]
    return best_col, bundle.parameters[best_col]["label"]


# ── Root-cause diagnosis ──────────────────────────────────────────────────────

def diagnose(bundle: MachineBundle,
             alarm: AlarmEvent,
             baseline_frac: float = 0.2,
             eval_window: int = 3,
             top_n: int = 6) -> Diagnosis:
    """
    Rank parameter contributions at an alarm and map them to a probable cause.

    The contribution of each parameter is its standardized deviation |z| from the
    healthy baseline, measured over a short window at the alarm. Contributions are
    normalized to a percentage share so the UI can show "X explains N% of this alarm".
    """
    # Focus the root-cause ranking on diagnostic parameters (exclude digital flags,
    # operating settings and near-constant channels), falling back to all if none.
    cols = bundle.param_cols(important_only=True) or bundle.param_cols()
    stats = _baseline_stats(bundle, cols, baseline_frac)

    i0 = alarm.index
    i1 = min(len(bundle.df), i0 + max(1, eval_window))
    window = bundle.df.iloc[i0:i1]

    contribs: List[ParamContribution] = []
    for c in cols:
        mu, sd = stats[c]
        val = float(pd.to_numeric(window[c], errors="coerce").mean())
        if sd < _EPS or not np.isfinite(val):
            z = 0.0
        else:
            z = (val - mu) / sd
        direction = "up" if z > 0.5 else ("down" if z < -0.5 else "flat")
        p = bundle.parameters[c]
        contribs.append(ParamContribution(
            col=c, label=p["label"], group=p["group"], unit=p.get("unit", ""),
            baseline=mu, value=val, z=float(z), direction=direction, pct=0.0,
        ))

    total = sum(abs(c.z) for c in contribs) or 1.0
    for c in contribs:
        c.pct = 100.0 * abs(c.z) / total
    contribs.sort(key=lambda c: abs(c.z), reverse=True)
    contribs = contribs[:top_n]

    sig = _match_signature(bundle.dataset, contribs)
    if sig is not None:
        cause, explanation, recommendation, name, conf, detail = sig
    else:
        cause, explanation, recommendation, name, conf = _generic_diagnosis(contribs)
        # Generic path: the two strongest contributors are the "matched" evidence.
        strong = [c.label for c in contribs if abs(c.z) >= 2.0][:3]
        detail = {"matched_count": 0, "pattern_count": 0,
                  "matched_labels": strong, "ambiguous_labels": []}

    return Diagnosis(alarm=alarm, contributions=contribs, cause=cause,
                     explanation=explanation, recommendation=recommendation,
                     signature=name, confidence=conf,
                     matched_count=detail["matched_count"],
                     pattern_count=detail["pattern_count"],
                     matched_labels=detail["matched_labels"],
                     ambiguous_labels=detail["ambiguous_labels"])


# ── Failure-signature library ─────────────────────────────────────────────────
# Each signature is an explicit rule: a list of (selector, direction) patterns the
# deviation must match. selector is a column name OR ("group", <GroupName>). A
# signature matches when ALL its patterns are satisfied by some contributor with
# |z| >= min_z. The most specific matching signature (most patterns) wins.

def _sel_match(contrib: ParamContribution, selector) -> bool:
    if isinstance(selector, tuple) and selector[0] == "group":
        return contrib.group == selector[1]
    return contrib.col == selector


def _pattern_ok(contribs, selector, direction, min_z) -> bool:
    for c in contribs:
        if _sel_match(c, selector) and abs(c.z) >= min_z and c.direction == direction:
            return True
    return False


def _pattern_evidence(contribs, selector, direction, min_z):
    """Return (matched_label, ambiguous_label) for a single pattern.

    matched_label: label of the strongest contributor that fully satisfies the
    pattern (right direction AND |z| >= min_z), else None.
    ambiguous_label: label of a contributor that points the right way but is too
    weak (0 < |z| < min_z), surfaced so the UI can say *why* confidence isn't higher.
    """
    matched, ambiguous = None, None
    best_match_z, best_amb_z = -1.0, -1.0
    for c in contribs:
        if not _sel_match(c, selector) or c.direction != direction:
            continue
        az = abs(c.z)
        if az >= min_z and az > best_match_z:
            best_match_z, matched = az, c.label
        elif az < min_z and az > best_amb_z:
            best_amb_z, ambiguous = az, c.label
    return matched, ambiguous


METROPT_SIGNATURES = [
    {
        "name": "Air leak / compressor overwork",
        "patterns": [(("group", "Pressure"), "down"), ("Motor_current", "up"),
                     ("Oil_temperature", "up")],
        "min_z": 1.5,
        "cause": "Probable air leak downstream — the compressor is overworking to hold pressure.",
        "explanation": "System pressure is falling while motor current and oil temperature "
                       "climb together: the unit is running harder and hotter to compensate "
                       "for air it cannot retain.",
        "recommendation": "Inspect pipe joints, the drain valve (DV) and tower seals for "
                          "audible/soapy leaks; check the air-intake filter and dryer. "
                          "Confirm no stuck-open drain before restarting under load.",
    },
    {
        "name": "Compressor overheating",
        "patterns": [("Oil_temperature", "up"), ("Motor_current", "up")],
        "min_z": 2.0,
        "cause": "Compressor overheating — cooling or lubrication is inadequate.",
        "explanation": "Oil temperature and motor current are both elevated with no matching "
                       "pressure loss, pointing to a cooling/lubrication fault rather than a leak.",
        "recommendation": "Check oil level and oil-cooler airflow, verify ambient ventilation, "
                          "and inspect the lubrication circuit. Reduce duty until temperature "
                          "returns to baseline.",
    },
    {
        "name": "Electrical overload",
        "patterns": [("Motor_current", "up")],
        "min_z": 2.5,
        "cause": "Motor electrical overload — mechanical or supply-side drag.",
        "explanation": "Motor current is sharply elevated while pressures and temperature stay "
                       "near baseline, suggesting increased mechanical load or a supply imbalance.",
        "recommendation": "Check motor bearings and coupling for drag, verify supply voltage "
                          "balance, and inspect for seized auxiliaries before sustained running.",
    },
    {
        "name": "Pressure-system fault",
        "patterns": [(("group", "Pressure"), "down")],
        "min_z": 2.0,
        "cause": "Pressure-system fault — loss of pneumatic pressure.",
        "explanation": "One or more pressure channels dropped well below baseline without a "
                       "clear thermal/electrical driver.",
        "recommendation": "Trace the affected pressure line, check valves and reservoir for "
                          "leaks, and verify the pressure sensor itself is reading true.",
    },
]

CMAPSS_SIGNATURES = [
    {
        "name": "Hot-section / turbine degradation",
        "patterns": [("sensor_4", "up"), (("group", "Speed"), "up")],
        "min_z": 2.0,
        "cause": "Hot-section degradation — turbine gas-path efficiency is eroding.",
        "explanation": "Exhaust-gas (LPT outlet) temperature is rising and shaft speeds are "
                       "drifting up to hold thrust: classic turbine gas-path wear.",
        "recommendation": "Borescope the HPT/LPT for blade wear and clearance loss; review "
                          "EGT margin trend and schedule hot-section inspection.",
    },
    {
        "name": "HPC efficiency loss / fouling",
        "patterns": [("sensor_3", "up"), ("sensor_11", "up")],
        "min_z": 2.0,
        "cause": "High-pressure-compressor efficiency loss — likely fouling.",
        "explanation": "HPC outlet temperature and static pressure are climbing together, "
                       "indicating the compressor is working harder for the same flow.",
        "recommendation": "Perform a compressor water-wash, inspect inlet/IGV condition, and "
                          "check bleed valve scheduling.",
    },
    {
        "name": "Gas-path degradation (general)",
        "patterns": [(("group", "Temperature"), "up")],
        "min_z": 2.0,
        "cause": "General gas-path degradation — multiple temperatures trending up.",
        "explanation": "Several gas-path temperatures have risen above baseline, consistent "
                       "with accumulated wear across the engine core.",
        "recommendation": "Trend EGT margin, plan a performance restoration at the next "
                          "opportunity, and monitor remaining useful life closely.",
    },
]

_SIGNATURES = {"MetroPT-3": METROPT_SIGNATURES, "C-MAPSS": CMAPSS_SIGNATURES}


def get_signatures(dataset: str) -> list:
    return _SIGNATURES.get(dataset, [])


def _match_signature(dataset: str, contribs: List[ParamContribution]):
    best = None
    best_n = 0
    for sig in get_signatures(dataset):
        if all(_pattern_ok(contribs, sel, d, sig["min_z"]) for sel, d in sig["patterns"]):
            if len(sig["patterns"]) > best_n:
                best, best_n = sig, len(sig["patterns"])
    if best is None:
        return None
    conf = "high" if best_n >= 3 else ("moderate" if best_n == 2 else "low")
    # Evidence breakdown so the UI can justify the confidence level.
    matched_labels, ambiguous_labels = [], []
    for sel, d in best["patterns"]:
        m, a = _pattern_evidence(contribs, sel, d, best["min_z"])
        if m:
            matched_labels.append(m)
        if a and a not in matched_labels:
            ambiguous_labels.append(a)
    # de-dup while preserving order
    matched_labels = list(dict.fromkeys(matched_labels))
    ambiguous_labels = [a for a in dict.fromkeys(ambiguous_labels) if a not in matched_labels]
    detail = {
        "matched_count": len(best["patterns"]),
        "pattern_count": len(best["patterns"]),
        "matched_labels": matched_labels,
        "ambiguous_labels": ambiguous_labels,
    }
    return best["cause"], best["explanation"], best["recommendation"], best["name"], conf, detail


def _generic_diagnosis(contribs: List[ParamContribution]):
    strong = [c for c in contribs if abs(c.z) >= 2.0] or contribs[:2]
    parts = [f"{c.label} {'rose' if c.direction == 'up' else 'fell'} "
             f"({c.z:+.1f}σ from normal)" for c in strong[:3]]
    cause = "Unrecognized deviation pattern — review the top contributors."
    explanation = ("The alarm is driven mainly by: " + "; ".join(parts) +
                   ". This combination does not match a known failure signature.")
    recommendation = ("Inspect the highest-deviation parameters above first. If the "
                      "pattern recurs, capture it as a new failure signature so future "
                      "alarms of this type are diagnosed automatically.")
    return cause, explanation, recommendation, None, "low"


# ── Detection evaluation (vs. ground-truth failure windows) ───────────────────
# Episodic alarms scored against bundle.failure_windows. An alarm "detects" a
# failure if its onset falls within `horizon` BEFORE the window start, or inside
# the window. Lead time = how early (positive) the first detecting alarm fired.

def _to_ts(x):
    return pd.Timestamp(x) if not isinstance(x, pd.Timestamp) else x


def _horizon_delta(time_kind: str, horizon_days: float, horizon_cycles: float):
    """Return the horizon as a comparable delta for this dataset's time kind."""
    if time_kind == "datetime":
        return pd.Timedelta(days=horizon_days)
    return float(horizon_cycles)


def _lead_value(time_kind: str, alarm_time, failure_start):
    """Positive = alarm fired this much BEFORE the failure. Units: hours | cycles."""
    if time_kind == "datetime":
        delta = _to_ts(failure_start) - _to_ts(alarm_time)
        return delta.total_seconds() / 3600.0  # hours
    return float(failure_start) - float(alarm_time)  # cycles


def evaluate_detection(bundle: MachineBundle, res: Dict[str, Any],
                       horizon_days: float = 7.0,
                       horizon_cycles: Optional[float] = None) -> Dict[str, Any]:
    """
    Match alarm onsets to ground-truth failure windows.

    Returns precision/recall/F1, the TP/FP/FN counts, and per-failure lead time.
    A failure is DETECTED if some alarm onset lies within `horizon` before the
    window start (or inside the window). An alarm is a TP if it detects any
    failure, else FP. Failures with no detecting alarm are FN.

    Horizon semantics differ by dataset type:
      • datetime (MetroPT-3): discrete failures spread over time → fixed
        `horizon_days` (default 7) window of credited early warning.
      • cycle (C-MAPSS): a single run-to-failure trajectory whose only failure
        is the terminal point → the whole run degrades toward it, so any
        pre-failure alarm is credited (horizon = full run length).
    """
    events = res.get("events", [])
    windows = list(bundle.failure_windows or [])
    time_kind = bundle.time_kind
    is_dt = time_kind == "datetime"
    if horizon_cycles is None:
        # span the full run so early degradation alarms count as detections
        horizon_cycles = float(len(bundle.df))
    horizon = _horizon_delta(time_kind, horizon_days, horizon_cycles)
    unit = "hours" if is_dt else "cycles"

    def _norm(t):
        return _to_ts(t) if is_dt else float(t)

    alarm_times = [(e, _norm(e.time)) for e in events]
    win_norm = [(_norm(ws), _norm(we)) for ws, we in windows]

    detected = [False] * len(win_norm)
    alarm_is_tp = [False] * len(alarm_times)
    lead_rows = []

    for wi, (ws, we) in enumerate(win_norm):
        earliest = None  # earliest detecting alarm for this failure
        for ai, (ev, at) in enumerate(alarm_times):
            # within horizon before start, or anywhere inside the window
            before_ok = (ws - at) <= horizon and at <= we
            inside_ok = ws <= at <= we
            if before_ok or inside_ok:
                detected[wi] = True
                alarm_is_tp[ai] = True
                if earliest is None or at < earliest[1]:
                    earliest = (ev, at)
        if earliest is not None:
            lead = _lead_value(time_kind, earliest[0].time, windows[wi][0])
            lead_rows.append({
                "failureStart": _t_iso(windows[wi][0]),
                "failureEnd": _t_iso(windows[wi][1]),
                "alarmIndex": int(earliest[0].index),
                "alarmTime": _t_iso(earliest[0].time),
                "lead": float(lead),
                "leadUnit": unit,
                "detected": True,
            })
        else:
            lead_rows.append({
                "failureStart": _t_iso(windows[wi][0]),
                "failureEnd": _t_iso(windows[wi][1]),
                "alarmIndex": None, "alarmTime": None,
                "lead": None, "leadUnit": unit, "detected": False,
            })

    # Two distinct levels, kept separate so the numbers stay honest:
    #  • Precision is ALARM-level: of all alarms raised, how many were near a real
    #    failure (true positives) vs. spurious (false positives).
    #  • Recall is FAILURE-level: of all known failures, how many were caught.
    tp_alarms = sum(alarm_is_tp)                 # useful alarms
    fp_alarms = len(alarm_times) - tp_alarms     # spurious alarms
    detected_failures = sum(detected)
    missed_failures = len(win_norm) - detected_failures   # failure-level FN

    precision = tp_alarms / (tp_alarms + fp_alarms) if (tp_alarms + fp_alarms) else 0.0
    recall = detected_failures / len(win_norm) if win_norm else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    leads = [r["lead"] for r in lead_rows if r["lead"] is not None]
    median_lead = float(np.median(leads)) if leads else None

    return {
        # alarm-level
        "tp": int(tp_alarms), "fp": int(fp_alarms),
        # failure-level
        "detectedFailures": int(detected_failures),
        "missedFailures": int(missed_failures),
        "fn": int(missed_failures),  # alias: failure-level false negatives
        "nFailures": len(win_norm), "nAlarms": len(alarm_times),
        "precision": float(precision), "recall": float(recall), "f1": float(f1),
        "medianLead": median_lead, "leadUnit": unit,
        "horizon": horizon_days if is_dt else horizon_cycles,
        "horizonUnit": "days" if is_dt else "cycles",
        "leadTimes": lead_rows,
        "hasGroundTruth": len(win_norm) > 0,
    }


def lead_time_for_alarm(bundle: MachineBundle, alarm: AlarmEvent):
    """Lead time from this alarm onset to the NEXT failure window start.

    Returns {value, unit, failureStart, late} or None if there is no ground
    truth or no failure at/after this alarm. ``late`` is True when the alarm
    fired inside or after the failure window (non-positive lead).
    """
    windows = list(bundle.failure_windows or [])
    if not windows:
        return None
    is_dt = bundle.time_kind == "datetime"
    at = _to_ts(alarm.time) if is_dt else float(alarm.time)

    # nearest failure whose START is >= alarm time (the one this alarm could warn of),
    # else fall back to the window the alarm sits inside / just after.
    best = None
    for ws, we in windows:
        wsn = _to_ts(ws) if is_dt else float(ws)
        wen = _to_ts(we) if is_dt else float(we)
        lead = _lead_value(bundle.time_kind, alarm.time, ws)
        # candidate if alarm is before window end (can still pertain to it)
        if at <= wen:
            if best is None or wsn < best[0]:
                best = (wsn, ws, we, lead)
    if best is None:
        return None
    _, ws, we, lead = best
    return {
        "value": float(lead),
        "unit": "hours" if is_dt else "cycles",
        "failureStart": _t_iso(ws),
        "failureEnd": _t_iso(we),
        "late": lead <= 0,
    }


def _t_iso(x):
    return x.isoformat() if hasattr(x, "isoformat") else float(x)
