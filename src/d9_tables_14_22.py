# src/d9_tables_14_22.py
"""
Decision D-9 -- rebuild Table 14 (tab:farbudget) and Table 22 (tab:phrank) with all
ELEVEN detectors: the seven already published, the three deep reconstruction models
added by D2, and one-class SVM added by D3.

CONVENTION, verified against the published tables before use. The candidate operating
points are the three swept percentiles {95, 99, 99.5} -- not all seven -- and the
budget test is on the MEAN pre-onset FAR across runs:

    PH(detector)    = max mean lead over the three percentiles          (ungated)
    L(detector,tau) = max mean lead among percentiles whose MEAN
                      pre-onset FAR <= tau, else 0.0                    (gated)

Verified: published Table 22 gives 3-sigma PH = 77.0, which is the maximum over
{95, 99, 99.5}; the 90th percentile would give 163.8. Published Table 14 gives Deep
SVDD L(0.05) = 14.8, again the 95th and not the 90th (which would be 34.7).

THE MEAN IS THE POINT. A detector can hold a valid alarm on one run and still score
L = 0, because the budget is applied to the mean FAR across runs. That is exactly the
LSTM-AE case this script was written to check.

Reads only existing result files; writes one NEW file:
    results/tables/d9_tables_14_22_eleven.csv

Entry point:
    python -m src.d9_tables_14_22
"""

import os
import sys
import logging

import pandas as pd

logger = logging.getLogger(__name__)

PERCENTILES = [95.0, 99.0, 99.5]
TAU_GRID_PCT = [5.0, 10.0, 20.0]
TAU_PCT = 10.0

SOURCES = [
    ("tradeoff_IMS.csv", "published seven"),
    ("tradeoff_IMS_deepmodels.csv", "D2 deep models"),
    ("d3_ocsvm_tradeoff.csv", "D3 one-class SVM"),
]

# Display names matching the manuscript's table rows.
PRETTY = {
    "three_sigma": "3sigma", "ewma": "EWMA", "cusum": "CUSUM",
    "hotelling_t2": "Hotelling T2", "isolation_forest": "Iso. Forest",
    "deep_svdd": "Deep SVDD", "rms_trend": "RMS-trend",
    "lstm_ae": "LSTM-AE", "tcn": "TCN-AE", "transformer_ad": "Transformer-AD",
    "one_class_svm": "One-Class SVM",
}


def load_all():
    """Concatenate the three trade-off sources, restricted to the three percentiles."""
    from src.config import PATHS
    frames = []
    for fname, tag in SOURCES:
        p = os.path.join(PATHS["results_tables"], fname)
        if not os.path.exists(p):
            logger.warning("missing %s (%s) -- skipped", p, tag)
            continue
        d = pd.read_csv(p)
        d = d[d["percentile"].isin(PERCENTILES)]
        keep = ["short_name", "method", "percentile",
                "lead_time_hours_mean", "far_preonset_pct_mean"]
        if "valid_frac" in d.columns:
            keep.append("valid_frac")
        frames.append(d[keep])
        logger.info("loaded %-32s %s (%d rows)", fname, tag, len(d))
    return pd.concat(frames, ignore_index=True)


def build(agg, save=True):
    """Compute PH, L(tau) and both rankings for every detector."""
    from src.config import PATHS

    rows = []
    for short, sub in agg.groupby("short_name"):
        row = {"short_name": short,
               "display": PRETTY.get(short, short),
               "method": sub["method"].iloc[0],
               "PH_h": float(sub["lead_time_hours_mean"].max())}
        for tau in TAU_GRID_PCT:
            within = sub[sub["far_preonset_pct_mean"] <= tau]
            row["L_tau%02d_h" % int(tau)] = (float(within["lead_time_hours_mean"].max())
                                             if not within.empty else 0.0)
        # Per-run nuance: does ANY run sit inside the budget at ANY percentile?
        if "valid_frac" in sub.columns:
            row["max_valid_frac"] = float(sub["valid_frac"].max())
        row["min_mean_far"] = float(sub["far_preonset_pct_mean"].min())
        row["valid_at_tau10"] = row["L_tau10_h"] > 0.0
        rows.append(row)

    out = pd.DataFrame(rows)
    # Rankings: PH descending; L(tau=0.10) descending, ties (all the zeros) share a rank.
    out["PH_rank"] = out["PH_h"].rank(ascending=False, method="min").astype(int)
    out["L_rank"] = out["L_tau10_h"].rank(ascending=False, method="min").astype(int)
    out = out.sort_values("PH_rank").reset_index(drop=True)

    if save:
        p = os.path.join(PATHS["results_tables"], "d9_tables_14_22_eleven.csv")
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
    pd.set_option("display.width", 220, "display.max_columns", 30)

    agg = load_all()
    t = build(agg)

    print("\n=== TABLE 14 (tab:farbudget) rebuilt, eleven detectors ===")
    print("    best valid lead (h) per FAR budget tau; 0.0 = no operating point in budget")
    print("    %-16s %8s %8s %8s   %s" % ("Detector", "t=0.05", "t=0.10", "t=0.20", "min mean FAR"))
    for _, r in t.sort_values("PH_rank").iterrows():
        print("    %-16s %8.1f %8.1f %8.1f   %.2f%%"
              % (r["display"], r["L_tau05_h"], r["L_tau10_h"], r["L_tau20_h"], r["min_mean_far"]))

    print("\n=== TABLE 22 (tab:phrank) rebuilt, eleven detectors ===")
    print("    %-16s %8s %4s %8s %5s  %s" % ("Method", "PH", "Rk", "L", "L Rk", "Valid?"))
    for _, r in t.iterrows():
        print("    %-16s %8.1f %4d %8.1f %5d  %s"
              % (r["display"], r["PH_h"], r["PH_rank"], r["L_tau10_h"],
                 r["L_rank"], "yes" if r["valid_at_tau10"] else "no"))

    print("\n=== the LSTM-AE question ===")
    l = t[t["short_name"] == "lstm_ae"]
    if not l.empty:
        r = l.iloc[0]
        print("    LSTM-AE min mean pre-onset FAR over {95,99,99.5} = %.2f%%" % r["min_mean_far"])
        print("    L(0.05)=%.1f  L(0.10)=%.1f  L(0.20)=%.1f" % (r["L_tau05_h"], r["L_tau10_h"], r["L_tau20_h"]))
        if "max_valid_frac" in r and pd.notna(r["max_valid_frac"]):
            print("    best per-run valid fraction = %.2f (one run inside budget)" % r["max_valid_frac"])
        anyvalid = (r["valid_at_tau10"] or r["L_tau05_h"] > 0 or r["L_tau20_h"] > 0)
        print("    -> attains a valid operating point in Table 14: %s" % ("YES" if anyvalid else "NO"))

    print("\n=== does Section 6.9's '3sigma is the best valid chart at tau=0.10' still hold? ===")
    valid10 = t[t["valid_at_tau10"]].sort_values("L_tau10_h", ascending=False)
    if valid10.empty:
        print("    No detector has a valid operating point at tau=0.10.")
    else:
        print("    Detectors with a valid operating point at tau=0.10, best lead first:")
        for _, r in valid10.iterrows():
            print("      %-16s L=%.1f h" % (r["display"], r["L_tau10_h"]))
        best = valid10.iloc[0]
        print("    Best valid at tau=0.10: %s (%.1f h)" % (best["display"], best["L_tau10_h"]))
        print("    -> Section 6.9's sentence %s"
              % ("HOLDS" if best["short_name"] == "three_sigma" else "DOES NOT HOLD"))


if __name__ == "__main__":
    main()
