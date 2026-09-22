"""Assert that every number printed in the manuscript's result tables equals
the value in the released result file that backs it.

This is what makes the Data and Code Availability sentence "no number is
hand-edited" a checkable claim rather than an assertion. Run directly, or via
tests/test_table_numbers.py.

    python paper/verify_tables.py          # report, exit 1 on any mismatch

A printed value matches when round(source, d) == printed, where d is the number
of decimals the manuscript actually prints (LaTeX decoration stripped first).
"""
from __future__ import annotations

import csv
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
TABLES = ROOT / "results" / "tables"

BS = chr(92)
MINUS = chr(8722)


# ---------------------------------------------------------------- loading
def load(name):
    with open(TABLES / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------- provenance
# The N-20 fix (2026-09-17) changed the FEMTO, Ferrara and ONGC results and was
# a verified no-op on IMS and XJTU-SY. Every file produced before it is
# therefore invalid for FEMTO/Ferrara/ONGC. The N=44 sign-test family must be
# read from the post-fix rerun below, NEVER from the pre-fix D3 output
# d3_ocsvm_holm_N44_invariant.csv (now in superseded/).
HOLM_SOURCE = "n20_raw_contrast_old_vs_new.csv"


def load_holm_family():
    """The N=44 detector x dataset family as re-run after the N-20 fix."""
    rows = [r for r in load(HOLM_SOURCE)
            if r["arm"] == "new" and r["dataset"] != "ONGC"]
    for r in rows:                      # normalise to the legacy column names
        r.setdefault("median_diff", r["median_diff_h"])
        r.setdefault("n_runs", r["n_runs_tested"])
    return rows


def table_block(label):
    """LaTeX source of the float carrying \\label{<label>}."""
    src = TEX.read_text(encoding="utf-8")
    i = src.find(BS + "label{" + label + "}")
    if i < 0:
        raise AssertionError("no such label: " + label)
    return src[src.rfind(BS + "begin{table", 0, i):src.find(BS + "end{table", i)]


def rows_of(label):
    """Body rows of a tabular: split on &, drop rule-only lines."""
    out = []
    for line in table_block(label).split(chr(10)):
        line = line.strip()
        if "&" not in line or (BS + BS) not in line:
            continue
        out.append([c.strip() for c in line.split(BS + BS)[0].split("&")])
    return out


# -------------------------------------------------------------- cleaning
def plain(cell):
    """Strip LaTeX decoration so the bare printed value remains."""
    s = cell.replace(BS + "dagger", "").replace(BS + "ddagger", "")
    s = s.replace(BS + ",", "").replace(BS + " ", " ")
    s = s.replace("$", "").replace("{", "").replace("}", "")
    s = s.replace("^", "").replace(MINUS, "-")
    return s.strip()


def nums(cell):
    return [float(m) for m in re.findall(r"[+-]?\d+\.?\d*", plain(cell))]


def decimals(cell):
    """Decimals actually printed, after stripping decoration."""
    m = re.search(r"[+-]?\d+\.(\d+)", plain(cell))
    return len(m.group(1)) if m else 0


def matches(printed, expected, d):
    """True when `printed` is a correct d-decimal rendering of `expected`.

    Exact halfway values (e.g. 56.125 at 2 dp) have two defensible renderings
    depending on the rounding mode, so both are accepted.
    """
    if abs(round(expected, d) - printed) <= 1e-9:
        return True
    scaled = expected * (10 ** d)
    if abs(scaled - int(scaled) - 0.5) < 1e-9:          # exact tie
        lo, hi = int(scaled) / 10 ** d, (int(scaled) + 1) / 10 ** d
        return min(abs(printed - lo), abs(printed - hi)) <= 1e-9
    return False


def cmp_cell(label, cell, expected, bad):
    got = nums(cell)
    if not got:
        return 0
    if not matches(got[0], expected, decimals(cell)):
        bad.append((label, plain(cell), round(expected, decimals(cell))))
    return 1


# ------------------------------------------------------ method identity
def key_of(text):
    """Canonical detector key from either a LaTeX row label or a CSV method."""
    t = plain(text).split(" (")[0]
    t = t.replace(chr(963), "sigma").replace(chr(178), "2")
    t = re.sub(r"[^A-Za-z0-9]", "", t).lower()
    if t.startswith("3"):
        return "3sigma"
    for pref, canon in (("ewma", "ewma"), ("cusum", "cusum"),
                        ("hot", "hotelling"), ("iso", "isoforest"),
                        ("oneclass", "ocsvm"), ("deepsvdd", "deepsvdd"),
                        ("rmstrend", "rmstrend"), ("lstm", "lstmae"),
                        ("tcn", "tcnae"), ("transf", "transformerad")):
        if t.startswith(pref):
            return canon
    return None


def index(rows, method_field="method", ds_field=None):
    out = {}
    for r in rows:
        k = key_of(r[method_field])
        if k is None:
            continue
        out[(r[ds_field], k) if ds_field else k] = r
    return out


# ------------------------------------------------- Table 4b: gap injection
GAP = {"3sigma": "three_sigma", "ewma": "ewma", "cusum": "cusum",
       "hotelling": "hotelling_t2", "isoforest": "isolation_forest"}
_GAPROWS = None


def gap_cell(ds, det, gap):
    """Table 4b basis: mean lead over runs that produced a VALID alarm, then
    averaged over the independent gap draws (defect D18).

    The released gap_injection.csv holds ONE draw per level, and its 5% cell for
    Hotelling T^2 on IMS (58.0 h) does not reproduce in any of five further
    draws. The manuscript states across-draw magnitudes, so this reads the
    multi-seed file.
    """
    global _GAPROWS
    if _GAPROWS is None:
        _GAPROWS = load("d18_gap_injection_multiseed.csv")
    per_seed = {}
    for r in _GAPROWS:
        if (r["dataset"] != ds or r["short_name"] != det
                or float(r["gap"]) != gap or r["valid"] != "True"):
            continue
        per_seed.setdefault(r["gap_seed"], []).append(float(r["lead"]))
    if not per_seed:
        return None
    return statistics.mean([statistics.mean(v) for v in per_seed.values()])


def check_gap(bad):
    n = 0
    grid = [("IMS", 0.0), ("IMS", 0.05), ("IMS", 0.2),
            ("XJTU-SY", 0.0), ("XJTU-SY", 0.05), ("XJTU-SY", 0.2)]
    for cells in rows_of("tab:robust"):
        if len(cells) != 7:
            continue
        k = key_of(cells[0])
        if k not in GAP:
            continue
        for idx, (ds, gap) in enumerate(grid, start=1):
            exp = gap_cell(ds, GAP[k], gap)
            if exp is not None:
                n += cmp_cell("T4b %s %s %g%%" % (k, ds, gap * 100), cells[idx], exp, bad)
    return n


# ------------------------------------------------------- Table 12: tradeoff
def check_tradeoff(bad):
    src = {}
    for fn in ("tradeoff_IMS.csv", "tradeoff_IMS_deepmodels.csv"):
        for r in load(fn):
            k = key_of(r["method"])
            if k:
                src[(k, float(r["percentile"]))] = (
                    float(r["lead_time_hours_mean"]), float(r["far_preonset_pct_mean"]))
    n = 0
    for cells in rows_of("tab:tradeoff"):
        if len(cells) != 7:
            continue
        k = key_of(cells[0])
        if k is None:
            continue
        for j, pct in enumerate((95.0, 99.0, 99.5)):
            if (k, pct) not in src:
                continue
            ld, far = src[(k, pct)]
            n += cmp_cell("T12 %s p%g Ld" % (k, pct), cells[1 + 2 * j], ld, bad)
            n += cmp_cell("T12 %s p%g FAR" % (k, pct), cells[2 + 2 * j], far, bad)
    return n


# --------------------------------------------------- Table 7: IMS run-level
def check_imssweep(bad):
    src = index(load("ims_runlevel_test_invariant.csv"))
    for r in load_holm_family():
        if r["dataset"] == "IMS":
            src.setdefault(key_of(r["method"]), r)
    n = 0
    for cells in rows_of("tab:imssweep"):
        if len(cells) != 5:
            continue
        k = key_of(cells[0])
        row = src.get(k)
        if row is None:
            continue
        printed = nums(cells[1])
        actual = [float(x) for x in row["run_diffs"].replace("+", "").split(",")]
        for a, b in zip(printed, actual):
            if abs(round(b, 1) - a) > 1e-9:
                bad.append(("T7 %s run diff" % k, str(a), round(b, 1)))
            n += 1
        n += cmp_cell("T7 %s median" % k, cells[2], float(row["median_diff"]), bad)
        n += cmp_cell("T7 %s p" % k, cells[4], float(row["sign_test_p"]), bad)
    return n


# ------------------------------------------------------ Table 6: equivalence
def check_equiv(bad):
    src = index(load("n20_d15_bootstrap_new_11det.csv"), ds_field="dataset")
    n = 0
    for cells in rows_of("tab:equiv"):
        if len(cells) != 7:
            continue
        k = key_of(cells[0])
        if k is None:
            continue
        for j, ds in enumerate(("XJTU-SY", "FEMTO", "Ferrara")):
            row = src.get((ds, k))
            if row is None:
                continue
            n += cmp_cell("T6 %s %s mean" % (ds, k), cells[1 + 2 * j],
                          float(row["mean_diff_h"]), bad)
            got = nums(cells[2 + 2 * j])
            if len(got) < 2:
                continue
            d = decimals(cells[2 + 2 * j])
            for val, exp, tag in ((got[0], float(row["ci_lo_h"]), "lo"),
                                  (got[1], float(row["ci_hi_h"]), "hi")):
                if abs(round(exp, d) - val) > 1e-9:
                    bad.append(("T6 %s %s CI-%s" % (ds, k, tag), str(val), round(exp, d)))
                n += 1
    return n


# --------------------------------------------------------- Table 8: Holm
HOLM_COLS = ("IMS", "XJTU-SY", "FEMTO", "Ferrara")


def check_holm(bad):
    """Table 8 is a detector x dataset matrix of raw sign-test p-values."""
    rows = load_holm_family()
    src = index(rows, ds_field="dataset")
    n = 0
    for cells in rows_of("tab:holm"):
        if len(cells) != 5:
            continue
        k = key_of(cells[0])
        if k is None:
            continue
        for j, ds in enumerate(HOLM_COLS, start=1):
            row = src.get((ds, k))
            if row is None:
                continue
            n += cmp_cell("T8 %s %s raw p" % (ds, k), cells[j],
                          float(row["sign_test_p"]), bad)
    # the caption asserts every adjusted p is 1.00 and nothing is rejected
    if not all(abs(float(r["holm_p"]) - 1.0) < 1e-12 for r in rows):
        bad.append(("T8 caption: all Holm p == 1.00", "claimed", "violated"))
    n += 1
    if any(r["holm_reject"] == "True" for r in rows):
        bad.append(("T8 caption: no hypothesis rejected", "claimed", "violated"))
    n += 1
    if len(rows) != 44:
        bad.append(("T8 family size N=44", str(len(rows)), 44))
    n += 1
    # N-20 provenance guard: the post-fix family has no nominally significant
    # cell, and its smallest raw p is 0.125 on FEMTO/Transformer-AD. The
    # pre-fix D3 file gives 0.031 on FEMTO/Isolation Forest instead, so this
    # fails immediately if anyone re-points check_holm at a stale source.
    ps = [(float(r["sign_test_p"]), r["dataset"], r["method"]) for r in rows]
    lo = min(ps)
    if abs(lo[0] - 0.125) > 1e-12 or lo[1] != "FEMTO" or "Transformer" not in lo[2]:
        bad.append(("T8 N-20 provenance: smallest raw p",
                    "%.3f %s %s" % lo, "0.125 FEMTO Transformer-AD"))
    n += 1
    if [x for x in ps if x[0] < 0.05]:
        bad.append(("T8 N-20 provenance: no cell significant uncorrected",
                    str([x for x in ps if x[0] < 0.05]), "none"))
    n += 1
    return n


# ------------------------------------------------- Table 2: IMS lead + CI
def check_imslead(bad):
    """Full-resolution (factor 1, aggregate) mean lead and bootstrap CI."""
    src = {}
    for r in load("benchmark_IMS_leadtime_ci_invariant.csv"):
        if r["mode"] != "aggregate" or float(r["factor"]) != 1:
            continue
        k = key_of(r["method"])
        if k:
            src[k] = r
    n = 0
    for cells in rows_of("tab:imslead"):
        if len(cells) != 3:
            continue
        k = key_of(cells[0])
        row = src.get(k)
        if row is None:
            continue
        n += cmp_cell("T2 %s lead" % k, cells[1],
                      float(row["lead_time_hours_mean"]), bad)
        got, d = nums(cells[2]), decimals(cells[2])
        if len(got) >= 2:
            for val, exp, tag in ((got[0], float(row["lead_time_hours_lo"]), "lo"),
                                  (got[1], float(row["lead_time_hours_hi"]), "hi")):
                if not matches(val, exp, d):
                    bad.append(("T2 %s CI-%s" % (k, tag), str(val), round(exp, d)))
                n += 1
    return n


# --------------------------------------- Table 19: IMS under both labels
def collapse_runs(fn):
    """Run-level aggregate-minus-decimate, collapsing sampling factors (4.9)."""
    import collections
    pair = collections.defaultdict(dict)
    for r in load(fn):
        if r["dataset"] != "IMS":
            continue
        v = r["lead_time_hours"]
        if v in ("", "nan", "NaN"):
            continue
        pair[(key_of(r["method"]), r["run"], r["factor"])][r["mode"]] = float(v)
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for (k, run, _f), d in pair.items():
        if "aggregate" in d and "decimate" in d:
            per[k][run].append(d["aggregate"] - d["decimate"])
    return {k: {run: statistics.mean(v) for run, v in runs.items()}
            for k, runs in per.items()}


def check_d17label(bad):
    corrected = collapse_runs("benchmark_IMS_long_invariant.csv")
    original = collapse_runs("d17_ims_long_originallabel.csv")
    n = 0
    for cells in rows_of("tab:d17label"):
        if len(cells) != 9:
            continue
        k = key_of(cells[0])
        if k is None:
            continue
        for col, src, tag in ((1, corrected, "corrected"), (4, original, "original")):
            runs = src.get(k)
            if not runs:
                continue
            exp = [runs[r] for r in sorted(runs)]
            got, d = nums(cells[col]), decimals(cells[col])
            for a, b in zip(got, exp):
                if not matches(a, b, d):
                    bad.append(("T19 %s %s run diff" % (k, tag), str(a), round(b, d)))
                n += 1
    return n

# ================================================================ N-20 rule
# Defect N-20 (fixed 2026-09-17 21:56) changed ONLY the aggregate resampling
# interval, and only where the native spacing is sub-minute -- FEMTO, Ferrara
# and ONGC. src/sampling.py:166 records why factor 1 escapes it: "factor=1 is
# identical across modes (no downsampling)", so at factor 1 the resampler is
# never entered. The consequence, MEASURED by check_n20_rule below rather than
# assumed:
#
#     aggregate, factor 1   -> identical pre- and post-fix
#     decimate,  any factor -> identical pre- and post-fix
#     aggregate, factor > 1 -> changed
#
# So an artifact computed from factor-1 rows alone is N-20-invariant and its
# pre-fix file stays canonical; anything reading an aggregate row at factor > 1
# must come from the post-fix rerun. check_n20_rule re-measures the rule on
# every test run, so it cannot quietly stop holding under a regenerated file.
N20_ARMS = {
    "FEMTO":   ("benchmark_FEMTO_long.csv",   "n20_rerun_long_FEMTO_main.csv"),
    "Ferrara": ("benchmark_Ferrara_long.csv", "n20_rerun_long_Ferrara_main.csv"),
    "ONGC":    ("benchmark_ONGC_long.csv",    "n20_rerun_long_ONGC_main.csv"),
}
N20_KEY = ("dataset", "run", "seed", "short_name", "mode", "factor")
N20_METRICS = ("effective_interval_min", "lead_time_hours", "detection_delay_hours",
               "far_preonset_pct", "lead_norm", "valid_alarm")


def _n20_index(rows):
    return {tuple(r[k] for k in N20_KEY): r for r in rows}


def _same_cell(a, b):
    """Equality that tolerates float text and the True/False valid_alarm column."""
    if a == b:
        return True
    try:
        fa, fb = float(a), float(b)
    except ValueError:
        return False
    if fa != fa and fb != fb:          # NaN == NaN for our purpose
        return True
    return abs(fa - fb) <= 1e-9


def check_n20_rule(bad):
    """Re-measure the N-20 invariance rule the MANIFEST relies on."""
    n = 0
    for ds, (pre_f, post_f) in sorted(N20_ARMS.items()):
        pre, post = _n20_index(load(pre_f)), _n20_index(load(post_f))
        shared = sorted(set(pre) & set(post))
        if not shared:
            bad.append(("N-20 rule %s: no comparable rows" % ds, "0", "600 or 100"))
            continue
        groups = {}
        for k in shared:
            mode, factor = k[4], int(float(k[5]))
            diff = sum(0 if _same_cell(pre[k][c], post[k][c]) else 1 for c in N20_METRICS)
            g = groups.setdefault((mode, factor), [0, 0])
            g[0] += 1
            g[1] += diff
        for (mode, factor), (cells, diffs) in sorted(groups.items()):
            invariant_expected = (factor == 1) or (mode == "decimate")
            if invariant_expected and diffs:
                bad.append(("N-20 rule %s %s f=%d must be invariant" % (ds, mode, factor),
                            "%d differing values" % diffs, "0"))
            if not invariant_expected and diffs == 0:
                bad.append(("N-20 rule %s %s f=%d must have changed" % (ds, mode, factor),
                            "0 differing values", "> 0"))
            n += 1
    return n


# --------------------------------------- FEMTO valid-alarm count (Section 6.2)
# "Across all eleven evaluated detectors ... 211/660 evaluations yield a valid
# alarm" spans BOTH modes and ALL five factors, so it is NOT factor-1 only and
# must come from the post-fix rerun. The pre-fix pair (ten detectors in
# benchmark_FEMTO_long.csv plus one-class SVM in d3_ocsvm_benchmark_long.csv)
# gives 193/660 instead -- the guard below fails if anyone re-points this at it.
FEMTO_VALID_SOURCE = "n20_rerun_long_FEMTO.csv"
FEMTO_VALID_PREFIX_PAIR = ("benchmark_FEMTO_long.csv", "d3_ocsvm_benchmark_long.csv")


def _count_valid(rows, dataset=None):
    rows = [r for r in rows if dataset is None or r["dataset"] == dataset]
    return sum(1 for r in rows if r["valid_alarm"] in ("True", "true", "1")), len(rows)


def check_femto_valid(bad):
    got, total = _count_valid(load(FEMTO_VALID_SOURCE))
    n = 0
    for printed, expected, label in ((211, got, "valid alarms"), (660, total, "evaluations")):
        if printed != expected:
            bad.append(("S6.2 FEMTO %s" % label, str(printed), expected))
        n += 1
    dets = len({r["short_name"] for r in load(FEMTO_VALID_SOURCE)})
    if dets != 11:
        bad.append(("S6.2 FEMTO detector count", str(dets), 11))
    n += 1
    # provenance guard: the superseded pre-fix pair gives 193/660, not 211/660
    v1, t1 = _count_valid(load(FEMTO_VALID_PREFIX_PAIR[0]))
    v2, t2 = _count_valid(load(FEMTO_VALID_PREFIX_PAIR[1]), dataset="FEMTO")
    if (v1 + v2, t1 + t2) != (193, 660):
        bad.append(("S6.2 N-20 provenance: pre-fix pair fingerprint",
                    "%d/%d" % (v1 + v2, t1 + t2), "193/660"))
    n += 1
    if v1 + v2 == got:
        bad.append(("S6.2 N-20 provenance: arms must differ",
                    "pre-fix equals post-fix", "211 != 193"))
    n += 1
    return n


# ------------------------------- Table 5: FEMTO / Ferrara cross-dataset rows
# Ten detectors come from the post-fix run-level files; the eleventh (one-class
# SVM) from the post-fix raw contrast, arm "new". Every one of these rows
# collapses over BOTH modes and ALL five factors, so none is factor-1 only and
# none may be read from a pre-fix file.
CROSSDS_SOURCES = {"FEMTO": "femto_runlevel_test_n20.csv",
                   "Ferrara": "ferrara_runlevel_test_n20.csv"}
CROSSDS_OCSVM = "n20_raw_contrast_old_vs_new.csv"


def _crossds_src():
    src = {}
    for ds, fname in CROSSDS_SOURCES.items():
        for r in load(fname):
            k = key_of(r["method"])
            if k:
                src[(ds, k)] = (float(r["median_diff"]), r["n_pos"], r["n_neg"],
                                r["all_same_sign"], float(r["sign_test_p"]))
    for r in load(CROSSDS_OCSVM):
        if r["arm"] == "new" and r["dataset"] in CROSSDS_SOURCES and key_of(r["method"]) == "ocsvm":
            src[(r["dataset"], "ocsvm")] = (float(r["median_diff_h"]), r["n_pos"], r["n_neg"],
                                            r["all_same_sign"], float(r["sign_test_p"]))
    return src


def _crossds_rows():
    """Table 5 rows, with the dataset each belongs to.

    The multirow cells embed a line break inside shortstack, which would
    truncate the row, so that inner break is neutralised before splitting.
    """
    out, ds = [], None
    inner = BS + BS + "("
    for line in table_block("tab:crossds").split(chr(10)):
        line = line.strip()
        if line.startswith(BS + "multirow"):
            for cand in ("XJTU-SY", "FEMTO", "Ferrara", "IMS"):
                if cand + inner in line or cand + BS + BS in line:
                    ds = cand
            line = line.replace(inner, "(")
        if "&" not in line or (BS + BS) not in line:
            continue
        cells = [c.strip() for c in line.split(BS + BS)[0].split("&")]
        if len(cells) == 6:
            out.append((ds, cells[1:]))
    return out


def check_crossds(bad):
    src = _crossds_src()
    n = 0
    for ds, cells in _crossds_rows():
        k = key_of(cells[0])
        if ds not in CROSSDS_SOURCES or k is None:
            continue
        exp = src.get((ds, k))
        if exp is None:
            bad.append(("T5 %s %s missing in post-N-20 source" % (ds, k), "row present", "absent"))
            continue
        med, npos, nneg, same, p = exp
        n += cmp_cell("T5 %s %s median" % (ds, k), cells[1], med, bad)
        printed_counts = plain(cells[2])
        if printed_counts != "%s/%s" % (npos, nneg):
            bad.append(("T5 %s %s n+/n-" % (ds, k), printed_counts, "%s/%s" % (npos, nneg)))
        n += 1
        # The cell is "yes"/"no", and a sign-consistent cell may carry a
        # superscript direction marker ("yes$^{-}$"), which plain() renders as
        # a trailing - or +. Both the verdict and the marker are checked.
        printed_same = plain(cells[3]).lower()
        marker = ""
        if printed_same[-1:] in ("-", "+"):
            printed_same, marker = printed_same[:-1], printed_same[-1:]
        expect_same = "yes" if same in ("True", "true") else "no"
        if printed_same != expect_same:
            bad.append(("T5 %s %s sign-consistent" % (ds, k), printed_same, expect_same))
        n += 1
        if marker:
            want = "-" if med < 0 else "+"
            if marker != want:
                bad.append(("T5 %s %s direction marker" % (ds, k), marker, want))
            n += 1
        elif expect_same == "yes":
            bad.append(("T5 %s %s direction marker" % (ds, k), "absent", "- or +"))
            n += 1
        n += cmp_cell("T5 %s %s sign-test p" % (ds, k), cells[4], p, bad)
    if n == 0:
        bad.append(("T5 FEMTO/Ferrara rows parsed", "0", "> 0"))
    return n


# ---------------------------------------------- Table 10: gated contrast
# Caption already says "on the post-N-20 reruns over all eleven detectors".
# Every column collapses over both modes and all five factors.
GATED_SOURCE = "rf2_gated_contrast_n20.csv"
GATED_ORDER = ("XJTU-SY", "FEMTO", "Ferrara", "IMS")


def _gated_stats(metric):
    out = {}
    for ds in GATED_ORDER:
        rows = [r for r in load(GATED_SOURCE)
                if r["dataset"] == ds and r["metric"] == metric]
        if not rows:
            continue
        meds = sorted(float(r["median_diff_h"]) for r in rows)
        out[ds] = (statistics.median(meds),
                   sum(1 for v in meds if v > 0),
                   sum(1 for v in meds if v < 0),
                   sum(1 for v in meds if v == 0),
                   sum(float(r["n_effective"]) for r in rows) / len(rows),
                   len(rows))
    return out


def check_gatedcontrast(bad):
    metric, n = None, 0
    seen = set()
    for line in table_block("tab:gatedcontrast").split(chr(10)):
        line = line.strip()
        if "Raw lead time" in line:
            metric = "raw"
            continue
        if "Gated lead time" in line:
            metric = "gated_D7"
            continue
        if metric is None or "&" not in line or (BS + BS) not in line:
            continue
        cells = [c.strip() for c in line.split(BS + BS)[0].split("&")]
        if len(cells) != 4 or cells[0] not in GATED_ORDER:
            continue
        ds = cells[0]
        exp = _gated_stats(metric).get(ds)
        if exp is None:
            bad.append(("T10 %s %s missing in source" % (metric, ds), "row present", "absent"))
            continue
        med, npos, nneg, nzero, neff, ndet = exp
        seen.add((metric, ds))
        n += cmp_cell("T10 %s %s median" % (metric, ds), cells[1], med, bad)
        printed = plain(cells[2])
        want = "%d/%d/%d" % (npos, nneg, nzero)
        if printed != want:
            bad.append(("T10 %s %s n+/n-/0" % (metric, ds), printed, want))
        n += 1
        n += cmp_cell("T10 %s %s n_eff" % (metric, ds), cells[3], neff, bad)
        if ndet != 11:
            bad.append(("T10 %s %s detector count" % (metric, ds), str(ndet), 11))
        n += 1
    if len(seen) != 8:
        bad.append(("T10 rows parsed", str(len(seen)), 8))
    return n


# ------------------------- Figure 4c/4d: FEMTO and ONGC conformal calibration
# calibration_{FEMTO,ONGC}[_pooled].csv predate the N-20 fix but are invariant
# under it for a reason stronger than the factor-1 rule: src/calibration.py
# calls load_pipeline WITHOUT downsample arguments, so it runs at the defaults
# downsample_mode="none", downsample_factor=1 and never enters the resampling
# code the fix changed. The structural guard below asserts that: the files carry
# no mode or factor column at all, so no resampled row can reach them. If a
# future rerun ever adds one, this fails and the invariance claim must be redone.
CALIB_INVARIANT = ("calibration_FEMTO.csv", "calibration_FEMTO_pooled.csv",
                   "calibration_ONGC.csv", "calibration_ONGC_pooled.csv")


def check_calibration_invariance(bad):
    n = 0
    for fname in CALIB_INVARIANT:
        cols = {c.lower() for c in load(fname)[0]}
        leaked = cols & {"mode", "factor", "effective_interval_min"}
        if leaked:
            bad.append(("Fig4 N-20 invariance: %s is resample-free" % fname,
                        "has " + ",".join(sorted(leaked)), "no mode/factor column"))
        n += 1
    # Section 6.11 prose: FEMTO pre-onset FAR 0.08--0.56 at alpha=0.05, pooled 0.27
    at05 = [float(r["empirical_far"]) for r in load("calibration_FEMTO.csv")
            if abs(float(r["alpha"]) - 0.05) < 1e-9]
    if len(at05) != 6:
        bad.append(("S6.11 FEMTO bearings at alpha=0.05", str(len(at05)), 6))
    n += 1
    for printed, got, label in ((0.08, min(at05), "FAR lower"), (0.56, max(at05), "FAR upper")):
        if not matches(printed, got, 2):
            bad.append(("S6.11 FEMTO %s" % label, str(printed), round(got, 2)))
        n += 1
    pooled = {float(r["alpha"]): float(r["empirical_far_mean"])
              for r in load("calibration_FEMTO_pooled.csv")}
    if not matches(0.27, pooled[0.05], 2):
        bad.append(("S6.11 FEMTO pooled FAR", "0.27", round(pooled[0.05], 2)))
    n += 1
    # Section 6.11 prose: ONGC empirical FAR 0.016, 0.030, 0.096 at alpha 0.01/0.02/0.05
    ongc = {float(r["alpha"]): float(r["empirical_far"]) for r in load("calibration_ONGC.csv")}
    for alpha, printed in ((0.01, 0.016), (0.02, 0.030), (0.05, 0.096)):
        if not matches(printed, ongc[alpha], 3):
            bad.append(("S6.11 ONGC FAR at alpha=%.2f" % alpha, str(printed), round(ongc[alpha], 3)))
        n += 1
    return n


# ------------------------------------------- Table 23: ONGC median difference
# Table 23 reports the POST-fix per-detector medians, column new_min. The same
# file keeps the pre-fix column old_min, whose largest magnitude is 4.5 min --
# which would falsify the caption "All differences are about a minute or less".
# The guard pins both, so reading the wrong column fails loudly.
ONGC_MINUTES = "n20_ongc_minutes.csv"
ONGC_MINUTES_COL = "new_min"          # post-fix column; "old_min" is the pre-fix arm
ONGC_ROW_KEYS = {"3sigma": "three_sigma", "ewma": "ewma", "hotelling": "hotelling_t2",
                 "isoforest": "isolation_forest", "rmstrend": "rms_trend"}


def check_ongc_minutes(bad):
    rows = {r["short_name"]: r for r in load(ONGC_MINUTES)}
    n = 0
    for cells in rows_of("tab:ongc"):
        if len(cells) != 2:
            continue
        k = key_of(cells[0])
        name = ONGC_ROW_KEYS.get(k)
        if name is None:
            continue
        n += cmp_cell("T23 ONGC %s median" % k, cells[1], float(rows[name][ONGC_MINUTES_COL]), bad)
    if n != 5:
        bad.append(("T23 rows parsed", str(n), 5))
    new_max = max(abs(float(r[ONGC_MINUTES_COL])) for r in rows.values())
    old_max = max(abs(float(r["old_min"])) for r in rows.values())
    if new_max > 1.5:
        bad.append(("T23 caption: about a minute or less", "%.2f min" % new_max, "<= 1.5 min"))
    n += 1
    # provenance guard: the pre-fix column must still be the one that breaks the caption
    if old_max <= 1.5:
        bad.append(("T23 N-20 provenance: old_min fingerprint", "%.2f min" % old_max, "> 1.5 min"))
    n += 1
    return n


CHECKS = [("Table 2 IMS lead + CI", check_imslead),
          ("Table 19 label contrast", check_d17label),
          ("Table 4b gap injection", check_gap),
          ("Table 6 equivalence", check_equiv),
          ("Table 7 IMS run-level", check_imssweep),
          ("Table 8 Holm", check_holm),
          ("Table 12 trade-off", check_tradeoff),
          ("Table 5 cross-dataset", check_crossds),
          ("Table 10 gated contrast", check_gatedcontrast),
          ("Table 23 ONGC minutes", check_ongc_minutes),
          ("Fig 4 calibration", check_calibration_invariance),
          ("S6.2 FEMTO valid alarms", check_femto_valid),
          ("N-20 invariance rule", check_n20_rule)]

def run(verbose=True):
    bad, total = [], 0
    for name, fn in CHECKS:
        before = len(bad)
        cnt = fn(bad)
        total += cnt
        if verbose:
            state = "OK" if len(bad) == before else "%d MISMATCH" % (len(bad) - before)
            print("  %-26s %4d values  %s" % (name, cnt, state))
    if verbose:
        print("  %-26s %4d values checked" % ("TOTAL", total))
    return bad


if __name__ == "__main__":
    print("Verifying manuscript table numbers against released result files")
    problems = run()
    if problems:
        print(chr(10) + "MISMATCHES:")
        for label, printed, expected in problems:
            print("   %-34s printed %-12s source %s" % (label, printed, expected))
        sys.exit(1)
    print(chr(10) + "All checked table numbers match their source files.")
