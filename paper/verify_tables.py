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
from decimal import ROUND_HALF_EVEN, Decimal
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


def tex_source():
    """Manuscript source with generated tables (\\input{gen/...}) expanded in place."""
    src = TEX.read_text(encoding="utf-8")
    return re.sub(r"\\input\{(gen/[^}]+)\}",
                  lambda m: (TEX.parent / (m.group(1) + ".tex")).read_text(encoding="utf-8"), src)


def table_block(label):
    """LaTeX source of the float carrying \\label{<label>}."""
    src = tex_source()
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
                        ("oneclass", "ocsvm"), ("ocsvm", "ocsvm"), ("deepsvdd", "deepsvdd"),
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

    Validity is Eq. 5: a row whose pre-onset FAR is undefined (empty pre-onset
    region) is not scoreable and never enters the mean, although the released
    `valid` column -- which follows the implementation -- marks it True.
    """
    global _GAPROWS
    if _GAPROWS is None:
        _GAPROWS = load("d18_gap_injection_multiseed.csv")
    per_seed = {}
    for r in _GAPROWS:
        if (r["dataset"] != ds or r["short_name"] != det
                or float(r["gap"]) != gap or not eq5_row(r, "lead")[1]):
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
            label = "T4b %s %s %g%%" % (k, ds, gap * 100)
            if exp is not None:
                n += cmp_cell(label, cells[idx], exp, bad)
            else:                       # no Eq.-5-valid alarm: the table must print "--"
                n += 1
                if plain(cells[idx]) != "--":
                    bad.append((label, plain(cells[idx]), "--"))
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
# ====================================================== Phase 1 consolidated tables
# The shortened manuscript (2026-09-23) merges Tables 2/12/15 -> tab:imsdet,
# 5/6/8 -> tab:crossds, 7/23 -> tab:imsongc, 21/22 -> tab:mechanism and
# 16/17 -> tab:hyperparams, and moves Table 11 into the fig:conformal caption.
# Every printed value is re-derived here from the MANIFEST source files.
RUNLEVEL = {"XJTU-SY": "xjtu_sy_runlevel_test.csv",      # N-20 no-op dataset
            "FEMTO": "femto_runlevel_test_n20.csv",      # post-fix (N-20)
            "Ferrara": "ferrara_runlevel_test_n20.csv",  # post-fix (N-20)
            "IMS": "ims_runlevel_test_invariant.csv"}    # N-20 no-op, D-2 invariant schema
ONGC_ROW_KEYS = {"3sigma": "three_sigma", "ewma": "ewma", "cusum": "cusum",
                 "hotelling": "hotelling_t2", "isoforest": "isolation_forest",
                 "deepsvdd": "deep_svdd", "ocsvm": "one_class_svm", "lstmae": "lstm_ae",
                 "tcnae": "tcn", "transformerad": "transformer_ad", "rmstrend": "rms_trend"}


def _runlevel_src():
    src = {}
    for ds, fname in RUNLEVEL.items():
        for r in load(fname):
            k = key_of(r["method"])
            if k:
                src[(ds, k)] = dict(med=float(r["median_diff"]), npos=r["n_pos"], nneg=r["n_neg"],
                                    same=r["all_same_sign"] in ("True", "true"),
                                    p=float(r["sign_test_p"]), runs=r["run_diffs"])
    for r in load_holm_family():                 # one-class SVM rows, post-fix arm
        if key_of(r["method"]) == "ocsvm":
            src[(r["dataset"], "ocsvm")] = dict(
                med=float(r["median_diff_h"]), npos=r["n_pos"], nneg=r["n_neg"],
                same=r["all_same_sign"] in ("True", "true"), p=float(r["sign_test_p"]),
                runs=r["run_diffs"])
    return src


def _block_rows(label, ncols):
    """(block, cells) for a tabular whose blocks start with \\multicolumn{..}{l}{\\emph{name}}."""
    out, blk = [], None
    for line in table_block(label).split(chr(10)):
        line = line.strip()
        mm = re.match(r"\\multicolumn\{\d+\}\{l\}\{\\emph\{([^}]*)\}", line)
        if mm:
            blk = mm.group(1)
            continue
        if "&" not in line or (BS + BS) not in line:
            continue
        cells = [c.strip() for c in line.split(BS + BS)[0].split("&")]
        if len(cells) == ncols:
            out.append((blk, cells))
    return out


def _counts(cell):
    """'3/0$^{\\mathrm{s}}$' -> ('3', '0', sign-consistent marker present)."""
    marked = "mathrm{s}" in cell
    c = cell.replace("$^{" + BS + "mathrm{s}}$", "").replace("$^" + BS + "ast$", "")
    a, b = plain(c).split("/")
    return a.strip(), b.strip(), marked


def check_crossds(bad):
    """tab:crossds -- XJTU-SY (guard added 2026-09-23), FEMTO and Ferrara x 11 detectors:
    median, mean and 95% CI, n+/n-, sign-consistency marker, sign-test p."""
    src = _runlevel_src()
    eq = {k: v for k, v in index(load("n20_d15_bootstrap_new_11det.csv"), ds_field="dataset").items()
          if k[0] in ("XJTU-SY", "FEMTO", "Ferrara")}
    n, seen = 0, set()
    for ds, cells in _block_rows("tab:crossds", 5):
        k = key_of(cells[0])
        if k is None or ds not in ("XJTU-SY", "FEMTO", "Ferrara"):
            continue
        s, e = src.get((ds, k)), eq.get((ds, k))
        tag = "T5 %s %s" % (ds, k)
        if s is None or e is None:
            bad.append((tag + " missing in source", "row present", "absent"))
            continue
        seen.add((ds, k))
        n += cmp_cell(tag + " median", cells[1], s["med"], bad)
        got, d = nums(cells[2]), decimals(cells[2])
        exp = (float(e["mean_diff_h"]), float(e["ci_lo_h"]), float(e["ci_hi_h"]))
        if len(got) != 3:
            bad.append((tag + " mean/CI parse", str(got), "3 values"))
        for val, x, t in zip(got, exp, ("mean", "CI-lo", "CI-hi")):
            if not matches(val, x, d):
                bad.append((tag + " " + t, str(val), round(x, d)))
            n += 1
        if not (-1.0 < exp[1] and exp[2] < 1.0):
            bad.append((tag + " equivalent at delta=1 h", "claimed", "violated"))
        n += 1
        a, b, marked = _counts(cells[3])
        if (a, b) != (s["npos"], s["nneg"]):
            bad.append((tag + " n+/n-", a + "/" + b, s["npos"] + "/" + s["nneg"]))
        n += 1
        if marked != s["same"]:
            bad.append((tag + " sign-consistent marker", str(marked), str(s["same"])))
        n += 1
        n += cmp_cell(tag + " sign-test p", cells[4], s["p"], bad)
    if len(seen) != 33:
        bad.append(("T5 rows parsed", str(len(seen)), 33))
    widest = max(max(abs(float(r["ci_lo_h"])), abs(float(r["ci_hi_h"]))) for r in eq.values())
    if widest >= 0.6:
        bad.append(("T5 caption: no endpoint reaches 0.6 h", "%.3f" % widest, "< 0.6"))
    return n + 1


def check_imsongc(bad):
    """tab:imsongc -- IMS per-run differences, median, n+/n-, p; ONGC post-fix minutes."""
    src = _runlevel_src()
    ongc = {r["short_name"]: r for r in load(ONGC_MINUTES)}
    n, seen = 0, 0
    for _, cells in _block_rows("tab:imsongc", 6):
        k = key_of(cells[0])
        if k is None:
            continue
        s, tag = src[("IMS", k)], "T6 IMS %s" % k
        seen += 1
        got = nums(cells[1])
        actual = [float(x) for x in s["runs"].replace("+", "").split(",")]
        if len(got) != 3:
            bad.append((tag + " run diffs parse", str(got), "3 values"))
        for a, b in zip(got, actual):
            if abs(round(b, 1) - a) > 1e-9:
                bad.append((tag + " run diff", str(a), round(b, 1)))
            n += 1
        n += cmp_cell(tag + " median", cells[2], s["med"], bad)
        a, b, marked = _counts(cells[3])
        if (a, b) != (s["npos"], s["nneg"]):
            bad.append((tag + " n+/n-", a + "/" + b, s["npos"] + "/" + s["nneg"]))
        # published IMS convention: tied runs are not sign-consistent (Deep SVDD)
        ties = sum(1 for v in actual if round(v, 1) == 0)
        if marked != (s["same"] and ties == 0):
            bad.append((tag + " sign-consistent marker", str(marked), str(s["same"] and ties == 0)))
        n += 2
        n += cmp_cell(tag + " sign-test p", cells[4], s["p"], bad)
        n += cmp_cell("T6 ONGC %s minutes" % k, cells[5],
                      float(ongc[ONGC_ROW_KEYS[k]][ONGC_MINUTES_COL]), bad)
    if seen != 11:
        bad.append(("T6 rows parsed", str(seen), 11))
    new_max = max(abs(float(r[ONGC_MINUTES_COL])) for r in ongc.values())
    old_max = max(abs(float(r["old_min"])) for r in ongc.values())
    if new_max > 1.5:
        bad.append(("T6 caption: ONGC about a minute or less", "%.2f min" % new_max, "<= 1.5 min"))
    if old_max <= 1.5:      # provenance: the pre-fix column must still break the caption
        bad.append(("T6 N-20 provenance: old_min fingerprint", "%.2f min" % old_max, "> 1.5 min"))
    return n + 2


def check_holm(bad):
    """The N=44 Holm family (now a tab:crossds caption sentence): the printed sign-test
    p of all 44 cells equals the post-fix family's raw p, every adjusted p is 1.00,
    nothing is rejected, and the smallest raw p is 0.125 (FEMTO, Transformer-AD)."""
    rows = load_holm_family()
    fam = {(r["dataset"], key_of(r["method"])): float(r["sign_test_p"]) for r in rows}
    printed = {}
    for ds, cells in _block_rows("tab:crossds", 5):
        if key_of(cells[0]):
            printed[(ds, key_of(cells[0]))] = cells[4]
    for _, cells in _block_rows("tab:imsongc", 6):
        if key_of(cells[0]):
            printed[("IMS", key_of(cells[0]))] = cells[4]
    n = 0
    for key, p in fam.items():
        if key not in printed:
            bad.append(("Holm family cell %s %s printed" % key, "absent", "present"))
            continue
        n += cmp_cell("Holm raw p %s %s" % key, printed[key], p, bad)
    for cond, label in ((len(rows) == 44, "family size N=44"),
                        (all(abs(float(r["holm_p"]) - 1.0) < 1e-12 for r in rows), "all adjusted p == 1.00"),
                        (not any(r["holm_reject"] == "True" for r in rows), "no hypothesis rejected"),
                        (not [r for r in rows if float(r["sign_test_p"]) < 0.05], "no raw p < 0.05")):
        if not cond:
            bad.append(("Holm caption: " + label, "claimed", "violated"))
        n += 1
    lo = min((float(r["sign_test_p"]), r["dataset"], r["method"]) for r in rows)
    if abs(lo[0] - 0.125) > 1e-12 or lo[1] != "FEMTO" or "Transformer" not in lo[2]:
        bad.append(("Holm N-20 provenance: smallest raw p", "%.3f %s %s" % lo, "0.125 FEMTO Transformer-AD"))
    return n + 1


def _imslead_src():
    src = {}
    for r in load("benchmark_IMS_leadtime_ci_invariant.csv"):
        if r["mode"] == "aggregate" and float(r["factor"]) == 1 and key_of(r["method"]):
            src[key_of(r["method"])] = r
    for r in load("d3_ocsvm_leadtime_ci.csv"):
        if (r["dataset"] == "IMS" and r["mode"] == "aggregate" and float(r["factor"]) == 1
                and key_of(r["method"]) == "ocsvm"):
            src["ocsvm"] = r
    return src


TRADEOFF_SOURCES = ("tradeoff_IMS.csv", "tradeoff_IMS_deepmodels.csv", "d3_ocsvm_tradeoff.csv")


def _tradeoff_src():
    src = {}
    for fn in TRADEOFF_SOURCES:
        for r in load(fn):
            k = key_of(r["method"])
            if k and r.get("dataset", "IMS") == "IMS":
                src[(k, float(r["percentile"]))] = (float(r["lead_time_hours_mean"]),
                                                    float(r["far_preonset_pct_mean"]))
    return src


def check_imsdet(bad):
    """tab:imsdet (old Tables 2, 12 and 15): raw lead + CI, PH, L at tau=.05/.10/.20 for all
    eleven IMS detectors. PH and L are ALSO re-derived from the threshold sweep, so the
    d9 file cannot drift from the trade-off table it summarises."""
    lead, trade = _imslead_src(), _tradeoff_src()
    d9 = {key_of(r["method"]): r for r in load("d9_tables_14_22_eleven.csv")}
    n, order = 0, []
    for cells in rows_of("tab:imsdet"):
        if len(cells) != 7 or key_of(cells[0]) is None:
            continue
        k = key_of(cells[0])
        tag, ld, r = "T2 %s" % k, lead[k], d9[k]
        order.append((k, float(r["PH_h"])))
        n += cmp_cell(tag + " raw lead", cells[1], float(ld["lead_time_hours_mean"]), bad)
        got, d = nums(cells[2]), decimals(cells[2])
        for val, x, t in zip(got, (float(ld["lead_time_hours_lo"]), float(ld["lead_time_hours_hi"])), ("lo", "hi")):
            if not matches(val, x, d):
                bad.append((tag + " CI-" + t, str(val), round(x, d)))
            n += 1
        sweep = [trade[(k, p)] for p in (95.0, 99.0, 99.5)]
        ph = max(x for x, _ in sweep)
        n += cmp_cell(tag + " PH", cells[3], float(r["PH_h"]), bad)
        if abs(ph - float(r["PH_h"])) > 1e-9:
            bad.append((tag + " PH != max swept lead", r["PH_h"], ph))
        n += 1
        for j, (col, tau) in enumerate((("L_tau05_h", 5), ("L_tau10_h", 10), ("L_tau20_h", 20))):
            n += cmp_cell(tag + " L tau=%d%%" % tau, cells[4 + j], float(r[col]), bad)
            ok = [x for x, far in sweep if far <= tau]
            if abs((max(ok) if ok else 0.0) - float(r[col])) > 1e-9:
                bad.append((tag + " L tau=%d%% re-derivation" % tau, r[col], max(ok) if ok else 0.0))
            n += 1
        if ("dagger" in cells[0]) != (float(r["L_tau10_h"]) == 0.0):
            bad.append((tag + " dagger iff no valid point at tau=0.10", cells[0], r["L_tau10_h"]))
        n += 1
    if len(order) != 11:
        bad.append(("T2 rows parsed", str(len(order)), 11))
    if [x for _, x in order] != sorted((x for _, x in order), reverse=True):
        bad.append(("T2 rows in PH order", str([k for k, _ in order]), "descending PH"))
    if [i for i, (k, _) in enumerate(order, 1) if k == "3sigma"] != [8]:
        bad.append(("T2 3-sigma is PH's eighth", str([k for k, _ in order]), "3sigma at 8"))
    if any(float(d9[k]["L_tau10_h"]) != 0.0 for k, _ in order[:7]):
        bad.append(("T2 top seven by PH all score L=0", "claimed", "violated"))
    return n + 3


def check_tradeoff(bad):
    src = _tradeoff_src()
    n, rows = 0, 0
    for cells in rows_of("tab:tradeoff"):
        if len(cells) != 7 or key_of(cells[0]) is None:
            continue
        k, rows = key_of(cells[0]), rows + 1
        for j, pct in enumerate((95.0, 99.0, 99.5)):
            ld, far = src[(k, pct)]
            n += cmp_cell("T12 %s p%g Ld" % (k, pct), cells[1 + 2 * j], ld, bad)
            n += cmp_cell("T12 %s p%g FAR" % (k, pct), cells[2 + 2 * j], far, bad)
            if ("dagger" in cells[2 + 2 * j]) != (far > 10.0):
                bad.append(("T12 %s p%g dagger" % (k, pct), cells[2 + 2 * j], far))
            n += 1
    if rows != 11:
        bad.append(("T12 rows parsed (eleven incl. one-class SVM)", str(rows), 11))
    return n


def check_gatedcontrast(bad):
    n, seen = 0, 0
    stats = {"raw": _gated_stats("raw"), "gated_D7": _gated_stats("gated_D7")}
    for cells in rows_of("tab:gatedcontrast"):
        if len(cells) != 7 or cells[0] not in GATED_ORDER:
            continue
        seen += 1
        for metric, off in (("raw", 1), ("gated_D7", 4)):
            med, npos, nneg, nzero, neff, ndet = stats[metric][cells[0]]
            tag = "T10 %s %s" % (metric, cells[0])
            n += cmp_cell(tag + " median", cells[off], med, bad)
            if plain(cells[off + 1]) != "%d/%d/%d" % (npos, nneg, nzero):
                bad.append((tag + " n+/n-/0", plain(cells[off + 1]), "%d/%d/%d" % (npos, nneg, nzero)))
            n += 1
            n += cmp_cell(tag + " n_eff", cells[off + 2], neff, bad)
            if ndet != 11:
                bad.append((tag + " detector count", str(ndet), 11))
            n += 1
    if seen != 4:
        bad.append(("T10 rows parsed", str(seen), 4))
    return n


DENOISE = {"Aggregate": "aggregate", "Decimate (raw)": "decimate", "Decimate + median": "median",
           "Decimate + moving avg": "moving_average", "Decimate + Kalman": "kalman",
           "Decimate + wavelet": "wavelet"}
MAG4 = {"three_sigma", "ewma", "cusum", "hotelling_t2"}


def check_mechanism(bad):
    """tab:mechanism (old Tables 21-22): noise-injection run-level diffs and the denoisers.
    Denoiser 'mean lead' is over ALL twelve chart-runs, valid or not (published convention);
    the aggregate and Kalman means are 75.6469 h, i.e. 75.6 -- the 75.7 once printed was a
    double rounding (defect N-29)."""
    noise = {("None (native)" if r["snr_db"] == "inf" else "%d dB" % float(r["snr_db"])): r
             for r in load("noise_snr_IMS_runlevel.csv")}
    den_rows = load("denoising_IMS.csv")
    n, seen = 0, 0
    for cells in rows_of("tab:mechanism"):
        if len(cells) == 4 and cells[0] in noise:
            r, tag, seen = noise[cells[0]], "T21 " + cells[0], seen + 1
            for a, b in zip(nums(cells[1]), [float(x) for x in r["run_diffs"].replace("+", "").split(",")]):
                if abs(round(b, 2) - a) > 1e-9:
                    bad.append((tag + " run diff", str(a), round(b, 2)))
                n += 1
            n += cmp_cell(tag + " mean", cells[2], float(r["mean_diff"]), bad)
            if plain(cells[3]) != "%s/3" % r["n_pos"]:
                bad.append((tag + " sign", plain(cells[3]), r["n_pos"] + "/3"))
            n += 1
        elif len(cells) == 3:
            key = next((v for lab, v in DENOISE.items() if cells[0].startswith(lab)), None)
            if key is None:
                continue
            sub = [r for r in den_rows if r["denoiser"] == key and r["short_name"] in MAG4]
            seen += 1
            n += cmp_cell("T22 %s mean lead" % key, cells[1],
                          statistics.mean(float(r["lead_time_hours"]) for r in sub), bad)
            nv = sum(1 for r in sub if r["valid_alarm"] == "True")
            if plain(cells[2]) != "%d/12" % nv or len(sub) != 12:
                bad.append(("T22 %s valid" % key, plain(cells[2]), "%d/12" % nv))
            n += 1
    if seen != 10:
        bad.append(("T21-22 rows parsed", str(seen), 10))
    return n


def _fmt_train(sec):
    if sec < 0.001:
        return "<1 ms"
    if sec < 0.1:
        return "%d ms" % round(sec * 1000)
    return ("%.2f s" if sec < 10 else "%.1f s") % sec


def check_compute(bad):
    """tab:hyperparams panel (b), old Table 17: training time and inference cost."""
    src = {}
    for fn in ("compute_cost_IMS_invariant.csv", "compute_cost_IMS_extra_invariant.csv"):
        for r in load(fn):
            src[key_of(r["method"])] = r
    n, seen = 0, 0
    for cells in rows_of("tab:hyperparams"):
        if len(cells) != 6:
            continue
        for off in (0, 3):
            k = key_of(cells[off]) if cells[off] else None
            if k is None or k not in src:
                continue
            r, seen = src[k], seen + 1
            if plain(cells[off + 1]) != _fmt_train(float(r["train_seconds"])):
                bad.append(("T17 %s train" % k, plain(cells[off + 1]), _fmt_train(float(r["train_seconds"]))))
            n += 1
            us = float(r["inference_us_per_window"])
            printed = nums(cells[off + 2])[0]
            if abs(printed - (round(us, 1) if us < 10 else round(us))) > 1e-9:
                bad.append(("T17 %s inference" % k, str(printed), us))
            n += 1
    if seen != 11:
        bad.append(("T17 detectors parsed", str(seen), 11))
    return n


def check_conformal_ims(bad):
    """fig:conformal caption, panel (a) values (old Table 11) from calibration_IMS.csv."""
    txt = (TEX.parent / "gen" / "conformal_values.tex").read_text(encoding="utf-8")
    if BS + "ConformalPanelA" not in tex_source().split(BS + "begin{document}")[1]:
        bad.append(("Fig4 caption uses the generated panel-(a) values", "absent", "present"))
    rows = load("calibration_IMS.csv")
    n = 1
    for run, lab in (("1st_test", "test 1"), ("2nd_test", "test 2"), ("3rd_test", "test 3")):
        seg = txt.split(lab, 1)[1].split(";")[0]
        got = [float(x) for x in re.findall(r"\d+\.\d+", seg)]
        exp = [next(float(r["empirical_far"]) for r in rows
                    if r["run"] == run and abs(float(r["alpha"]) - a) < 1e-9)
               for a in (0.01, 0.05, 0.10, 0.20)]
        if len(got) != 4:
            bad.append(("Fig4a %s parse" % lab, str(got), "4 values"))
        for g, e in zip(got, exp):
            if not matches(g, e, 2):
                bad.append(("Fig4a %s FAR" % lab, str(g), round(e, 2)))
            n += 1
    return n


def check_prose_additions(bad):
    """Numbers stated in prose by the shortening pass (G3, D18, ONGC, N-29)."""
    body = tex_source()
    n = 0

    def need(cond, label, printed="", expected=""):
        nonlocal n
        n += 1
        if not cond:
            bad.append(("prose: " + label, printed, expected))

    g3 = load("rg3_raw_invariance.csv")
    need(len(g3) == 99, "G3 99 dataset x detector x indicator cells", str(len(g3)), 99)
    need(max(abs(float(r["max_abs_dev_run_diff_h"])) for r in g3) == 0.0, "G3 max |deviation| 0.000 h")
    need(sum(int(r["row_nan_mismatch"]) for r in g3) == 0, "G3 no NaN mismatch")
    need("0.000~h across all 99 dataset" in body, "G3 sentence present")
    # D18: Hotelling T2 on IMS across the five gap draws
    gaps = load("d18_gap_injection_multiseed.csv")
    base = {r["run"]: float(r["lead"]) for r in gaps
            if r["dataset"] == "IMS" and r["short_name"] == "hotelling_t2" and float(r["gap"]) == 0.0}
    per = {}
    for r in gaps:
        if r["dataset"] == "IMS" and r["short_name"] == "hotelling_t2" and float(r["gap"]) == 0.2:
            per.setdefault(r["gap_seed"], {})[r["run"]] = (float(r["lead"]), r["valid"] == "True")
    means = [statistics.mean(v for v, ok in d.values() if ok) for d in per.values()]
    collapsed = [s for s, d in per.items() if abs(d["3rd_test"][0] - base["3rd_test"]) > 1.0]
    changed = {run for d in per.values() for run, (v, _) in d.items() if abs(v - base[run]) > 1e-9}
    need(len(collapsed) == 2 and len(per) == 5, "D18 collapses in 2 of 5 draws", str(len(collapsed)), 2)
    need(changed == {"3rd_test"}, "D18 driven by a single run", str(changed), "{3rd_test}")
    for v, label in ((statistics.mean(means), "134.9"), (min(means), "58.0"), (max(means), "186.1"),
                     (base["3rd_test"], "315.9"), (min(d["3rd_test"][0] for d in per.values()), "59.7")):
        need(abs(round(v, 1) - float(label)) < 1e-9, "D18 value " + label, "%.1f" % v, label)
    worst, frozen = 0.0, []
    for det in ("three_sigma", "ewma", "cusum", "hotelling_t2", "isolation_forest"):
        b = gap_cell("IMS", det, 0.0)
        seeds = {}
        for r in gaps:
            if (r["dataset"] == "IMS" and r["short_name"] == det and float(r["gap"]) == 0.05
                    and r["valid"] == "True"):
                seeds.setdefault(r["gap_seed"], []).append(float(r["lead"]))
        dev = max(abs(statistics.mean(v) - b) for v in seeds.values())
        worst = max(worst, dev)
        if dev == 0.0:
            frozen.append(det)
    need(sorted(frozen) == ["ewma", "hotelling_t2"], "D18 5%: Hotelling and EWMA unchanged", str(frozen))
    need(abs(round(worst, 2) - 0.83) < 1e-9, "D18 5%: max per-draw deviation 0.83 h", "%.3f" % worst, "0.83")
    need("collapses in 2 of the 5 draws" in body, "D18 sentence present")
    # ONGC case study: factor-1 leads from the post-fix rerun (factor 1 is N-20-invariant anyway)
    lead = {r["short_name"]: float(r["lead_time_hours"]) for r in load("n20_rerun_long_ONGC.csv")
            if float(r["factor"]) == 1 and r["mode"] == "aggregate"}
    need(len(lead) == 11 and len([v for v in lead.values() if 30.0 <= round(v, 1) <= 35.5]) == 9,
         "ONGC nine of eleven alarm 30-35 h")
    need(len([v for v in lead.values() if 34.9 <= round(v, 1) <= 35.3]) == 7, "ONGC seven within 34.9-35.3 h")
    for k, v in (("cusum", 33.9), ("hotelling_t2", 30.4), ("rms_trend", 22.8), ("deep_svdd", 0.0)):
        need(abs(round(lead[k], 1) - v) < 1e-9, "ONGC %s lead %.1f h" % (k, v), "%.1f" % lead[k], v)
    need("every detector achieves a long warning" not in body, "ONGC overclaim removed")
    # ONGC gating (final pass): only Hotelling T2 and RMS-trend are valid at tau = 10%
    ong = {r["short_name"]: r for r in load("n20_rerun_long_ONGC.csv")
           if float(r["factor"]) == 1 and r["mode"] == "aggregate"}
    valid = sorted(k for k, r in ong.items() if r["valid_alarm"] in ("True", "true", "1"))
    need(valid == ["hotelling_t2", "rms_trend"], "ONGC valid at tau=10%: Hotelling T2 and RMS-trend only", str(valid))
    far = {k: float(r["far_preonset_pct"]) for k, r in ong.items()}
    inval = [k for k in ong if k not in valid and float(ong[k]["lead_time_hours"]) > 0]
    need(len(inval) == 8, "ONGC eight alarming detectors invalid", str(len(inval)), 8)
    for v, label in ((far["hotelling_t2"], "6.5"), (far["rms_trend"], "0.1"),
                     (min(far[k] for k in inval), "11.7"), (max(far[k] for k in inval), "95.2")):
        need(abs(round(v, 1) - float(label)) < 1e-9, "ONGC pre-onset FAR " + label, "%.2f" % v, label)
    need(min(inval, key=lambda k: far[k]) == "isolation_forest" and max(inval, key=lambda k: far[k]) == "cusum",
         "ONGC FAR range endpoints Isolation Forest / CUSUM")
    gap = float(load("ongc_onset_markers.csv")[0]["max_lead_hours"])
    need(round(gap) == 6, "ONGC onset ~6 h before shutdown", "%.2f" % gap, 6)
    early = [float(ong[k]["lead_time_hours"]) - gap for k in inval]
    need(round(min(early)) == 28 and round(max(early)) == 29, "ONGC invalid alarms precede onset by 28-29 h",
         "%.1f-%.1f" % (min(early), max(early)), "28-29")
    need("only Hotelling $T^2$ (pre-onset FAR 6.5" in body, "ONGC gating sentence present (App. D.2)")
    need("only Hotelling $T^2$ and RMS-trend are valid" in body, "ONGC gating sentence present (Sec. 7.2)")
    need("aggregation's 75.6~h" in body and "75.7" not in body, "N-29 corrected 75.6 in prose")
    return n


# ------------------------------------------------ Eq. 5 validity counts (final pass)
# The released valid_alarm column follows the implementation, which counts an alarm
# valid when its pre-onset FAR is undefined and scores a no-onset run by a positional
# fallback. The manuscript's counts apply Eq. 5 through src/eq5_validity.py. This
# check re-derives every restated count here, independently of that script, and then
# asserts the script's outputs agree.
NA = ("", "nan", "NaN", "NaT", "None")


def eq5_row(r, lead="lead_time_hours"):
    """(scoreable, valid, empty_pre, no_onset) for one row under Eq. 5."""
    has_lead = r[lead] not in NA
    no_onset = r.get("t_onset", "defined") in NA
    empty = has_lead and r["far_preonset_pct"] in NA and not no_onset
    scoreable = not (no_onset or empty)
    valid = (scoreable and has_lead and float(r[lead]) > 0
             and float(r["far_preonset_pct"]) <= 10.0)
    return scoreable, valid, empty, no_onset


def _tally(rows, lead="lead_time_hours"):
    t = [eq5_row(r, lead) for r in rows]
    return (sum(v for _, v, _, _ in t), sum(s for s, _, _, _ in t),
            sum(e for _, _, e, _ in t), sum(o for _, _, _, o in t))


def check_eq5(bad):
    n = 0
    body = tex_source()

    def need(cond, label, printed="", expected=""):
        nonlocal n
        n += 1
        if not cond:
            bad.append(("Eq.5: " + label, printed, expected))

    audit = {r["site"]: r for r in load("eq5_validity_audit.csv")}

    def agrees(site, tally):
        a = audit[site]
        got = (int(float(a["eq5_valid"])), int(float(a["eq5_scoreable"])),
               int(float(a["excluded_empty_pre"])), int(float(a["excluded_no_onset"])))
        need(got == tally, "eq5_validity_audit.csv agrees: " + site, str(got), str(tally))

    # --- Section 6.3 headline: five window-magnitude detectors, all modes x factors
    xj = load("benchmark_XJTU-SY_long.csv")
    five = ("three_sigma", "ewma", "hotelling_t2", "isolation_forest", "rms_trend")
    x5 = [r for r in xj if r["short_name"] in five]
    v, s, e, o = _tally(x5)
    need((v, s, e, o, len(x5)) == (48, 230, 170, 50, 450), "S6.3 48/230, 170+50 excluded of 450",
         "%d/%d %d+%d of %d" % (v, s, e, o, len(x5)))
    need(sum(r["valid_alarm"] == "True" for r in x5) == 209, "released column still gives 209 (implementation)")
    need("%d of %d scoreable evaluations yield a valid alarm (%d of %d" % (v, s, e + o, len(x5)) in body,
         "S6.3 headline sentence")
    need("%d because the onset precedes the first scored window, %d because Bearing1" % (e, o) in body,
         "S6.3 exclusion breakdown")
    need("The %d/%d valid-alarm figure" % (v, s) in body, "S6.7 per-bearing restatement")
    need("209/450" not in body and "20/50" not in body, "no pre-Eq.5 count survives")
    agrees("S6.3 five window-magnitude detectors, all modes x factors", (v, s, e, o))

    # --- Table 7, per bearing at full resolution (aggregate, factor 1)
    full = [r for r in x5 if r["mode"] == "aggregate" and float(r["factor"]) == 1]
    by = {}
    for r in full:
        by.setdefault(r["run"], []).append(r)
    printed = {plain(c[0]).replace(BS, ""): c for c in rows_of("tab:perbearing") if c[0].startswith("Bearing")}
    need(len(printed) == 10, "Table 7 has ten bearing rows", str(len(printed)), 10)
    tot_v = tot_sc = none = 0
    for run, rows in by.items():
        cells = printed[run]
        flags = [eq5_row(r) for r in rows]
        if all(fl[3] for fl in flags):
            need("n.s." in cells[3] and "^a" in cells[3], "T7 %s not scoreable (no onset)" % run, cells[3])
            continue
        if all(fl[2] for fl in flags):
            need("n.s." in cells[3] and "^b" in cells[3], "T7 %s not scoreable (empty pre-onset)" % run, cells[3])
            continue
        need(all(fl[0] for fl in flags), "T7 %s wholly scoreable" % run)
        leads = [float(r["lead_time_hours"]) for r, fl in zip(rows, flags) if fl[1]]
        need(plain(cells[3]) == str(len(leads)), "T7 %s V/5" % run, cells[3], len(leads))
        tot_v += len(leads)
        tot_sc += 1
        if leads:
            n += cmp_cell("T7 %s mean" % run, cells[4], statistics.mean(leads), bad)
            n += cmp_cell("T7 %s best" % run, cells[5], max(leads), bad)
        else:
            none += 1
            need(plain(cells[4]) == "--" and plain(cells[5]) == "0.00", "T7 %s no valid detector" % run)
    blk = table_block("tab:perbearing")
    need("{%d/%d}" % (tot_v, 5 * tot_sc) in blk and "{%d/%d}" % (none, tot_sc) in blk,
         "T7 totals %d/%d and %d/%d" % (tot_v, 5 * tot_sc, none, tot_sc))
    agrees("Table 7 total (full resolution, aggregate)", _tally(full))

    # --- Section 6.3 sequence length 15: the one extra bearing is not scoreable
    b25 = [eq5_row(r) for r in xj if r["run"] == "Bearing2_5" and float(r["factor"]) == 1
           and r["lead_time_hours"] not in NA]
    need(b25 and all(fl[2] for fl in b25), "Bearing2_5 empty pre-onset at f=1 for every detector")
    s15 = [r for r in load("seqlen15_xjtu.csv") if r["seq_len"] == "15" and r["na"] == "False"]
    extra = {r["run"] for r in s15} - {r["run"] for r in load("seqlen15_xjtu.csv") if r["seq_len"] == "30"}
    need(extra == {"Bearing2_5"}, "seq-len 15 adds only Bearing2_5", str(extra))
    need(not any(r["valid"] == "True" for r in s15 if r["run"] != "Bearing2_5"),
         "no deep valid alarm on the two scoreable bearings")
    need("on the two scoreable bearings the deep models still yield no valid alarm" in body, "S6.3 seq-len sentence")

    # --- Table 4(a): 3sigma pooled over factors, from the row-level persistence rerun
    pl = [r for r in load("persistence_sensitivity_IMS_invariant_long.csv")
          if r["short_name"] == "three_sigma" and r["mode"] == "aggregate"]
    row = [c for c in rows_of("tab:robust") if "all factors" in c[0]][0]
    fr = {}
    for i, p in enumerate(("1", "3", "5", "10"), start=1):
        sub = [r for r in pl if r["persistence"] == p]
        v, s, _, _ = _tally(sub)
        need(s == 13, "T4a persistence %s: 13 scoreable" % p, str(s), 13)
        fr[p] = v / s
        n += cmp_cell("T4a all factors, persistence " + p, row[i], v / s, bad)
    need("falls from %.2f to %.2f by persistence 10" % (fr["1"], fr["10"]) in body, "S6.2 persistence prose")
    agrees("Table 4a 3sigma valid-alarm frac., all factors (4 persistences)", _tally(pl))
    rel = {(r["persistence"], r["detector"]): r for r in load("persistence_sensitivity_IMS_invariant.csv")}
    for p in ("1", "3", "5", "10"):                     # the rerun reproduces the released summary
        pub = [r for r in pl if r["persistence"] == p]
        frac = sum(r["valid_alarm"] == "True" for r in pub) / len(pub)
        need(abs(frac - float(rel[(p, "three_sigma")]["valid_frac_agg_all_factors"])) < 1e-9,
             "persistence rerun reproduces released summary at %s" % p)

    # --- Table 4(b) prose: XJTU-SY changes at 20% and the across-draw spread
    for det in ("three_sigma", "ewma", "cusum", "isolation_forest"):
        d = gap_cell("XJTU-SY", det, 0.2) - gap_cell("XJTU-SY", det, 0.0)
        # leads are multiples of 1/60 h, so snap float noise before rounding a tie
        txt = "%+.2f" % float(Decimal(repr(round(d, 9))).quantize(Decimal("0.01"), ROUND_HALF_EVEN))
        need(("$%s$~h" % txt) in body, "S6.2 XJTU-SY 20%% change %s" % det, txt)
    need(gap_cell("XJTU-SY", "hotelling_t2", 0.0) is None
         and "Hotelling $T^2$ has no valid alarm on a scoreable XJTU-SY bearing" in body,
         "S6.2 Hotelling T2 has no Eq.5-valid XJTU alarm")
    gaps = load("d18_gap_injection_multiseed.csv")
    spread = 0.0
    for det in ("three_sigma", "ewma", "cusum", "isolation_forest"):
        for g in (0.05, 0.2):
            per = {}
            for r in gaps:
                if (r["dataset"] == "XJTU-SY" and r["short_name"] == det and float(r["gap"]) == g
                        and eq5_row(r, "lead")[1]):
                    per.setdefault(r["gap_seed"], []).append(float(r["lead"]))
            m = [statistics.mean(x) for x in per.values()]
            spread = max(spread, max(m) - min(m))
    bound = -(-spread * 100 // 1) / 100
    need("and %.2f~h on XJTU-SY" % bound in body, "S6.2 XJTU-SY across-draw spread", "%.3f" % spread)
    sc_runs = {r["run"] for r in gaps if r["dataset"] == "XJTU-SY" and eq5_row(r, "lead")[0]}
    need(len(sc_runs) == 6 and "two of the 6 scoreable bearings on XJTU-SY" in body, "S6.2 six scoreable XJTU bearings")
    agrees("Table 4b historian gaps (mean over valid alarms)", _tally(gaps, "lead"))

    # --- Section 6.10: at f=20 test 2 drops out of every feature-group cell
    ab = load("feature_coarsening_ablation_IMS_long.csv")
    runs = {}
    for r in ab:
        if eq5_row(r)[0]:
            runs.setdefault(r["factor"], set()).add(r["run"])
    need(len(runs["20"]) == 2 and all(len(runs[f]) == 3 for f in ("1", "2", "5", "10")),
         "S6.10 steps of 1/3, 1/2 at f=20")
    need("steps of 1/3 (1/2 at $f=20$" in body, "S6.10 sentence")

    # --- Section 6.12 / Figure 6: training sweep
    ts = load("femto_training_sweep_long.csv")
    frac = {}
    for det in ("three_sigma", "ewma", "cusum", "hotelling_t2", "isolation_forest"):
        for t in ("0.2", "0.3", "0.4", "0.5", "0.6"):
            sub = [r for r in ts if r["short_name"] == det and r["train_fraction"] == t]
            v, s, _, _ = _tally(sub)
            need(s == (5 if t == "0.2" else 6), "T sweep %s %s scoreable bearings" % (det, t), str(s))
            frac[(det, t)] = v / s
    T = ("0.2", "0.3", "0.4", "0.5", "0.6")
    f3 = lambda det, t: "%.3f" % frac[(det, t)]  # noqa: E731
    for frag in ("training fraction (%.2f) and falls to %s at $T=0.30$ and %s from $T=0.40$ on"
                 % (frac[("three_sigma", "0.2")], f3("three_sigma", "0.3"), f3("three_sigma", "0.4")),
                 "Hotelling $T^2$ starts at %s, falls to %s at $T=0.30$ and settles at %s"
                 % (f3("hotelling_t2", "0.2"), f3("hotelling_t2", "0.3"), f3("hotelling_t2", "0.4")),
                 "EWMA stays within %.3f--%.3f" % (min(frac[("ewma", t)] for t in T),
                                                   max(frac[("ewma", t)] for t in T)),
                 "CUSUM stays within %s--%s apart from a one-bearing rise to %s at $T=0.50$"
                 % (f3("cusum", "0.2"), f3("cusum", "0.3"), f3("cusum", "0.5")),
                 "Isolation Forest starts at %s, dips to %s at $T=0.30$ and ends at %s"
                 % (f3("isolation_forest", "0.2"), f3("isolation_forest", "0.3"), f3("isolation_forest", "0.6"))):
        need(frag in body, "S6.12 " + frag[:40], frag)
    spc = []
    for det in ("three_sigma", "ewma", "cusum", "hotelling_t2"):
        for t in T:
            spc.append(frac[(det, t)])
    need("SPC baseline (${\\approx}%.2f$)" % statistics.mean(spc) in body, "Fig 6 caption SPC baseline",
         "%.3f" % statistics.mean(spc))
    fig = {(r["short_name"], r["train_fraction"]): float(r["valid_frac"]) for r in load("eq5_femto_training_sweep.csv")}
    need(all(abs(fig[k] - frac[k]) < 1e-12 for k in frac), "Figure 6 source equals the Eq.5 recomputation")
    agrees("S6.12 / Figure 6 training sweep, all cells", _tally(ts))

    # --- counts that comply as printed: their sources hold no unscoreable row
    for name, site in (("n20_rerun_long_FEMTO.csv", "S6.4 FEMTO eleven detectors, all modes x factors"),
                       ("tradeoff_IMS_long.csv", "S6.1 / Table 9 IMS trade-off"),
                       ("tradeoff_IMS_deepmodels_long.csv", "S6.1 / Table 9 IMS trade-off, deep models"),
                       ("ablation_features_IMS_long.csv", "Table 10 feature-group ablation"),
                       ("denoising_IMS.csv", "Appendix D.1 denoisers")):
        rows = load(name)
        v, s, e, o = _tally(rows)
        need(s == len(rows), "%s: every row scoreable" % name, "%d/%d" % (s, len(rows)))
        agrees(site, (v, s, e, o))
    fem = load("n20_rerun_long_FEMTO.csv")
    need(_tally(fem)[:2] == (211, 660) and "211/660 FEMTO evaluations" in body, "S6.4 FEMTO 211/660 under Eq.5")
    for name, site in (("n20_rerun_long_ONGC.csv", "Appendix D.2 ONGC gating"),
                       ("benchmark_IMS_long_invariant.csv", "S6.1 IMS full resolution (deep 0/3, Table 2 L_tau)")):
        rows = [r for r in load(name) if r["mode"] == "aggregate" and float(r["factor"]) == 1]
        v, s, e, o = _tally(rows)
        need(s == len(rows), "%s f=1: every row scoreable" % name)
        agrees(site, (v, s, e, o))

    # --- Table 8: the gated arm already applies Eq. 5; independent re-derivation agrees
    gc = load("eq5_gated_crosscheck.csv")
    need(len(gc) == 44 and all(r["agrees"] == "True" for r in gc), "Table 8 gated arm re-derived under Eq.5",
         "%d agree" % sum(r["agrees"] == "True" for r in gc), 44)
    return n


# ------------------------------------ abstract / S6.4 / S6.6 equivalence wording (final pass)
def check_equivalence_wording(bad):
    n = 0
    body = tex_source()
    abstract = body[body.find(BS + "begin{abstract}"):body.find(BS + "end{abstract}")]

    def need(cond, label, printed="", expected=""):
        nonlocal n
        n += 1
        if not cond:
            bad.append(("equivalence: " + label, printed, expected))

    rows = load("n20_d15_bootstrap_new_11det.csv")
    multi = [r for r in rows if r["dataset"] in ("XJTU-SY", "FEMTO", "Ferrara")]
    need(len(multi) == 33 and all(r["verdict"] == "equivalent" for r in multi), "33 of 33 equivalent")
    ends = [abs(float(r[k])) for r in multi for k in ("ci_lo_h", "ci_hi_h")]
    need(max(ends) < 0.6 and round(max(ends), 3) == 0.560, "max |endpoint| 0.560 < 0.6", "%.6f" % max(ends))
    need("every 95\\% interval lying inside $\\pm 0.6$~h" in abstract and "-0.45" not in abstract,
         "abstract: inside +-0.6 h, no -0.45")
    below = [r for r in multi if float(r["ci_hi_h"]) < 0]
    need(len(below) == 5 and "Exactly five cells" in body, "S6.4 exactly five cells wholly below zero",
         str(len(below)), 5)
    ims = {r["method"]: r for r in rows if r["dataset"].startswith("IMS (invariant")}
    cu, ho = ims.pop("CUSUM (k=0.5, h=5.0)"), ims.pop("Hotelling T²")
    need(float(cu["ci_lo_h"]) > 1.0, "IMS CUSUM strictly beyond +1 h", cu["ci_lo_h"])
    need(float(ho["ci_lo_h"]) == 1.0, "IMS Hotelling T2 lower bound exactly +1 h", ho["ci_lo_h"])
    need(len(ims) == 9 and all(float(r["ci_lo_h"]) < 1.0 < float(r["ci_hi_h"]) for r in ims.values()),
         "IMS nine intervals straddle the margin")
    need("too wide to decide in 9 of 11 cells, favours aggregation beyond the margin for CUSUM" in abstract,
         "abstract IMS sentence")
    frag = ("CUSUM's lies wholly above it ([$%+.2f$, $%+.2f$]~h)" % (float(cu["ci_lo_h"]), float(cu["ci_hi_h"])),
            "sits exactly on it ([$%+.2f$, $%+.2f$]~h)" % (float(ho["ci_lo_h"]), float(ho["ci_hi_h"])))
    for f in frag:
        need(f in body, "S6.6 " + f[:30], f)
    return n


# ------------------------------------------- final-pass factual corrections (Part 4)
def check_factual_corrections(bad):
    n = 0
    body = tex_source()

    def need(cond, label, printed="", expected=""):
        nonlocal n
        n += 1
        if not cond:
            bad.append(("facts: " + label, printed, expected))

    on = {}
    for r in load("onset_sensitivity.csv"):
        if r["kind"] == "rms_kurt" and r["method"] == "terminal":
            on.setdefault(r["run"], []).append(float(r["onset_pct"]))
    sp = {k: max(v) - min(v) for k, v in on.items()}
    need(sp["1st_test"] < 0.1, "S6.2 test 1 k-spread < 0.1 pt", "%.3f" % sp["1st_test"])
    need("moves by less than 0.1 percentage points of run span on test~1, %.1f on test~3 and %.1f on the "
         "slow-degrading test~2" % (sp["3rd_test"], sp["2nd_test"]) in body, "S6.2 per-run onset spread")
    need("less than two percent of run span" not in body, "S6.2 false 'under two percent' removed")
    need("%.1f on IMS" % statistics.median(sp.values()) in body, "S6.2 IMS median spread")
    fer = [abs(float(r["median_diff_h"])) * 60 for r in load("n20_raw_contrast_old_vs_new.csv")
           if r["arm"] == "new" and r["dataset"] == "Ferrara"]
    need(len(fer) == 11 and max(fer) < 1.0 and "within $\\pm1$~min, no detector" in body,
         "S6.5 Ferrara medians within 1 min", "%.3f" % max(fer))
    win = {}
    for r in load("femto_training_sweep_long.csv"):
        win[(r["bearing"], r["train_fraction"])] = int(r["n_train_windows"])
    at_default = sorted(v for (b, t), v in win.items() if t == "0.5")
    need((min(win.values()), max(win.values()), statistics.median(at_default)) == (20, 335, 88)
         and "across FEMTO bearings and training fractions" in body, "S4.5 FEMTO 20-335, median 88")
    ew = [float(r["far_preonset_pct_mean"]) for r in load("tradeoff_IMS.csv") if r["short_name"] == "ewma"]
    need(round(max(ew), 1) > 22.1 and "across the tabulated thresholds (Table" in body,
         "S6.9 19.0-22.1% scoped to tabulated thresholds", "%.1f" % max(ew))
    for gone in ("refuted on every dataset tested", "tidy but unsupported", "dataset-specific noise",
                 "a property of that draw", "does not cost", "decimated raw samples"):
        need(gone not in body, "removed: " + gone)
    return n


CHECKS = [("Table imsdet (old 2/12/15)", check_imsdet),
          ("Table 19 label contrast", check_d17label),
          ("Table 4b gap injection", check_gap),
          ("Table crossds (old 5/6)", check_crossds),
          ("Table imsongc (old 7/23)", check_imsongc),
          ("Holm N=44 family (old 8)", check_holm),
          ("Table tradeoff (+OC-SVM)", check_tradeoff),
          ("Table gated contrast", check_gatedcontrast),
          ("Table mechanism (21/22)", check_mechanism),
          ("Table compute (old 17)", check_compute),
          ("Fig 4a IMS conformal", check_conformal_ims),
          ("Fig 4 calibration", check_calibration_invariance),
          ("Prose: G3/D18/ONGC/N-29", check_prose_additions),
          ("S6.2 FEMTO valid alarms", check_femto_valid),
          ("N-20 invariance rule", check_n20_rule),
          ("Eq. 5 validity counts", check_eq5),
          ("Abstract equivalence", check_equivalence_wording),
          ("Part 4 factual fixes", check_factual_corrections)]

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
