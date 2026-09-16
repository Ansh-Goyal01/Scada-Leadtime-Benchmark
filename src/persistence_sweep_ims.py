"""
The missing generator for `results/tables/persistence_sensitivity_IMS.csv` (defect N-15).

The published file backs Table 5 (`tab:persistence`) and the Section 6.2 claim that
"the 3-sigma valid-alarm fraction is 1.00 at every persistence, so the deployable-
detector recommendation does not depend on this parameter". No script in the repo
produces it, and its `valid_frac_f1_agg` column does not reproduce from
`benchmark_IMS_long.csv` (which gives 0.67, not 1.00). This script closes both gaps:
it regenerates the table from the pipeline and reports what the data actually say.

The alarm-persistence filter is `THRESHOLD["alarm_persistence"]`, read by
`run_benchmark` at call time, so the sweep sets it per iteration and restores it --
the same pattern `src/training_sweep.py` uses to sweep the train fraction.

Six non-sequence detectors only, matching the published file (no deep AEs).

Usage
-----
    python -m src.persistence_sweep_ims                   # invariant schema (D-2 default)
    python -m src.persistence_sweep_ims --schema legacy   # the published 445-dim schema
    python -m src.persistence_sweep_ims --smoke           # persistence 3 only
"""

import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd

from src.benchmark import run_benchmark
from src.config import PATHS, THRESHOLD
from src.d2_convention_recompute import per_detector

logger = logging.getLogger(__name__)

PERSISTENCES = [1, 3, 5, 10]
DETECTORS = ["rms_trend", "three_sigma", "ewma", "cusum", "hotelling_t2",
             "isolation_forest"]
PUBLISHED = "persistence_sensitivity_IMS.csv"     # never written by this script


def valid_fraction(df: pd.DataFrame, detector: str, factor_one_only: bool) -> float:
    """Valid-alarm fraction for one detector on the aggregate arm."""
    s = df[(df.short_name == detector) & (df["mode"] == "aggregate")]
    if factor_one_only:
        s = s[s.factor == 1]
    if not len(s):
        return float("nan")
    return float(s["valid_alarm"].astype(str).str.lower().eq("true").mean())


def sweep(schema: str, persistences: list) -> pd.DataFrame:
    rows = []
    original = THRESHOLD["alarm_persistence"]
    try:
        for p in persistences:
            THRESHOLD["alarm_persistence"] = p      # read by run_benchmark at call time
            logger.info("=== alarm_persistence = %d (schema=%s) ===", p, schema)
            df = run_benchmark(dataset="IMS", methods=DETECTORS, control=True,
                               feature_mode=schema, save=False)
            stats = per_detector(df, "IMS").set_index("short_name")
            for det in DETECTORS:
                if det not in stats.index:
                    continue
                r = stats.loc[det]
                rows.append({
                    "persistence": p,
                    "detector": det,
                    "median_agg_minus_dec_h": round(float(r["median_h"]), 4),
                    "n_pos": int(r["n_pos"]),
                    "n_neg": int(r["n_neg"]),
                    "valid_frac_f1_agg": valid_fraction(df, det, True),
                    # --- added for traceability, absent from the published file ---
                    "schema": schema,
                    "n_zero": int(r["n_zero"]),
                    "sign_test_p": round(float(r["p_raw"]), 4),
                    "valid_frac_agg_all_factors": valid_fraction(df, det, False),
                })
    finally:
        THRESHOLD["alarm_persistence"] = original
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="invariant", choices=["invariant", "legacy"])
    ap.add_argument("--smoke", action="store_true", help="persistence=3 only")
    args = ap.parse_args()

    try:                                   # N-13: cp1252 console cannot print sigma
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    persistences = [3] if args.smoke else PERSISTENCES
    out = sweep(args.schema, persistences)

    name = f"persistence_sensitivity_IMS_{args.schema}.csv"
    assert name != PUBLISHED, "must never write the published file"
    path = os.path.join(PATHS["results_tables"], name)
    if not args.smoke:
        if os.path.exists(path):
            raise SystemExit(f"refusing to overwrite existing {path}")
        out.to_csv(path, index=False)
        print(f"\nWrote {path}  ({len(out)} rows)")

    print("\n" + "=" * 88)
    print(f"Table 5 (tab:persistence) regenerated -- schema = {args.schema}")
    print("=" * 88)
    piv = out.pivot(index="detector", columns="persistence",
                    values="median_agg_minus_dec_h")
    print("\nmedian aggregate - decimate (h), factors collapsed by MEAN per run (Sec 4.8)")
    print(piv.to_string(float_format=lambda v: f"{v:8.2f}"))

    print("\nvalid-alarm fraction, factor=1 aggregate  (Table 5's bottom row)")
    vp = out.pivot(index="detector", columns="persistence", values="valid_frac_f1_agg")
    print(vp.to_string(float_format=lambda v: f"{v:8.2f}"))

    print("\nsign tallies n_pos/n_neg/n_zero and exact sign-test p")
    for p in persistences:
        print(f"  --- persistence = {p} ---")
        for _, r in out[out.persistence == p].iterrows():
            print(f"    {r['detector']:<18}{r['n_pos']}+/{r['n_neg']}-/{r['n_zero']}0"
                  f"   p={r['sign_test_p']:.2f}   med={r['median_agg_minus_dec_h']:+7.2f}")

    # ---- the N-15 question, answered directly -------------------------------
    print("\n" + "=" * 88)
    print("N-15: does the published '3-sigma valid-alarm fraction = 1.00 at every")
    print("persistence' hold?")
    print("=" * 88)
    ts = out[out.detector == "three_sigma"]
    for _, r in ts.iterrows():
        print(f"  persistence {int(r['persistence']):>2}: "
              f"f=1 aggregate {r['valid_frac_f1_agg']:.2f}   "
              f"all factors aggregate {r['valid_frac_agg_all_factors']:.2f}   "
              f"(published: 1.00)")
    if np.allclose(ts["valid_frac_f1_agg"].values, 1.0):
        print("\n  -> published value CONFIRMED.")
    else:
        print("\n  -> published value NOT reproduced. The Section 6.2 sentence "
              "'the 3-sigma valid-alarm fraction is 1.00 at every persistence'")
        print("     does not follow from the pipeline output.")


if __name__ == "__main__":
    main()
