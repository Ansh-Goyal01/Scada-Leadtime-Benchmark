# src/d17_original_label.py
"""
Reviewer D item D17 (register 1.4) -- the IMS sweep under the ORIGINAL test-3 label.

The corrected test-3 failure label is the author's relabeling (Appendix C), and test 3
is one of the three IMS runs behind the directional trend, so this script also reports
the full sweep under the original label.

This reruns the full IMS controlled sweep -- all ten detectors -- with 3rd_test's
failure time set back to the original 2004-04-08 09:16, and reports it beside the
corrected 2004-04-18 02:42 label.

HOW THE LABEL IS CHANGED. ``config.py`` is NOT edited. The label is patched in memory
inside a context manager that restores it, which is safe and exact here because
``load_pipeline_controlled`` loads the cached ``*_features.parquet`` when it exists,
so ``DATASET["failure_times"]`` never reaches feature extraction. It changes only
(a) the ``failure_time`` the pipeline returns and (b) the onset, which is estimated
relative to that time. Features, splits and windowing are bit-identical between the
two arms, so the contrast isolates the label and nothing else.

CONVENTION. Differences are collapsed by MEAN over factors and seeds within each mode,
per Section 4.8, using the repo's own ``run_level_diffs`` / ``exact_sign_test``.
The corrected-label arm is read from the existing invariant re-baseline
(``benchmark_IMS_long_invariant.csv``, decision D-2) rather than recomputed, so both
arms sit on the same 49-dim schema.

THE POINT TO STATE PLAINLY. Under the original label the failure is placed ~10 days
before the end of the run, so a large part of the test region lies AFTER the nominal
failure. If a detector cannot earn positive lead on test 3 in EITHER mode, its
aggregate-minus-decimate difference for that run is exactly zero -- and the sign test
excludes zero-difference runs (Section 4.8). Test 3 then drops out of the count and
IMS falls from n = 3 to n_effective = 2, where the exact two-sided sign test floors at
p = 0.50 and can never reach alpha. This script reports n_effective and the attainable
floor per detector so that consequence is visible rather than inferred.

Outputs (all NEW; no published file is touched):
    results/tables/d17_ims_long_originallabel.csv
    results/tables/d17_label_comparison.csv

Entry point:
    python -m src.d17_original_label
"""

import os
import sys
import logging
from contextlib import contextmanager

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ORIGINAL_LABEL = "2004-04-08 09:16:00"
CORRECTED_LABEL = "2004-04-18 02:42:00"
RELABELLED_RUN = "3rd_test"

SEED = 42

# The corrected-label arm, on the invariant schema (decision D-2).
CORRECTED_LONG = "benchmark_IMS_long_invariant.csv"


@contextmanager
def temporary_failure_label(run_name, label):
    """
    Patch one run's failure time in memory, then restore it.

    ``src.config.DATASET`` is a module-level dict imported by reference in
    ``datasets.py`` and ``sampling.py``, so mutating it in place is visible to both.
    The restore runs even if the sweep raises.
    """
    from src import config
    previous = config.DATASET["failure_times"][run_name]
    config.DATASET["failure_times"][run_name] = label
    logger.info("failure label for %s: %s -> %s", run_name, previous, label)
    try:
        yield
    finally:
        config.DATASET["failure_times"][run_name] = previous
        logger.info("failure label for %s restored to %s", run_name, previous)


def run_original_label(save=True):
    """Run the full IMS controlled sweep, all ten detectors, under the original label."""
    from src.benchmark import run_benchmark
    from src.config import PATHS

    with temporary_failure_label(RELABELLED_RUN, ORIGINAL_LABEL):
        df = run_benchmark(dataset="IMS", control=True, seeds=[SEED], save=False)

    if save and not df.empty:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        p = os.path.join(PATHS["results_tables"], "d17_ims_long_originallabel.csv")
        df.to_csv(p, index=False)
        logger.info("Saved -> %s (%d rows)", p, len(df))
    return df


def label_comparison(orig_long, save=True):
    """
    Build the side-by-side table: per-run diffs, median, sign counts, sign-test p,
    and -- the item's actual question -- n_effective and the attainable floor.
    """
    from src.stats_rigor import run_level_diffs, exact_sign_test
    from src.config import PATHS

    corrected_path = os.path.join(PATHS["results_tables"], CORRECTED_LONG)
    corrected_long = pd.read_csv(corrected_path)

    rows = []
    for label_name, long_df in (("corrected (2004-04-18)", corrected_long),
                                ("original (2004-04-08)", orig_long)):
        rl = run_level_diffs(long_df, metric="lead_time_hours")
        for method, sub in rl.groupby("method"):
            sub = sub.sort_values("run")
            diffs = sub["diff"].values
            st = exact_sign_test(diffs)
            n_eff = st["n_effective"]

            t3 = sub[sub["run"] == RELABELLED_RUN]
            t3_diff = float(t3["diff"].iloc[0]) if not t3.empty else np.nan
            t3_agg = float(t3["agg"].iloc[0]) if not t3.empty else np.nan
            t3_dec = float(t3["dec"].iloc[0]) if not t3.empty else np.nan

            rows.append({
                "label": label_name,
                "method": method,
                "n_runs": st["n"],
                "run_diffs": ", ".join("%+.2f" % v for v in diffs),
                "median_diff_h": st["median"],
                "n_pos": st["n_pos"], "n_neg": st["n_neg"], "n_zero": st["n_zero"],
                "n_effective": n_eff,
                "all_same_sign": st["all_same_sign"],
                "sign_test_p": st["p_value"],
                # Attainable floor of the EXACT TWO-SIDED sign test at this n_eff.
                # Two-sided doubles the one-tail, so the floor is 2 * 0.5^n_eff,
                # capped at 1. At n_eff = 2 that is 0.50; at n_eff = 3, 0.25.
                "two_sided_floor": (min(1.0, 2.0 * 0.5 ** n_eff) if n_eff > 0 else 1.0),
                "test3_agg_h": t3_agg,
                "test3_dec_h": t3_dec,
                "test3_diff_h": t3_diff,
                "test3_is_zero": bool(t3_diff == 0.0) if not np.isnan(t3_diff) else False,
                "test3_guaranteed_miss": bool(t3_agg == 0.0 and t3_dec == 0.0)
                                         if not (np.isnan(t3_agg) or np.isnan(t3_dec)) else False,
            })

    out = pd.DataFrame(rows)
    if save:
        p = os.path.join(PATHS["results_tables"], "d17_label_comparison.csv")
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
    pd.set_option("display.width", 260, "display.max_columns", 40, "display.max_rows", 300)

    orig = run_original_label()
    cmp_df = label_comparison(orig)

    for label in ("corrected (2004-04-18)", "original (2004-04-08)"):
        sub = cmp_df[cmp_df["label"] == label].sort_values("method")
        print("\n=== D17: IMS run-level aggregate-decimate, label = %s ===" % label)
        print("    (mean collapse over factors and seeds, Section 4.8)")
        for _, r in sub.iterrows():
            print("  %-24s diffs=[%-24s] med=%+8.2f  n+/n-/0=%d/%d/%d  n_eff=%d  "
                  "same_sign=%-5s p=%.4f  floor=%.2f"
                  % (r["method"], r["run_diffs"], r["median_diff_h"],
                     r["n_pos"], r["n_neg"], r["n_zero"], r["n_effective"],
                     r["all_same_sign"], r["sign_test_p"], r["two_sided_floor"]))

    print("\n=== D17: what happens to test 3 under the original label ===")
    sub = cmp_df[cmp_df["label"] == "original (2004-04-08)"].sort_values("method")
    for _, r in sub.iterrows():
        print("  %-24s agg=%7.2f  dec=%7.2f  diff=%+7.2f  zero=%-5s  guaranteed_miss=%s"
              % (r["method"], r["test3_agg_h"], r["test3_dec_h"], r["test3_diff_h"],
                 r["test3_is_zero"], r["test3_guaranteed_miss"]))

    print("\n=== D17: effective n and the sign-test floor ===")
    for label in ("corrected (2004-04-18)", "original (2004-04-08)"):
        sub = cmp_df[cmp_df["label"] == label]
        dropped = int((sub["test3_is_zero"]).sum())
        print("  %-24s  detectors with test 3 dropped (zero diff): %d of %d"
              % (label, dropped, len(sub)))
        for n_eff, grp in sub.groupby("n_effective"):
            floor = min(1.0, 2.0 * 0.5 ** n_eff) if n_eff > 0 else 1.0
            print("      n_eff=%d -> two-sided floor p=%.2f : %d detectors"
                  % (n_eff, floor, len(grp)))


if __name__ == "__main__":
    main()
