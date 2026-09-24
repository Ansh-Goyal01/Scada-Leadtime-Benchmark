# src/d2_deep_tradeoff.py
"""
Reviewer D item D2 (register 1.3 / 0.2) — deep reconstruction models in the IMS
threshold sweep that produced Table 16 (``tab:tradeoff``).

The submitted Section 6.1 stated that LSTM-AE, TCN-AE and Transformer-AD have no valid
operating point at any threshold, but the sweep behind Table 16 did not include them. This script
runs exactly the same sweep that produced Table 16 -- ``src.tradeoff.tradeoff_for_run``,
unmodified -- for the three deep models at the 95th, 99th and 99.5th percentiles, so
the assertion becomes evidence.

Nothing existing is modified. ``tradeoff_for_run`` already accepts a ``methods`` list
and its default is ``EXPERIMENT["methods_to_run"]``, which already contains all three
deep models; Table 16's omission was a run-time choice, not a code limitation.

Outputs (NEW files -- the published tradeoff_IMS*.csv are never touched):
    results/tables/tradeoff_IMS_deepmodels_long.csv   per (run, method, percentile)
    results/tables/tradeoff_IMS_deepmodels.csv        mean across runs, Table-16 shape

Entry point:
    python -m src.d2_deep_tradeoff
"""

import os
import sys
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# The three deep reconstruction models Section 6.1 makes the claim about.
DEEP_METHODS = ["lstm_ae", "tcn", "transformer_ad"]

# The three percentiles Table 16 reports.
PERCENTILES = [95.0, 99.0, 99.5]

# The pre-onset FAR budget tau, as a percentage. Operating points above this are
# daggered in Table 16 and are invalid under the gated metric (Eq. 5).
TAU_PCT = 10.0

SEED = 42


def run_deep_tradeoff(runs: list = None,
                      methods: list = None,
                      percentiles: list = None,
                      seed: int = SEED,
                      save: bool = True) -> tuple:
    """
    Sweep threshold percentiles for the deep models on every IMS run.

    Returns (long, agg). ``long`` is one row per (run, method, percentile);
    ``agg`` is the mean across runs, in the shape Table 16 reports.
    """
    from src.tradeoff import tradeoff_for_run
    from src.datasets import default_runs
    from src.config import PATHS

    runs = runs or default_runs("IMS")
    methods = methods or DEEP_METHODS
    percentiles = percentiles or PERCENTILES

    frames = []
    for run_name in runs:
        logger.info("[%s] sweeping %s at %s", run_name, methods, percentiles)
        frames.append(tradeoff_for_run(run_name, dataset="IMS", methods=methods,
                                       percentiles=percentiles, seed=seed))
    long = pd.concat(frames, ignore_index=True)

    # Same collapse as src.tradeoff.run_tradeoff: mean across runs per
    # (method, percentile). Reproduced rather than imported because run_tradeoff
    # would overwrite the published tradeoff_IMS.csv.
    agg = (long.groupby(["dataset", "method", "short_name", "percentile"])
           .agg(lead_time_hours_mean=("lead_time_hours", "mean"),
                lead_time_hours_std=("lead_time_hours", "std"),
                far_preonset_pct_mean=("far_preonset_pct", "mean"),
                far_preonset_pct_std=("far_preonset_pct", "std"),
                far_preonset_pct_min=("far_preonset_pct", "min"),
                far_preonset_pct_max=("far_preonset_pct", "max"),
                valid_frac=("valid_alarm", "mean"),
                n_runs=("run", "nunique"))
           .reset_index())

    # Dagger rule, exactly as Table 16's caption states it: the mean pre-onset FAR
    # exceeds the tau = 10% budget.
    agg["dagger"] = agg["far_preonset_pct_mean"] > TAU_PCT
    # The stronger per-run question Section 6.1 actually claims: is there ANY run at
    # this percentile whose pre-onset FAR sits inside the budget?
    agg["any_run_within_budget"] = agg["far_preonset_pct_min"] <= TAU_PCT

    if save:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        lp = os.path.join(PATHS["results_tables"], "tradeoff_IMS_deepmodels_long.csv")
        ap = os.path.join(PATHS["results_tables"], "tradeoff_IMS_deepmodels.csv")
        long.to_csv(lp, index=False)
        agg.to_csv(ap, index=False)
        logger.info("Saved -> %s (%d rows)", lp, len(long))
        logger.info("Saved -> %s (%d rows)", ap, len(agg))
    return long, agg


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
    long, agg = run_deep_tradeoff()

    pd.set_option("display.width", 220, "display.max_columns", 40)
    print("\n=== D2: per-run detail ===")
    print(long[["run", "short_name", "percentile", "lead_time_hours",
                "far_preonset_pct", "valid_alarm"]].to_string(index=False))

    print("\n=== D2: Table-16 shape (mean across runs) ===")
    for _, r in agg.sort_values(["short_name", "percentile"]).iterrows():
        dag = "†" if r["dagger"] else " "
        print(f"{r['short_name']:16s} p={r['percentile']:5.1f}  "
              f"Ld={r['lead_time_hours_mean']:8.2f}  "
              f"FAR={r['far_preonset_pct_mean']:6.2f}{dag}  "
              f"[per-run FAR {r['far_preonset_pct_min']:.1f}-{r['far_preonset_pct_max']:.1f}]  "
              f"valid_frac={r['valid_frac']:.2f}  "
              f"any_run_in_budget={bool(r['any_run_within_budget'])}")

    # The decisive question for Section 6.1.
    valid = agg[agg["valid_frac"] > 0]
    print("\n=== D2: does any deep model have a valid operating point in the sweep? ===")
    if valid.empty:
        print("NO deep model attains a valid alarm at any percentile tested. "
              "Section 6.1's claim is SUPPORTED by this evidence.")
    else:
        print("At least one deep model HAS a valid operating point. "
              "Section 6.1 is WRONG as written and must be corrected:")
        print(valid[["short_name", "percentile", "lead_time_hours_mean",
                     "far_preonset_pct_mean", "valid_frac"]].to_string(index=False))


if __name__ == "__main__":
    main()
