# src/n20_propagate.py
"""
N-20 / D-10 propagation: what moves once FEMTO, Ferrara and ONGC are re-run with aggregate and
decimate on the same effective logging interval.

Arms
    old : the published long files (FEMTO/Ferrara/ONGC produced with the minute-rounding bug)
          + the d3 OC-SVM rows, IMS on the invariant schema (D-2)
    new : FEMTO/Ferrara/ONGC from results/tables/n20_rerun_long_<DS>.csv (10 detectors + OC-SVM,
          post-fix); IMS and XJTU-SY unchanged (verified by src/n20_resample_fix.py)

Outputs (all NEW, results/tables/):
    n20_raw_contrast_old_vs_new.csv     run-level raw contrast + Holm N=44, both arms
    n20_manuscript_cells.csv            every printed cell of Tables 8, 9, 11 (FEMTO/Ferrara)
                                        and the ONGC table, against both arms, with tex line
    n20_ongc_minutes.csv                ONGC median-over-factors difference (min), both arms
    n20_d15_bootstrap_{old,new}.csv     D15 equivalence via src.d15_equivalence.analyse itself
    n20_d15_tost_{old,new}.csv            (10 detectors, the published family)
    n20_d15_{bootstrap,tost}_new_11det.csv   same, OC-SVM added (33 multi-bearing cells)
    n20_d15_replay_check.csv            old-arm replay vs the published d15 file (must be exact)

Entry point:  python -m src.n20_propagate
"""

import contextlib
import logging
import os
import shutil
import sys
import tempfile

import pandas as pd

logger = logging.getLogger(__name__)

N20_DATASETS = ["FEMTO", "Ferrara", "ONGC"]
ALL = ["IMS", "XJTU-SY", "FEMTO", "Ferrara", "ONGC"]
TEX = os.path.join("paper", "files", "scada_ijphm.tex")


def _t(name=""):
    from src.config import PATHS
    return os.path.join(PATHS["results_tables"], name)


def long_frame(dataset, arm):
    """Long rows for one dataset in one arm, eleven detectors."""
    from src.rf2_rg3_gated_contrast import load_published
    if arm == "new" and dataset in N20_DATASETS:
        return pd.read_csv(_t(f"n20_rerun_long_{dataset}.csv"))
    return load_published(dataset)


def raw_contrast():
    from src.rf2_rg3_gated_contrast import contrast_table, with_holm
    out = []
    for arm in ("old", "new"):
        df = pd.concat([long_frame(d, arm) for d in ALL], ignore_index=True)
        t = with_holm(contrast_table(df, "lead_time_hours", "raw"))
        t["arm"] = arm
        out.append(t)
    res = pd.concat(out, ignore_index=True)
    res.to_csv(_t("n20_raw_contrast_old_vs_new.csv"), index=False)
    return res


def ongc_minutes(arm):
    """ONGC table convention: median over the five factors of (agg - dec) lead, in minutes."""
    df = long_frame("ONGC", arm)
    p = df.pivot_table(index=["short_name", "factor"], columns="mode",
                       values="lead_time_hours", aggfunc="mean")
    diff = (p["aggregate"] - p["decimate"]) * 60.0
    return diff.groupby(level="short_name").median()


def _line_of(tex_lines, label, row_name, dataset=None):
    """1-based tex line of a table row inside the tabular carrying \\label{label}."""
    start = next(i for i, l in enumerate(tex_lines) if "\\label{%s}" % label in l)
    for i in range(start, len(tex_lines)):
        l = tex_lines[i].strip()
        if l.startswith("\\end{tabular}"):
            break
        cells = [c.strip() for c in l.split("&")]
        if len(cells) < 2:
            continue
        if dataset is None and cells[0] == row_name:
            return i + 1
        if dataset is not None and cells[0] == dataset and \
                cells[1].replace("$^\\ddagger$", "") == row_name:
            return i + 1
    return None


def manuscript_cells(raw):
    import src.rf2_rg3_gated_contrast as rf
    rf.TEX_NAMES.setdefault("One-class SVM", "one_class_svm")
    pub = rf.published_values(TEX)
    pub = pub[pub["dataset"].isin(["FEMTO", "Ferrara"])].copy()
    with open(TEX, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    names = {}
    for disp, sn in rf.TEX_NAMES.items():
        names.setdefault(sn, []).append(disp)

    rows = []
    for _, r in pub.iterrows():
        line = None
        for disp in names[r["short_name"]]:
            line = (_line_of(lines, "tab:holm", disp, r["dataset"])
                    if r["table"] == "tab:holm" else _line_of(lines, r["table"], disp))
            if line:
                break
        rec = {"table": r["table"], "tex_line": line, "dataset": r["dataset"],
               "short_name": r["short_name"], "field": r["field"],
               "printed": r["published"], "dp": r["dp"]}
        tol = 0.5 * 10 ** (-r["dp"]) + 1e-9
        for arm in ("old", "new"):
            h = raw[(raw["arm"] == arm) & (raw["dataset"] == r["dataset"])
                    & (raw["short_name"] == r["short_name"])].iloc[0]
            v = float(h[r["field"]])
            rec[arm] = v
            rec[f"{arm}_matches_print"] = bool(abs(v - r["published"]) <= tol)
        rows.append(rec)

    ongc_rows = {"$3\\sigma$": "three_sigma", "EWMA": "ewma",
                 "Hotelling $T^2$": "hotelling_t2", "Isolation Forest": "isolation_forest",
                 "RMS-trend": "rms_trend"}
    old_m, new_m = ongc_minutes("old"), ongc_minutes("new")
    pd.DataFrame({"old_min": old_m, "new_min": new_m}).to_csv(_t("n20_ongc_minutes.csv"))
    for disp, sn in ongc_rows.items():
        ln = _line_of(lines, "tab:ongc", disp)
        cell = lines[ln - 1].strip()
        cell = cell[:-2] if cell.endswith("\\\\") else cell
        printed = float(cell.split("&")[1].replace("$", "").replace("+", "").strip())
        rec = {"table": "tab:ongc", "tex_line": ln, "dataset": "ONGC", "short_name": sn,
               "field": "median_diff_min", "printed": printed, "dp": 1}
        for arm, series in (("old", old_m), ("new", new_m)):
            v = float(series[sn])
            rec[arm] = v
            rec[f"{arm}_matches_print"] = bool(abs(v - printed) <= 0.05 + 1e-9)
        rows.append(rec)

    out = pd.DataFrame(rows)
    out["moves"] = out["old_matches_print"] & ~out["new_matches_print"]
    out.to_csv(_t("n20_manuscript_cells.csv"), index=False)
    return out


@contextlib.contextmanager
def _redirected_tables(tmp):
    """Point PATHS['results_tables'] at a temp dir so d15's writer cannot touch published files."""
    from src.config import PATHS
    old = PATHS["results_tables"]
    PATHS["results_tables"] = tmp
    try:
        yield
    finally:
        PATHS["results_tables"] = old


def _d15_sources(arm, with_ocsvm):
    """Absolute inputs in d15's own SOURCES order; arm frames are materialised to temp CSVs."""
    import src.d15_equivalence as d15mod
    tmp_in = tempfile.mkdtemp(prefix="n20_d15_in_")
    label_to_ds = {
        "IMS (published, legacy 445-dim)": None,
        "IMS (invariant re-baseline, D-2)": "IMS",
        "XJTU-SY": "XJTU-SY", "FEMTO": "FEMTO", "Ferrara": "Ferrara", "ONGC": "ONGC",
    }
    sources = {}
    for label, fname in d15mod.SOURCES.items():
        ds = label_to_ds[label]
        if ds is None:                       # legacy IMS arm: published file, 10 detectors
            sources[label] = os.path.abspath(_t(fname))
            continue
        if with_ocsvm or (arm == "new" and ds in N20_DATASETS):
            df = long_frame(ds, arm)
        else:
            df = pd.read_csv(_t(fname))
        if not with_ocsvm:
            df = df[df["short_name"] != "one_class_svm"]
        p = os.path.join(tmp_in, os.path.basename(fname))
        df.to_csv(p, index=False)
        sources[label] = os.path.abspath(p)
    return sources


def d15(arm, with_ocsvm=False):
    import src.d15_equivalence as d15mod
    sources = _d15_sources(arm, with_ocsvm)
    tmp_out = tempfile.mkdtemp(prefix="n20_d15_out_")
    saved = dict(d15mod.SOURCES)
    d15mod.SOURCES.clear()
    d15mod.SOURCES.update(sources)
    try:
        with _redirected_tables(tmp_out):
            boot, tost = d15mod.analyse()
    finally:
        d15mod.SOURCES.clear()
        d15mod.SOURCES.update(saved)
        shutil.rmtree(tmp_out, ignore_errors=True)
    suffix = arm + ("_11det" if with_ocsvm else "")
    boot.to_csv(_t(f"n20_d15_bootstrap_{suffix}.csv"), index=False)
    tost.to_csv(_t(f"n20_d15_tost_{suffix}.csv"), index=False)
    return boot, tost


def d15_replay_check(boot_old):
    pub = pd.read_csv(_t("d15_equivalence_bootstrap.csv"))
    m = pub.merge(boot_old, on=["dataset", "method"], suffixes=("_pub", "_replay"))
    dev = max(float((m[c + "_pub"] - m[c + "_replay"]).abs().max())
              for c in ("n_runs", "mean_diff_h", "ci_lo_h", "ci_hi_h"))
    out = pd.DataFrame([{"rows_pub": len(pub), "rows_replay": len(boot_old),
                         "rows_matched": len(m), "max_abs_dev": dev,
                         "verdicts_identical": bool((m["verdict_pub"]
                                                     == m["verdict_replay"]).all())}])
    out.to_csv(_t("n20_d15_replay_check.csv"), index=False)
    return out


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.WARNING)
    raw = raw_contrast()
    cells = manuscript_cells(raw)
    b_old, _ = d15("old")
    print(d15_replay_check(b_old).to_string(index=False))
    d15("new")
    d15("new", with_ocsvm=True)
    print("printed cells reproduced by old arm: %d / %d"
          % (int(cells["old_matches_print"].sum()), len(cells)))
    print("printed cells that move under the fix: %d" % int(cells["moves"].sum()))


if __name__ == "__main__":
    main()
