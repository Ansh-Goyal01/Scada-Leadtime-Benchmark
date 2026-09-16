"""
Correction to Phase 0.5(B): recompute the IMS legacy-vs-invariant comparison under
the PAPER'S convention, not the one used in session 2.

Session 2's `src/ims_schema_check.py` collapsed the five within-run sampling factors
by the MEDIAN and reported a pooled 15-pair Wilcoxon test. Both are wrong:

  * Section 4.8 (`scada_ijphm.tex:252`) and Table 10's caption (`:491`) both specify
    collapsing factors to "one MEAN difference per run";
  * Section 4.8 explicitly disavows the pooled 15-pair test -- it "inflates the
    effective sample size fivefold and yields overconfident p-values".

This script implements the published protocol exactly:
  1. pair on (run, seed, method, factor); diff = aggregate - decimate;
  2. collapse factors within a run by the MEAN -> one observation per run;
  3. exact two-sided sign test on run-level diffs, zero-difference runs dropped;
  4. Holm-Bonferroni across the N=40 detector x dataset family (Section 4.9).

It first VERIFIES that the legacy IMS column reproduces published Table 10 and that
the 40 raw p-values reproduce published Table 11. Read-only: writes no result file.
"""

import sys
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import binomtest

try:                                          # N-13: cp1252 console cannot print sigma
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

TABLES = "results/tables"
INFERENTIAL = ["IMS", "XJTU-SY", "FEMTO", "Ferrara"]   # ONGC excluded, n=1 (Section 4.9)

# Published Table 10 (tab:imssweep, scada_ijphm.tex:497-506), for verification only.
TABLE10 = {
    "three_sigma":      ([27.1, 18.4, 15.6], 18.4, 0.25),
    "isolation_forest": ([19.9, 12.2, 1.8], 12.2, 0.25),
    "ewma":             ([22.6, 5.0, 5.8], 5.8, 0.25),
    "cusum":            ([22.6, 5.0, 5.4], 5.4, 0.25),
    "hotelling_t2":     ([3.3, 12.3, 4.6], 4.6, 0.25),
    "deep_svdd":        ([15.2, 0.0, 1.8], 1.8, 0.50),
    "rms_trend":        ([-19.4, 0.0, 2.8], 0.0, 1.00),
    "lstm_ae":          ([-1.4, -0.4, -1.7], -1.4, 0.25),
    "tcn":              ([-1.4, -0.4, -0.2], -0.4, 0.25),
    "transformer_ad":   ([-1.4, -0.4, -2.5], -1.4, 0.25),
}


def run_level_diffs(df: pd.DataFrame,
                    metric: str = "lead_time_hours",
                    collapse: str = "mean") -> pd.DataFrame:
    """One (aggregate - decimate) observation per run x detector, Section 4.8."""
    key = ["run", "seed", "short_name", "factor"]
    wide = df.pivot_table(index=key, columns="mode", values=metric, aggfunc="mean")
    if not {"aggregate", "decimate"}.issubset(wide.columns):
        return pd.DataFrame()
    wide = wide.dropna(subset=["aggregate", "decimate"]).reset_index()
    wide["diff"] = wide["aggregate"] - wide["decimate"]
    return (wide.groupby(["run", "short_name"])["diff"]
                .agg(collapse).reset_index()
                .rename(columns={"diff": "run_diff_h"}))


def sign_test(diffs: Iterable[float]) -> dict:
    """Exact two-sided sign test; zero-difference runs excluded (Section 4.8)."""
    d = np.asarray([x for x in diffs if not np.isnan(x)], dtype=float)
    nz = d[d != 0]
    n_pos, n_neg = int((nz > 0).sum()), int((nz < 0).sum())
    n = n_pos + n_neg
    p = binomtest(n_pos, n, 0.5, alternative="two-sided").pvalue if n else 1.0
    return {"n_runs": len(d), "n_pos": n_pos, "n_neg": n_neg,
            "n_zero": int((d == 0).sum()),
            "median_h": float(np.median(d)) if len(d) else np.nan,
            "mean_h": float(np.mean(d)) if len(d) else np.nan,
            "p_raw": float(p)}


def holm(pvals: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni step-down adjusted p-values."""
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    n = len(p)
    adj = np.empty(n)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (n - rank) * p[idx])
        adj[idx] = min(running, 1.0)
    return adj


def per_detector(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    rl = run_level_diffs(df)
    rows = []
    for det, g in rl.groupby("short_name"):
        g = g.sort_values("run")
        rows.append({"dataset": dataset, "short_name": det,
                     "run_diffs": list(np.round(g["run_diff_h"].values, 4)),
                     **sign_test(g["run_diff_h"].values)})
    return pd.DataFrame(rows)


def main() -> None:
    pub = {ds: pd.read_csv(f"{TABLES}/benchmark_{ds}_long.csv") for ds in INFERENTIAL}
    inv = pd.read_csv(f"{TABLES}/benchmark_IMS_long_invariant.csv")

    legacy = {ds: per_detector(d, ds) for ds, d in pub.items()}
    ims_inv = per_detector(inv, "IMS")

    # ---- VERIFICATION 1: does the legacy IMS column reproduce published Table 10? ----
    print("=" * 92)
    print("VERIFICATION 1 -- legacy IMS under the mean convention vs published Table 10")
    print("=" * 92)
    L = legacy["IMS"].set_index("short_name")
    ok = True
    print(f"{'detector':<18}{'recomputed run diffs':<28}{'published Table 10':<26}"
          f"{'med':>7}{'pub':>7}{'p':>7}{'pub':>7}  match")
    for det, (pub_diffs, pub_med, pub_p) in TABLE10.items():
        r = L.loc[det]
        got = [round(float(x), 1) for x in r["run_diffs"]]
        med, p = round(float(r["median_h"]), 1), round(float(r["p_raw"]), 2)
        hit = (got == pub_diffs) and (med == round(pub_med, 1)) and (p == round(pub_p, 2))
        ok = ok and hit
        print(f"{det:<18}{str(got):<28}{str(pub_diffs):<26}"
              f"{med:7.1f}{pub_med:7.1f}{p:7.2f}{pub_p:7.2f}  {'OK' if hit else 'MISMATCH'}")
    print(f"\nTable 10 reproduction: {'PASS' if ok else 'FAIL'}")
    if not ok:
        print("\nSTOPPING -- the published legacy column does not reproduce under the "
              "paper's own stated convention. That is a separate defect; report it.")
        return

    # ---- VERIFICATION 2: the N=40 Holm family (published Table 11) ----------------
    fam = pd.concat([legacy[ds] for ds in INFERENTIAL], ignore_index=True)
    fam["holm_p"] = holm(fam["p_raw"].values)
    print("\n" + "=" * 92)
    print("VERIFICATION 2 -- N=40 Holm family, legacy (published Table 11)")
    print("=" * 92)
    print(f"  family size N = {len(fam)}")
    imin = fam["p_raw"].idxmin()
    print(f"  smallest raw p = {fam.loc[imin, 'p_raw']:.3f}  "
          f"({fam.loc[imin, 'dataset']} / {fam.loc[imin, 'short_name']})")
    print(f"  its Holm-adjusted p = {fam.loc[imin, 'holm_p']:.3f}")
    print(f"  rejected at alpha=0.05: {int((fam['holm_p'] < 0.05).sum())} of {len(fam)}")
    print("  published: smallest raw p = 0.031 (Isolation Forest on FEMTO), "
          "Holm 1.00, 0 of 40 rejected")

    # ---- THE CORRECTED 0.5(B) COMPARISON -----------------------------------------
    print("\n" + "=" * 92)
    print("CORRECTED 0.5(B): IMS legacy vs invariant -- MEAN collapse, run-level sign test")
    print("=" * 92)
    I = ims_inv.set_index("short_name")
    print(f"{'detector':<18}{'legacy run diffs':<26}{'med':>7}{'p':>6}   "
          f"{'invariant run diffs':<28}{'med':>7}{'p':>6}{'delta_med':>11}")
    cmp_rows = []
    for det in TABLE10:
        l, i = L.loc[det], I.loc[det]
        lm, im = float(l["median_h"]), float(i["median_h"])
        print(f"{det:<18}{str([round(float(x), 1) for x in l['run_diffs']]):<26}"
              f"{lm:7.1f}{float(l['p_raw']):6.2f}   "
              f"{str([round(float(x), 1) for x in i['run_diffs']]):<28}"
              f"{im:7.1f}{float(i['p_raw']):6.2f}{im - lm:11.1f}")
        cmp_rows.append({"short_name": det,
                         "legacy_signs": f"{l['n_pos']}+/{l['n_neg']}-/{l['n_zero']}0",
                         "invariant_signs": f"{i['n_pos']}+/{i['n_neg']}-/{i['n_zero']}0"})

    print("\nsign tallies over the 3 runs (n+/n-/n_zero)")
    for r in cmp_rows:
        print(f"  {r['short_name']:<18}legacy {r['legacy_signs']:<14}"
              f"invariant {r['invariant_signs']}")

    # ---- Holm with the invariant IMS rows substituted in --------------------------
    fam_inv = pd.concat([ims_inv] + [legacy[ds] for ds in INFERENTIAL if ds != "IMS"],
                        ignore_index=True)
    fam_inv["holm_p"] = holm(fam_inv["p_raw"].values)
    print("\n" + "=" * 92)
    print("N=40 Holm family with the INVARIANT IMS rows substituted in")
    print("=" * 92)
    jmin = fam_inv["p_raw"].idxmin()
    print(f"  smallest raw p = {fam_inv.loc[jmin, 'p_raw']:.3f}  "
          f"({fam_inv.loc[jmin, 'dataset']} / {fam_inv.loc[jmin, 'short_name']})")
    print(f"  rejected at alpha=0.05: "
          f"{int((fam_inv['holm_p'] < 0.05).sum())} of {len(fam_inv)}")
    ims_l = fam[fam.dataset == "IMS"][["short_name", "p_raw", "holm_p"]]
    ims_i = fam_inv[fam_inv.dataset == "IMS"][["short_name", "p_raw", "holm_p"]]
    m = ims_l.merge(ims_i, on="short_name", suffixes=("_legacy", "_invariant"))
    print("\n  IMS rows of the family:")
    print(m.to_string(index=False, float_format=lambda v: f"{v:7.3f}"))


if __name__ == "__main__":
    main()
