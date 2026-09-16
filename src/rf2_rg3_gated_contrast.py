# src/rf2_rg3_gated_contrast.py
"""
Reviewer F item RF-2 (register 1.1) and Reviewer G item RG-3 (register 1.5), in one pass.

RF-2 -- the run-level aggregate-minus-decimate contrast on the GATED lead L (Eq. 5) as well as
        on raw lead, per dataset x detector, all five datasets, all eleven detectors, with
        median delta, n+/n-, TIE COUNT, exact two-sided sign-test p and Holm across the N = 44
        family (11 detectors x {IMS, XJTU-SY, FEMTO, Ferrara}; ONGC n = 1 is reported but never
        enters the family). Companion: valid-alarm fraction under aggregate vs decimate.

RG-3 -- the same contrast, raw and gated, with the degradation onset taken from the ``pca1`` and
        ``kurt_only`` health indicators instead of the default ``rms_kurt``. Raw lead has no
        onset term, so its differences should be invariant; this is VERIFIED end to end by
        re-running the repo's own ``run_benchmark`` once per indicator (every detector
        re-fitted), not assumed.

VALIDITY CONVENTION (decision D-7, the minimum already in the manuscript)
    scoreable : ``t_onset`` is defined AND ``far_preonset_pct`` is defined.
                A row with an empty pre-onset region (FAR_pre undefined) or no onset at all
                (XJTU Bearing1_2 under rms_kurt -- whose ``far_preonset_pct`` column holds a
                LEGACY FAR, defect N-12, so NaN alone does not catch it) is UNSCOREABLE.
    valid     : scoreable AND lead > 0 AND FAR_pre <= tau (tau = 10 %).
    L (D-7)   : lead if valid, 0 if scoreable-but-invalid, and EXCLUDED (NaN) if unscoreable.
                Unscoreable rows are excluded from every validity denominator and are never
                counted valid.
    L (strict): secondary, Eq. 5 read literally -- unscoreable rows count as invalid, L = 0.
    The published ``valid_alarm`` column is deliberately NOT used: it skips the gate when FAR_pre
    is NaN (N-7) and carries the legacy VLT test on no-onset runs (N-12).

SCHEMA (decision D-2): IMS is read from / re-run on the 49-dim invariant schema. The published
legacy IMS file is used ONLY to cross-check Tables 10 and 11, which still carry legacy values.

Run-level differences use ``src.stats_rigor.run_level_diffs`` (mean collapse over factors and
seeds within mode, Section 4.8), unmodified. Nothing existing is modified; no published result
file is written. The onset indicator is switched IN MEMORY for the duration of a rerun only.

Sub-commands:
    python -m src.rf2_rg3_gated_contrast onsets
    python -m src.rf2_rg3_gated_contrast rerun --dataset IMS --indicator pca1
    python -m src.rf2_rg3_gated_contrast analyse

Outputs (all NEW, results/tables/):
    rf2_crosscheck_raw_vs_published.csv   raw-lead rebuild vs Tables 7-11 (parsed from the .tex)
    rf2_gated_contrast.csv                 raw and gated contrast + Holm, both conventions
    rf2_valid_fraction_agg_vs_dec.csv      companion validity table
    rg3_onsets.csv                         onset per run x indicator (+ Table 4 check on IMS)
    rg3_rerun_long_<DS>_<IND>.csv          one per rerun arm
    rg3_reproduction_check.csv             rms_kurt rerun vs the published long files
    rg3_raw_invariance.csv                 raw-lead deviation across indicators
    rg3_contrast_by_indicator.csv          raw and gated contrast per indicator + shift
    rg3_valid_fraction_<IND>.csv           companion validity table per indicator
"""

import argparse
import contextlib
import logging
import os
import sys

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TAU_PCT = 10.0
SEED = 42
INDICATORS = ["rms_kurt", "pca1", "kurt_only"]
DATASETS = ["IMS", "XJTU-SY", "FEMTO", "Ferrara", "ONGC"]
HOLM_DATASETS = ["IMS", "XJTU-SY", "FEMTO", "Ferrara"]
OCSVM = "one_class_svm"
# Datasets without kurtosis channels (checked in ``compute_onsets``): kurt_only is undefined.
NO_KURTOSIS = {"ONGC"}

# Published long files per dataset (D-2: invariant IMS). OC-SVM rows come from d3.
PUBLISHED = {
    "IMS": "benchmark_IMS_long_invariant.csv",
    "XJTU-SY": "benchmark_XJTU-SY_long.csv",
    "FEMTO": "benchmark_FEMTO_long.csv",
    "Ferrara": "benchmark_Ferrara_long.csv",
    "ONGC": "benchmark_ONGC_long.csv",
}
IMS_LEGACY = "benchmark_IMS_long.csv"
OCSVM_FILE = "d3_ocsvm_benchmark_long.csv"

TEX = os.path.join("paper", "files", "scada_ijphm.tex")

# Manuscript display name -> short_name.
TEX_NAMES = {
    r"$3\sigma$": "three_sigma", "EWMA": "ewma", "CUSUM": "cusum",
    r"Hotelling $T^2$": "hotelling_t2", r"Iso.\ Forest": "isolation_forest",
    "Deep SVDD": "deep_svdd", "RMS-trend": "rms_trend", "LSTM-AE": "lstm_ae",
    "TCN-AE": "tcn", "Transformer-AD": "transformer_ad", "Transf.-AD": "transformer_ad",
}
TEX_DATASETS = {"IMS": "IMS", "XJTU": "XJTU-SY", "FEMTO": "FEMTO", "Ferrara": "Ferrara"}

KEY = ["dataset", "run", "short_name", "mode", "factor"]


def _tables_dir():
    from src.config import PATHS
    return PATHS["results_tables"]


def _read(name):
    return pd.read_csv(os.path.join(_tables_dir(), name))


def _write(df, name):
    path = os.path.join(_tables_dir(), name)
    df.to_csv(path, index=False)
    logger.info("Saved -> %s (%d rows)", path, len(df))


# ─────────────────────────── validity convention ───────────────────────────────

def add_gated_columns(long_df):
    """Return a copy with scoreable / valid_d7 / L_d7 / L_strict columns (D-7 convention)."""
    df = long_df.copy()
    lead = df["lead_time_hours"]
    far = df["far_preonset_pct"]
    has_lead = lead.notna()
    scoreable = has_lead & df["t_onset"].notna() & far.notna()
    valid = scoreable & (lead > 0) & (far <= TAU_PCT)
    df["scoreable"] = scoreable
    df["valid_d7"] = valid
    df["L_d7"] = np.where(scoreable, np.where(valid, lead, 0.0), np.nan)
    df["L_strict"] = np.where(has_lead, np.where(valid, lead, 0.0), np.nan)
    return df


def load_published(dataset, legacy_ims=False):
    """Published long rows for one dataset with its OC-SVM rows appended."""
    fname = IMS_LEGACY if (legacy_ims and dataset == "IMS") else PUBLISHED[dataset]
    base = _read(fname)
    oc = _read(OCSVM_FILE)
    oc = oc[oc["dataset"] == dataset]
    return pd.concat([base, oc], ignore_index=True)


# ─────────────────────────── contrast statistics ───────────────────────────────

def contrast_table(long_df, metric, label):
    """Run-level exact sign test per (dataset, detector) on ``metric``. Holm is added later."""
    from src.stats_rigor import run_level_diffs, exact_sign_test

    rows = []
    for (ds, short), grp in long_df.groupby(["dataset", "short_name"]):
        n_with_lead = grp.loc[grp["lead_time_hours"].notna(), "run"].nunique()
        rl = run_level_diffs(grp, metric=metric).sort_values("run")
        st = exact_sign_test(rl["diff"].values)
        rows.append({
            "dataset": ds, "short_name": short, "method": grp["method"].iloc[0],
            "metric": label,
            "n_runs_with_lead": int(n_with_lead),
            "n_runs_tested": st["n"],
            "n_runs_excluded_unscoreable": int(n_with_lead) - st["n"],
            "run_diffs": ", ".join("%+.4f" % v for v in rl["diff"].values),
            "median_diff_h": st["median"],
            "n_pos": st["n_pos"], "n_neg": st["n_neg"], "n_ties": st["n_zero"],
            "n_effective": st["n_effective"],
            "p_floor_two_sided": min(1.0, 2 * 0.5 ** st["n_effective"])
            if st["n_effective"] else 1.0,
            "sign_test_p": st["p_value"],
            "all_same_sign": st["all_same_sign"],
        })
    return pd.DataFrame(rows)


def with_holm(table):
    """Holm across the N = 44 family; ONGC rows are carried with NaN Holm columns."""
    from src.stats_rigor import holm_bonferroni

    out = table.copy()
    out["holm_p"] = np.nan
    out["holm_reject"] = False
    out["family_size"] = np.nan
    fam = out["dataset"].isin(HOLM_DATASETS).values
    adj, rej = holm_bonferroni(out.loc[fam, "sign_test_p"].values)
    out.loc[fam, "holm_p"] = adj
    out.loc[fam, "holm_reject"] = rej
    out.loc[fam, "family_size"] = int(fam.sum())
    return out


def valid_fraction_table(long_df):
    """Valid-alarm fraction per (dataset, detector, mode), plus validity flips across modes."""
    rows = []
    df = long_df[long_df["lead_time_hours"].notna()]
    for (ds, short), sub in df.groupby(["dataset", "short_name"]):
        rec = {"dataset": ds, "short_name": short}
        for mode in ("aggregate", "decimate"):
            m = sub[sub["mode"] == mode]
            n_all, n_sc, n_val = len(m), int(m["scoreable"].sum()), int(m["valid_d7"].sum())
            rec[f"{mode}_n_rows"] = n_all
            rec[f"{mode}_n_unscoreable"] = n_all - n_sc
            rec[f"{mode}_n_valid"] = n_val
            rec[f"{mode}_valid_frac_d7"] = n_val / n_sc if n_sc else np.nan
            rec[f"{mode}_valid_frac_strict"] = n_val / n_all if n_all else np.nan
        agg = sub[sub["mode"] == "aggregate"].set_index(["run", "factor"])
        dec = sub[sub["mode"] == "decimate"].set_index(["run", "factor"])
        pair = agg.join(dec, how="inner", lsuffix="_a", rsuffix="_d")
        both = pair[pair["scoreable_a"] & pair["scoreable_d"]]
        flip = both["valid_d7_a"] != both["valid_d7_d"]
        same_lead = both["lead_time_hours_a"] == both["lead_time_hours_d"]
        rec["n_pairs_both_scoreable"] = len(both)
        rec["n_validity_flips"] = int(flip.sum())
        rec["n_flips_valid_only_under_aggregate"] = int((flip & both["valid_d7_a"]).sum())
        rec["n_flips_valid_only_under_decimate"] = int((flip & both["valid_d7_d"]).sum())
        rec["n_flips_with_identical_raw_lead"] = int((flip & same_lead).sum())
        rows.append(rec)
    return pd.DataFrame(rows)


# ─────────────────────────── published-table parser ────────────────────────────

def _tex_rows(tex, label):
    """Data rows (lists of cells) of the tabular that carries ``\\label{label}``."""
    i = tex.index("\\label{%s}" % label)
    body = tex[i:tex.index("\\end{tabular}", i)]
    rows = []
    for line in body.split("\n"):
        line = line.strip()
        if "&" not in line or "\\textbf" in line:
            continue
        line = line[:-2] if line.endswith("\\\\") else line
        rows.append([c.strip() for c in line.split("&")])
    return rows


def _num(cell):
    return float(cell.replace("$", "").strip())


def _name(cell):
    return TEX_NAMES[cell.replace("$^\\ddagger$", "").strip()]


def published_values(tex_path=TEX):
    """Parse Tables 7-11 into (table, dataset, short_name, field, published, dp) rows."""
    with open(tex_path, encoding="utf-8") as fh:
        tex = fh.read()
    out = []
    for label, ds in (("tab:xjtu", "XJTU-SY"), ("tab:femto", "FEMTO"),
                      ("tab:ferrara", "Ferrara")):
        for c in _tex_rows(tex, label):
            sn = _name(c[0])
            pos, neg = c[2].split("/")
            out += [(label, ds, sn, "median_diff_h", _num(c[1]), 2),
                    (label, ds, sn, "n_pos", int(pos), 0),
                    (label, ds, sn, "n_neg", int(neg), 0),
                    (label, ds, sn, "sign_test_p", _num(c[4]), 3)]
    for c in _tex_rows(tex, "tab:imssweep"):
        sn = _name(c[0])
        for k, v in enumerate(c[1].replace("$", "").split(",")):
            out.append(("tab:imssweep", "IMS", sn, "run_diff_%d" % (k + 1), float(v), 1))
        out += [("tab:imssweep", "IMS", sn, "median_diff_h", _num(c[2]), 1),
                ("tab:imssweep", "IMS", sn, "sign_test_p", _num(c[4]), 2)]
    for c in _tex_rows(tex, "tab:holm"):
        ds, sn = TEX_DATASETS[c[0]], _name(c[1])
        out += [("tab:holm", ds, sn, "sign_test_p", _num(c[2]), 3),
                ("tab:holm", ds, sn, "holm_p", _num(c[3]), 3)]
    return pd.DataFrame(out, columns=["table", "dataset", "short_name", "field",
                                      "published", "dp"])


def crosscheck(pub, computed, arm):
    """Compare parsed published values with a computed raw table at published precision."""
    rows = []
    idx = computed.set_index(["dataset", "short_name"])
    for _, r in pub.iterrows():
        rec = {**r.to_dict(), "arm": arm, "computed": np.nan, "match": False}
        key = (r["dataset"], r["short_name"])
        if key in idx.index:
            h = idx.loc[key]
            if r["field"].startswith("run_diff_"):
                k = int(r["field"].rsplit("_", 1)[1]) - 1
                diffs = [float(x) for x in h["run_diffs"].split(",")]
                val = diffs[k] if k < len(diffs) else np.nan
            else:
                val = float(h[r["field"]])
            tol = 0.5 * 10 ** (-r["dp"]) + 1e-9
            rec["computed"] = val
            rec["match"] = bool(np.isfinite(val) and abs(val - r["published"]) <= tol)
        rows.append(rec)
    return pd.DataFrame(rows)


# ─────────────────────────── onset indicators (RG-3) ───────────────────────────

def _kurt_only_hi(df):
    """
    Kurtosis-only HI: the kurtosis half of ``rms_kurt`` -- the baseline-z of the mean kurt_ch*
    trend, same baseline convention (``_baseline_z``). Table 4 has no generator in the repo;
    this construction is accepted only if it reproduces Table 4's published onset positions.
    """
    from src.onset import _baseline_z
    kurt = [c for c in df.columns if c.startswith("kurt_ch")]
    if not kurt:
        raise ValueError("kurt_only HI needs kurt_ch* columns")
    s = _baseline_z(df[kurt].mean(axis=1))
    s.name = "kurt_only_hi"
    return s


@contextlib.contextmanager
def onset_indicator(kind):
    """Switch ONSET['health_indicator'] (adding 'kurt_only') in memory; always restored."""
    import src.onset as onset_mod
    from src.config import ONSET
    original_hi, original_kind = onset_mod.health_indicator, ONSET["health_indicator"]

    def patched(df, channels=None, kind="rms_mean"):
        if kind == "kurt_only":
            return _kurt_only_hi(df)
        return original_hi(df, channels=channels, kind=kind)

    onset_mod.health_indicator = patched
    ONSET["health_indicator"] = kind
    try:
        yield
    finally:
        onset_mod.health_indicator = original_hi
        ONSET["health_indicator"] = original_kind


def compute_onsets():
    """Onset per dataset x run x indicator, with % of run span on Table 4's basis."""
    from src import load_pipeline
    from src.config import SPLIT
    from src.datasets import default_runs
    from src.onset import onset_for_run

    rows = []
    for ds in DATASETS:
        for run in default_runs(ds):
            base = load_pipeline(run, dataset=ds)
            df = base["df_full"]
            n = len(df)
            frac = base.get("train_fraction", SPLIT["train_fraction"])
            train_end = df.index[min(int(n * frac), n - 1)]
            t_fail = pd.Timestamp(base["failure_time"])
            span = (t_fail - df.index[0]).total_seconds()
            test_start = pd.Timestamp(base["ts_test"][0])
            has_kurt = any(c.startswith("kurt_ch") for c in df.columns)
            for kind in INDICATORS:
                note = ""
                if not has_kurt and kind != "pca1":
                    note = ("n/a: no kurt_ch* columns" if kind == "kurt_only"
                            else "falls back to rms-only z (no kurt_ch* columns)")
                if kind == "kurt_only" and not has_kurt:
                    on = None
                else:
                    with onset_indicator(kind):
                        on = onset_for_run(df, train_end=train_end, t_fail=t_fail)
                rows.append({
                    "dataset": ds, "run": run, "indicator": kind, "note": note,
                    "t_onset": on if on is not None else pd.NaT,
                    "onset_pct": 100 * (on - df.index[0]).total_seconds() / span
                    if on is not None else np.nan,
                    "max_lead_hours": (t_fail - on).total_seconds() / 3600
                    if on is not None else np.nan,
                    "test_start": test_start,
                    "onset_before_test_start": bool(on is not None and on <= test_start),
                })
    out = pd.DataFrame(rows)
    _write(out, "rg3_onsets.csv")
    return out


def rerun(dataset, indicator):
    """One end-to-end arm: ``run_benchmark`` under the given onset indicator, 11 detectors."""
    from src.benchmark import run_benchmark
    if dataset in NO_KURTOSIS and indicator == "kurt_only":
        logger.warning("[%s] has no kurt_ch* columns: kurt_only is undefined, arm skipped",
                       dataset)
        return pd.DataFrame()
    control = dataset == "IMS"
    with onset_indicator(indicator):
        # Mirror the published calls: the ten default detectors in one call, then OC-SVM
        # alone (as src/d3_ocsvm.py did), so detector order and RNG consumption match.
        main_df = run_benchmark(dataset=dataset, control=control, seeds=[SEED], save=False)
        oc_df = run_benchmark(dataset=dataset, methods=[OCSVM], control=control,
                              seeds=[SEED], save=False)
    df = pd.concat([main_df, oc_df], ignore_index=True)
    df["onset_indicator"] = indicator
    df["feature_mode"] = "invariant (controlled, D-2)" if control else "load_pipeline (invariant)"
    _write(df, "rg3_rerun_long_%s_%s.csv" % (dataset, indicator))
    return df


# ─────────────────────────────── analysis ──────────────────────────────────────

def analyse_rf2():
    pub = published_values()
    inv = pd.concat([add_gated_columns(load_published(d)) for d in DATASETS],
                    ignore_index=True)
    leg = pd.concat([add_gated_columns(load_published(d, legacy_ims=True))
                     for d in DATASETS], ignore_index=True)
    raw_inv = with_holm(contrast_table(inv, "lead_time_hours", "raw"))
    raw_leg = with_holm(contrast_table(leg, "lead_time_hours", "raw"))
    cc = pd.concat([
        crosscheck(pub, raw_leg, "A: as printed (IMS legacy file)"),
        crosscheck(pub[pub["dataset"] == "IMS"], raw_inv,
                   "B: IMS invariant (D-2) vs printed legacy - differences expected"),
    ], ignore_index=True)
    _write(cc, "rf2_crosscheck_raw_vs_published.csv")

    parts = [raw_inv]
    for metric, label in (("L_d7", "gated_D7"), ("L_strict", "gated_strict")):
        parts.append(with_holm(contrast_table(inv, metric, label)))
    gated = pd.concat(parts, ignore_index=True)
    gated["ims_schema"] = "invariant (D-2)"
    gated["validity_convention"] = gated["metric"].map({
        "raw": "n/a (raw lead carries no gate)",
        "gated_D7": "D-7: empty pre-onset region or no onset = unscoreable; excluded from "
                    "the denominator and never counted valid",
        "gated_strict": "strict Eq. 5: unscoreable counted invalid (L = 0)"})
    _write(gated, "rf2_gated_contrast.csv")

    vf = valid_fraction_table(inv)
    vf["validity_convention"] = ("D-7: valid_frac_d7 = valid / scoreable rows; "
                                 "valid_frac_strict = valid / all rows")
    _write(vf, "rf2_valid_fraction_agg_vs_dec.csv")
    return cc, gated, vf


def _reproduction(rr):
    pub = pd.concat([load_published(d) for d in DATASETS], ignore_index=True)
    base = rr[rr["onset_indicator"] == "rms_kurt"]
    m = base.merge(pub, on=KEY, suffixes=("_rerun", "_pub"), how="outer", indicator=True)
    rows = []
    for (ds, sn), sub in m.groupby(["dataset", "short_name"]):
        both = sub[sub["_merge"] == "both"]
        rec = {"dataset": ds, "short_name": sn, "n_rows_both": len(both),
               "n_rows_one_side_only": int((sub["_merge"] != "both").sum())}
        for col in ("lead_time_hours", "far_preonset_pct"):
            a, b = both[col + "_rerun"], both[col + "_pub"]
            dev = (a - b).abs()
            rec[col + "_max_abs_dev"] = float(dev.max()) if dev.notna().any() else 0.0
            rec[col + "_nan_mismatch"] = int((a.isna() != b.isna()).sum())
        rec["t_onset_mismatch"] = int((both["t_onset_rerun"].astype(str)
                                       != both["t_onset_pub"].astype(str)).sum())
        rows.append(rec)
    out = pd.DataFrame(rows)
    _write(out, "rg3_reproduction_check.csv")
    return out


def _raw_invariance(rr):
    wide = rr.pivot_table(index=KEY, columns="onset_indicator", values="lead_time_hours",
                          aggfunc="first", dropna=False)
    rl = {}
    for ind in INDICATORS:
        sub = rr[rr["onset_indicator"] == ind]
        if not sub.empty:
            rl[ind] = contrast_table(sub, "lead_time_hours", "raw") \
                .set_index(["dataset", "short_name"])
    rows = []
    if "rms_kurt" not in rl:
        return pd.DataFrame()
    for ind in [i for i in INDICATORS if i != "rms_kurt" and i in rl]:
        for key, ref in rl["rms_kurt"].iterrows():
            if key not in rl[ind].index:
                continue
            alt = rl[ind].loc[key]
            d_ref = np.array([float(x) for x in ref["run_diffs"].split(",")]) \
                if ref["run_diffs"] else np.array([])
            d_alt = np.array([float(x) for x in alt["run_diffs"].split(",")]) \
                if alt["run_diffs"] else np.array([])
            w = wide.xs(key, level=("dataset", "short_name"))
            row_dev = (w[ind] - w["rms_kurt"]).abs()
            rows.append({
                "dataset": key[0], "short_name": key[1], "indicator": ind,
                "max_abs_dev_row_lead_h": float(row_dev.max()) if row_dev.notna().any() else 0.0,
                "row_nan_mismatch": int((w[ind].isna() != w["rms_kurt"].isna()).sum()),
                "max_abs_dev_run_diff_h": float(np.max(np.abs(d_alt - d_ref)))
                if len(d_alt) == len(d_ref) and len(d_ref) else np.nan,
                "n_run_diffs": len(d_ref),
                "median_rms_kurt_h": ref["median_diff_h"],
                "median_alt_h": alt["median_diff_h"],
            })
    out = pd.DataFrame(rows)
    _write(out, "rg3_raw_invariance.csv")
    return out


def analyse_rg3():
    tdir = _tables_dir()
    arms = []
    for ds in DATASETS:
        for ind in INDICATORS:
            p = os.path.join(tdir, "rg3_rerun_long_%s_%s.csv" % (ds, ind))
            if os.path.exists(p):
                arms.append(pd.read_csv(p))
            else:
                logger.warning("missing arm %s / %s", ds, ind)
    if not arms:
        return None
    rr = pd.concat(arms, ignore_index=True)
    rep = _reproduction(rr)
    inv = _raw_invariance(rr)

    out = []
    for ind in INDICATORS:
        sub = add_gated_columns(rr[rr["onset_indicator"] == ind])
        if sub.empty:
            continue
        for metric, label in (("lead_time_hours", "raw"), ("L_d7", "gated_D7"),
                              ("L_strict", "gated_strict")):
            t = with_holm(contrast_table(sub, metric, label))
            t["indicator"] = ind
            out.append(t)
        vf = valid_fraction_table(sub)
        vf["indicator"] = ind
        _write(vf, "rg3_valid_fraction_%s.csv" % ind)
    by = pd.concat(out, ignore_index=True)
    ref = by[by["indicator"] == "rms_kurt"].set_index(["dataset", "short_name", "metric"])
    shifts = []
    for _, r in by.iterrows():
        k = (r["dataset"], r["short_name"], r["metric"])
        shifts.append(r["median_diff_h"] - ref.loc[k, "median_diff_h"]
                      if k in ref.index else np.nan)
    by["median_shift_vs_rms_kurt_h"] = shifts
    by["sign_pattern"] = (by["n_pos"].astype(str) + "+/" + by["n_neg"].astype(str) + "-/"
                          + by["n_ties"].astype(str) + "=")
    _write(by, "rg3_contrast_by_indicator.csv")
    return rep, inv, by


def _setup():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")   # N-13 guard
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")


def main(argv=None):
    _setup()
    ap = argparse.ArgumentParser(description="RF-2 / RG-3 gated and onset-indicator contrast")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("onsets")
    r = sp.add_parser("rerun")
    r.add_argument("--dataset", required=True, choices=DATASETS)
    r.add_argument("--indicator", required=True, choices=INDICATORS)
    a = sp.add_parser("analyse")
    a.add_argument("--part", choices=["rf2", "rg3", "all"], default="all")
    args = ap.parse_args(argv)

    if args.cmd == "onsets":
        print(compute_onsets().to_string(index=False))
    elif args.cmd == "rerun":
        rerun(args.dataset, args.indicator)
    else:
        if args.part in ("rf2", "all"):
            analyse_rf2()
        if args.part in ("rg3", "all"):
            analyse_rg3()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
