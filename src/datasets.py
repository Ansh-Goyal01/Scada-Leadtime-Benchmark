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


# ───────────────────────── per-snapshot stats helper ──────────────────────────

def _snapshot_stats(x2d: np.ndarray, ts: pd.Timestamp) -> dict:
    """
    Per-snapshot time-domain stats for a (n_samples, n_channels) raw waveform block,
    mirroring preprocessing.load_ims_run so the columns match (rms_ch{i}, kurt_ch{i},
    skew_ch{i}, p2p_ch{i}, crest_ch{i}, var_ch{i}).
    """
    from src.preprocessing import _kurtosis, _skewness
    row = {"timestamp": ts}
    for ch in range(x2d.shape[1]):
        x = x2d[:, ch].astype(np.float64)
        rms = float(np.sqrt(np.mean(x ** 2)))
        row[f"rms_ch{ch}"]   = rms
        row[f"kurt_ch{ch}"]  = float(_kurtosis(x))
        row[f"skew_ch{ch}"]  = float(_skewness(x))
        row[f"p2p_ch{ch}"]   = float(np.max(x) - np.min(x))
        row[f"crest_ch{ch}"] = float(np.max(np.abs(x)) / (rms + 1e-12))
        row[f"var_ch{ch}"]   = float(np.var(x))
    return row


def _ingest_run_csvs(run_dir: str, reader, start: pd.Timestamp, step: pd.Timedelta,
                     cache_name: str) -> pd.DataFrame:
    """
    Generic run-to-failure ingest: apply ``reader(path)->(n,ch) array`` to each snapshot
    file (sorted), compute per-snapshot stats, index by a synthetic uniform clock
    (start + k·step). Caches the resulting snapshot-stats DataFrame to processed/.
    """
    import os
    from src.config import PATHS
    from src.preprocessing import save_processed, load_processed
    cache = os.path.join(PATHS["processed"], cache_name)
    if os.path.exists(cache):
        return load_processed(cache)
    files = sorted([f for f in os.scandir(run_dir) if f.is_file()],
                   key=lambda f: _numkey(f.name))
    if not files:
        raise FileNotFoundError(f"No snapshot files in {run_dir}")
    recs = []
    for k, f in enumerate(files):
        try:
            arr = reader(f.path)
        except Exception as e:
            logger.warning("skip %s: %s", f.name, e)
            continue
        recs.append(_snapshot_stats(arr, start + k * step))
        if (k + 1) % 200 == 0:
            logger.info("  ingested %d/%d files", k + 1, len(files))
    df = pd.DataFrame(recs).set_index("timestamp").sort_index()
    save_processed(df, cache)
    return df


def _numkey(name: str):
    import re
    m = re.findall(r"\d+", name)
    return [int(x) for x in m] if m else [0]


# ─────────────────────────── XJTU-SY / FEMTO (download) ────────────────────────

@register_loader("XJTU-SY")
def _load_xjtu(run_name: str, **kw) -> RunBundle:
    """
    XJTU-SY run-to-failure bearing. Each snapshot CSV holds 32768 samples (1.28 s @
    25.6 kHz) in two columns (horizontal, vertical); files are recorded once per minute.
    run_name is a bearing folder, e.g. 'Bearing1_1' under a condition dir. Failure = last
    snapshot (run-to-failure). See scripts/download_data.py.
    """
    import os
    from src.config import PATHS
    root = PATHS.get("raw_xjtu", os.path.join(os.path.dirname(PATHS["processed"]), "raw", "XJTU-SY"))
    run_dir = _find_run_dir(root, run_name)

    def reader(path):
        d = pd.read_csv(path)
        return d.select_dtypes(include=[np.number]).values[:, :2]

    start = pd.Timestamp("2019-01-01")
    df = _ingest_run_csvs(run_dir, reader, start, pd.Timedelta(minutes=1),
                          f"XJTU_{run_name}_features.parquet")
    return RunBundle(
        snapshot_df=df, failure_time=str(df.index[-1]),
        dataset="XJTU-SY", run_name=run_name,
        train_fraction=0.5, raw_waveform_available=True,
        channels=[c for c in df.columns if c.startswith("rms_ch")],
        meta={"fs": 25600, "snapshot_s": 1.28, "interval": "1min"},
    )


@register_loader("FEMTO")
def _load_femto(run_name: str, **kw) -> RunBundle:
    """
    FEMTO/PRONOSTIA run-to-failure bearing. Each acc_*.csv row is
    [hour, minute, second, microsec, horiz_accel, vert_accel]; 2560 samples/file
    (0.1 s @ 25.6 kHz), recorded every 10 s. run_name e.g. 'Bearing1_1'. See
    scripts/download_data.py.
    """
    import os
    from src.config import PATHS
    root = PATHS.get("raw_femto", os.path.join(os.path.dirname(PATHS["processed"]), "raw", "FEMTO"))
    run_dir = _find_run_dir(root, run_name)

    def reader(path):
        d = pd.read_csv(path, header=None)
        return d.iloc[:, 4:6].values    # last two columns = horiz/vert acceleration

    start = pd.Timestamp("2011-01-01")
    df = _ingest_run_csvs(run_dir, reader, start, pd.Timedelta(seconds=10),
                          f"FEMTO_{run_name}_features.parquet")
    return RunBundle(
        snapshot_df=df, failure_time=str(df.index[-1]),
        dataset="FEMTO", run_name=run_name,
        train_fraction=0.5, raw_waveform_available=True,
        channels=[c for c in df.columns if c.startswith("rms_ch")],
        meta={"fs": 25600, "snapshot_s": 0.1, "interval": "10s"},
    )


def _find_run_dir(root: str, run_name: str) -> str:
    """Locate a bearing run folder by name anywhere under ``root`` (condition subdirs)."""
    import os
    if not os.path.isdir(root):
        raise FileNotFoundError(
            f"{root} not found. Run `python scripts/download_data.py` first."
        )
    for dirpath, dirnames, _ in os.walk(root):
        if os.path.basename(dirpath) == run_name:
            return dirpath
        if run_name in dirnames:
            return os.path.join(dirpath, run_name)
    raise FileNotFoundError(f"Run {run_name!r} not found under {root}")
