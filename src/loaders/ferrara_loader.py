# src/loaders/ferrara_loader.py
"""
University of Ferrara run-to-failure bearing dataset loader (Arpa et al., Data in
Brief 55 (2024) 110620). Fifth dataset in the study.

On-disk layout (Mendeley PART 1):
    <raw_ferrara>/E{n}/E{n}/E{n}_{k}.mat      (k = 1..N_n, sorted numerically)
Each .mat holds:
    y  : (128000, 1) float64 acceleration in g  (5 s at 25.6 kHz)
    Fs : 25600 Hz

Six bearing runs E1..E6 with the task-confirmed file counts
(4917, 1985, 2386, 669, 1721, 509). Constant speed and radial load (NOT
time-varying), so the dataset is directly compatible with the leakage-free onset
detector without normalization. Snapshots are contiguous (no inter-file pause), so
the synthetic clock advances by exactly snapshot_duration = 5 s per file and the
total lifetime is n_files x 5 s. Failure = last recorded snapshot (RUL -> 0), the
same last-sample convention used for IMS 3rd_test and XJTU/FEMTO.

The accelerometer is UNIAXIAL (single channel), unlike FEMTO/XJTU (two channels).
We duplicate the single channel into two identical signal columns so the
channel-invariant feature schema's per-channel mean/max aggregation is well defined
and numerically identical to the single-channel case (mean == max == the channel);
this keeps the 49-dim invariant feature space identical in shape to the 2-channel
datasets and cross-dataset-comparable.
"""

from __future__ import annotations

import os
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# The six run-to-failure bearings and their task-confirmed snapshot counts.
FERRARA_RUNS = ("E1", "E2", "E3", "E4", "E5", "E6")

SNAPSHOT_DURATION_S = 5.0        # 128000 samples / 25600 Hz = 5 s per .mat file
SAMPLING_RATE_HZ = 25600
TRAIN_FRACTION = 0.50


def _read_mat_signal(path: str) -> np.ndarray:
    """Read one Ferrara .mat -> (n_samples, 2) array.

    Single uniaxial channel 'y' is duplicated into two identical columns (see module
    docstring): the channel-invariant schema then aggregates mean/max over the two
    (identical) channels, which equals the single-channel value.
    """
    import scipy.io as sio
    m = sio.loadmat(path)
    y = np.asarray(m["y"], dtype=np.float64).ravel()
    return np.column_stack([y, y])   # duplicate uniaxial channel -> 2 identical cols


def _resolve_run_dir(root: str, run_name: str) -> str:
    """Locate the flat directory of E{n}_*.mat files for a run.

    Handles the observed nesting <root>/E{n}/E{n}/*.mat as well as a flatter
    <root>/E{n}/*.mat, by walking down until a directory containing .mat files is
    found.
    """
    if not os.path.isdir(root):
        raise FileNotFoundError(
            f"{root} not found. Place the Ferrara download there (Mendeley PART 1)."
        )
    # Find the directory (at or under a folder named run_name) that actually holds .mat.
    candidates = []
    for dirpath, _dirnames, files in os.walk(root):
        if any(f.lower().endswith(".mat") for f in files):
            parts = dirpath.replace("\\", "/").split("/")
            if run_name in parts:
                candidates.append(dirpath)
    if not candidates:
        raise FileNotFoundError(f"Ferrara run {run_name!r}: no .mat directory under {root}")
    # Prefer the deepest match (the innermost E{n}/E{n} leaf).
    return sorted(candidates, key=lambda p: p.count(os.sep))[-1]


def register(register_loader, ingest_run_csvs):
    """Register the 'Ferrara' loader into src.datasets._LOADERS.

    Called from src.datasets at import time with its ``register_loader`` decorator and
    the generic ``_ingest_run_csvs`` ingest helper (which computes per-snapshot stats
    and caches to processed/). Passing them in avoids a circular import at module load.
    """

    @register_loader("Ferrara")
    def _load_ferrara(run_name: str, **kw):
        from src.datasets import RunBundle
        from src.config import PATHS

        root = PATHS.get(
            "raw_ferrara",
            os.path.join(os.path.dirname(PATHS["processed"]), "raw",
                         "Run-to-failure vibration dataset of self-aligning "
                         "double-row ball bearings - PART 1"),
        )
        run_dir = _resolve_run_dir(root, run_name)

        # Contiguous 5 s snapshots -> synthetic uniform clock at 5 s spacing.
        df = ingest_run_csvs(
            run_dir, _read_mat_signal,
            start=pd.Timestamp("2024-01-01"),
            step=pd.Timedelta(seconds=SNAPSHOT_DURATION_S),
            cache_name=f"Ferrara_{run_name}_features.parquet",
            file_prefix=None,
        )
        return RunBundle(
            snapshot_df=df,
            failure_time=str(df.index[-1]),          # last snapshot = failure (RUL->0)
            dataset="Ferrara", run_name=run_name,
            train_fraction=TRAIN_FRACTION,
            raw_waveform_available=True,
            channels=[c for c in df.columns if c.startswith("rms_ch")],
            meta={"fs": SAMPLING_RATE_HZ, "snapshot_s": SNAPSHOT_DURATION_S,
                  "interval": "5s", "channels_native": 1, "condition": "constant"},
        )

    return _load_ferrara
