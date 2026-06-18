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


def default_runs(dataset: str) -> list:
    """Default run list per dataset (the unit over which we aggregate/bootstrap)."""
    if dataset == "ONGC":
        return ["LPC"]
    if dataset == "XJTU-SY":
        return list(XJTU_NPY_RUNS.keys())   # 10 run-to-failure bearings, conditions 1 & 2
    if dataset == "FEMTO":
        return list(FEMTO_RUNS)             # 6 Learning_set run-to-failure bearings
    from src.config import EXPERIMENT
    return EXPERIMENT["runs_to_evaluate"]   # IMS


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
    from src.preprocessing import save_processed, load_processed
    rename = {c: f"rms_ch{i}" for i, c in enumerate(VIB_COLS)}

    # Parsing the source .xlsx takes ~20s; cache the renamed snapshot frame to parquet
    # so subsequent loads (esp. the live console) are sub-second like the other datasets.
    cache = os.path.join(PATHS["processed"], f"ONGC_{run_name}_features.parquet")
    if os.path.exists(cache):
        df = load_processed(cache)
    else:
        before = os.path.join(PATHS_raw_ongc(PATHS), "Before_Shutdown.xlsx")
        after = os.path.join(PATHS_raw_ongc(PATHS), "After_Shutdown.xlsx")
        d = load_ongc_run(before, after)
        df = pd.concat([d["df_train"], d["df_test"]]).sort_index()
        # map the 4 vibration channels onto rms_ch0..rms_ch3 so the rms-based feature/onset
        # machinery applies unchanged
        df = df.rename(columns=rename)[list(rename.values())]
        save_processed(df, cache)
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
                     cache_name: str, file_prefix: str = None) -> pd.DataFrame:
    """
    Generic run-to-failure ingest: apply ``reader(path)->(n,ch) array`` to each snapshot
    file (sorted), compute per-snapshot stats, index by a synthetic uniform clock
    (start + k·step). Caches the resulting snapshot-stats DataFrame to processed/.

    ``file_prefix`` restricts ingest to files whose name starts with it (e.g. "acc_"
    for FEMTO, whose run folders also contain temp_*.csv temperature files that must
    NOT be fed to the acceleration reader).
    """
    import os
    from src.config import PATHS
    from src.preprocessing import save_processed, load_processed
    cache = os.path.join(PATHS["processed"], cache_name)
    if os.path.exists(cache):
        return load_processed(cache)
    files = [f for f in os.scandir(run_dir) if f.is_file()]
    if file_prefix is not None:
        files = [f for f in files if f.name.startswith(file_prefix)]
    files = sorted(files, key=lambda f: _numkey(f.name))
    if not files:
        raise FileNotFoundError(
            f"No snapshot files in {run_dir}"
            + (f" matching prefix {file_prefix!r}" if file_prefix else ""))
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

# XJTU-SY canonical 10 run-to-failure bearings (conditions 1 & 2, bearings 1-5).
# The .npy download stores each bearing's full life as x<split><cond>_<bearing>.npy of
# shape (n_snapshots, 32768, 2). The non-`b` file stems below map to the bearings whose
# snapshot counts EXACTLY match the published XJTU-SY lifetimes (Wang et al. 2020); the
# `b1..b5` files are the uploader's augmented copies (lifetimes do not match) and are
# deliberately excluded so each physical bearing is counted once.
XJTU_NPY_RUNS = {
    "Bearing1_1": "xtr1_1", "Bearing1_2": "xtr1_2", "Bearing1_3": "xte1_3",
    "Bearing1_4": "xte1_4", "Bearing1_5": "xte1_5",
    "Bearing2_1": "xtr2_1", "Bearing2_2": "xtr2_2", "Bearing2_3": "xte2_3",
    "Bearing2_4": "xte2_4", "Bearing2_5": "xte2_5",
}


@register_loader("XJTU-SY")
def _load_xjtu(run_name: str, **kw) -> RunBundle:
    """
    XJTU-SY run-to-failure bearing (2 ch, 32768 samples/snapshot @ 25.6 kHz, 1/min).
    Failure = last snapshot (RUL → 0). ``run_name`` e.g. 'Bearing1_3'.

    Two on-disk layouts are supported:
      * .npy bundle (this download): flat dir of x<...>.npy arrays of shape
        (n_snapshots, 32768, 2). Canonical bearings resolved via XJTU_NPY_RUNS.
      * per-CSV run folders (official MediaFire release): handled by the CSV path.
    """
    import os
    from src.config import PATHS
    root = PATHS.get("raw_xjtu", os.path.join(os.path.dirname(PATHS["processed"]), "raw", "XJTU-SY"))

    npy_path = _resolve_xjtu_npy(root, run_name)
    if npy_path is not None:
        df = _ingest_run_npy(npy_path, start=pd.Timestamp("2019-01-01"),
                             step=pd.Timedelta(minutes=1),
                             cache_name=f"XJTU_{run_name}_features.parquet")
    else:
        run_dir = _find_run_dir(root, run_name)

        def reader(path):
            d = pd.read_csv(path)
            return d.select_dtypes(include=[np.number]).values[:, :2]

        df = _ingest_run_csvs(run_dir, reader, pd.Timestamp("2019-01-01"),
                              pd.Timedelta(minutes=1), f"XJTU_{run_name}_features.parquet")

    cond = "35Hz" if "1_" in run_name or "1." in run_name else "37.5Hz"
    return RunBundle(
        snapshot_df=df, failure_time=str(df.index[-1]),
        dataset="XJTU-SY", run_name=run_name,
        train_fraction=0.5, raw_waveform_available=True,
        channels=[c for c in df.columns if c.startswith("rms_ch")],
        meta={"fs": 25600, "snapshot_s": 1.28, "interval": "1min", "condition": cond},
    )


def _resolve_xjtu_npy(root: str, run_name: str) -> Optional[str]:
    """Return the .npy file path for a run if the bundle layout is present, else None."""
    import os
    stem = XJTU_NPY_RUNS.get(run_name, run_name)
    if not stem.startswith("x"):
        stem = "x" + stem.lstrip("xy")
    cand = os.path.join(root, f"{stem}.npy")
    return cand if os.path.exists(cand) else None


def _ingest_run_npy(npy_path: str, start: pd.Timestamp, step: pd.Timedelta,
                    cache_name: str) -> pd.DataFrame:
    """
    Ingest a (n_snapshots, n_samples, n_channels) .npy array: per-snapshot time-domain
    stats indexed by a synthetic uniform clock. Cached to processed/.
    """
    import os
    from src.config import PATHS
    from src.preprocessing import save_processed, load_processed
    cache = os.path.join(PATHS["processed"], cache_name)
    if os.path.exists(cache):
        return load_processed(cache)
    arr = np.load(npy_path, allow_pickle=True)
    if arr.ndim != 3:
        raise ValueError(f"{npy_path}: expected (n,samples,channels), got {arr.shape}")
    recs = []
    for k in range(arr.shape[0]):
        recs.append(_snapshot_stats(arr[k], start + k * step))
    df = pd.DataFrame(recs).set_index("timestamp").sort_index()
    save_processed(df, cache)
    logger.info("XJTU ingest %s → %d snapshots", os.path.basename(npy_path), len(df))
    return df


@register_loader("FEMTO")
def _load_femto(run_name: str, **kw) -> RunBundle:
    """
    FEMTO/PRONOSTIA run-to-failure bearing. Each acc_*.csv row is
    [hour, minute, second, microsec, horiz_accel, vert_accel]; 2560 samples/file
    (0.1 s @ 25.6 kHz), recorded every 10 s. run_name e.g. 'Bearing1_1'.

    Only the six Learning_set bearings (FEMTO_RUNS) are exposed: they are the
    complete run-to-failure trajectories (run until the 20 g vibration stop), so a
    failure -- and hence a lead time -- is actually observed. The Test_set /
    Validation_Set copies are deliberately truncated mid-life for the RUL-prediction
    challenge (no observed failure) and would make lead time undefined, so we ignore
    them even though same-named folders exist on disk. See scripts/download_data.py.
    """
    import os
    from src.config import PATHS
    root = PATHS.get("raw_femto", os.path.join(os.path.dirname(PATHS["processed"]), "raw", "FEMTO"))
    run_dir = _find_femto_learning_dir(root, run_name)

    def reader(path):
        # Acc CSVs are usually comma-separated; some mirrors use ';'. Sniff once.
        d = pd.read_csv(path, header=None, sep=None, engine="python")
        return d.iloc[:, 4:6].values    # last two columns = horiz/vert acceleration

    start = pd.Timestamp("2011-01-01")
    df = _ingest_run_csvs(run_dir, reader, start, pd.Timedelta(seconds=10),
                          f"FEMTO_{run_name}_features.parquet",
                          file_prefix="acc_")
    return RunBundle(
        snapshot_df=df, failure_time=str(df.index[-1]),
        dataset="FEMTO", run_name=run_name,
        train_fraction=0.5, raw_waveform_available=True,
        channels=[c for c in df.columns if c.startswith("rms_ch")],
        meta={"fs": 25600, "snapshot_s": 0.1, "interval": "10s"},
    )


# FEMTO Learning_set: the six complete run-to-failure bearings (PRONOSTIA, IEEE PHM
# 2012). Conditions 1 (1800 rpm/4000 N) and 2 (1650 rpm/4200 N) and 3 (1500/5000).
FEMTO_RUNS = ("Bearing1_1", "Bearing1_2", "Bearing2_1",
              "Bearing2_2", "Bearing3_1", "Bearing3_2")


def _find_femto_learning_dir(root: str, run_name: str) -> str:
    """Locate a FEMTO run folder, preferring the Learning_set (run-to-failure) copy.

    The on-disk tree nests bearings under Training_set/Learning_set,
    Test_set/Test_set and Validation_Set/Full_Test_Set. We must pick the
    Learning_set one, since only it runs to failure. Falls back to a generic
    recursive search if no Learning_set copy exists.
    """
    import os
    if not os.path.isdir(root):
        raise FileNotFoundError(
            f"{root} not found. Place the FEMTO download there (see scripts/download_data.py)."
        )
    learning_hits, other_hits = [], []
    for dirpath, _dirnames, _files in os.walk(root):
        if os.path.basename(dirpath) == run_name:
            parts = {p.lower() for p in dirpath.replace("\\", "/").split("/")}
            if any("learning" in p for p in parts):
                learning_hits.append(dirpath)
            else:
                other_hits.append(dirpath)
    if learning_hits:
        return learning_hits[0]
    if other_hits:
        logger.warning("FEMTO %s: no Learning_set copy found; using %s (may be truncated)",
                       run_name, other_hits[0])
        return other_hits[0]
    raise FileNotFoundError(f"FEMTO run {run_name!r} not found under {root}")


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
