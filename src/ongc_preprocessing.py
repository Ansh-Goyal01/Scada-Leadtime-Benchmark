# src/ongc_preprocessing.py
"""
ONGC Solar Turbine data loader and preprocessor.

Separate from preprocessing.py (IMS): different format (Excel, engineering
units mm/s, 10-sec sampling, timestamp string "DD-MM-YYYY# HH:MM:SS").

Output contract: same dict shape as load_ims_run() so all downstream code
(features.py, models.py, lead_time.py) works unchanged.

Key decisions recorded for paper methods section:
  failure_time = "2023-11-13 09:46:00"
    Row 42609 in Before_Shutdown.xlsx, "Stopped" annotation.
    Operator shutdown decision. Machine still spinning (Ncp=102) at this point.
    This is the event we want to predict. NOT the physical ramp-down (09:57).

  train_fraction = 0.60
    Rows 0-25618, ends 2023-11-11 10:34. Pure normal operation.
    Last 40% contains degradation signal + shutdown event.

  Ncp dropped: speed is constant at ~102 RPM during normal operation.
    It drops only after shutdown decision — consequence, not predictor.

  After_Shutdown not used: machine is off, vibration ~0.6 mm/s (noise floor).
    Including it would distort FAR computation.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)

TIMESTAMP_FMT  = "%d-%m-%Y# %H:%M:%S"
VIB_COLS       = ["LPC_DE_X_Vib", "LPC_DE_Y_Vib", "LPC_NDE_X_Vib", "LPC_NDE_Y_Vib"]
FAILURE_TIME   = "2023-11-13 09:46:00"
TRAIN_FRACTION = 0.60


def load_ongc_run(before_path: str, after_path: str) -> dict:
    """
    Load and split the ONGC Solar Turbine dataset.

    Parameters
    ----------
    before_path : path to Before_Shutdown.xlsx
    after_path  : path to After_Shutdown.xlsx (loaded only to log the gap)

    Returns
    -------
    dict:
        "df_train"     : DataFrame  normal operation (rows 0..60%)
        "df_test"      : DataFrame  degradation period (rows 60%..100%)
        "failure_time" : str        operator shutdown timestamp
        "vib_cols"     : list[str]  vibration column names
    """
    before = pd.read_excel(before_path)
    after  = pd.read_excel(after_path)
    logger.info(f"Loaded Before={before.shape}, After={after.shape}")

    before["ts"] = pd.to_datetime(before["Time Stamp"], format=TIMESTAMP_FMT)
    after["ts"]  = pd.to_datetime(after["Time Stamp"],  format=TIMESTAMP_FMT)

    gap_sec = (after["ts"].iloc[0] - before["ts"].iloc[-1]).total_seconds()
    logger.info(f"Gap between files: {gap_sec:.0f}s")

    # Keep vibration + index only. Drop Ncp, Time Stamp string, Unnamed:6.
    before = before[["ts"] + VIB_COLS].set_index("ts").sort_index()

    n         = len(before)
    split_idx = int(n * TRAIN_FRACTION)
    df_train  = before.iloc[:split_idx].copy()
    df_test   = before.iloc[split_idx:].copy()

    logger.info(f"Train: {df_train.shape} ({df_train.index[0]} -> {df_train.index[-1]})")
    logger.info(f"Test:  {df_test.shape}  ({df_test.index[0]} -> {df_test.index[-1]})")

    t_fail = pd.Timestamp(FAILURE_TIME)
    assert df_test.index[0] <= t_fail <= df_test.index[-1], (
        f"failure_time {FAILURE_TIME} not in test window "
        f"[{df_test.index[0]}, {df_test.index[-1]}]"
    )

    return {
        "df_train":     df_train,
        "df_test":      df_test,
        "failure_time": FAILURE_TIME,
        "vib_cols":     VIB_COLS,
    }