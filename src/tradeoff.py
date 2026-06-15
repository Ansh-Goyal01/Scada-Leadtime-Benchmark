# src/tradeoff.py
"""
Lead-time vs pre-onset-FAR trade-off curves (Phase D10, reviewer W6 / action #9).

The novelty figure: analogous to an ROC curve but for prognostics. Sweeping the alarm
threshold percentile traces, per method, the achievable trade-off between **detection
lead time** (warning hours before failure) and the **pre-onset false-alarm rate** (FAR
measured over the full data-anchored normal region, not the old 5% marker). A method
that dominates lies up-and-to-the-left (long lead, low FAR).

Each (method × percentile) point is averaged across runs. We emit a long table and one
figure per dataset.

Entry point:
    python -m src.tradeoff --dataset IMS
"""

import os
import logging
import argparse
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_PERCENTILES = [90.0, 92.5, 95.0, 97.5, 99.0, 99.5, 99.9]


def tradeoff_for_run(run_name: str,
                     dataset: str = "IMS",
                     methods: list = None,
                     percentiles: list = None,
                     seed: int = 42) -> pd.DataFrame:
    """
    Sweep threshold percentiles for one run; return long rows of
    (method, percentile, lead_time_hours, far_preonset_pct, valid_alarm).
    """
    from src import load_pipeline
    from src.benchmark import make_detectors
    from src.lead_time import evaluate_all_methods
    from src.onset import onset_for_run
    from src.config import SPLIT, THRESHOLD, EXPERIMENT

    methods = methods or [m for m in EXPERIMENT["methods_to_run"]
                          if m != "conformal_if"]  # conformal sets its own alarm level
    percentiles = percentiles or DEFAULT_PERCENTILES

    pipe = load_pipeline(run_name, dataset=dataset)
    df = pipe["df_full"]
    n = len(df)
    train_end = df.index[min(int(n * pipe["train_fraction"]), n - 1)]
    t_fail = pd.Timestamp(pipe["failure_time"])
    onset = onset_for_run(df, train_end=train_end, t_fail=t_fail)

    rows = []
    for pct in percentiles:
        dets = make_detectors(methods, seed)
        _, results = evaluate_all_methods(
            detectors=dets,
            X_train=pipe["X_train"], X_test=pipe["X_test"],
            timestamps_test=pipe["ts_test"], failure_time=pipe["failure_time"],
            normal_period_fraction=SPLIT["normal_period_fraction"],
            threshold_strategy="percentile", threshold_percentile=pct,
            alarm_persistence=THRESHOLD["alarm_persistence"],
            t_onset=onset, far_budget=0.10, X_cal=pipe.get("X_cal"),
        )
        for r in results:
            rows.append({
                "dataset": dataset, "run": run_name, "method": r["method"],
                "short_name": r["short_name"], "percentile": pct,
                "lead_time_hours": r["lead_time_hours"],
                "far_preonset_pct": r["far_preonset_pct"],
                "valid_alarm": r["valid_alarm"],
            })
    return pd.DataFrame(rows)


def run_tradeoff(dataset: str = "IMS",
                 runs: list = None,
                 methods: list = None,
                 percentiles: list = None,
                 seed: int = 42,
                 save: bool = True) -> pd.DataFrame:
    """Sweep across runs, average per (method, percentile), save table + figure."""
    from src.config import PATHS, EXPERIMENT

    if runs is None:
        runs = ["LPC"] if dataset == "ONGC" else EXPERIMENT["runs_to_evaluate"]
    percentiles = percentiles or DEFAULT_PERCENTILES

    frames = []
    for r in runs:
        try:
            frames.append(tradeoff_for_run(r, dataset=dataset, methods=methods,
                                           percentiles=percentiles, seed=seed))
        except Exception as e:
            logger.error("[%s] tradeoff failed: %s", r, e)
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames, ignore_index=True)

    # average across runs per (method, percentile)
    agg = (long.groupby(["dataset", "method", "short_name", "percentile"])
           .agg(lead_time_hours_mean=("lead_time_hours", "mean"),
                lead_time_hours_std=("lead_time_hours", "std"),
                far_preonset_pct_mean=("far_preonset_pct", "mean"),
                far_preonset_pct_std=("far_preonset_pct", "std"),
                valid_frac=("valid_alarm", "mean"),
                n_runs=("run", "nunique"))
           .reset_index())

    if save and not long.empty:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        long.to_csv(os.path.join(PATHS["results_tables"],
                                 f"tradeoff_{dataset}_long.csv"), index=False)
        agg.to_csv(os.path.join(PATHS["results_tables"],
                                f"tradeoff_{dataset}.csv"), index=False)
        _plot_tradeoff(agg, dataset)
    return agg


def _plot_tradeoff(agg: pd.DataFrame, dataset: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from src.config import PATHS, PLOT

    method_colors = PLOT.get("method_colors", {})
    fig, ax = plt.subplots(figsize=(8, 5.5))

    for sn, sub in agg.groupby("short_name"):
        sub = sub.sort_values("far_preonset_pct_mean")
        color = method_colors.get(sn, None)
        label = sub["method"].iloc[0]
        ax.plot(sub["far_preonset_pct_mean"], sub["lead_time_hours_mean"],
                "o-", color=color, linewidth=1.8, markersize=6, label=label, zorder=3)
        # annotate percentile at each point
        for _, row in sub.iterrows():
            ax.annotate(f"{row['percentile']:g}",
                        (row["far_preonset_pct_mean"], row["lead_time_hours_mean"]),
                        textcoords="offset points", xytext=(5, 4), fontsize=7,
                        color=color)

    ax.axvline(10.0, color="#FF9800", linewidth=1.5, linestyle=":",
               label="10% FAR budget")
    ax.set_xlabel("Pre-onset False Alarm Rate (%)  — lower is better", fontsize=11)
    ax.set_ylabel("Detection Lead Time (hours)  — higher is better", fontsize=11)
    ax.set_title(f"Lead-Time vs Pre-onset FAR Trade-off — {dataset}\n"
                 f"(threshold percentile swept; mean across runs)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    os.makedirs(PATHS["results_figures"], exist_ok=True)
    out = os.path.join(PATHS["results_figures"], f"tradeoff_far_vlt_{dataset}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    logger.info("Saved FAR–VLT trade-off figure → %s", out)
    plt.close(fig)


def _setup_logging():
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    _setup_logging()
    ap = argparse.ArgumentParser(description="Lead-time vs pre-onset-FAR trade-off curves")
    ap.add_argument("--dataset", default="IMS")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    agg = run_tradeoff(dataset=args.dataset, seed=args.seed, save=True)
    if agg.empty:
        print("No trade-off results produced.")
        return
    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n=== FAR–VLT trade-off (mean across runs) ===")
    print(agg[["method", "percentile", "lead_time_hours_mean",
               "far_preonset_pct_mean", "valid_frac"]].to_string(index=False))


if __name__ == "__main__":
    main()
