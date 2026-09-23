"""Negative tests for the Phase 1 verify_tables.py guards: each must go RED when pointed at
the wrong source or shown a tampered value (a guard that cannot fail is decoration).
Run: python revision-artifacts/phase1/negative_tests.py   (exit 0 = every guard bit)
"""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "paper"))
import verify_tables as vt  # noqa: E402

results = []


def expect_red(name, fn):
    bad = []
    try:
        fn(bad)
        red = bool(bad)
    except Exception as e:            # a crash on a wrong source also counts as red
        red, bad = True, [("exception", type(e).__name__, str(e)[:60])]
    results.append((name, red, bad[:1]))


orig_runlevel = dict(vt.RUNLEVEL)
vt.RUNLEVEL["XJTU-SY"] = "femto_runlevel_test_n20.csv"          # wrong dataset's file
expect_red("XJTU guard vs FEMTO file", vt.check_crossds)
vt.RUNLEVEL.update(orig_runlevel)

orig_family = vt.load_holm_family
vt.load_holm_family = lambda: [dict(r, median_diff=r["median_diff_h"], n_runs=r["n_runs_tested"])
                               for r in vt.load(vt.HOLM_SOURCE)
                               if r["arm"] == "old" and r["dataset"] != "ONGC"]   # pre-N-20 arm
expect_red("Holm family vs pre-N-20 arm", vt.check_holm)
vt.load_holm_family = orig_family

vt.ONGC_MINUTES_COL = "old_min"                                   # pre-N-20 ONGC column
expect_red("ONGC column vs old_min", vt.check_imsongc)
vt.ONGC_MINUTES_COL = "new_min"

orig_src = vt.tex_source
vt.tex_source = lambda: orig_src().replace("199.6", "199.7", 1)   # tamper one printed PH
expect_red("imsdet tampered PH", vt.check_imsdet)
vt.tex_source = lambda: orig_src().replace("Aggregate (historian) & 75.6", "Aggregate (historian) & 75.7", 1)  # N-29
expect_red("mechanism N-29 double rounding", vt.check_mechanism)
vt.tex_source = lambda: orig_src().replace("collapses in 2 of the 5 draws", "collapses in some draws")
expect_red("D18 sentence removed", vt.check_prose_additions)
vt.tex_source = lambda: orig_src().replace("only Hotelling $T^2$ and RMS-trend are valid", "all detectors are valid")
expect_red("ONGC gating sentence removed", vt.check_prose_additions)
vt.tex_source = orig_src
orig_load = vt.load
vt.load = lambda name: [dict(r, valid_alarm="True") if r.get("short_name") == "isolation_forest" else r
                        for r in orig_load(name)]                  # Isolation Forest flipped to valid
expect_red("ONGC gating valid set tampered", vt.check_prose_additions)
vt.load = orig_load
vt.TRADEOFF_SOURCES = ("tradeoff_IMS.csv", "tradeoff_IMS_deepmodels.csv")      # drop OC-SVM source
expect_red("tradeoff without OC-SVM source", vt.check_tradeoff)

ok = all(red for _, red, _ in results)
for name, red, b in results:
    print("%-34s %s %s" % (name, "RED (good)" if red else "GREEN -- GUARD DOES NOT BITE", b))
sys.exit(0 if ok else 1)
