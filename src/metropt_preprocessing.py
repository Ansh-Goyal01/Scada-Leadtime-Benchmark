# src/metropt_preprocessing.py
"""
MetroPT-3 air-compressor loader  →  MachineBundle.
==================================================

MetroPT-3 (Metro do Porto, APU air-production unit) is the headline *real*
compressor for the diagnostic console: it natively logs pressures, oil
temperature and motor current at 1 Hz, with documented real failures — exactly
the multi-parameter "what was the temperature / current / RPM when the alarm
fired" story the site engineers need.

Source (download manually — see scripts/download_data.py):
    UCI Machine Learning Repository #791 "MetroPT-3 Dataset" → Zenodo record.
    A single CSV; place it at  data/raw/MetroPT3/MetroPT3.csv

The raw file is ~1.6 GB at 1 Hz (~15M rows). Loading every sample into a browser
is neither possible nor useful, so we RESAMPLE on load to a coarser interval
(default 1 min: mean for analog sensors, max for digital flags). This is also
what a real SCADA historian stores, so it keeps the demo honest as well as fast.
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

REAL_PATH    = os.path.join(BASE_DIR, "data", "raw", "MetroPT3", "MetroPT3.csv")
# Alternate real-file locations/spellings seen across dataset mirrors. The first
# one that exists is used before falling back to the synthetic fixture.
REAL_PATH_ALTS = [
    os.path.join(BASE_DIR, "data", "raw", "MetroPT3(AirCompressor).csv"),
    os.path.join(BASE_DIR, "data", "raw", "MetroPT3", "MetroPT3(AirCompressor).csv"),
]
FIXTURE_PATH = os.path.join(BASE_DIR, "data", "raw", "_fixtures", "MetroPT3.csv")

# ── Parameter spec: analog sensors map to physical parameters; digital flags kept
#    as context (not used for alarming by default). Column names match the public
#    CSV; the loader also tolerates common alias spellings.
# High-contrast industrial palette (explicit per-parameter colours — no two adjacent hues
# are similar, and they survive the dark-SCADA background and anomaly spikes).
PARAM_SPEC = [
    {"col": "Oil_temperature", "label": "Oil Temperature",      "unit": "°C",  "group": "Temperature", "color": "#FF6B35", "important": True},
    {"col": "Motor_current",   "label": "Motor Current",        "unit": "A",   "group": "Current",     "color": "#A855F7", "important": True},
    {"col": "TP2",             "label": "Compressor Pressure",  "unit": "bar", "group": "Pressure",    "color": "#22D3EE", "important": True},
    {"col": "TP3",             "label": "Pneumatic Pressure",   "unit": "bar", "group": "Pressure",    "color": "#3B82F6", "important": True},
    {"col": "H1",              "label": "Pressure H1",          "unit": "bar", "group": "Pressure",    "color": "#10B981", "important": True},
    {"col": "DV_pressure",     "label": "Towers Pressure Drop", "unit": "bar", "group": "Pressure",    "color": "#F59E0B", "important": True},
    {"col": "Reservoirs",      "label": "Reservoir Pressure",   "unit": "bar", "group": "Pressure",    "color": "#EF4444", "important": True},
    {"col": "Oil_level",       "label": "Oil Level",            "unit": "",    "group": "Digital",     "important": False},
    {"col": "COMP",            "label": "Compressor On",        "unit": "",    "group": "Digital",     "important": False},
    {"col": "DV_eletric",      "label": "Drain Valve (elec.)",  "unit": "",    "group": "Digital",     "important": False},
    {"col": "Caudal_impulses", "label": "Air-flow Impulses",    "unit": "",    "group": "Digital",     "important": False},
]

# Column-name aliases seen across mirrors of the dataset → canonical names above.
_ALIASES = {
    "oil_temperature": "Oil_temperature", "oiltemperature": "Oil_temperature",
    "motor_current": "Motor_current", "motorcurrent": "Motor_current",
    "dv_pressure": "DV_pressure", "dv pressure": "DV_pressure",
    "dv_eletric": "DV_eletric", "dv_electric": "DV_eletric",
    "reservoirs": "Reservoirs", "caudal_impulses": "Caudal_impulses",
    "oil_level": "Oil_level", "timestamp": "timestamp", "time": "timestamp",
}

# Reported failure spans from the MetroPT-3 source documentation (approximate;
# air-leak / compressor events). Shown as overlays only — the alarm engine itself
# is data-driven, so these never *create* alarms, they just mark known truth.
REPORTED_FAILURES = [
    ("2020-04-18 00:00:00", "2020-04-18 23:59:00"),
    ("2020-05-29 23:30:00", "2020-05-30 06:00:00"),
    ("2020-06-05 10:00:00", "2020-06-07 14:30:00"),
    ("2020-07-15 14:30:00", "2020-07-15 19:00:00"),
]


def _resolve(path: Optional[str]) -> str:
    if path:
        if not os.path.exists(path):
            raise FileNotFoundError(f"MetroPT-3 file not found: {path}")
        return path
    if os.path.exists(REAL_PATH):
        return REAL_PATH
    for alt in REAL_PATH_ALTS:
        if os.path.exists(alt):
            logger.info("MetroPT-3 real CSV found at %s", alt)
            return alt
    if os.path.exists(FIXTURE_PATH):
        logger.info("MetroPT-3 real CSV not found; using synthetic fixture.")
        return FIXTURE_PATH
    raise FileNotFoundError(
        "MetroPT-3 data not found.\n"
        f"  • Place the real CSV at: {REAL_PATH}\n"
        f"  • Or generate a fixture: python scripts/make_demo_fixtures.py"
    )


def _canonical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to the canonical spelling; drop unnamed index cols."""
    df = df.loc[:, [c for c in df.columns if not str(c).lower().startswith("unnamed")]]
    rename = {}
    for c in df.columns:
        key = str(c).strip().lower()
        if key in _ALIASES:
            rename[c] = _ALIASES[key]
    return df.rename(columns=rename)


def load_metropt(path: Optional[str] = None,
                 resample: Optional[str] = "1min",
                 max_rows: Optional[int] = None) -> MachineBundle:
    """
    Load MetroPT-3 into a MachineBundle.

    Parameters
    ----------
    path : str, optional
        Explicit CSV path. If None, use the real file when present, else the
        synthetic fixture.
    resample : str, optional
        Pandas offset alias to downsample the 1 Hz stream (default "1min").
        Analog sensors are mean-aggregated; digital flags max-aggregated. Pass
        None to keep the native rate (only sane for the fixture).
    max_rows : int, optional
        Hard cap on rows READ from disk (safety valve for the giant real CSV).
    """
    src = _resolve(path)
    is_fixture = os.path.abspath(src) == os.path.abspath(FIXTURE_PATH)

    try:
        df = pd.read_csv(src, nrows=max_rows)
    except Exception as e:
        raise ValueError(f"Failed to read MetroPT-3 CSV at {src}: {e}") from e

    df = _canonical_columns(df)
    if "timestamp" not in df.columns:
        # Some mirrors store the time in the first column without a header name.
        first = df.columns[0]
        df = df.rename(columns={first: "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    if len(df) == 0:
        raise ValueError(f"MetroPT-3: no parseable timestamps in {src}.")

    spec = [s for s in PARAM_SPEC if s["col"] in df.columns]
    if not spec:
        raise ValueError(
            f"MetroPT-3: none of the expected sensor columns found in {src}. "
            f"Columns present: {list(df.columns)[:12]}"
        )
    analog = [s["col"] for s in spec if s["group"] != "Digital"]
    digital = [s["col"] for s in spec if s["group"] == "Digital"]

    keep = ["timestamp"] + analog + digital
    df = df[keep]

    if resample:
        df = df.set_index("timestamp")
        agg = {c: "mean" for c in analog}
        agg.update({c: "max" for c in digital})
        df = df.resample(resample).agg(agg).dropna(how="all").reset_index()

    registry = build_registry(spec)
    health = [s["col"] for s in spec if s.get("important")]

    span = (df["timestamp"].min(), df["timestamp"].max())
    windows = []
    if not is_fixture:
        for a, b in REPORTED_FAILURES:
            a, b = pd.Timestamp(a), pd.Timestamp(b)
            if b >= span[0] and a <= span[1]:
                windows.append((max(a, span[0]), min(b, span[1])))

    bundle = MachineBundle(
        df=df, parameters=registry, time_col="timestamp", time_kind="datetime",
        dataset="MetroPT-3", unit_label="Air Production Unit (APU) — Metro do Porto",
        health_params=health, failure_windows=windows,
        source="fixture" if is_fixture else "real",
        meta={
            "resample": resample, "n_rows": int(len(df)),
            "failure_windows_source": "MetroPT-3 source documentation (approximate)",
            "path": src,
        },
    )
    return validate_bundle(bundle)
