# src/console_paper_adapter.py
"""
Bridge the paper's RunBundle world into the console's MachineBundle world.
====================================================================================

The diagnostic console renders from a :class:`~src.console_data.MachineBundle`
(named physical parameters, a time column, ground-truth ``failure_windows``).
The paper's lead-time pipeline speaks :class:`~src.datasets.RunBundle`
(datetime-indexed ``rms_ch{i}`` signal channels + a single ``failure_time``).

This module adapts the latter to the former for the four paper datasets
(IMS / ONGC / XJTU-SY / FEMTO) so the console can display them WITHOUT
re-implementing any analytics:

  * the ``rms_ch{i}`` channels become named parameters in the Vibration group,
  * the ground-truth ``failure_windows`` is the single span
    ``[t_onset, t_fail]`` — the SAME degradation onset the paper anchors its
    lead-time metric to (``src.onset.onset_for_run``), computed leakage-free
    from the training baseline. This keeps the console's failure shading and
    the paper's lead-time denominator identical, by construction.

The paper-side primitives needed to recompute the FAR-gated lead-time metric
(failure_time, t_onset, train_fraction) are stashed in ``bundle.meta`` so the
evaluation layer (``src/console_api.py``) can re-run ``evaluate_method`` on the
exact same run without reloading.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from src.console_data import MachineBundle, build_registry, validate_bundle

logger = logging.getLogger(__name__)


# Per-dataset display metadata. Units: ONGC vibration is engineering-unit mm/s
# (real SCADA historian); the lab bearing sets (IMS/XJTU/FEMTO) are acceleration
# RMS in g.
_DATASET_INFO = {
    "IMS":     {"unit": "g",    "label": "IMS bearing"},
    "ONGC":    {"unit": "mm/s", "label": "ONGC Solar-Turbine LPC"},
    "XJTU-SY": {"unit": "g",    "label": "XJTU-SY bearing"},
    "FEMTO":   {"unit": "g",    "label": "FEMTO/PRONOSTIA bearing"},
}


def _channel_label(dataset: str, col: str, native: Optional[list], ch_idx: int) -> str:
    """Human label for an ``rms_ch{i}`` column, using native sensor names when known."""
    if native and ch_idx < len(native):
        return f"{native[ch_idx]} RMS"
    return f"Channel {ch_idx} RMS"


def run_bundle_to_machine_bundle(rb, *, with_onset: bool = True) -> MachineBundle:
    """
    Convert a paper :class:`RunBundle` into a console :class:`MachineBundle`.

    Parameters
    ----------
    rb : RunBundle
        From ``src.datasets.load_run(dataset, run_name)``.
    with_onset : bool
        If True (default) compute the leakage-free degradation onset and use
        ``[t_onset, t_fail]`` as the ground-truth failure window. If onset
        detection fails, fall back to a point window at ``t_fail``.
    """
    info = _DATASET_INFO.get(rb.dataset, {"unit": "", "label": rb.dataset})

    # snapshot_df is datetime-indexed; lift the index into an explicit time column.
    df = rb.snapshot_df.copy()
    df.index.name = "timestamp"
    df = df.reset_index().rename(columns={df.index.name or "index": "timestamp"})
    if "timestamp" not in df.columns:
        df = df.rename(columns={df.columns[0]: "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Expose the rms_ch* signal channels as named Vibration parameters.
    rms_cols = [c for c in df.columns if c.startswith("rms_ch")]
    if not rms_cols:
        raise ValueError(
            f"{rb.dataset}/{rb.run_name}: no rms_ch* channels in snapshot frame "
            f"(have {list(df.columns)[:8]})."
        )
    native = (rb.meta or {}).get("native_channels")
    spec = []
    for c in rms_cols:
        ch_idx = int(c.replace("rms_ch", ""))
        spec.append({
            "col": c,
            "label": _channel_label(rb.dataset, c, native, ch_idx),
            "unit": info["unit"],
            "group": "Vibration",
            "important": True,
        })
    registry = build_registry(spec)

    # Keep only the time column + exposed parameters (drop kurt_/skew_/… feature
    # columns the console doesn't render; the paper metric recomputes from raw).
    df = df[["timestamp"] + rms_cols]

    # Ground-truth failure window = [onset, failure], the paper's lead-time anchor.
    t_fail = pd.Timestamp(rb.failure_time)
    t_onset = None
    if with_onset:
        try:
            from src.onset import onset_for_run
            n = len(rb.snapshot_df)
            train_end = rb.snapshot_df.index[min(int(n * rb.train_fraction), n - 1)]
            t_onset = onset_for_run(rb.snapshot_df, train_end=train_end, t_fail=t_fail)
        except Exception as e:  # onset is best-effort; never block the bundle
            logger.warning("%s/%s: onset detection failed (%s); using point window.",
                           rb.dataset, rb.run_name, e)

    if t_onset is not None:
        windows = [(t_onset, t_fail)]
    else:
        windows = [(t_fail, t_fail)]

    bundle = MachineBundle(
        df=df,
        parameters=registry,
        time_col="timestamp",
        time_kind="datetime",
        dataset=rb.dataset,
        unit_label=f"{info['label']} — {rb.run_name}",
        health_params=list(rms_cols),
        failure_windows=windows,
        source="real",
        meta={
            "run_name": rb.run_name,
            "failure_time": str(t_fail),
            "t_onset": (str(t_onset) if t_onset is not None else None),
            "train_fraction": float(rb.train_fraction),
            "channels": list(rms_cols),
            "native_channels": native,
            "raw_waveform_available": bool(rb.raw_waveform_available),
            "paper_dataset": True,
            **(rb.meta or {}),
        },
    )
    return validate_bundle(bundle)


def load_machine_bundle(dataset: str, run_name: str, **load_kw) -> MachineBundle:
    """Load a paper dataset run directly as a console MachineBundle."""
    from src.datasets import load_run
    rb = load_run(dataset, run_name, **load_kw)
    return run_bundle_to_machine_bundle(rb)
