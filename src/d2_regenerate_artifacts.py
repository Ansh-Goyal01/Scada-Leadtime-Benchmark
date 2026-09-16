"""
Regenerate the IMS controlled-sweep artifacts under the invariant schema (decision D-2).

Every artifact here is produced by the repo's OWN generator functions, fed the
invariant long frame instead of the legacy one -- no statistics are reimplemented:

    src.benchmark.aggregate_long                    -> benchmark_IMS_aggregate_*
    src.benchmark.bootstrap_ci_across_runs          -> benchmark_IMS_leadtime_ci_*   (Table 2)
    src.benchmark.paired_test_aggregate_vs_decimate -> benchmark_IMS_paired_test_*   (diagnostic)
    src.stats_rigor.ims_runlevel_table              -> ims_runlevel_test_*           (Table 10)
    src.stats_rigor.family_holm                     -> paired_tests_holm_*           (Table 11)

`src.stats_rigor._read_long` hardcodes `benchmark_{dataset}_long.csv`, which is why the
CLI there cannot regenerate these; this script supplies the frame directly and leaves
`stats_rigor` untouched.

Output files carry an `_invariant` suffix. The originally published files are NOT
overwritten -- the response letter needs both columns side by side, and `results/` is
gitignored (defect N-3), so an overwrite would be unrecoverable.
"""

import argparse
import os
import sys

import pandas as pd

from src.benchmark import (aggregate_long, bootstrap_ci_across_runs,
                           paired_test_aggregate_vs_decimate)
from src.config import PATHS
from src.stats_rigor import family_holm, ims_runlevel_table

try:                                       # N-13: cp1252 console cannot print sigma
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

T = PATHS["results_tables"]
INFERENTIAL = ["IMS", "XJTU-SY", "FEMTO", "Ferrara"]     # ONGC excluded, n=1


def _write(df: pd.DataFrame, name: str, force: bool) -> None:
    path = os.path.join(T, name)
    if os.path.exists(path) and not force:
        print(f"  SKIP  {name} (exists; pass --force to replace)")
        return
    df.to_csv(path, index=False)
    print(f"  wrote {name}  ({len(df)} rows)")


def _ci_row(r: pd.Series) -> str:
    return f"[{r['lead_time_hours_lo']:.1f}, {r['lead_time_hours_hi']:.1f}]"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="replace existing *_invariant.csv outputs")
    args = ap.parse_args()

    inv = pd.read_csv(os.path.join(T, "benchmark_IMS_long_invariant.csv"))
    others = {ds: pd.read_csv(os.path.join(T, f"benchmark_{ds}_long.csv"))
              for ds in INFERENTIAL if ds != "IMS"}
    legacy_ims = pd.read_csv(os.path.join(T, "benchmark_IMS_long.csv"))

    print("=" * 92)
    print("Regenerating IMS controlled-sweep artifacts on the INVARIANT schema (D-2)")
    print("=" * 92)

    agg = aggregate_long(inv)
    ci = bootstrap_ci_across_runs(inv, metric="lead_time_hours")
    paired = paired_test_aggregate_vs_decimate(inv, metric="lead_time_hours")
    runlevel = ims_runlevel_table(inv)

    tables = [runlevel] + [ims_runlevel_table(d) for d in others.values()]
    fam = family_holm(tables, alpha=0.05, p_col="sign_test_p")

    _write(agg, "benchmark_IMS_aggregate_invariant.csv", args.force)
    _write(ci, "benchmark_IMS_leadtime_ci_invariant.csv", args.force)
    _write(paired, "benchmark_IMS_paired_test_invariant.csv", args.force)
    _write(runlevel, "ims_runlevel_test_invariant.csv", args.force)
    _write(fam, "paired_tests_holm_invariant.csv", args.force)

    # ---- Table 2 (tab:imslead) -------------------------------------------------
    print("\n" + "=" * 92)
    print("TABLE 2 (tab:imslead) -- IMS mean raw lead at full resolution, 95% bootstrap CI")
    print("=" * 92)
    old = bootstrap_ci_across_runs(
        legacy_ims[(legacy_ims.factor == 1) & (legacy_ims["mode"] == "aggregate")],
        metric="lead_time_hours").set_index("method")
    new = ci[(ci.factor == 1) & (ci["mode"] == "aggregate")].set_index("method")
    print(f"{'method':<24}{'OLD':>8}{'OLD 95% CI':>20}{'NEW':>8}{'NEW 95% CI':>20}{'delta':>8}")
    for m in old.index:
        o, n = old.loc[m], new.loc[m]
        d = float(n["lead_time_hours_mean"]) - float(o["lead_time_hours_mean"])
        print(f"{m:<24}{o['lead_time_hours_mean']:8.1f}{_ci_row(o):>20}"
              f"{n['lead_time_hours_mean']:8.1f}{_ci_row(n):>20}{d:8.1f}")

    # ---- Table 10 (tab:imssweep) ----------------------------------------------
    print("\n" + "=" * 92)
    print("TABLE 10 (tab:imssweep) -- run-level aggregate vs decimate, INVARIANT")
    print("=" * 92)
    print(runlevel[["method", "run_diffs", "median_diff", "n_pos", "n_neg",
                    "all_same_sign", "sign_test_p"]]
          .to_string(index=False, float_format=lambda v: f"{v:8.3f}"))

    # ---- Table 11 (tab:holm) ---------------------------------------------------
    print("\n" + "=" * 92)
    print("TABLE 11 (tab:holm) -- N=40 family with invariant IMS rows")
    print("=" * 92)
    print(f"  family size N = {int(fam['family_size'].iloc[0])}, "
          f"rejected = {int(fam['holm_reject'].sum())}")
    jmin = fam["sign_test_p"].idxmin()
    print(f"  smallest raw p = {fam.loc[jmin, 'sign_test_p']:.3f} "
          f"({fam.loc[jmin, 'dataset']} / {fam.loc[jmin, 'method']}), "
          f"Holm {fam.loc[jmin, 'holm_p']:.3f}")
    print(fam[fam.dataset == "IMS"][["method", "median_diff", "sign_test_p", "holm_p",
                                     "holm_reject"]]
          .to_string(index=False, float_format=lambda v: f"{v:8.3f}"))

    # ---- Figure 3 (fig:sweep) --------------------------------------------------
    print("\n" + "=" * 92)
    print("FIGURE 3 (fig:sweep) -- mean lead (h) vs factor, by mode; OLD -> NEW")
    print("=" * 92)
    for det in ("3σ Rule (σ=3.0)", "Isolation Forest"):
        print(f"  --- {det} ---")
        print(f"  {'factor':>7}{'OLD agg':>9}{'OLD dec':>9}{'NEW agg':>9}{'NEW dec':>9}")
        for f in sorted(inv.factor.unique()):
            vals = []
            for d in (legacy_ims, inv):
                for mode in ("aggregate", "decimate"):
                    s = d[(d.method == det) & (d.factor == f) & (d["mode"] == mode)]
                    vals.append(s["lead_time_hours"].mean())
            print(f"  {f:>7}{vals[0]:9.1f}{vals[1]:9.1f}{vals[2]:9.1f}{vals[3]:9.1f}")


if __name__ == "__main__":
    main()
