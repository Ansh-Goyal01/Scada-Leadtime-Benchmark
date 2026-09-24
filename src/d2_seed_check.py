# src/d2_seed_check.py
"""
Robustness check on the ONE cell that carries defect N-16.

D2 (see src/d2_deep_tradeoff.py) found exactly one valid operating point in the whole
deep-model threshold sweep: LSTM-AE, 3rd_test, 99.5th percentile -- FAR_pre 4.19%,
lead 59.67 h, valid_alarm True. That single cell refutes the submitted claim that the deep
models have no valid operating point at any threshold. Because the deep detectors are
stochastic, this script
re-runs that one cell across several seeds and reports how often a valid operating
point appears and how far the pre-onset FAR moves.

THIS IS A CHECK, NOT A PROTOCOL CHANGE. The paper's fixed-seed protocol stands: seed
42 is and remains the reported configuration, and no published number is recomputed
here. The extra seeds exist only to say how fragile the N-16 counterexample is, and
must be reported as a robustness check rather than folded into any headline number.

Uses ``src.tradeoff.tradeoff_for_run`` unmodified, varying only its existing ``seed``
argument -- which ``benchmark.make_detectors`` injects into lstm_ae's random_state.

Output (NEW):
    results/tables/d2_seed_check_lstmae.csv

Entry point:
    python -m src.d2_seed_check
"""

import os
import sys
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# The cell under test.
RUN = "3rd_test"
METHOD = "lstm_ae"
PERCENTILE = 99.5

# The paper's protocol seed, listed first so it is unmistakable in the output.
PROTOCOL_SEED = 42
SEEDS = [42, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Pre-onset FAR budget, as a percentage.
TAU_PCT = 10.0


def run_seed_check(seeds=None, save=True):
    """Re-run the single cell once per seed; return the long frame."""
    from src.tradeoff import tradeoff_for_run
    from src.config import PATHS

    seeds = seeds or SEEDS
    rows = []
    for seed in seeds:
        logger.info("seed %d: %s / %s / %.1f", seed, RUN, METHOD, PERCENTILE)
        df = tradeoff_for_run(RUN, dataset="IMS", methods=[METHOD],
                              percentiles=[PERCENTILE], seed=seed)
        df = df.copy()
        df["seed"] = seed
        rows.append(df)
    out = pd.concat(rows, ignore_index=True)

    if save:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        p = os.path.join(PATHS["results_tables"], "d2_seed_check_lstmae.csv")
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
    pd.set_option("display.width", 200, "display.max_columns", 20)

    df = run_seed_check()

    print("\n=== D2 seed check: LSTM-AE / %s / %.1fth percentile ===" % (RUN, PERCENTILE))
    print("    (robustness check only -- the paper's fixed-seed protocol is unchanged)")
    for _, r in df.sort_values("seed").iterrows():
        mark = "  <- PROTOCOL SEED" if r["seed"] == PROTOCOL_SEED else ""
        print("  seed %2d  lead=%8.2f h  FAR_pre=%7.2f%%  valid=%-5s%s"
              % (r["seed"], r["lead_time_hours"], r["far_preonset_pct"],
                 r["valid_alarm"], mark))

    n = len(df)
    n_valid = int(df["valid_alarm"].sum())
    far = df["far_preonset_pct"].astype(float)
    lead = df["lead_time_hours"].astype(float)

    print("\n=== summary over %d seeds ===" % n)
    print("  valid operating point: %d/%d seeds (%.0f%%)" % (n_valid, n, 100.0 * n_valid / n))
    print("  FAR_pre  min=%.2f%%  median=%.2f%%  max=%.2f%%  (budget tau=%.0f%%)"
          % (far.min(), far.median(), far.max(), TAU_PCT))
    print("  FAR_pre within budget: %d/%d seeds" % (int((far <= TAU_PCT).sum()), n))
    print("  lead     min=%.2f  median=%.2f  max=%.2f h" % (lead.min(), lead.median(), lead.max()))

    print("\n=== reading ===")
    if n_valid == n:
        print("  The counterexample holds at EVERY seed tested. N-16 is robust;")
        print("  tex:275's universal fails under any seed, not just seed 42.")
    elif n_valid == 0:
        print("  The counterexample appears at NO seed other than the protocol seed.")
        print("  N-16 still stands under the paper's own protocol, but the correction")
        print("  must be worded as seed-specific.")
    else:
        print("  The counterexample appears at %d of %d seeds. N-16 stands -- a universal" % (n_valid, n))
        print("  claim fails on one counterexample -- but the corrected sentence should")
        print("  report the frequency rather than imply the valid point is always attained.")


if __name__ == "__main__":
    main()
