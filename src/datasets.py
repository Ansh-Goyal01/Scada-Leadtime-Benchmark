# src/datasets.py
"""
Unified multi-dataset loader (Phase C keystone).

Every dataset yields the SAME intermediate contract — a RunBundle wrapping a
datetime-indexed per-snapshot DataFrame whose signal channels are named ``rms_ch{i}``
(plus optional ``kurt_ch{i}`` etc.) — so the existing feature / onset / lead-time
pipeline works unchanged across IMS, ONGC, XJTU-SY and FEMTO regardless of their
native format or channel count.

  IMS   : lab bearings, raw 20.48 kHz waveforms → per-snapshot stats (cached parquet).
  ONGC  : real Solar-Turbine LPC, 4 vib channels in mm/s @10 s (already SCADA-aggregated).
  XJTU  : 15 run-to-failure bearings, 2 ch @25.6 kHz (download — see scripts/download_data.py).
  FEMTO : PRONOSTIA run-to-failure bearings, 2 ch (download).

Loaders return a RunBundle; src.load_pipeline consumes ``snapshot_df`` + metadata.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RunBundle:
    snapshot_df: pd.DataFrame          # datetime-indexed; signal cols named rms_ch{i}
    failure_time: str                  # ISO timestamp of failure / stop
    dataset: str
    run_name: str
    train_fraction: float = 0.50       # normal-baseline fraction (per dataset)
    raw_waveform_available: bool = False
    channels: Optional[List[str]] = None
    meta: dict = field(default_factory=dict)


_LOADERS: dict = {}


def register_loader(name: str):
    def deco(fn: Callable):
        _LOADERS[name] = fn
        return fn
    return deco


def list_datasets() -> list:
    return sorted(_LOADERS.keys())


def load_run(dataset: str, run_name: str, **kw) -> RunBundle:
    if dataset not in _LOADERS:
        raise KeyError(f"No loader for dataset {dataset!r}; have {list_datasets()}")
    return _LOADERS[dataset](run_name, **kw)


# ───────────────────────────────── IMS ────────────────────────────────────────

@register_loader("IMS")
def _load_ims(run_name: str, use_spectral: bool = False, **kw) -> RunBundle:
    from src.config import PATHS, DATASET, SPLIT
    from src.preprocessing import load_processed
    if use_spectral:
        from src import ensure_spectral_cache
        df = ensure_spectral_cache(run_name)
    else:
        df = load_processed(os.path.join(PATHS["processed"], f"{run_name}_features.parquet"))
    return RunBundle(
        snapshot_df=df,
        failure_time=DATASET["failure_times"][run_name],
        dataset="IMS", run_name=run_name,
        train_fraction=SPLIT["train_fraction"],
        raw_waveform_available=True,
        channels=[c for c in df.columns if c.startswith("rms_ch")],
    )


# ──────────────────────────────── ONGC ────────────────────────────────────────

@register_loader("ONGC")
def _load_ongc(run_name: str = "LPC", **kw) -> RunBundle:
    """
    Real ONGC Solar-Turbine low-pressure-compressor run. The 4 vibration channels are
    already engineering-unit (mm/s) RMS-style values at 10 s logging — i.e. genuine
    SCADA-historian data — so they map directly onto the rms_ch{i} signal slots and skip
    the spectral stage (no raw waveform available). Only the pre-shutdown file is used;
    After_Shutdown is machine-off (noise floor) and would distort FAR.
    """
    from src.config import PATHS
    from src.ongc_preprocessing import (
        load_ongc_run, VIB_COLS, FAILURE_TIME, TRAIN_FRACTION,
    )
    before = os.path.join(PATHS_raw_ongc(PATHS), "Before_Shutdown.xlsx")
    after = os.path.join(PATHS_raw_ongc(PATHS), "After_Shutdown.xlsx")
    d = load_ongc_run(before, after)
    df = pd.concat([d["df_train"], d["df_test"]]).sort_index()
    # map the 4 vibration channels onto rms_ch0..rms_ch3 so the rms-based feature/onset
    # machinery applies unchanged
    rename = {c: f"rms_ch{i}" for i, c in enumerate(VIB_COLS)}
    df = df.rename(columns=rename)[list(rename.values())]
    return RunBundle(
        snapshot_df=df,
        failure_time=FAILURE_TIME,
        dataset="ONGC", run_name=run_name,
        train_fraction=TRAIN_FRACTION,
        raw_waveform_available=False,
        channels=list(rename.values()),
        meta={"native_channels": VIB_COLS, "sampling": "10s"},
    )


def PATHS_raw_ongc(PATHS: dict) -> str:
    return PATHS.get("raw_ongc", os.path.join(os.path.dirname(PATHS["processed"]), "raw", "ONGC"))


# ─────────────────────────── XJTU-SY / FEMTO (download) ────────────────────────

@register_loader("XJTU-SY")
def _load_xjtu(run_name: str, **kw) -> RunBundle:
    raise NotImplementedError(
        "XJTU-SY not present. Run `python scripts/download_data.py --dataset XJTU-SY` "
        "then this loader will ingest the per-bearing CSVs (2 ch @25.6 kHz)."
    )


@register_loader("FEMTO")
def _load_femto(run_name: str, **kw) -> RunBundle:
    raise NotImplementedError(
        "FEMTO/PRONOSTIA not present. Run `python scripts/download_data.py --dataset FEMTO` "
        "then this loader will ingest the per-bearing acc CSVs."
    )
