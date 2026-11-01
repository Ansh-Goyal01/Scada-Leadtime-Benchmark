# src/r2_review2_tables.py
"""Round-2 review analyses, computed only from already-released result files.

R2-B3  Equivalence-margin sensitivity. Re-reads the 95% bootstrap CIs behind Table 5
       (n20_d15_bootstrap_new_11det.csv, the 33 multi-bearing cells) and counts, at each
       margin delta, the cells that are equivalent (CI inside [-delta, +delta]) and the
       cells showing either mechanism superior beyond delta (CI wholly outside).
R2-B2  Per-run validity on IMS. Counts, per detector, threshold percentile and budget tau,
       the runs on which Eq. 5 holds (lead > 0 and pre-onset FAR <= tau), from the
       per-run threshold-sweep files behind Tables 2 and 9.

    python -m src.r2_review2_tables

Writes results/tables/r2_margin_sensitivity.csv and results/tables/r2_valid_runs_IMS.csv.
"""
from pathlib import Path

import pandas as pd

TABLES = Path(__file__).resolve().parents[1] / "results" / "tables"
MULTI = ("XJTU-SY", "FEMTO", "Ferrara")
DELTAS = (1.0, 0.75, 0.56, 0.5, 0.25, 0.1, 0.05)
SWEEP = ("tradeoff_IMS_long.csv", "tradeoff_IMS_deepmodels_long.csv", "d3_ocsvm_tradeoff_long.csv")
PCTS = (95.0, 99.0, 99.5)          # the three thresholds of Tables 2 and 9
TAUS = (5.0, 10.0, 20.0)


def margin_sensitivity():
    b = pd.read_csv(TABLES / "n20_d15_bootstrap_new_11det.csv")
    m = b[b["dataset"].isin(MULTI)]
    assert len(m) == 33, len(m)
    rows = []
    for d in DELTAS:
        rows.append({
            "delta_h": d, "n_cells": len(m),
            "n_equivalent": int(((m["ci_lo_h"] > -d) & (m["ci_hi_h"] < d)).sum()),
            "n_decimate_superior_beyond": int((m["ci_hi_h"] < -d).sum()),
            "n_aggregate_superior_beyond": int((m["ci_lo_h"] > d).sum()),
        })
    out = pd.DataFrame(rows)
    out["max_abs_endpoint_h"] = m[["ci_lo_h", "ci_hi_h"]].abs().max(axis=1).max()
    out["min_upper_of_negative_cis_h"] = m.loc[m["ci_hi_h"] < 0, "ci_hi_h"].min()
    out.to_csv(TABLES / "r2_margin_sensitivity.csv", index=False)
    return out


def valid_runs_ims():
    d = pd.concat([pd.read_csv(TABLES / f) for f in SWEEP], ignore_index=True)
    d = d[(d["dataset"] == "IMS") & d["percentile"].isin(PCTS)]
    assert d.groupby("short_name")["run"].nunique().eq(3).all()
    rows = []
    for (short, pct), g in d.groupby(["short_name", "percentile"]):
        for tau in TAUS:
            ok = (g["lead_time_hours"] > 0) & g["far_preonset_pct"].notna() & (g["far_preonset_pct"] <= tau)
            rows.append({"short_name": short, "percentile": pct, "tau_pct": tau,
                         "n_runs": len(g), "n_valid_runs": int(ok.sum()),
                         "valid_runs": ";".join(sorted(g.loc[ok, "run"]))})
    out = pd.DataFrame(rows)
    best = out.groupby(["short_name", "tau_pct"])["n_valid_runs"].transform("max")
    out["best_over_thresholds"] = best
    out.to_csv(TABLES / "r2_valid_runs_IMS.csv", index=False)
    return out


if __name__ == "__main__":
    print(margin_sensitivity().to_string(index=False))
    v = valid_runs_ims()
    print(v[v["tau_pct"] == 10.0].pivot(index="short_name", columns="percentile", values="n_valid_runs"))
