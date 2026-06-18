# src/console_data.py
"""
Shared data contract for the diagnostic console (MetroPT-3 + C-MAPSS).
=====================================================================

Both multivariate machines (the MetroPT-3 air compressor and the C-MAPSS
turbofan) are loaded into a single, console-friendly structure — the
``MachineBundle`` — so the alarm engine (``src/diagnosis.py``) and the Dash
app (``src/diagnostic_console.py``) work identically regardless of which
machine is selected.

This is deliberately separate from the vibration ``RunBundle`` in
``src/datasets.py``: that contract is channel-centric (``rms_ch{i}``) and aimed
at the lead-time benchmark, whereas the console needs *named physical
parameters* (pressure, temperature, current, speed, flow) with units, colors
and grouping for the at-a-glance diagnostic view.

A ``MachineBundle`` carries:
  * ``df``           — tidy, time-sorted frame; one column per parameter + a time column
  * ``parameters``   — registry: column -> {label, unit, color, group, type, important}
  * ``failure_windows`` — list of (start, end) ground-truth degradation/failure spans
  * ``health_params``   — the parameters used to build the multivariate alarm signal

Nothing here imports Dash, so loaders and tests stay UI-free.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ── Color system (dark-industrial theme) ──────────────────────────────────────
# Each parameter GROUP gets a coherent hue family; parameters within a group are
# assigned distinct, evenly-spaced shades so a "Temperature" trace always reads as
# warm and a "Pressure" trace always reads as cool — professional and legible on
# a dark slate background.
GROUP_PALETTE: Dict[str, List[str]] = {
    "Temperature": ["#f97316", "#fb923c", "#fdba74", "#ea580c", "#f59e0b"],
    "Pressure":    ["#38bdf8", "#0ea5e9", "#7dd3fc", "#0284c7", "#22d3ee"],
    "Current":     ["#a855f7", "#c084fc", "#9333ea"],
    "Voltage":     ["#e879f9", "#d946ef"],
    "Speed":       ["#34d399", "#10b981", "#6ee7b7", "#059669"],
    "Flow":        ["#facc15", "#eab308", "#fde047"],
    "Vibration":   ["#f43f5e", "#fb7185", "#e11d48", "#fda4af"],
    "Setting":     ["#94a3b8", "#cbd5e1", "#64748b"],
    "Digital":     ["#64748b", "#94a3b8", "#475569", "#cbd5e1"],
    "Other":       ["#60a5fa", "#818cf8", "#a78bfa", "#f472b6", "#4ade80"],
}

# Stable order in which groups are presented in the UI.
GROUP_ORDER: List[str] = [
    "Temperature", "Pressure", "Current", "Voltage",
    "Speed", "Flow", "Vibration", "Setting", "Digital", "Other",
]


@dataclass
class MachineBundle:
    """A single machine's full diagnostic record."""
    df: pd.DataFrame                       # time-sorted; parameter cols + time_col
    parameters: Dict[str, Dict[str, Any]]  # col -> {label, unit, color, group, type, important}
    time_col: str                          # name of the time/index column in df
    time_kind: str                         # "datetime" | "cycle"
    dataset: str                           # "MetroPT-3" | "C-MAPSS"
    unit_label: str                        # e.g. "Air Production Unit (APU)" / "Engine #1"
    health_params: List[str]               # parameters that drive the alarm signal
    failure_windows: List[Tuple] = field(default_factory=list)   # [(start, end), ...]
    source: str = "fixture"                # "real" | "fixture"
    meta: dict = field(default_factory=dict)

    # ── convenience accessors ────────────────────────────────────────────────
    def param_cols(self, important_only: bool = False) -> List[str]:
        cols = [c for c in self.df.columns if c in self.parameters]
        if important_only:
            cols = [c for c in cols if self.parameters[c].get("important")]
        return cols

    def groups(self) -> List[str]:
        present = {self.parameters[c]["group"] for c in self.param_cols()}
        return [g for g in GROUP_ORDER if g in present]

    def label(self, col: str) -> str:
        p = self.parameters.get(col, {})
        unit = p.get("unit")
        base = p.get("label", col)
        return f"{base} ({unit})" if unit else base

    def time_values(self) -> pd.Series:
        return self.df[self.time_col]

    def nearest_index(self, t) -> int:
        """Row index whose time is closest to ``t`` (robust to exact-match misses)."""
        tv = self.df[self.time_col].values
        if self.time_kind == "datetime":
            t = pd.Timestamp(t)
            diffs = np.abs(pd.to_datetime(tv).view("int64") - t.value)
        else:
            diffs = np.abs(tv.astype("float64") - float(t))
        return int(np.argmin(diffs))


def build_registry(spec: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Turn a per-parameter spec list into a color-assigned registry.

    Each spec entry: {col, label, unit, group, type?, important?}. Colors are
    assigned per group from GROUP_PALETTE so the result is visually coherent and
    deterministic (no random colors → reproducible screenshots for the paper).
    """
    registry: Dict[str, Dict[str, Any]] = {}
    group_counts: Dict[str, int] = {}
    for entry in spec:
        col = entry["col"]
        group = entry.get("group", "Other")
        palette = GROUP_PALETTE.get(group, GROUP_PALETTE["Other"])
        idx = group_counts.get(group, 0)
        color = palette[idx % len(palette)]
        group_counts[group] = idx + 1
        registry[col] = {
            "label": entry.get("label", col),
            "unit": entry.get("unit", ""),
            "color": entry.get("color", color),
            "group": group,
            "type": entry.get("type", group.lower()),
            "important": bool(entry.get("important", True)),
        }
    return registry


def validate_bundle(b: MachineBundle) -> MachineBundle:
    """
    Boundary validation so the UI never receives a malformed bundle.

    Raises ValueError with a clear, actionable message on any structural problem
    (missing time column, no parameters, empty frame, non-monotonic time).
    """
    if b.df is None or len(b.df) == 0:
        raise ValueError(f"{b.dataset}: loaded an empty frame — check the source file.")
    if b.time_col not in b.df.columns:
        raise ValueError(f"{b.dataset}: time column {b.time_col!r} missing from data.")
    present = [c for c in b.parameters if c in b.df.columns]
    if not present:
        raise ValueError(
            f"{b.dataset}: none of the declared parameters are present in the data. "
            f"Declared={list(b.parameters)[:6]}..., have={list(b.df.columns)[:6]}..."
        )
    missing = [c for c in b.parameters if c not in b.df.columns]
    if missing:
        logger.warning("%s: dropping %d declared parameter(s) absent from data: %s",
                       b.dataset, len(missing), missing)
        for c in missing:
            b.parameters.pop(c, None)
    if not b.health_params:
        b.health_params = b.param_cols(important_only=True) or b.param_cols()[:5]
    b.health_params = [c for c in b.health_params if c in b.parameters]
    # Ensure time-sorted; coerce numeric parameter columns.
    b.df = b.df.sort_values(b.time_col).reset_index(drop=True)
    for c in b.param_cols():
        b.df[c] = pd.to_numeric(b.df[c], errors="coerce")
    return b
