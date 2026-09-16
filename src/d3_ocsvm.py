# src/d3_ocsvm.py
"""
Reviewer D item D3 (register 1.7) -- one-class SVM.

Section 4.5 states that one-class SVM was evaluated, but no results table contains it.
The detector IS implemented and wired up (``src.models.OneClassSVMDetector``, dispatched
at ``models.py:623``, parameters at ``config.py:166``, and it is even listed in
``benchmark.py``'s ``_DETERMINISTIC`` set) -- it is simply absent from
``EXPERIMENT["methods_to_run"]``. So the claim is runnable, not fabricated, and the fix
is a run rather than a deletion.

This script runs OC-SVM across every dataset on exactly the paths the published sweeps
used (IMS on the controlled path, the other four on the standard path) and derives the
rows the manuscript's OC-SVM-bearing tables would need:

    Table 2  (tab:imslead)   IMS mean raw lead + 95% bootstrap CI
    Table 7  (tab:xjtu)      XJTU-SY, same
    Table 8  (tab:femto)     FEMTO, same
    Table 9  (tab:ferrara)   Ferrara, same
    Table 11 (tab:holm)      run-level sign test, Holm across the family -- now N = 44
    Table 14 (tab:farbudget) best valid lead per FAR budget tau
    Table 16 (tab:tradeoff)  lead vs pre-onset FAR at the 95th/99th/99.5th percentiles
    Table 22 (tab:phrank)    Saxena prognostic horizon vs the gated metric L

Nothing existing is modified and no published result file is written. Every statistic
comes from the repo's own generators (``bootstrap_ci_across_runs``, ``ims_runlevel_table``,
``family_holm``, ``tradeoff_for_run``).

Outputs (all NEW):
    results/tables/d3_ocsvm_benchmark_long.csv
    results/tables/d3_ocsvm_leadtime_ci.csv
    results/tables/d3_ocsvm_holm_N44_invariant.csv
    results/tables/d3_ocsvm_holm_N44_legacy.csv
    results/tables/d3_ocsvm_tradeoff_long.csv
    results/tables/d3_ocsvm_tradeoff.csv
    results/tables/d3_ocsvm_farbudget_phrank.csv

Entry point:
    python -m src.d3_ocsvm
"""

import os
import sys
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

METHOD = "one_class_svm"
SEED = 42

# The three percentiles Table 16 reports, and the subset from which Tables 14 and 22
# are derived (verified: the published Table 22 PH for 3-sigma is 77.0, the maximum
# over {95, 99, 99.5}, not the 163.8 the 90th percentile would give).
PERCENTILES = [95.0, 99.0, 99.5]

# FAR budgets in Table 14, as percentages.
TAU_GRID_PCT = [5.0, 10.0, 20.0]

# tau for Table 22's gated column.
TAU_PCT = 10.0

# IMS runs the controlled sweep; the other four run the standard path. This mirrors
# how the published benchmarks were produced (control=True appears only in
# benchmark_IMS_long.csv).
DATASETS = [
    ("IMS", True),
    ("XJTU-SY", False),
    ("FEMTO", False),
    ("Ferrara", False),
    ("ONGC", False),
]

# The Holm family is the union of (detector x dataset) sign tests over the four
# inferential datasets. ONGC (n=1) is never included -- family_holm's own rule.
HOLM_DATASETS = ["IMS", "XJTU-SY", "FEMTO", "Ferrara"]

# Which long file supplies the existing 40 cells. IMS uses the invariant re-baseline
# per decision D-2; the published legacy file is also reported for the response letter.
HOLM_SOURCES_INVARIANT = {
    "IMS": "benchmark_IMS_long_invariant.csv",
    "XJTU-SY": "benchmark_XJTU-SY_long.csv",
    "FEMTO": "benchmark_FEMTO_long.csv",
    "Ferrara": "benchmark_Ferrara_long.csv",
}
HOLM_SOURCES_LEGACY = dict(HOLM_SOURCES_INVARIANT, IMS="benchmark_IMS_long.csv")


def run_ocsvm_benchmark(save=True):
    """Run the OC-SVM sweep on every dataset. Returns the pooled long frame."""
    from src.benchmark import run_benchmark
    from src.config import PATHS

    frames = []
    for dataset, control in DATASETS:
        logger.info("=== OC-SVM sweep: %s (control=%s) ===", dataset, control)
        df = run_benchmark(dataset=dataset, methods=[METHOD], control=control,
                           seeds=[SEED], save=False)
        if df.empty:
            logger.warning("[%s] produced no rows", dataset)
            continue
        frames.append(df)
    long = pd.concat(frames, ignore_index=True)

    if save:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        p = os.path.join(PATHS["results_tables"], "d3_ocsvm_benchmark_long.csv")
        long.to_csv(p, index=False)
        logger.info("Saved -> %s (%d rows)", p, len(long))
    return long


def leadtime_ci(long, save=True):
    """Tables 2/7/8/9: mean raw lead + 95% bootstrap CI, resampling runs."""
    from src.benchmark import bootstrap_ci_across_runs
    from src.config import PATHS

    ci = bootstrap_ci_across_runs(long, metric="lead_time_hours", seed=SEED)
    if save:
        p = os.path.join(PATHS["results_tables"], "d3_ocsvm_leadtime_ci.csv")
        ci.to_csv(p, index=False)
        logger.info("Saved -> %s (%d rows)", p, len(ci))
    return ci


def holm_n44(long, sources, save=True, tag="invariant"):
    """
    Table 11: rebuild the whole family with OC-SVM added, so N goes 40 -> 44.

    The existing 40 cells are recomputed from the published long files using the
    repo's own ``ims_runlevel_table``, not read from paired_tests_holm.csv, so the
    whole family passes through one implementation of the Section 4.8 convention.
    """
    from src.stats_rigor import ims_runlevel_table, family_holm
    from src.config import PATHS

    tables = []
    for dataset in HOLM_DATASETS:
        path = os.path.join(PATHS["results_tables"], sources[dataset])
        if not os.path.exists(path):
            logger.warning("missing %s -- Holm family incomplete", path)
            continue
        base = pd.read_csv(path)
        # Add this dataset's OC-SVM rows to its own long frame before collapsing.
        oc = long[long["dataset"] == dataset]
        merged = pd.concat([base, oc], ignore_index=True) if not oc.empty else base
        tables.append(ims_runlevel_table(merged))

    fam = family_holm(tables)
    if save and not fam.empty:
        p = os.path.join(PATHS["results_tables"], "d3_ocsvm_holm_N44_%s.csv" % tag)
        fam.to_csv(p, index=False)
        logger.info("Saved -> %s (%d rows, family_size=%s)",
                    p, len(fam), fam["family_size"].iloc[0])
    return fam


def run_ocsvm_tradeoff(save=True):
    """Table 16: the IMS threshold sweep, OC-SVM only."""
    from src.tradeoff import tradeoff_for_run
    from src.datasets import default_runs
    from src.config import PATHS

    frames = []
    for run_name in default_runs("IMS"):
        logger.info("[%s] OC-SVM trade-off sweep", run_name)
        frames.append(tradeoff_for_run(run_name, dataset="IMS", methods=[METHOD],
                                       percentiles=PERCENTILES, seed=SEED))
    long = pd.concat(frames, ignore_index=True)

    agg = (long.groupby(["dataset", "method", "short_name", "percentile"])
           .agg(lead_time_hours_mean=("lead_time_hours", "mean"),
                far_preonset_pct_mean=("far_preonset_pct", "mean"),
                far_preonset_pct_min=("far_preonset_pct", "min"),
                far_preonset_pct_max=("far_preonset_pct", "max"),
                valid_frac=("valid_alarm", "mean"),
                n_runs=("run", "nunique"))
           .reset_index())
    agg["dagger"] = agg["far_preonset_pct_mean"] > TAU_PCT

    if save:
        lp = os.path.join(PATHS["results_tables"], "d3_ocsvm_tradeoff_long.csv")
        ap = os.path.join(PATHS["results_tables"], "d3_ocsvm_tradeoff.csv")
        long.to_csv(lp, index=False)
        agg.to_csv(ap, index=False)
        logger.info("Saved -> %s, %s", lp, ap)
    return long, agg


def farbudget_phrank(agg, save=True):
    """
    Tables 14 and 22, using the published convention verified against the manuscript:
    the candidate operating points are the three swept percentiles, PH is the best
    ungated lead among them, and L(tau) is the best lead whose mean pre-onset FAR
    sits within the budget (0.0 when none does).
    """
    from src.config import PATHS

    rows = []
    for short, sub in agg.groupby("short_name"):
        row = {"dataset": "IMS", "short_name": short,
               "method": sub["method"].iloc[0],
               "PH_best_raw_lead_h": float(sub["lead_time_hours_mean"].max())}
        for tau in TAU_GRID_PCT:
            within = sub[sub["far_preonset_pct_mean"] <= tau]
            row["L_tau%02d_h" % int(tau)] = (float(within["lead_time_hours_mean"].max())
                                             if not within.empty else 0.0)
        row["valid_at_tau10"] = row["L_tau10_h"] > 0.0
        rows.append(row)
    out = pd.DataFrame(rows)

    if save:
        p = os.path.join(PATHS["results_tables"], "d3_ocsvm_farbudget_phrank.csv")
        out.to_csv(p, index=False)
        logger.info("Saved -> %s (%d rows)", p, len(out))
    return out


def _setup_logging():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")   # N-13 guard
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    _setup_logging()
    pd.set_option("display.width", 240, "display.max_columns", 40, "display.max_rows", 300)

    long = run_ocsvm_benchmark()
    ci = leadtime_ci(long)
    fam_inv = holm_n44(long, HOLM_SOURCES_INVARIANT, tag="invariant")
    fam_leg = holm_n44(long, HOLM_SOURCES_LEGACY, tag="legacy")
    tl, tagg = run_ocsvm_tradeoff()
    fb = farbudget_phrank(tagg)

    print("\n=== D3: OC-SVM raw lead, full resolution (f=1, aggregate) ===")
    sub = ci[(ci["factor"] == 1) & (ci["mode"] == "aggregate")]
    for _, r in sub.iterrows():
        print("  %-10s n=%2d  mean=%8.2f h  CI=[%8.2f, %8.2f]"
              % (r["dataset"], r["n_runs"], r["lead_time_hours_mean"],
                 r["lead_time_hours_lo"], r["lead_time_hours_hi"]))

    print("\n=== D3: valid-alarm fraction and pre-onset FAR at f=1 ===")
    f1 = long[(long["factor"] == 1) & (long["mode"] == "aggregate")]
    for ds, s in f1.groupby("dataset", sort=False):
        print("  %-10s valid=%d/%d  mean FAR_pre=%.1f%%"
              % (ds, int(s["valid_alarm"].sum()), len(s),
                 s["far_preonset_pct"].mean()))

    for tag, fam in (("invariant (D-2 baseline)", fam_inv), ("legacy (as published)", fam_leg)):
        if fam.empty:
            continue
        print("\n=== D3: Holm family with OC-SVM, IMS %s -- N=%d ==="
              % (tag, fam["family_size"].iloc[0]))
        oc = fam[fam["method"].str.contains("SVM")]
        for _, r in oc.iterrows():
            print("  %-10s %-24s diffs=[%s] med=%+7.2f  n+/n-=%d/%d  p=%.4f  holm_p=%.4f  reject=%s"
                  % (r["dataset"], r["method"], r["run_diffs"], r["median_diff"],
                     r["n_pos"], r["n_neg"], r["sign_test_p"], r["holm_p"], r["holm_reject"]))
        print("  family rejections: %d of %d" % (int(fam["holm_reject"].sum()), len(fam)))

    print("\n=== D3: Table 16 row (IMS trade-off) ===")
    for _, r in tagg.iterrows():
        print("  p=%5.1f  Ld=%8.2f  FAR=%6.2f%s  [per-run %.1f-%.1f]  valid_frac=%.2f"
              % (r["percentile"], r["lead_time_hours_mean"], r["far_preonset_pct_mean"],
                 "+" if r["dagger"] else " ",
                 r["far_preonset_pct_min"], r["far_preonset_pct_max"], r["valid_frac"]))

    print("\n=== D3: Tables 14 and 22 rows ===")
    for _, r in fb.iterrows():
        print("  PH=%.1f  L(tau=0.05)=%.1f  L(tau=0.10)=%.1f  L(tau=0.20)=%.1f  valid@0.10=%s"
              % (r["PH_best_raw_lead_h"], r["L_tau05_h"], r["L_tau10_h"],
                 r["L_tau20_h"], r["valid_at_tau10"]))


if __name__ == "__main__":
    main()
