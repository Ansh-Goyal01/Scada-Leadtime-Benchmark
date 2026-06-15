# src/benchmark.py
"""
Statistical benchmark harness — adds the rigour the headline experiment was missing:
a data-anchored degradation onset, onset-relative lead-time metrics, multiple seeds,
bootstrap confidence intervals across runs, and a paired significance test for the
aggregate-vs-decimate SCADA-sampling claim.

Design
------
For each run we compute ONE degradation onset at full resolution (factor=1) and reuse it
across every sampling factor (mirroring how sampling.py anchors the lead-time denominator
to factor=1). We then sweep (mode × factor × seed × method) exactly like
sampling.run_sampling_sweep — reusing derive_counts() so the feature window and alarm
persistence stay constant in wall-clock time — but evaluate with the onset-relative,
FAR-budget-gated metrics from lead_time.evaluate_all_methods.

Output is a single LONG-format DataFrame (one row per atomic evaluation), which the
aggregation / statistics functions consume:

    dataset, run, seed, method, short_name, mode, factor, effective_interval_min,
    t_onset, t_fail, max_lead_hours,
    lead_time_hours, detection_delay_hours, far_preonset_pct, lead_norm,
    vlt_legacy_hours, far_legacy_pct, valid_alarm,
    n_test_windows, window_rows, persistence_windows, window_floored

Entry point:
    python -m src.benchmark --dataset IMS
    python -m src.benchmark --dataset IMS --seeds 42,1,7 --quick
"""

import os
import copy
import logging
import argparse
import numpy as np
import pandas as pd

from src import load_pipeline
from src.config import (
    PATHS, FEATURES, SPLIT, THRESHOLD, MODELS, EXPERIMENT, SAMPLING, ONSET,
)
from src.models import get_all_models
from src.lead_time import evaluate_all_methods
from src.onset import onset_for_run
from src.sampling import derive_counts, load_pipeline_controlled

logger = logging.getLogger(__name__)

# Detectors whose output does not depend on the RNG seed — run once, broadcast.
_DETERMINISTIC = {"three_sigma", "ewma", "hotelling_t2", "one_class_svm"}

DEFAULT_FAR_BUDGET = 0.10


# ─────────────────────────── detector construction ────────────────────────────

def make_detectors(methods: list, seed: int):
    """Instantiate detectors with the RNG seed injected into stochastic models."""
    params = copy.deepcopy(MODELS)
    if "isolation_forest" in params:
        params["isolation_forest"]["random_state"] = seed
    if "lstm_ae" in params:
        params["lstm_ae"]["random_state"] = seed
    return get_all_models({"methods_to_run": methods, "model_params": params})


# ───────────────────────────── per-run onset ──────────────────────────────────

def compute_run_onset(run_name: str, dataset: str = "IMS") -> dict:
    """
    Compute the degradation onset + failure time for one run at full resolution.

    Returns dict: t_onset, t_fail, base_min, available info. The onset baseline is the
    training window only (leakage-free).
    """
    base = load_pipeline(run_name, dataset=dataset)       # factor=1, no downsample
    df = base["df_full"]
    n = len(df)
    train_frac = base.get("train_fraction", SPLIT["train_fraction"])
    train_end = df.index[min(int(n * train_frac), n - 1)]
    t_fail = pd.Timestamp(base["failure_time"])
    onset = onset_for_run(df, train_end=train_end, t_fail=t_fail)
    max_lead = ((t_fail - onset).total_seconds() / 3600.0) if onset is not None else float("nan")
    return {
        "t_onset":  onset,
        "t_fail":   t_fail,
        "base_min": base["effective_interval_min"],
        "max_lead_hours": max_lead,
        "onset_method": ONSET.get("method", "terminal"),
    }


# ───────────────────────────── main sweep ─────────────────────────────────────

def run_benchmark(dataset: str = "IMS",
                  runs: list = None,
                  methods: list = None,
                  seeds: list = None,
                  modes: list = None,
                  factors: list = None,
                  far_budget: float = DEFAULT_FAR_BUDGET,
                  control: bool = False,
                  save: bool = True) -> pd.DataFrame:
    """
    Run the full (run × mode × factor × seed × method) benchmark with onset-relative,
    FAR-budget-gated metrics. Returns the long-format results DataFrame.

    ``runs`` defaults to the dataset's configured run list (currently IMS only).
    Deterministic detectors are evaluated once (seed=seeds[0]) and broadcast across the
    seed axis to avoid wasted compute; only Isolation Forest / LSTM-AE vary with seed.
    """
    if runs is None:
        runs = ["LPC"] if dataset == "ONGC" else EXPERIMENT["runs_to_evaluate"]
    if control and dataset != "IMS":
        logger.warning("controlled sweep currently supports IMS only; using standard path for %s", dataset)
        control = False
    methods = methods or EXPERIMENT["methods_to_run"]
    seeds   = seeds   or [EXPERIMENT["random_seed"]]
    modes   = modes   or SAMPLING["modes"]
    factors = factors or SAMPLING["factors"]
    overlap = FEATURES["overlap"]
    min_window_rows = SAMPLING["min_window_rows"]

    rows = []
    for run_name in runs:
        info = compute_run_onset(run_name, dataset=dataset)
        onset, t_fail, base_min = info["t_onset"], info["t_fail"], info["base_min"]
        if onset is None:
            logger.warning("[%s] no onset detected — onset-relative metrics will be NaN.", run_name)
        logger.info("[%s] onset=%s  t_fail=%s  max_lead=%.1fh",
                    run_name, onset, t_fail, info["max_lead_hours"])

        # Window + persistence held constant in wall-clock (same convention as sampling.py)
        window_minutes = SAMPLING["window_minutes"] or FEATURES["window_size"] * base_min
        if SAMPLING["persistence_minutes"] is not None:
            persistence_minutes = SAMPLING["persistence_minutes"]
        else:
            base_stride_min = FEATURES["window_size"] * (1.0 - overlap) * base_min
            persistence_minutes = THRESHOLD["alarm_persistence"] * base_stride_min

        for mode in modes:
            for factor in factors:
                c = derive_counts(base_min, factor, window_minutes,
                                  persistence_minutes, overlap, min_window_rows)
                if c["window_floored"] and not control:
                    logger.warning("[%s] mode=%s factor=%d: window floored to %d rows",
                                   run_name, mode, factor, c["window_rows"])

                dmode = "none" if factor == 1 else mode
                for si, seed in enumerate(seeds):
                    methods_this_seed = methods if si == 0 else \
                        [m for m in methods if m not in _DETERMINISTIC]
                    if not methods_this_seed:
                        continue
                    try:
                        if control:
                            # CONTROLLED path: feature-level resampling — window content and
                            # alarm persistence held constant; only the logging interval changes.
                            pipe = load_pipeline_controlled(run_name, factor=factor, mode=dmode)
                            persistence_windows = THRESHOLD["alarm_persistence"]
                            window_rows = pipe["window_size_used"]
                            window_floored = False
                        else:
                            pipe = load_pipeline(
                                run_name,
                                dataset=dataset,
                                window_size=c["window_rows"],
                                downsample_factor=factor,
                                downsample_mode=dmode,
                            )
                            persistence_windows = c["persistence_windows"]
                            window_rows = c["window_rows"]
                            window_floored = c["window_floored"]
                    except Exception as e:
                        logger.error("[%s] load failed mode=%s factor=%d: %s",
                                     run_name, mode, factor, e)
                        continue

                    dets = make_detectors(methods_this_seed, seed)
                    _, results = evaluate_all_methods(
                        detectors=dets,
                        X_train=pipe["X_train"], X_test=pipe["X_test"],
                        timestamps_test=pipe["ts_test"], failure_time=pipe["failure_time"],
                        normal_period_fraction=SPLIT["normal_period_fraction"],
                        threshold_strategy=THRESHOLD["strategy"],
                        threshold_percentile=THRESHOLD["percentile"],
                        alarm_persistence=persistence_windows,
                        t_onset=onset, far_budget=far_budget,
                        X_cal=pipe.get("X_cal"),
                    )
                    for r in results:
                        rows.append({
                            "dataset": dataset, "run": run_name, "seed": seed,
                            "method": r["method"], "short_name": r["short_name"],
                            "mode": mode, "factor": factor,
                            "effective_interval_min": round(pipe["effective_interval_min"], 2),
                            "t_onset": onset, "t_fail": t_fail,
                            "max_lead_hours": round(info["max_lead_hours"], 2)
                                              if np.isfinite(info["max_lead_hours"]) else np.nan,
                            "lead_time_hours": r["lead_time_hours"],
                            "detection_delay_hours": r["detection_delay_hours"],
                            "far_preonset_pct": r["far_preonset_pct"],
                            "lead_norm": r["lead_norm"],
                            "vlt_legacy_hours": r["VLT_hours"],
                            "far_legacy_pct": r["FAR_pct"],
                            "valid_alarm": r["valid_alarm"],
                            "n_test_windows": len(pipe["ts_test"]),
                            "window_rows": window_rows,
                            "persistence_windows": persistence_windows,
                            "window_floored": window_floored,
                            "control": control,
                            "onset_method": info["onset_method"],
                        })
                logger.info("[%s] mode=%s factor=%d (~%.0f min) done",
                            run_name, mode, factor, c["effective_min"])

    df = pd.DataFrame(rows)
    if save and not df.empty:
        os.makedirs(PATHS["results_tables"], exist_ok=True)
        out = os.path.join(PATHS["results_tables"], f"benchmark_{dataset}_long.csv")
        df.to_csv(out, index=False)
        logger.info("Saved long-format results → %s (%d rows)", out, len(df))
    return df


# ──────────────────────────── statistics ──────────────────────────────────────

def aggregate_long(df: pd.DataFrame,
                   metrics: list = None,
                   group: list = None) -> pd.DataFrame:
    """
    Mean / median / std across runs (seeds averaged first) per (dataset, method, mode,
    factor). Returns a wide aggregate table.
    """
    metrics = metrics or ["lead_time_hours", "detection_delay_hours",
                          "far_preonset_pct", "lead_norm", "valid_alarm"]
    group = group or ["dataset", "method", "mode", "factor", "effective_interval_min"]
    # collapse seeds first (mean within run) so runs are the aggregation unit
    by_run = (df.groupby(group + ["run"])[metrics].mean().reset_index())
    agg = by_run.groupby(group)[metrics].agg(["mean", "median", "std", "count"])
    agg.columns = [f"{m}_{s}" for m, s in agg.columns]
    return agg.reset_index()


def bootstrap_ci_across_runs(df: pd.DataFrame,
                             metric: str = "lead_time_hours",
                             group: list = None,
                             n_boot: int = 2000,
                             alpha: float = 0.05,
                             seed: int = 42) -> pd.DataFrame:
    """
    Bootstrap CI for ``metric`` by resampling RUNS (the unit of generalization) with
    replacement, per group. Seeds are averaged within each run first.

    Returns one row per group with mean, lo, hi (the (alpha/2, 1-alpha/2) percentiles),
    and n_runs.
    """
    group = group or ["dataset", "method", "mode", "factor", "effective_interval_min"]
    rng = np.random.RandomState(seed)
    by_run = (df.groupby(group + ["run"])[metric].mean().reset_index())

    out = []
    for keys, sub in by_run.groupby(group):
        vals = sub[metric].dropna().values
        n = len(vals)
        if n == 0:
            continue
        if n == 1:
            mean, lo, hi = float(vals[0]), float(vals[0]), float(vals[0])
        else:
            boots = np.array([rng.choice(vals, n, replace=True).mean() for _ in range(n_boot)])
            mean = float(vals.mean())
            lo = float(np.percentile(boots, 100 * alpha / 2))
            hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
        row = dict(zip(group, keys if isinstance(keys, tuple) else (keys,)))
        row.update({f"{metric}_mean": mean, f"{metric}_lo": lo, f"{metric}_hi": hi, "n_runs": n})
        out.append(row)
    return pd.DataFrame(out)


def paired_test_aggregate_vs_decimate(df: pd.DataFrame,
                                      metric: str = "lead_time_hours",
                                      test: str = "wilcoxon") -> pd.DataFrame:
    """
    Paired test of aggregate vs decimate for ``metric``. Pairs are formed on
    (dataset, run, seed, method, factor) — the same condition under the two mechanisms —
    and pooled per (dataset, method). Reports statistic, p-value, n_pairs, median paired
    difference (aggregate − decimate), and a rank-biserial effect size.

    A negative median difference ⇒ aggregation reduces the metric (e.g. shorter lead time).
    """
    from scipy import stats

    key = ["dataset", "run", "seed", "method", "factor"]
    wide = df.pivot_table(index=key, columns="mode", values=metric, aggfunc="mean")
    if not {"aggregate", "decimate"}.issubset(wide.columns):
        logger.warning("paired test: need both aggregate & decimate; got %s", list(wide.columns))
        return pd.DataFrame()
    wide = wide.dropna(subset=["aggregate", "decimate"]).reset_index()
    wide["diff"] = wide["aggregate"] - wide["decimate"]

    out = []
    for (ds, method), sub in wide.groupby(["dataset", "method"]):
        d = sub["diff"].values
        n = len(d)
        nonzero = d[d != 0]
        if len(nonzero) < 1:
            stat, p = float("nan"), 1.0
        elif test == "wilcoxon":
            try:
                stat, p = stats.wilcoxon(sub["aggregate"], sub["decimate"],
                                         zero_method="wilcox", alternative="two-sided")
            except Exception:
                stat, p = float("nan"), float("nan")
        else:  # paired t-test
            stat, p = stats.ttest_rel(sub["aggregate"], sub["decimate"])
        # rank-biserial effect size from sign of differences
        n_pos = int((d > 0).sum()); n_neg = int((d < 0).sum())
        rbc = (n_pos - n_neg) / n if n else float("nan")
        out.append({
            "dataset": ds, "method": method, "metric": metric, "test": test,
            "n_pairs": n, "statistic": float(stat) if stat == stat else np.nan,
            "p_value": float(p) if p == p else np.nan,
            "median_diff_agg_minus_dec": float(np.median(d)),
            "mean_diff_agg_minus_dec": float(np.mean(d)),
            "rank_biserial": rbc,
        })
    return pd.DataFrame(out)


# ─────────────────────────────── CLI ──────────────────────────────────────────

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
    ap = argparse.ArgumentParser(description="SCADA lead-time statistical benchmark")
    ap.add_argument("--dataset", default="IMS")
    ap.add_argument("--seeds", default=None, help="comma-separated, e.g. 42,1,7")
    ap.add_argument("--far-budget", type=float, default=DEFAULT_FAR_BUDGET)
    ap.add_argument("--control", action="store_true",
                    help="controlled feature-level sampling sweep (W7 fix)")
    ap.add_argument("--quick", action="store_true", help="2nd_test only, factors 1,2,10")
    args = ap.parse_args()

    seeds = [int(s) for s in args.seeds.split(",")] if args.seeds else None
    runs = ["2nd_test"] if args.quick else None
    factors = [1, 2, 10] if args.quick else None

    df = run_benchmark(dataset=args.dataset, runs=runs, seeds=seeds,
                       factors=factors, far_budget=args.far_budget,
                       control=args.control, save=True)
    if df.empty:
        print("No results produced.")
        return

    agg = aggregate_long(df)
    ci = bootstrap_ci_across_runs(df, metric="lead_time_hours")
    paired = paired_test_aggregate_vs_decimate(df, metric="lead_time_hours")

    os.makedirs(PATHS["results_tables"], exist_ok=True)
    agg.to_csv(os.path.join(PATHS["results_tables"], f"benchmark_{args.dataset}_aggregate.csv"), index=False)
    ci.to_csv(os.path.join(PATHS["results_tables"], f"benchmark_{args.dataset}_leadtime_ci.csv"), index=False)
    paired.to_csv(os.path.join(PATHS["results_tables"], f"benchmark_{args.dataset}_paired_test.csv"), index=False)

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n=== Lead-time bootstrap CI (resampling runs) — factor=1 baseline ===")
    base = ci[ci["factor"] == 1] if "factor" in ci.columns else ci
    print(base[["method", "mode", "lead_time_hours_mean",
                "lead_time_hours_lo", "lead_time_hours_hi", "n_runs"]].to_string(index=False))
    print("\n=== Paired test: aggregate vs decimate (lead_time_hours) ===")
    print(paired.to_string(index=False))


if __name__ == "__main__":
    main()
