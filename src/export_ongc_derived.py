# src/export_ongc_derived.py
"""
Export the derived ONGC artifacts that the paper cites, for release under the NDA.

Reviewer D's only reproducibility reservation was that one dataset could not be used to
repeat the tests. The ONGC raw waveforms and channel-level measurements are proprietary
and stay unreleased; what a reader actually needs to check the n=1 case study is the
DERIVED health-indicator series that fixes the degradation onset, plus the onset/failure
markers. Every other ONGC number the paper cites already ships in results/tables/
(per-detector lead time and pre-onset FAR, the sampling sweep, the conformal calibration
series, and the Table D.2 minute-differences).

What is released here
    results/tables/ongc_health_indicator.csv   timestamp, hours_from_start, health_indicator
    results/tables/ongc_onset_markers.csv      run-level scalars: start/train-end/onset/failure

What is NOT released, and is asserted against below
    raw vibration waveforms; the per-channel rms_ch* / kurt_ch* measurements; any asset,
    site, tag or channel identifier. The health indicator is a single scalar per timestamp
    aggregated across all four channels, from which the per-channel values cannot be
    recovered.

Absolute timestamps and the run label "LPC" are already public: they appear in the
released results/tables/benchmark_ONGC_long.csv and in Appendix D.2 of the paper, so this
export widens no disclosure boundary.

    python -m src.export_ongc_derived
"""

from __future__ import annotations

import logging
import os
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RUN = "LPC"
DATASET = "ONGC"

# The onset already published in results/tables/benchmark_ONGC_long.csv and in
# Appendix D.2. The exported series must reproduce it, or the export is wrong.
EXPECTED_ONSET = pd.Timestamp("2023-11-13 03:44:01")
EXPECTED_FAIL = pd.Timestamp("2023-11-13 09:46:00")

_FORBIDDEN = re.compile(r"^(rms|kurt|skew|p2p|crest|std|mean|max|min)_ch\d+$", re.I)


def _assert_no_channel_level(df: pd.DataFrame, what: str) -> None:
    """Refuse to write anything carrying per-channel measurements."""
    bad = [c for c in df.columns if _FORBIDDEN.match(str(c))]
    if bad:
        raise SystemExit(f"REFUSING TO WRITE {what}: channel-level columns present: {bad}")


def build() -> tuple:
    from src import load_pipeline
    from src.config import ONSET, SPLIT
    from src.onset import health_indicator, detect_onset

    pipe = load_pipeline(RUN, dataset=DATASET)
    df = pipe["df_full"]
    n = len(df)
    train_frac = pipe.get("train_fraction", SPLIT["train_fraction"])
    train_end = df.index[min(int(n * train_frac), n - 1)]
    t_fail = pd.Timestamp(pipe["failure_time"])

    # Same call the benchmark makes, so the released series is the one behind the paper.
    hi = health_indicator(df, kind=ONSET.get("health_indicator", "rms_mean"))
    onset = detect_onset(
        hi, train_end=train_end, t_fail=t_fail,
        method=ONSET.get("method", "terminal"),
        baseline_fraction=ONSET.get("baseline_fraction", 0.2),
        sigma_k=ONSET.get("sigma_k", 4.0),
        persistence=ONSET.get("persistence", 5),
        gap_tol=ONSET.get("gap_tol", 10),
    )

    t0 = df.index[0]
    series = pd.DataFrame({
        "timestamp": hi.index,
        "hours_from_start": (hi.index - t0).total_seconds() / 3600.0,
        "health_indicator": hi.to_numpy(dtype=float),
    })

    markers = pd.DataFrame([{
        "dataset": DATASET, "run": RUN,
        "t_start": t0, "t_train_end": train_end,
        "t_onset": onset, "t_fail": t_fail,
        "n_samples": int(n),
        # .dt.total_seconds() is resolution-independent; DatetimeIndex.view("int64")
        # exposes the backing unit (microseconds here, not nanoseconds) and a hard-coded
        # /1e9 silently reported 0.01 s for this 10 s stream.
        "interval_s": round(float(df.index.to_series().diff().dt.total_seconds().median()), 3),
        "health_indicator": ONSET.get("health_indicator", "rms_mean"),
        "onset_method": ONSET.get("method", "terminal"),
        "sigma_k": ONSET.get("sigma_k", 4.0),
        "persistence": ONSET.get("persistence", 5),
        "gap_tol": ONSET.get("gap_tol", 10),
        "max_lead_hours": round((t_fail - onset).total_seconds() / 3600.0, 4),
    }])
    return series, markers, onset


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from src.config import PATHS

    series, markers, onset = build()

    _assert_no_channel_level(series, "ongc_health_indicator.csv")
    _assert_no_channel_level(markers, "ongc_onset_markers.csv")
    assert list(series.columns) == ["timestamp", "hours_from_start", "health_indicator"], \
        f"unexpected columns in the HI series: {list(series.columns)}"
    assert series["health_indicator"].notna().all(), "HI series has NaNs"
    iv = float(markers.loc[0, "interval_s"])
    assert 9.0 <= iv <= 11.0, f"interval_s={iv}: expected the documented 10 s SCADA rate"

    if onset != EXPECTED_ONSET:
        raise SystemExit(f"onset {onset} != published {EXPECTED_ONSET}; export not written")
    assert pd.Timestamp(markers.loc[0, "t_fail"]) == EXPECTED_FAIL

    out = PATHS["results_tables"]
    os.makedirs(out, exist_ok=True)
    p1 = os.path.join(out, "ongc_health_indicator.csv")
    p2 = os.path.join(out, "ongc_onset_markers.csv")
    series.round({"hours_from_start": 6, "health_indicator": 6}).to_csv(p1, index=False)
    markers.to_csv(p2, index=False)
    print(f"wrote {p1}  ({len(series)} rows)")
    print(f"wrote {p2}")
    print(f"onset reproduced: {onset}  (matches published)")


if __name__ == "__main__":
    main()
