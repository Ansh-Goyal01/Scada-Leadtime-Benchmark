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


CHECKS = [("Table 2 IMS lead + CI", check_imslead),
          ("Table 19 label contrast", check_d17label),
          ("Table 4b gap injection", check_gap),
          ("Table 6 equivalence", check_equiv),
          ("Table 7 IMS run-level", check_imssweep),
          ("Table 8 Holm", check_holm),
          ("Table 12 trade-off", check_tradeoff)]


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
