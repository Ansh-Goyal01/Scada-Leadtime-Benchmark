"""
Apply Eq. 5 of the manuscript to the released result files and restate every
valid-alarm count the paper prints.

Eq. 5: an alarm is valid iff ``L > 0`` and ``FAR_pre <= tau`` (tau = 10 %). When
the pre-onset region is empty -- the onset estimator places ``t_o`` at or before
the first scored window -- ``FAR_pre`` is undefined, the alarm cannot be gated,
and the evaluation is EXCLUDED from the validity denominator, never counted
valid. A run with no detectable onset has no pre-onset region at all and is
excluded for the same reason.

Why this script exists. The raw ``valid_alarm`` column in the benchmark files
follows the implementation (``src/lead_time.py``), which (a) passes an alarm
whose ``FAR_pre`` is NaN whenever its lead is positive, and (b) scores a run
with no onset by the legacy positional 5 % marker. The manuscript's counts
apply Eq. 5 instead, through this script. Nothing here rewrites a released file.

Classification of one evaluation row:

* ``no_onset``   -- ``t_onset`` undefined (XJTU-SY Bearing1_2 under rms_kurt);
* ``empty_pre``  -- ``far_preonset_pct`` undefined while the lead is defined;
* ``na``         -- the lead itself is undefined (a deep sequence model that
                    could not form a sequence; Section 4.5 counts it as no
                    valid alarm, which this script keeps);
* otherwise scoreable, and valid iff ``lead > 0 and far_preonset_pct <= 10``.

Usage::

    python -m src.eq5_validity           # writes results/tables/eq5_*.csv
"""

import os
import sys

import numpy as np
import pandas as pd

from src.stats_rigor import run_level_diffs

TAB = os.path.join("results", "tables")
TAU_PCT = 10.0
FIVE = ["three_sigma", "ewma", "hotelling_t2", "isolation_forest", "rms_trend"]
GAP_DETS = ["three_sigma", "ewma", "cusum", "hotelling_t2", "isolation_forest"]


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(TAB, name), low_memory=False)


def classify(df: pd.DataFrame, lead: str = "lead_time_hours") -> pd.DataFrame:
    """Return a copy with boolean columns na, no_onset, empty_pre, scoreable, eq5."""
    out = df.copy()
    has_lead = out[lead].notna()
    far = out["far_preonset_pct"]
    out["na"] = ~has_lead
    out["no_onset"] = out["t_onset"].isna() if "t_onset" in out else False
    out["empty_pre"] = has_lead & far.isna() & ~out["no_onset"]
    out["scoreable"] = ~(out["no_onset"] | out["empty_pre"])
    out["eq5"] = out["scoreable"] & has_lead & (out[lead] > 0) & (far <= TAU_PCT)
    return out


def published_valid(df: pd.DataFrame, col: str = "valid_alarm") -> pd.Series:
    return df[col].astype(str).str.lower().isin(["true", "1"])


def assert_group_invariant(df: pd.DataFrame, keys: list) -> None:
    """An empty pre-onset region is a property of the run and its split, not of the
    detector: every detector with a lead in one group must agree on it."""
    sub = df[~df["na"]]
    mixed = sub.groupby(keys)["empty_pre"].nunique()
    if (mixed > 1).any():
        raise AssertionError(f"empty_pre not detector-invariant in {mixed[mixed > 1].index[:5].tolist()}")


def audit_row(site, source, df, published_num, published_den, note=""):
    return {
        "site": site, "source": source,
        "published_valid": published_num, "published_den": published_den,
        "eq5_valid": int(df["eq5"].sum()), "eq5_scoreable": int(df["scoreable"].sum()),
        "excluded_empty_pre": int(df["empty_pre"].sum()),
        "excluded_no_onset": int(df["no_onset"].sum()),
        "complies": (published_num == int(df["eq5"].sum())
                     and published_den == int(df["scoreable"].sum())),
        "note": note,
    }


# ---------------------------------------------------------------- XJTU-SY
def xjtu_sites(audit: list) -> pd.DataFrame:
    src = "benchmark_XJTU-SY_long.csv"
    d = classify(read(src))
    assert_group_invariant(d, ["run", "mode", "factor"])
    five = d[d.short_name.isin(FIVE)]
    audit.append(audit_row("S6.3 five window-magnitude detectors, all modes x factors",
                           src, five, int(published_valid(five).sum()), len(five)))

    full = five[(five["mode"] == "aggregate") & (five.factor == 1)]
    rows = []
    for run, g in full.groupby("run"):
        valid = g[g.eq5]["lead_time_hours"]
        status = ("no_onset" if g.no_onset.all() else
                  "empty_pre" if g.empty_pre.all() else "scoreable")
        if status == "scoreable" and not g.scoreable.all():
            raise AssertionError(f"{run}: partially scoreable at full resolution")
        rows.append({"run": run, "status": status,
                     "published_valid_of_5": int(published_valid(g).sum()),
                     "eq5_valid_of_5": int(g.eq5.sum()) if status == "scoreable" else np.nan,
                     "mean_valid_lead_h": valid.mean() if len(valid) else np.nan,
                     "best_valid_lead_h": valid.max() if len(valid) else np.nan})
    pb = pd.DataFrame(rows)
    audit.append(audit_row("Table 7 total (full resolution, aggregate)", src, full,
                           int(published_valid(full).sum()), len(full)))
    sc = pb[pb.status == "scoreable"]
    audit.append({"site": "Table 7 bearings with no valid detector", "source": src,
                  "published_valid": 2, "published_den": 10,
                  "eq5_valid": int((sc.eq5_valid_of_5 == 0).sum()), "eq5_scoreable": len(sc),
                  "excluded_empty_pre": int((pb.status == "empty_pre").sum()),
                  "excluded_no_onset": int((pb.status == "no_onset").sum()),
                  "complies": False, "note": "counts bearings, not evaluations"})

    # Section 6.3 sequence-length claim: seqlen15_xjtu.csv carries no FAR column.
    # Its one extra usable bearing is Bearing2_5, whose pre-onset region is empty at
    # full resolution for every detector with a lead; a sequence model scores a subset
    # of the same test windows, so its pre-onset region is empty too.
    seq = read("seqlen15_xjtu.csv")
    s15 = seq[(seq.seq_len == 15) & ~seq.na.astype(bool)]
    status = pb.set_index("run")["status"]
    s15 = s15.assign(scoreable=s15.run.map(status).eq("scoreable"))
    audit.append({"site": "S6.3 deep models at seq-len 15 (bearings with a valid alarm)",
                  "source": "seqlen15_xjtu.csv + " + src,
                  "published_valid": int(s15[published_valid(s15, "valid")].run.nunique()),
                  "published_den": 10,
                  "eq5_valid": int(s15[s15.scoreable & published_valid(s15, "valid")].run.nunique()),
                  "eq5_scoreable": int(s15[s15.scoreable].run.nunique()),
                  "excluded_empty_pre": int(s15[~s15.scoreable].run.nunique()),
                  "excluded_no_onset": 0, "complies": False,
                  "note": "excluded bearing(s): " + ",".join(sorted(s15[~s15.scoreable].run.unique()))})
    return pb


# ---------------------------------------------------------------- FEMTO
def femto_site(audit: list) -> None:
    src = "n20_rerun_long_FEMTO.csv"
    d = classify(read(src))
    audit.append(audit_row("S6.4 FEMTO eleven detectors, all modes x factors", src, d,
                           int(published_valid(d).sum()), len(d)))


def training_sweep(audit: list) -> pd.DataFrame:
    src = "femto_training_sweep_long.csv"
    d = classify(read(src))
    assert_group_invariant(d, ["bearing", "train_fraction"])
    rows = []
    for (det, t), g in d.groupby(["short_name", "train_fraction"]):
        den = g[g.scoreable]
        rows.append({"short_name": det, "train_fraction": t,
                     "valid_frac": den.eq5.sum() / len(den), "n_valid": int(den.eq5.sum()),
                     "n_scoreable": len(den), "na_count": int(den.na.sum()),
                     "n_excluded": int((~g.scoreable).sum()),
                     "published_valid_frac": published_valid(g).mean()})
    out = pd.DataFrame(rows)
    audit.append(audit_row("S6.12 / Figure 6 training sweep, all cells", src, d,
                           int(published_valid(d).sum()), len(d),
                           "N/A cells stay in the denominator as no valid alarm (Section 4.5)"))
    return out


# ---------------------------------------------------------------- IMS
def ims_sites(audit: list) -> pd.DataFrame:
    src = "persistence_sensitivity_IMS_invariant_long.csv"
    p = classify(read(src))
    assert_group_invariant(p, ["persistence", "run", "mode", "factor"])
    rows = []
    for (pers, det), g in p[p["mode"] == "aggregate"].groupby(["persistence", "short_name"]):
        f1 = g[g.factor == 1]
        rows.append({"persistence": pers, "short_name": det,
                     "valid_frac_f1": f1.eq5.sum() / f1.scoreable.sum(),
                     "n_valid_f1": int(f1.eq5.sum()), "n_scoreable_f1": int(f1.scoreable.sum()),
                     "valid_frac_all_factors": g.eq5.sum() / g.scoreable.sum(),
                     "n_valid_all": int(g.eq5.sum()), "n_scoreable_all": int(g.scoreable.sum()),
                     "published_valid_frac_all": published_valid(g).mean()})
    ts = p[(p.short_name == "three_sigma") & (p["mode"] == "aggregate")]
    audit.append(audit_row("Table 4a 3sigma valid-alarm frac., all factors (4 persistences)",
                           src, ts, int(published_valid(ts).sum()), len(ts)))

    ab = classify(read("feature_coarsening_ablation_IMS_long.csv"))
    den = (ab[ab.scoreable].groupby(["factor", "group", "short_name"]).run.nunique()
           .groupby("factor").agg(["min", "max"]).reset_index())
    audit.append(audit_row("S6.10 feature-group ablation repeated at every factor",
                           "feature_coarsening_ablation_IMS_long.csv", ab,
                           int(published_valid(ab).sum()), len(ab),
                           "runs per cell by factor: " + "; ".join(
                               f"f={r.factor}:{r['min']}-{r['max']}" for _, r in den.iterrows())))
    return pd.DataFrame(rows)


def no_onset_runs() -> dict:
    """Runs with no detectable onset, per dataset, from the benchmark files. The gap sweep
    (src/d18_gap_multiseed.py) calls the same compute_run_onset on the same runs but writes no
    t_onset column, and for a no-onset run its far_preonset_pct is the positional legacy FAR --
    so the no-onset status must be carried over, or Bearing1_2 is silently scored."""
    out = {}
    for ds, f in (("IMS", "benchmark_IMS_long_invariant.csv"), ("XJTU-SY", "benchmark_XJTU-SY_long.csv")):
        b = read(f)
        out[ds] = set(b[b.t_onset.isna()].run)
    return out


def gap_table(audit: list) -> pd.DataFrame:
    src = "d18_gap_injection_multiseed.csv"
    raw = read(src)
    none = no_onset_runs()
    on = [np.nan if r in none.get(ds, set()) else "defined" for ds, r in zip(raw.dataset, raw.run)]
    g = classify(raw.assign(t_onset=on), lead="lead")
    rows = []
    for (ds, det, gap), s in g[g.short_name.isin(GAP_DETS)].groupby(["dataset", "short_name", "gap"]):
        per_eq5 = s[s.eq5].groupby("gap_seed").lead.mean()
        per_pub = s[published_valid(s, "valid")].groupby("gap_seed").lead.mean()
        counts = s[s.scoreable].groupby("gap_seed").eq5.sum()
        rows.append({"dataset": ds, "short_name": det, "gap": gap,
                     "mean_valid_lead_h": per_eq5.mean() if len(per_eq5) else np.nan,
                     "draw_min_h": per_eq5.min() if len(per_eq5) else np.nan,
                     "draw_max_h": per_eq5.max() if len(per_eq5) else np.nan,
                     "n_valid_min": int(counts.min()), "n_valid_max": int(counts.max()),
                     "n_scoreable_runs": int(s[s.scoreable].run.nunique()),
                     "published_mean_valid_lead_h": per_pub.mean() if len(per_pub) else np.nan})
    audit.append(audit_row("Table 4b historian gaps (mean over valid alarms)", src, g,
                           int(published_valid(g, "valid").sum()), len(g),
                           "excluded runs: " + ",".join(sorted(g[~g.scoreable].run.unique()))))
    return pd.DataFrame(rows)


def compliant_sites(audit: list) -> None:
    """Files behind counts that need no restatement: zero unscoreable rows."""
    full_res = lambda d: d[(d["mode"] == "aggregate") & (d.factor == 1)]  # noqa: E731
    for site, src, flt in (
        ("S6.1 IMS full resolution (deep 0/3, Table 2 L_tau)", "benchmark_IMS_long_invariant.csv", full_res),
        ("S6.1 / Table 9 IMS trade-off", "tradeoff_IMS_long.csv", None),
        ("S6.1 / Table 9 IMS trade-off, deep models", "tradeoff_IMS_deepmodels_long.csv", None),
        ("Table 10 feature-group ablation", "ablation_features_IMS_long.csv", None),
        ("Appendix D.1 denoisers", "denoising_IMS.csv", None),
        ("Appendix D.2 ONGC gating", "n20_rerun_long_ONGC.csv", full_res),
    ):
        d = read(src)
        c = classify(flt(d) if flt else d)
        audit.append(audit_row(site, src, c, int(published_valid(c).sum()), len(c)))


# ------------------------------------------------ Table 8 independent re-derivation
GATED_SOURCES = {"IMS": ["benchmark_IMS_long_invariant.csv", "d3_ocsvm_benchmark_long.csv"],
                 "XJTU-SY": ["benchmark_XJTU-SY_long.csv", "d3_ocsvm_benchmark_long.csv"],
                 "FEMTO": ["n20_rerun_long_FEMTO.csv"],
                 "Ferrara": ["n20_rerun_long_Ferrara.csv"]}


def gated_crosscheck() -> pd.DataFrame:
    """Recompute Table 8's gated arm under Eq. 5 and compare with rf2_gated_contrast_n20.csv."""
    ref = read("rf2_gated_contrast_n20.csv")
    ref = ref[ref.metric == "gated_D7"].set_index(["dataset", "short_name"])
    rows = []
    for ds, files in GATED_SOURCES.items():
        d = pd.concat([read(f) for f in files], ignore_index=True)
        d = classify(d[d.dataset == ds])
        d["L_eq5"] = np.where(d.scoreable & ~d.na, np.where(d.eq5, d.lead_time_hours, 0.0), np.nan)
        diffs = run_level_diffs(d.dropna(subset=["L_eq5"]), metric="L_eq5")
        for det, grp in d.groupby("short_name"):
            rd = diffs[diffs.method == grp.method.iloc[0]]["diff"]
            r = ref.loc[(ds, det)]
            rows.append({"dataset": ds, "short_name": det,
                         "median_diff_h": float(rd.median()) if len(rd) else np.nan,
                         "n_effective": int((rd != 0).sum()),
                         "ref_median_diff_h": float(r["median_diff_h"]),
                         "ref_n_effective": int(r["n_effective"])})
    out = pd.DataFrame(rows)
    out["agrees"] = (np.isclose(out.median_diff_h.fillna(0), out.ref_median_diff_h.fillna(0), atol=1e-9)
                     & (out.n_effective == out.ref_n_effective))
    return out


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    audit = []
    pb = xjtu_sites(audit)
    femto_site(audit)
    sweep = training_sweep(audit)
    pers = ims_sites(audit)
    gap = gap_table(audit)
    compliant_sites(audit)
    gated = gated_crosscheck()
    audit.append({"site": "Table 8 gated arm (independent re-derivation)",
                  "source": "rf2_gated_contrast_n20.csv", "published_valid": np.nan,
                  "published_den": np.nan, "eq5_valid": np.nan, "eq5_scoreable": np.nan,
                  "excluded_empty_pre": np.nan, "excluded_no_onset": np.nan,
                  "complies": bool(gated.agrees.all()),
                  "note": f"{int(gated.agrees.sum())}/{len(gated)} (dataset, detector) cells agree"})

    outputs = {"eq5_validity_audit.csv": pd.DataFrame(audit),
               "eq5_xjtu_perbearing.csv": pb,
               "eq5_femto_training_sweep.csv": sweep,
               "eq5_persistence_IMS.csv": pers,
               "eq5_gap_table4b.csv": gap,
               "eq5_gated_crosscheck.csv": gated}
    for name, df in outputs.items():
        df.to_csv(os.path.join(TAB, name), index=False)
        print(f"wrote {name} ({len(df)} rows)")
    print(pd.DataFrame(audit)[["site", "published_valid", "published_den", "eq5_valid",
                               "eq5_scoreable", "excluded_empty_pre", "excluded_no_onset",
                               "complies"]].to_string())


if __name__ == "__main__":
    main()
