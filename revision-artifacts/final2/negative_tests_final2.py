"""Negative tests for the guards added in the final submission pass. Each must go RED.

1. check_eq5 pointed at the implementation's rule (NaN FAR passes; positional fallback counts)
2. check_equivalence_wording on the manuscript before Part 3 (e1ea46d^)
3. check_factual_corrections on the manuscript before Part 4 (ef9088f^)

    python revision-artifacts/final2/negative_tests_final2.py     # exit 0 only if all RED
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "paper"))
import verify_tables as vt  # noqa: E402

ORIG_ROW, ORIG_TEX = vt.eq5_row, vt.tex_source


def tex_at(rev):
    out = subprocess.run(["git", "show", f"{rev}:paper/files/scada_ijphm.tex"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return lambda: vt.re.sub(r"\\input\{(gen/[^}]+)\}",
                             lambda m: (vt.TEX.parent / (m.group(1) + ".tex")).read_text(encoding="utf-8"), out)


def impl_rule(r, lead="lead_time_hours"):
    col = "valid_alarm" if "valid_alarm" in r else "valid"
    return True, r[col] == "True", False, False


CASES = [
    ("Eq.5 guard vs implementation valid_alarm", lambda: setattr(vt, "eq5_row", impl_rule),
     lambda bad: (vt.check_eq5(bad), vt.check_gap(bad))),
    ("equivalence wording vs pre-Part-3 text", lambda: setattr(vt, "tex_source", tex_at("e1ea46d^")),
     vt.check_equivalence_wording),
    ("factual fixes vs pre-Part-4 text", lambda: setattr(vt, "tex_source", tex_at("ef9088f^")),
     vt.check_factual_corrections),
]

ok = True
for name, arm, run in CASES:
    vt.eq5_row, vt.tex_source = ORIG_ROW, ORIG_TEX
    arm()
    bad = []
    try:
        run(bad)
    except Exception as e:  # noqa: BLE001 -- a crash is also a failure of the tampered input
        bad.append(("exception", type(e).__name__, str(e)[:60]))
    red = bool(bad)
    ok &= red
    print(f"{name:42s} {'RED (good)' if red else 'GREEN (guard is decoration!)'} {len(bad)} mismatches")
vt.eq5_row, vt.tex_source = ORIG_ROW, ORIG_TEX
bad = []
for fn in (vt.check_eq5, vt.check_equivalence_wording, vt.check_factual_corrections):
    fn(bad)
print("restored inputs:", "GREEN" if not bad else bad)
sys.exit(0 if ok and not bad else 1)
