# src/run_sampling.py
"""
Entry point for the SCADA-rate sampling sweep — the paper's core experiment.

Usage:
    python -m src.run_sampling                 # all 3 IMS runs, both modes, all methods
    python -m src.run_sampling --run 2nd_test  # single run
    python -m src.run_sampling --quick         # fast smoke: 2nd_test, decimate, IForest only

Produces (under results/):
    tables/sampling_sweep_{run}.csv
    tables/sampling_sweep_all.csv
    tables/sampling_sweep_aggregate.csv
    figures/lead_time_vs_sampling_{run}.png             (raw hours, per run)
    figures/lead_time_vs_sampling_aggregate.png         (normalized median — headline)
    figures/lead_time_vs_sampling_aggregate_raw.png     (raw mean ± std — appendix)
"""

import os
import argparse
import logging

from src.config import PATHS, EXPERIMENT
from src.sampling import run_sampling_sweep, run_sampling_sweep_all_runs
from src.lead_time import plot_lead_time_vs_sampling


def _setup_logging():
    # Windows consoles default to cp1252, which cannot encode method names like "3σ".
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="SCADA-rate sampling sweep")
    parser.add_argument("--run", default="all",
                        help="'all', or a run name like '2nd_test'")
    parser.add_argument("--quick", action="store_true",
                        help="fast smoke test: 2nd_test, decimate mode, IForest only")
    args = parser.parse_args()

    _setup_logging()
    fig_dir = PATHS["results_figures"]
    os.makedirs(fig_dir, exist_ok=True)

    if args.quick:
        logging.info("QUICK smoke test: 2nd_test / decimate / isolation_forest")
        sweep = run_sampling_sweep(
            "2nd_test",
            modes=["decimate"],
            methods=["isolation_forest"],
        )
        print(sweep.to_string(index=False))
        plot_lead_time_vs_sampling(
            sweep, run_name="2nd_test",
            save_path=os.path.join(fig_dir, "lead_time_vs_sampling_2nd_test_quick.png"),
        )
        return

    if args.run == "all":
        all_df, agg = run_sampling_sweep_all_runs()
        # Per-run figures (raw hours — interpretable within a single run)
        for run_name in all_df["run"].unique():
            plot_lead_time_vs_sampling(
                all_df[all_df["run"] == run_name], run_name=run_name, value="raw",
                save_path=os.path.join(fig_dir, f"lead_time_vs_sampling_{run_name}.png"),
            )
        # Headline aggregate figure: normalized VLT, median across runs. Median-only
        # (no min–max band) — with four methods the bands overlap too heavily to read.
        plot_lead_time_vs_sampling(
            agg, value="normalized", show_band=False,
            save_path=os.path.join(fig_dir, "lead_time_vs_sampling_aggregate.png"),
        )
        # Appendix comparison: raw hours, mean ± std band (shows the scale-dominated view).
        plot_lead_time_vs_sampling(
            agg, value="raw", show_band=True,
            save_path=os.path.join(fig_dir, "lead_time_vs_sampling_aggregate_raw.png"),
        )
        print("\n=== Aggregate across runs (normalized median + raw) ===")
        cols = [
            "mode", "factor", "effective_interval_min", "method",
            "VLT_norm_median", "VLT_norm_min", "VLT_norm_max",
            "VLT_hours_median", "VLT_hours_mean", "VLT_hours_std",
            "FAR_pct_median", "n_runs",
        ]
        print(agg[[c for c in cols if c in agg.columns]].to_string(index=False))
    else:
        sweep = run_sampling_sweep(args.run)
        plot_lead_time_vs_sampling(
            sweep, run_name=args.run,
            save_path=os.path.join(fig_dir, f"lead_time_vs_sampling_{args.run}.png"),
        )
        print(sweep.to_string(index=False))


if __name__ == "__main__":
    main()
