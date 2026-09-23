"""Phase 1 merge guard: every numeric value printed in an old table must reappear in the
generated table that absorbs it (stop rule: 'a merge that would drop a value').

Old values : revision-artifacts/inventory_before.csv (table-cell rows, parsed from the
             Phase 0 manuscript) -- the frozen 'before' state.
New values : paper/files/gen/*.tex (table body AND caption).
Run        : python revision-artifacts/phase1/compare_old_new.py
"""
import csv, re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
GEN = ROOT / "paper/files/gen"
GROUPS = {
    "tab_crossds": ["tab:crossds", "tab:equiv", "tab:holm"],
    "tab_imsongc": ["tab:imssweep", "tab:ongc"],
    "tab_gatedcontrast": ["tab:gatedcontrast"],
    "tab_imsdet": ["tab:imslead", "tab:farbudget", "tab:phrank"],
    "tab_tradeoff": ["tab:tradeoff"],
    "tab_mechanism": ["tab:noise", "tab:denoise"],
    "tab_hyperparams": ["tab:hyperparams", "tab:compute"],
    "conformal_values": ["tab:conformal"],
}
NUM = re.compile(r"[+-]?\d+(?:,\d{3})*(?:\.\d+)?")
# Documented, author-sanctioned or corrective differences. Anything NOT listed fails.
EXCEPTIONS = {
    ("tab:imslead", "10"): "tau=10% group headings; the merged caption states tau = 0.10",
    ("tab:imslead", "180.3"): "N-29 double rounding: source mean 180.2496 h -> 180.2 (d3_ocsvm_leadtime_ci.csv)",
    ("tab:denoise", "75.7"): "N-29 double rounding: source mean 75.6469 h -> 75.6 (denoising_IMS.csv)",
    ("tab:phrank", "4"): "7-detector ranks superseded by the author-mandated 11-detector ranking (M2)",
    ("tab:phrank", "5"): "7-detector ranks superseded by the author-mandated 11-detector ranking (M2)",
    ("tab:phrank", "6"): "7-detector ranks superseded by the author-mandated 11-detector ranking (M2)",
    ("tab:phrank", "7"): "7-detector ranks superseded by the author-mandated 11-detector ranking (M2)",
}


def toks(s):
    s = s.replace("−", "-").replace("$-$", "-").replace("{,}", ",")
    return {t.lstrip("+") for t in NUM.findall(s)}


old = {}
for r in csv.DictReader(open(ROOT / "revision-artifacts/inventory_before.csv", encoding="utf-8")):
    if r["item_type"] == "table-cell":
        old.setdefault(r["group_id"], []).append((r["location"], r["value"]))

fail = 0
for gen, labels in GROUPS.items():
    new_text = (GEN / (gen + ".tex")).read_text(encoding="utf-8")
    new_text = re.sub(r"\\label\{[^}]*\}|\\ref\{[^}]*\}|\\[a-zA-Z]+", " ", new_text)
    new = toks(new_text)
    for lab in labels:
        missing = []
        for loc, val in old.get(lab, []):
            for t in toks(val):
                if t not in new and t.lstrip("-") not in new:
                    why = EXCEPTIONS.get((lab, t))
                    if why:
                        print("      documented: %s %s -> %s" % (lab, t, why))
                    else:
                        missing.append((loc.split("|", 1)[1].strip(), val, t))
        print("%-18s <- %-20s cells %3d  missing %d" % (gen, lab, len(old.get(lab, [])), len(missing)))
        for mm in missing:
            print("      MISSING", mm)
        fail += len(missing)
sys.exit(1 if fail else 0)
