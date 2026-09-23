"""Splice the Phase 1 checks into paper/verify_tables.py (run once).

Removes the per-table checks of floats that no longer exist (Tables 2, 5, 6, 7, 8, 10,
12, 23 in their old layouts), inserts vt_phase1_block.py before CHECKS, and rewires
CHECKS. Each removal is asserted to find exactly one definition.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
VT = ROOT / "paper" / "verify_tables.py"
BLOCK = (pathlib.Path(__file__).parent / "vt_phase1_block.py").read_text(encoding="utf-8")
s = VT.read_text(encoding="utf-8")


def cut(start_marker, end_marker):
    """Remove s[start_marker : end_marker) -- the start must occur exactly once."""
    global s
    assert s.count(start_marker) == 1, start_marker
    a = s.index(start_marker)
    b = s.index(end_marker, a)
    s = s[:a] + s[b:]


cut("# ------------------------------------------------------- Table 12: tradeoff",
    "# --------------------------------------------------- Table 7: IMS run-level")
cut("# --------------------------------------------------- Table 7: IMS run-level",
    "# ------------------------------------------------------ Table 6: equivalence")
cut("# ------------------------------------------------------ Table 6: equivalence",
    "# --------------------------------------------------------- Table 8: Holm")
cut("# --------------------------------------------------------- Table 8: Holm",
    "# ------------------------------------------------- Table 2: IMS lead + CI")
cut("# ------------------------------------------------- Table 2: IMS lead + CI",
    "# --------------------------------------- Table 19: IMS under both labels")
cut("# ------------------------------- Table 5: FEMTO / Ferrara cross-dataset rows",
    "# ---------------------------------------------- Table 10: gated contrast")
cut("def check_gatedcontrast(bad):", "# ------------------------- Figure 4c/4d")
cut("ONGC_ROW_KEYS = {", "CHECKS = [")
s = s.replace("CHECKS = [", BLOCK + "\n\nCHECKS = [", 1)
i = s.index("CHECKS = [")
old_checks = s[i:s.index("]\n", i) + 1]
new_checks = '''CHECKS = [("Table imsdet (old 2/12/15)", check_imsdet),
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
          ("N-20 invariance rule", check_n20_rule)]'''
s = s.replace(old_checks, new_checks)
old_key = '("oneclass", "ocsvm"), ("deepsvdd", "deepsvdd"),'
assert s.count(old_key) == 1
s = s.replace(old_key, '("oneclass", "ocsvm"), ("ocsvm", "ocsvm"), ("deepsvdd", "deepsvdd"),')
for gone in ("def check_imslead", "def check_equiv", "def check_imssweep", "def check_ongc_minutes",
             "def _crossds_rows", "HOLM_COLS"):
    assert gone not in s, gone
VT.write_text(s, encoding="utf-8")
print("verify_tables.py spliced;", len(re.findall(r"^def check_", s, re.M)), "check functions")
