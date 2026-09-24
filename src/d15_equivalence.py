# src/d15_equivalence.py
"""
Reviewer D item D15 (register 1.2) -- equivalence evidence for the aggregate-vs-decimate
headline: a margin-based test instead of reading a non-significant difference as no effect.

Margin: delta = 1 hour, pre-specified on operational grounds (a maintenance planner
cannot act on sub-hour differences in warning time -- mobilising a crew, ordering
parts). The margin is fixed before any result is read.

PRIMARY -- two-sided 95% bootstrap CI on the run-level aggregate-minus-decimate
difference, per dataset x detector. Equivalence is established where the interval lies
entirely inside (-delta, +delta). The bootstrap convention is reused verbatim from
``src.benchmark.bootstrap_ci_across_runs``: runs are the resampling unit, B = 2000,
seed 42, percentile interval at (2.5, 97.5).

SECONDARY -- TOST by two one-sided exact sign tests, reported ONLY where the non-zero
difference count supports it. The sign test drops zero-difference runs (the paper's own
rule, Section 4.8), so the minimum attainable one-sided p is 0.5^(n_pos + n_neg) PER
DETECTOR. TOST needs both one-sided tests to reject at alpha = 0.05, which requires
n_pos + n_neg >= 5. Cells below that floor are marked infeasible and no p is reported
for them -- reporting one would be meaningless.

Run-level differences come from ``src.stats_rigor.run_level_diffs``, which collapses
factors and seeds by MEAN within each mode (Section 4.8 convention), unmodified.

Reads only published result files; writes NEW files:
    results/tables/d15_equivalence_bootstrap.csv   primary, per dataset x detector
    results/tables/d15_equivalence_tost.csv        secondary, with feasibility floors

Entry point:
    python -m src.d15_equivalence
"""

import os
import sys
import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

# Pre-specified equivalence margin, in hours, on operational grounds.
DELTA_H = 1.0

# Bootstrap convention, reused from src.benchmark.bootstrap_ci_across_runs.
N_BOOT = 2000
SEED = 42
ALPHA = 0.05

# TOST feasibility: 0.5^n <= alpha requires n >= 5 at alpha = 0.05.
TOST_ALPHA = 0.05

# Which long-format file backs each dataset. IMS appears twice: the published legacy
# 445-dim sweep and the invariant re-baseline (decision D-2). Both are reported so the
# response letter can show the pair.
SOURCES = {
    "IMS (published, legacy 445-dim)": "benchmark_IMS_long.csv",
    "IMS (invariant re-baseline, D-2)": "benchmark_IMS_long_invariant.csv",
    "XJTU-SY": "benchmark_XJTU-SY_long.csv",
    "FEMTO": "benchmark_FEMTO_long.csv",
    "Ferrara": "benchmark_Ferrara_long.csv",
    "ONGC": "benchmark_ONGC_long.csv",
}


def bootstrap_ci_diffs(diffs, rng, n_boot=N_BOOT, alpha=ALPHA):
    """
    Two-sided percentile bootstrap CI on the MEAN of run-level differences.

    Identical in construction to ``bootstrap_ci_across_runs``: resample the run vector
    with replacement n times, take the mean, read the (alpha/2, 1-alpha/2) percentiles.
    A single RandomState is threaded through all groups, exactly as the existing
    function does, so the draw sequence matches that convention.
    """
    vals = np.asarray(diffs, dtype=float)
    vals = vals[~np.isnan(vals)]
    n = len(vals)
    if n == 0:
        return np.nan, np.nan, np.nan, 0
    if n == 1:
        v = float(vals[0])
        return v, v, v, 1
    boots = np.array([rng.choice(vals, n, replace=True).mean() for _ in range(n_boot)])
    return (float(vals.mean()),
            float(np.percentile(boots, 100 * alpha / 2)),
            float(np.percentile(boots, 100 * (1 - alpha / 2))),
            n)


def one_sided_sign_test(diffs, bound, direction):
    """
    One-sided exact sign test against a shifted null, as used for TOST.

    direction "greater": H0 median <= bound  vs  H1 median > bound.
        Count runs above/below ``bound``; ties at exactly ``bound`` are dropped
        (the same zero-exclusion rule the paper's two-sided sign test uses).
        p = P(X >= n_above) under Binom(n_eff, 0.5).

    direction "less":    H0 median >= bound  vs  H1 median < bound.
        p = P(X >= n_below) under Binom(n_eff, 0.5).
    """
    d = np.asarray(diffs, dtype=float)
    d = d[~np.isnan(d)]
    n_above = int((d > bound).sum())
    n_below = int((d < bound).sum())
    n_eff = n_above + n_below
    if n_eff == 0:
        return {"n_above": n_above, "n_below": n_below, "n_eff": 0, "p": 1.0}
    k = n_above if direction == "greater" else n_below
    p = float(stats.binom.sf(k - 1, n_eff, 0.5))
    return {"n_above": n_above, "n_below": n_below, "n_eff": n_eff, "p": p}


def analyse(metric="lead_time_hours", delta=DELTA_H):
    """Compute the primary bootstrap table and the secondary TOST table."""
    from src.stats_rigor import run_level_diffs, exact_sign_test
    from src.config import PATHS

    tables_dir = PATHS["results_tables"]

    # One RandomState threaded through every group, matching the existing convention.
    rng = np.random.RandomState(SEED)

    boot_rows, tost_rows = [], []
    for label, fname in SOURCES.items():
        path = os.path.join(tables_dir, fname)
        if not os.path.exists(path):
            logger.warning("missing %s -- skipped", path)
            continue
        long_df = pd.read_csv(path)
        rl = run_level_diffs(long_df, metric=metric)
        if rl.empty:
            logger.warning("[%s] no run-level diffs", label)
            continue

        for method, sub in rl.groupby("method"):
            diffs = sub.sort_values("run")["diff"].values

            # ---- PRIMARY: bootstrap CI on the run-level difference ----
            mean, lo, hi, n = bootstrap_ci_diffs(diffs, rng)
            # Four outcomes, and the two non-equivalent ones are NOT the same finding.
            # A CI entirely above +delta means aggregation BEATS decimation by more
            # than the margin -- that supports the paper's direction while refuting
            # equivalence. A CI entirely below -delta would mean aggregation costs
            # more than the margin, which would contradict the paper.
            if n <= 1:
                verdict = "untestable (n=1 run)"
            elif np.isfinite(lo) and np.isfinite(hi) and lo > -delta and hi < delta:
                verdict = "equivalent"
            elif np.isfinite(lo) and np.isfinite(hi) and lo >= delta:
                verdict = "aggregate superior beyond margin"
            elif np.isfinite(lo) and np.isfinite(hi) and hi <= -delta:
                verdict = "aggregate inferior beyond margin"
            else:
                verdict = "inconclusive"
            boot_rows.append({
                "dataset": label, "method": method, "n_runs": n,
                "mean_diff_h": mean, "ci_lo_h": lo, "ci_hi_h": hi,
                "delta_h": delta, "verdict": verdict,
                "ci_width_h": (hi - lo) if np.isfinite(hi) and np.isfinite(lo) else np.nan,
            })

            # ---- SECONDARY: TOST feasibility, then TOST ----
            st = exact_sign_test(diffs)
            n_eff = st["n_effective"]                 # n_pos + n_neg on the raw diffs
            floor = 0.5 ** n_eff if n_eff > 0 else 1.0
            feasible = floor <= TOST_ALPHA            # equivalently n_eff >= 5

            row = {
                "dataset": label, "method": method, "n_runs": st["n"],
                "n_pos": st["n_pos"], "n_neg": st["n_neg"], "n_zero": st["n_zero"],
                "n_effective": n_eff,
                "attainable_one_sided_floor": floor,
                "tost_feasible": feasible,
                "median_diff_h": st["median"],
            }
            if feasible:
                lower = one_sided_sign_test(diffs, -delta, "greater")
                upper = one_sided_sign_test(diffs, +delta, "less")
                p_tost = max(lower["p"], upper["p"])
                row.update({
                    "p_lower": lower["p"], "n_eff_lower": lower["n_eff"],
                    "p_upper": upper["p"], "n_eff_upper": upper["n_eff"],
                    "p_tost": p_tost,
                    "tost_equivalent": bool(p_tost < TOST_ALPHA),
                })
            else:
                row.update({
                    "p_lower": np.nan, "n_eff_lower": np.nan,
                    "p_upper": np.nan, "n_eff_upper": np.nan,
                    "p_tost": np.nan, "tost_equivalent": None,
                })
            tost_rows.append(row)

    boot = pd.DataFrame(boot_rows)
    tost = pd.DataFrame(tost_rows)

    os.makedirs(tables_dir, exist_ok=True)
    bp = os.path.join(tables_dir, "d15_equivalence_bootstrap.csv")
    tp = os.path.join(tables_dir, "d15_equivalence_tost.csv")
    boot.to_csv(bp, index=False)
    tost.to_csv(tp, index=False)
    logger.info("Saved -> %s (%d rows)", bp, len(boot))
    logger.info("Saved -> %s (%d rows)", tp, len(tost))
    return boot, tost


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
    boot, tost = analyse()
    pd.set_option("display.width", 240, "display.max_columns", 40, "display.max_rows", 200)

    print("\n=== D15 PRIMARY: bootstrap 95%% CI on run-level aggregate-decimate diff "
          "(delta = %g h, B=%d, seed=%d) ===" % (DELTA_H, N_BOOT, SEED))
    for ds, sub in boot.groupby("dataset", sort=False):
        print("\n--- %s ---" % ds)
        for _, r in sub.iterrows():
            print("  %-26s n=%2d  mean=%+8.2f  CI=[%+8.2f, %+8.2f]  %s"
                  % (r["method"], r["n_runs"], r["mean_diff_h"],
                     r["ci_lo_h"], r["ci_hi_h"], r["verdict"]))

    print("\n=== D15 SECONDARY: TOST feasibility and results ===")
    for ds, sub in tost.groupby("dataset", sort=False):
        print("\n--- %s ---" % ds)
        for _, r in sub.iterrows():
            base = ("  %-26s n+/n-=%d/%d (zeros %d) n_eff=%2d  floor=%.5f"
                    % (r["method"], r["n_pos"], r["n_neg"], r["n_zero"],
                       r["n_effective"], r["attainable_one_sided_floor"]))
            if r["tost_feasible"]:
                print(base + "  p_TOST=%.4f  equivalent=%s"
                      % (r["p_tost"], bool(r["tost_equivalent"])))
            else:
                print(base + "  INFEASIBLE - floor exceeds alpha=0.05, no p reported")

    print("\n=== D15 SUMMARY ===")
    for v, n in boot["verdict"].value_counts().items():
        print("  bootstrap: %s: %d cells" % (v, n))
    print("  TOST feasible: %d of %d cells"
          % (int(tost["tost_feasible"].sum()), len(tost)))


if __name__ == "__main__":
    main()
