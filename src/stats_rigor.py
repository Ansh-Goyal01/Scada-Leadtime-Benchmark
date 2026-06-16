# src/stats_rigor.py
"""
Run-level statistical rigor for the SCADA aggregate-vs-decimate claim.

WHY THIS MODULE EXISTS
----------------------
The original benchmark paired test (``benchmark.py::paired_test_aggregate_vs_decimate``)
pools 15 "pairs" per detector on IMS: 3 runs × 5 coarsening factors. But the five
factors *within a run* share a single physical degradation trajectory — they are
**pseudoreplicates**, not independent observations. Treating them as 15 independent
pairs inflates the effective sample size fivefold and produces an over-confident
p-value (e.g. 3σ: p=0.003). The honest unit of inference is the **run** (n=3 on IMS,
n=10 on XJTU, n=1 on ONGC → no inference).

This module collapses each run to a single mean(aggregate − decimate) difference
across factors and applies:
  * an **exact two-sided sign test** (binomial) — assumption-light, the conservative
    choice at n=3, where its p-value *floors* at 2·(1/2)^3 = 0.25 for 3/3 concordant
    diffs (so "significant" is structurally impossible and must not be claimed); and
  * **Holm–Bonferroni** step-down correction across the explicitly-defined
    detector × dataset family.

Everything here is pure (operates on the existing ``benchmark_<DS>_long.csv`` files)
and depends only on numpy / pandas / scipy — no statsmodels.
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from src.config import PATHS

logger = logging.getLogger(__name__)

# Datasets whose run count is large enough to even attempt inference.
# ONGC is n=1 (single asset) → case study only, never enters a test family.
INFERENTIAL_DATASETS = ("IMS", "XJTU-SY", "FEMTO")


# ───────────────────────────── core statistics ─────────────────────────────────

def run_level_diffs(long_df: pd.DataFrame,
                    metric: str = "lead_time_hours") -> pd.DataFrame:
    """
    Collapse pseudoreplicated factors to one difference per run.

    For each (dataset, method, run) we average ``metric`` over factors and seeds
    within each mode, then take aggregate − decimate. The result is a tidy frame
    with one row per (dataset, method, run): the honest unit of inference.

    Returns columns: dataset, method, run, agg, dec, diff.
    """
    needed = {"dataset", "method", "run", "mode", metric}
    missing = needed - set(long_df.columns)
    if missing:
        raise ValueError(f"run_level_diffs: missing columns {sorted(missing)}")

    # Average over factors AND seeds within each (dataset, method, run, mode).
    g = (long_df
         .groupby(["dataset", "method", "run", "mode"])[metric]
         .mean()
         .reset_index())
    wide = g.pivot_table(index=["dataset", "method", "run"],
                         columns="mode", values=metric).reset_index()
    if not {"aggregate", "decimate"}.issubset(wide.columns):
        logger.warning("run_level_diffs: need both aggregate & decimate modes; got %s",
                       [c for c in wide.columns if c not in ("dataset", "method", "run")])
        return pd.DataFrame(columns=["dataset", "method", "run", "agg", "dec", "diff"])

    wide = wide.dropna(subset=["aggregate", "decimate"])
    out = wide.rename(columns={"aggregate": "agg", "decimate": "dec"})[
        ["dataset", "method", "run", "agg", "dec"]].copy()
    out["diff"] = out["agg"] - out["dec"]
    return out.reset_index(drop=True)


def exact_sign_test(diffs: Sequence[float]) -> dict:
    """
    Exact two-sided sign test on a vector of run-level differences.

    Zeros (exact ties) are dropped before the binomial test, per the standard
    sign-test convention. The p-value is the exact binomial tail under H0: P(+)=0.5,
    doubled for two-sidedness and capped at 1.0.

    Returns: n, n_pos, n_neg, n_zero, n_effective, median, p_value, all_same_sign.
    """
    d = np.asarray(list(diffs), dtype=float)
    d = d[~np.isnan(d)]
    n = int(d.size)
    n_pos = int((d > 0).sum())
    n_neg = int((d < 0).sum())
    n_zero = int((d == 0).sum())
    n_eff = n_pos + n_neg
    median = float(np.median(d)) if n else float("nan")

    if n_eff == 0:
        p = 1.0
    else:
        k = min(n_pos, n_neg)
        # Two-sided exact binomial tail: 2 * P(X <= k) under p=0.5, capped at 1.
        cdf = stats.binom.cdf(k, n_eff, 0.5)
        p = float(min(1.0, 2.0 * cdf))

    return {
        "n": n,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "n_zero": n_zero,
        "n_effective": n_eff,
        "median": median,
        "p_value": p,
        "all_same_sign": bool(n_eff > 0 and (n_pos == 0 or n_neg == 0)),
    }


def holm_bonferroni(pvals: Iterable[float], alpha: float = 0.05):
    """
    Holm step-down correction.

    Returns (adjusted_pvals, reject_flags) in the ORIGINAL input order. NaN p-values
    are carried through as NaN (adjusted=NaN, reject=False) and excluded from the
    family size used for the correction.

    Holm: sort ascending; the i-th smallest (0-indexed) is compared at
    alpha/(m-i); adjusted p_(i) = max over j<=i of (m-j)*p_(j), clipped to <=1 and
    enforced monotone non-decreasing.
    """
    p = np.asarray(list(pvals), dtype=float)
    n = p.size
    adj = np.full(n, np.nan, dtype=float)
    reject = np.zeros(n, dtype=bool)

    valid_idx = np.where(~np.isnan(p))[0]
    m = valid_idx.size
    if m == 0:
        return adj, reject

    order = valid_idx[np.argsort(p[valid_idx], kind="stable")]
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * p[idx]
        running = max(running, val)          # enforce monotonicity
        adj[idx] = min(1.0, running)
    reject[order] = adj[order] < alpha
    # Once Holm fails to reject, all subsequent (larger-p) hypotheses are retained.
    failed = False
    for idx in order:
        if failed:
            reject[idx] = False
        elif not reject[idx]:
            failed = True
    return adj, reject


# ───────────────────────────── table builders ──────────────────────────────────

def ims_runlevel_table(long_df: pd.DataFrame,
                       metric: str = "lead_time_hours") -> pd.DataFrame:
    """
    Per-detector run-level table for one dataset (IMS by design, but works for any).

    One row per method: per-run diffs spelled out, median, sign counts, exact sign-test
    p-value, sign-consistency flag. Holm adjustment is added later across the family by
    :func:`family_holm`.
    """
    rl = run_level_diffs(long_df, metric=metric)
    if rl.empty:
        return rl
    rows = []
    for (ds, method), sub in rl.groupby(["dataset", "method"]):
        sub = sub.sort_values("run")
        st = exact_sign_test(sub["diff"].values)
        rows.append({
            "dataset": ds,
            "method": method,
            "n_runs": st["n"],
            "run_diffs": ", ".join(f"{v:+.1f}" for v in sub["diff"].values),
            "median_diff": st["median"],
            "n_pos": st["n_pos"],
            "n_neg": st["n_neg"],
            "all_same_sign": st["all_same_sign"],
            "sign_test_p": st["p_value"],
        })
    return pd.DataFrame(rows).sort_values(["dataset", "method"]).reset_index(drop=True)


def family_holm(tables: Sequence[pd.DataFrame],
                alpha: float = 0.05,
                p_col: str = "sign_test_p") -> pd.DataFrame:
    """
    Concatenate per-dataset run-level tables into one family and apply Holm.

    The multiple-testing family is the union of all (detector × dataset)
    aggregate-vs-decimate sign tests over the inferential datasets. ONGC (n=1) is
    never passed in. Adds columns: holm_p, holm_reject, family_size, fwer_uncorrected.
    """
    tabs = [t for t in tables if t is not None and not t.empty]
    if not tabs:
        return pd.DataFrame()
    fam = pd.concat(tabs, ignore_index=True)
    holm_p, reject = holm_bonferroni(fam[p_col].values, alpha=alpha)
    fam = fam.copy()
    fam["holm_p"] = holm_p
    fam["holm_reject"] = reject
    m = int(np.sum(~np.isnan(fam[p_col].values)))
    fam["family_size"] = m
    fam["fwer_uncorrected"] = 1.0 - (1.0 - alpha) ** m if m else np.nan
    return fam


# ───────────────────────────────── CLI ─────────────────────────────────────────

def _read_long(dataset: str) -> pd.DataFrame | None:
    path = os.path.join(PATHS["results_tables"], f"benchmark_{dataset}_long.csv")
    if not os.path.exists(path):
        logger.warning("missing long CSV for %s: %s", dataset, path)
        return None
    return pd.read_csv(path)


def main(argv: Sequence[str] | None = None) -> int:
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    ap = argparse.ArgumentParser(description="Run-level sign tests + Holm across the family.")
    ap.add_argument("--datasets", nargs="+", default=list(INFERENTIAL_DATASETS),
                    help="Inferential datasets to include in the Holm family.")
    ap.add_argument("--metric", default="lead_time_hours")
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args(argv)

    per_ds_tables = []
    for ds in args.datasets:
        long_df = _read_long(ds)
        if long_df is None:
            continue
        tab = ims_runlevel_table(long_df, metric=args.metric)
        if tab.empty:
            logger.warning("no run-level diffs for %s (need both modes)", ds)
            continue
        per_ds_tables.append(tab)
        # Emit the per-dataset run-level table (IMS is the headline one).
        out = os.path.join(PATHS["results_tables"], f"{ds.lower().replace('-', '_')}_runlevel_test.csv")
        tab.to_csv(out, index=False)
        logger.info("wrote %s", out)
        print(f"\n=== {ds} run-level sign test ({args.metric}) ===")
        print(tab.to_string(index=False))

    fam = family_holm(per_ds_tables, alpha=args.alpha, p_col="sign_test_p")
    if not fam.empty:
        out = os.path.join(PATHS["results_tables"], "paired_tests_holm.csv")
        fam.to_csv(out, index=False)
        logger.info("wrote %s", out)
        m = int(fam["family_size"].iloc[0])
        print(f"\n=== Holm–Bonferroni across family (N={m}, α={args.alpha}) ===")
        print(fam[["dataset", "method", "n_runs", "median_diff", "all_same_sign",
                   "sign_test_p", "holm_p", "holm_reject"]].to_string(index=False))
        n_rej = int(fam["holm_reject"].sum())
        print(f"\nSurviving Holm at α={args.alpha}: {n_rej} of {len(fam)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
