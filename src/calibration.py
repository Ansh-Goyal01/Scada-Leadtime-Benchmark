# src/calibration.py
"""
Conformal calibration validation (Phase D9, reviewer W8 / action #6, #10).

The ConformalDetector claims a distribution-free guarantee: on exchangeable normal
data, the empirical false-alarm rate is ≤ α. This module *validates* that claim on
held-out normal data, using the data-anchored degradation **onset** as the boundary of
"definitely normal" rather than the old arbitrary first-5%-of-test marker.

For each target α we calibrate on X_cal and measure the actual fraction of pre-onset
test windows whose conformal p-value < α. A well-calibrated detector lies on or below
the diagonal. We emit a long-format table (one row per dataset/run/α) and a figure.

Entry point:
    python -m src.calibration --dataset IMS
"""

import os
import logging
import argparse
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_ALPHAS = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20]


def calibration_for_run(run_name: str,
                        dataset: str = "IMS",
                        alphas: list = None,
                        seed: int = 42) -> pd.DataFrame:
    """
    Calibrate a conformal Isolation Forest on a run and measure empirical FAR over the
    pre-onset (definitely-normal) region of the test split, across target α levels.

    Returns long-format rows: dataset, run, alpha, empirical_far, n_preonset, n_cal.
    """
    from src import load_pipeline
    from src.models import IsolationForestDetector
    from src.uncertainty import ConformalDetector
    from src.onset import onset_for_run
    from src.config import SPLIT

    alphas = alphas or DEFAULT_ALPHAS
    pipe = load_pipeline(run_name, dataset=dataset)

    # onset anchored on full-resolution health indicator (leakage-free: train-only baseline)
    df = pipe["df_full"]
    n = len(df)
    train_end = df.index[min(int(n * pipe["train_fraction"]), n - 1)]
    t_fail = pd.Timestamp(pipe["failure_time"])
    onset = onset_for_run(df, train_end=train_end, t_fail=t_fail)

    ts_test = pipe["ts_test"]
    if onset is not None:
        pre_mask = np.asarray(ts_test < onset)
    else:
        # fall back to the positional normal marker if no onset detected
        k = int(len(ts_test) * SPLIT["normal_period_fraction"])
        pre_mask = np.zeros(len(ts_test), dtype=bool)
        pre_mask[:max(k, 1)] = True

    n_pre = int(pre_mask.sum())
    if n_pre == 0:
        logger.warning("[%s] no pre-onset window to score — skipping", run_name)
        return pd.DataFrame()

    X_pre = pipe["X_test"][pre_mask]
    X_cal = pipe.get("X_cal")
    cal = X_cal if X_cal is not None else pipe["X_train"]

    # one fit; p-values computed once, thresholded at each α (monotone, so cheap)
    base = IsolationForestDetector(random_state=seed)
    cdet = ConformalDetector(base, alpha=alphas[0]).calibrate(pipe["X_train"], cal)
    pvals = cdet.predict_pvalue(X_pre)

    rows = []
    for a in alphas:
        far = float(np.mean(pvals < a))
        rows.append({
            "dataset": dataset, "run": run_name, "alpha": a,
            "empirical_far": far, "n_preonset": n_pre, "n_cal": len(cal),
            "calibrated": bool(far <= a + 1e-9),
        })
    return pd.DataFrame(rows)


def run_calibration(dataset: str = "IMS",
                    runs: list = None,
                    alphas: list = None,
                    seed: int = 42,
                    save: bool = True) -> pd.DataFrame:
    """Aggregate calibration validation across a dataset's runs. Saves table + figure."""
    from src.config import PATHS, EXPERIMENT

    if runs is None:
        runs = ["LPC"] if dataset == "ONGC" else EXPERIMENT["runs_to_evaluate"]
    alphas = alphas or DEFAULT_ALPHAS

    frames = []
    for r in runs:
        try:
            frames.append(calibration_for_run(r, dataset=dataset, alphas=alphas, seed=seed))
        except Exception as e:
            logger.error("[%s] calibration failed: %s", r, e)
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames, ignore_index=True)

    # pooled: mean empirical FAR across runs per α
    pooled = (long.groupby("alpha")["empirical_far"]
              .agg(["mean", "std", "count"]).reset_index()
              .rename(columns={"mean": "empirical_far_mean",
                               "std": "empirical_far_std", "count": "n_runs"}))
    pooled["calibrated"] = pooled["empirical_far_mean"] <= pooled["alpha"] + 1e-9

    if save and not long.empty:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        long.to_csv(os.path.join(PATHS["results_tables"],
                                 f"calibration_{dataset}.csv"), index=False)
        pooled.to_csv(os.path.join(PATHS["results_tables"],
                                   f"calibration_{dataset}_pooled.csv"), index=False)
        _plot_calibration(long, pooled, dataset)
    return pooled


def _plot_calibration(long: pd.DataFrame, pooled: pd.DataFrame, dataset: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from src.config import PATHS

    alphas = pooled["alpha"].values
    fig, ax = plt.subplots(figsize=(6, 5))
    amax = float(max(alphas))
    ax.plot([0, amax], [0, amax], "k--", linewidth=1.2, label="Perfect calibration")

    # per-run thin lines
    for run, sub in long.groupby("run"):
        sub = sub.sort_values("alpha")
        ax.plot(sub["alpha"], sub["empirical_far"], "-", alpha=0.35,
                linewidth=1.0, color="#90A4AE")

    # pooled mean ± std
    m = pooled.sort_values("alpha")
    ax.plot(m["alpha"], m["empirical_far_mean"], "o-", color="#1976D2",
            linewidth=2, markersize=7, label="Conformal IF (mean across runs)")
    if m["empirical_far_std"].notna().any():
        lo = (m["empirical_far_mean"] - m["empirical_far_std"]).clip(lower=0)
        hi = m["empirical_far_mean"] + m["empirical_far_std"]
        ax.fill_between(m["alpha"], lo, hi, alpha=0.15, color="#1976D2")

    ax.set_xlabel("Target FAR (α)", fontsize=11)
    ax.set_ylabel("Empirical FAR on pre-onset normal data", fontsize=11)
    ax.set_title(f"Conformal Calibration — {dataset}\n(region below diagonal = valid guarantee)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    os.makedirs(PATHS["results_figures"], exist_ok=True)
    out = os.path.join(PATHS["results_figures"], f"calibration_curve_{dataset}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    logger.info("Saved calibration curve → %s", out)
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
    ap = argparse.ArgumentParser(description="Conformal calibration validation")
    ap.add_argument("--dataset", default="IMS")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    pooled = run_calibration(dataset=args.dataset, seed=args.seed, save=True)
    if pooled.empty:
        print("No calibration results produced.")
        return
    pd.set_option("display.width", 200)
    print("\n=== Conformal calibration (pooled across runs) ===")
    print(pooled.to_string(index=False))


if __name__ == "__main__":
    main()
