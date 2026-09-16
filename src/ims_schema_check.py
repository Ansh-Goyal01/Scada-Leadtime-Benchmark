"""
Phase 0.5(B) — IMS on the CONTROLLED path under the INVARIANT feature schema.

Decision D-2 (see IJPHM-PROGRESS.md §4): the published IMS results were produced on
the controlled path under the 445-dim LEGACY feature schema, while the other four
datasets ran the 49-dim INVARIANT schema. Defect N-2 records that `config.py` calls
the legacy schema "back-compat and appendix comparison only" and that §4.2 of the
paper argues at length that it is ill-posed (p >> n).

This script measures the difference. It does NOT swap anything in:

  * it writes a NEW result file, `benchmark_IMS_long_invariant.csv`;
  * it never writes `benchmark_IMS_long.csv` (run_benchmark is called with save=False);
  * `load_pipeline_controlled(feature_mode=...)` defaults to "legacy", so every existing
    caller — and the published file — is untouched and stays bit-reproducible.

Usage
-----
    python -m src.ims_schema_check              # full sweep
    python -m src.ims_schema_check --smoke      # one run, two factors (timing check)
"""

import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd

from src.benchmark import run_benchmark, paired_test_aggregate_vs_decimate
from src.config import PATHS

logger = logging.getLogger(__name__)

PUBLISHED = "benchmark_IMS_long.csv"
NEW_FILE = "benchmark_IMS_long_invariant.csv"


def run_level_diffs(df: pd.DataFrame, metric: str = "lead_time_hours") -> pd.DataFrame:
    """
    DO NOT USE FOR REPORTED NUMBERS. This is NOT the paper's convention.

    Section 4.8 (`scada_ijphm.tex:252`) and Table 10's caption (`:491`) both specify
    collapsing the five within-run factors by the MEAN, not the median. The median
    used here masks a run whose mean difference is negative, which is exactly what
    made the session-2 reading ("no sign reversal anywhere") wrong.

    Use `src.d2_convention_recompute.run_level_diffs` instead: it collapses by the
    mean and applies the run-level exact sign test plus Holm. Kept here only so the
    sweep-and-write path in main() stays runnable unchanged.
    """
    key = ["run", "seed", "method", "short_name", "factor"]
    wide = df.pivot_table(index=key, columns="mode", values=metric, aggfunc="mean")
    if not {"aggregate", "decimate"}.issubset(wide.columns):
        return pd.DataFrame()
    wide = wide.dropna(subset=["aggregate", "decimate"]).reset_index()
    wide["diff"] = wide["aggregate"] - wide["decimate"]
    out = (wide.groupby(["run", "short_name"])["diff"]
                .median()
                .reset_index()
                .rename(columns={"diff": "run_level_diff_h"}))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="one run, factors 1 and 2 — timing check only, writes nothing")
    ap.add_argument("--report-only", action="store_true",
                    help="skip the sweep; re-report from the existing new result file")
    args = ap.parse_args()

    # Detector names carry sigma ("3-sigma rule", "RMS-Trend (k-sigma)"). On Windows the
    # default console codec is cp1252 and printing them raises UnicodeEncodeError, which
    # is the same encoding fault that corrupts Figures 2 and 10 (register item 4.1).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    runs = ["2nd_test"] if args.smoke else None
    factors = [1, 2] if args.smoke else None

    print("=" * 78)
    print("Phase 0.5(B) — IMS controlled path, INVARIANT schema")
    print("=" * 78)

    out_path = os.path.join(PATHS["results_tables"], NEW_FILE)

    if args.report_only:
        df_new = pd.read_csv(out_path)
        print(f"Read  {out_path}  ({len(df_new)} rows, re-reporting — no sweep run)")
    else:
        df_new = run_benchmark(
            dataset="IMS",
            runs=runs,
            factors=factors,
            control=True,
            feature_mode="invariant",
            save=False,             # never touch the published file
        )
        df_new["feature_mode"] = "invariant"

    if args.smoke:
        print(f"\nSMOKE OK — {len(df_new)} rows, nothing written.")
        print(df_new[["run", "short_name", "mode", "factor", "n_test_windows",
                      "lead_time_hours", "valid_alarm"]].head(20).to_string(index=False))
        return

    if not args.report_only:
        if os.path.exists(out_path):
            raise SystemExit(f"refusing to overwrite existing {out_path}")
        df_new.to_csv(out_path, index=False)
        print(f"\nWrote {out_path}  ({len(df_new)} rows)")

    pub_path = os.path.join(PATHS["results_tables"], PUBLISHED)
    df_pub = pd.read_csv(pub_path)
    print(f"Read  {pub_path}  ({len(df_pub)} rows, published 445-dim legacy)")

    # ── per-run contrast, side by side ──────────────────────────────────────────
    inv = run_level_diffs(df_new).rename(columns={"run_level_diff_h": "invariant"})
    leg = run_level_diffs(df_pub).rename(columns={"run_level_diff_h": "legacy_published"})
    side = leg.merge(inv, on=["run", "short_name"], how="outer")
    side["delta"] = side["invariant"] - side["legacy_published"]

    print("\n" + "=" * 78)
    print("PER-RUN aggregate - decimate lead-time difference (h), collapsing factors")
    print("legacy_published = 445-dim (as published) | invariant = 49-dim + top-k")
    print("=" * 78)
    for run, g in side.groupby("run"):
        print(f"\n--- {run} ---")
        print(g[["short_name", "legacy_published", "invariant", "delta"]]
              .to_string(index=False, float_format=lambda v: f"{v:8.3f}"))

    # ── sign summary across the three runs, per detector ────────────────────────
    print("\n" + "=" * 78)
    print("SIGN SUMMARY across the three IMS runs (n_+/n_-, zero-diff runs excluded)")
    print("=" * 78)
    rows = []
    for det, g in side.groupby("short_name"):
        for col in ("legacy_published", "invariant"):
            d = g[col].dropna().values
            rows.append({
                "short_name": det, "schema": col,
                "median_h": float(np.median(d)) if len(d) else np.nan,
                "n_pos": int((d > 0).sum()), "n_neg": int((d < 0).sum()),
                "n_zero": int((d == 0).sum()),
            })
    summ = pd.DataFrame(rows).pivot(index="short_name", columns="schema",
                                    values=["median_h", "n_pos", "n_neg", "n_zero"])
    print(summ.to_string(float_format=lambda v: f"{v:7.3f}"))

    # ── pooled paired test, both schemas ────────────────────────────────────────
    print("\n" + "=" * 78)
    print("POOLED paired test — NOT THE PAPER'S TEST. Section 4.8 explicitly disavows")
    print("pooling the factors as 15 pairs: it 'inflates the effective sample size")
    print("fivefold and yields overconfident p-values'. Diagnostic only; never report.")
    print("Use src/d2_convention_recompute.py for the run-level sign test + Holm.")
    print("=" * 78)
    for label, d in (("legacy_published", df_pub), ("invariant", df_new)):
        pt = paired_test_aggregate_vs_decimate(d, metric="lead_time_hours")
        if len(pt):
            print(f"\n--- {label} ---")
            print(pt[["method", "n_pairs", "median_diff_agg_minus_dec",
                      "p_value", "rank_biserial"]]
                  .to_string(index=False, float_format=lambda v: f"{v:8.4f}"))

    # ── dimensionality / validity context ───────────────────────────────────────
    print("\n" + "=" * 78)
    print("CONTEXT")
    print("=" * 78)
    for label, d in (("legacy_published", df_pub), ("invariant", df_new)):
        v = d["valid_alarm"].astype(str).str.lower().eq("true")
        print(f"  {label:<18} rows={len(d):4d}  valid={int(v.sum()):4d}  "
              f"test_windows={sorted(d['n_test_windows'].unique())}")


if __name__ == "__main__":
    main()
