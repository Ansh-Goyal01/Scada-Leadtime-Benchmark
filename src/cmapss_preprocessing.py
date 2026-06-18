# src/cmapss_preprocessing.py
"""
NASA C-MAPSS turbofan loader  →  MachineBundle.
===============================================

C-MAPSS gives the fullest 8-parameter spread — multiple temperatures, pressures,
shaft speeds and flows — on run-to-failure engine trajectories, so it's the
"all gauges lit" companion to the real MetroPT-3 compressor.

Source (download manually — see scripts/download_data.py):
    NASA Turbofan Engine Degradation Simulation Data ("CMAPSSData").
    Place the text files at  data/raw/CMAPSS/{train,test,RUL}_FD00{1..4}.txt

Each row: unit, cycle, op_setting_1..3, sensor_1..21  (whitespace-separated, no header).
One *unit* = one engine flown to failure; we treat a single unit as the machine
trajectory shown in the console, with a selector for the others.
"""

from __future__ import annotations

import os
import logging
from typing import List, Optional

import numpy as np
import pandas as pd

from src.config import BASE_DIR
from src.console_data import MachineBundle, build_registry, validate_bundle

logger = logging.getLogger(__name__)

REAL_DIR    = os.path.join(BASE_DIR, "data", "raw", "CMAPSS")
FIXTURE_DIR = os.path.join(BASE_DIR, "data", "raw", "_fixtures", "CMAPSS")

# Canonical C-MAPSS sensor map (NASA PCoE documentation). label/unit/group, and
# whether the channel is informative on FD001 (constants are kept but de-emphasised).
SENSOR_SPEC = [
    # col,   label,                          unit,     group,         important
    ("sensor_2",  "LPC Outlet Temp (T24)",   "°R",     "Temperature", True),
    ("sensor_3",  "HPC Outlet Temp (T30)",   "°R",     "Temperature", True),
    ("sensor_4",  "LPT Outlet Temp (T50)",   "°R",     "Temperature", True),
    ("sensor_7",  "HPC Outlet Pressure (P30)", "psia", "Pressure",    True),
    ("sensor_11", "HPC Static Pressure (Ps30)", "psia","Pressure",    True),
    ("sensor_6",  "Bypass Pressure (P15)",   "psia",   "Pressure",    False),
    ("sensor_8",  "Physical Fan Speed (Nf)", "rpm",    "Speed",       True),
    ("sensor_9",  "Physical Core Speed (Nc)","rpm",    "Speed",       True),
    ("sensor_13", "Corrected Fan Speed (NRf)","rpm",   "Speed",       True),
    ("sensor_14", "Corrected Core Speed (NRc)","rpm",  "Speed",       True),
    ("sensor_12", "Fuel Flow Ratio (phi)",   "pps/psi","Flow",        True),
    ("sensor_15", "Bypass Ratio (BPR)",      "",       "Flow",        True),
    ("sensor_20", "HPT Coolant Bleed (W31)", "lbm/s",  "Flow",        True),
    ("sensor_21", "LPT Coolant Bleed (W32)", "lbm/s",  "Flow",        True),
    ("sensor_17", "Bleed Enthalpy (htBleed)","",       "Flow",        True),
    # Near-constant on FD001 — present for completeness, not used for alarming.
    ("sensor_1",  "Fan Inlet Temp (T2)",     "°R",     "Temperature", False),
    ("sensor_5",  "Fan Inlet Pressure (P2)", "psia",   "Pressure",    False),
    ("sensor_10", "Engine Pressure Ratio (epr)","",    "Pressure",    False),
    ("sensor_16", "Burner Fuel-Air (farB)",  "",       "Flow",        False),
    ("sensor_18", "Demanded Fan Speed",      "rpm",    "Speed",       False),
    ("sensor_19", "Demanded Corr. Fan Speed","",       "Speed",       False),
    ("op_setting_1", "Altitude Setting",     "",       "Setting",     False),
    ("op_setting_2", "Mach Setting",         "",       "Setting",     False),
    ("op_setting_3", "Throttle Setting",     "",       "Setting",     False),
]

_COLUMNS = ["unit", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"] + \
           [f"sensor_{i}" for i in range(1, 22)]

# Parameters that drive the multivariate alarm (the most diagnostic gas-path signals).
HEALTH_PARAMS = ["sensor_3", "sensor_4", "sensor_7", "sensor_11", "sensor_9", "sensor_15"]


def _resolve_dir() -> tuple:
    if os.path.isdir(REAL_DIR) and any(f.startswith("train_FD") for f in os.listdir(REAL_DIR)):
        return REAL_DIR, "real"
    if os.path.isdir(FIXTURE_DIR) and any(f.startswith("train_FD") for f in os.listdir(FIXTURE_DIR)):
        logger.info("C-MAPSS real files not found; using synthetic fixture.")
        return FIXTURE_DIR, "fixture"
    raise FileNotFoundError(
        "C-MAPSS data not found.\n"
        f"  • Place train_FD001.txt … at: {REAL_DIR}\n"
        f"  • Or generate a fixture:    python scripts/make_demo_fixtures.py"
    )


def list_units(subset: str = "FD001", path: Optional[str] = None) -> List[int]:
    """Return the available engine unit numbers for a subset."""
    base = path or _resolve_dir()[0]
    f = os.path.join(base, f"train_{subset}.txt")
    if not os.path.exists(f):
        raise FileNotFoundError(f"C-MAPSS subset file missing: {f}")
    df = pd.read_csv(f, sep=r"\s+", header=None, usecols=[0], names=["unit"])
    return sorted(int(u) for u in df["unit"].unique())


def load_cmapss(subset: str = "FD001",
                unit: Optional[int] = None,
                path: Optional[str] = None) -> MachineBundle:
    """
    Load one C-MAPSS engine run-to-failure trajectory into a MachineBundle.

    Parameters
    ----------
    subset : str
        One of FD001..FD004 (FD001 = single condition / single fault: cleanest).
    unit : int, optional
        Engine unit number; defaults to the first available unit.
    path : str, optional
        Explicit directory of the C-MAPSS text files.
    """
    base, source = (path, "real") if path else _resolve_dir()
    f = os.path.join(base, f"train_{subset}.txt")
    if not os.path.exists(f):
        raise FileNotFoundError(f"C-MAPSS subset file missing: {f}")

    try:
        df = pd.read_csv(f, sep=r"\s+", header=None, names=_COLUMNS)
    except Exception as e:
        raise ValueError(f"Failed to read C-MAPSS file {f}: {e}") from e
    if df.shape[1] != len(_COLUMNS):
        raise ValueError(
            f"C-MAPSS {subset}: expected {len(_COLUMNS)} columns, got {df.shape[1]}."
        )

    units = sorted(int(u) for u in df["unit"].unique())
    if unit is None:
        unit = units[0]
    if unit not in units:
        raise ValueError(f"C-MAPSS {subset}: unit {unit} not found (have {units[:5]}…).")

    run = df[df["unit"] == unit].sort_values("cycle").reset_index(drop=True)
    if len(run) < 5:
        raise ValueError(f"C-MAPSS {subset} unit {unit}: trajectory too short ({len(run)} cycles).")

    spec = [
        {"col": c, "label": lbl, "unit": u, "group": g, "important": imp}
        for (c, lbl, u, g, imp) in SENSOR_SPEC if c in run.columns
    ]
    registry = build_registry(spec)
    keep = ["cycle"] + [s["col"] for s in spec]
    run = run[keep]

    last_cycle = int(run["cycle"].max())
    # Run-to-failure: the unit fails at its final cycle → mark it (degenerate window
    # = drawn as a failure line by the console).
    failure_windows = [(last_cycle, last_cycle)]
    health = [c for c in HEALTH_PARAMS if c in registry]

    bundle = MachineBundle(
        df=run, parameters=registry, time_col="cycle", time_kind="cycle",
        dataset="C-MAPSS", unit_label=f"Turbofan Engine #{unit} ({subset})",
        health_params=health, failure_windows=failure_windows, source=source,
        meta={"subset": subset, "unit": unit, "units_available": units,
              "failure_cycle": last_cycle, "path": f},
    )
    return validate_bundle(bundle)
