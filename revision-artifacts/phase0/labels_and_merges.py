"""Phase 0, step 6: printed number of every float label, and the Phase 1 merge pre-checks.

Reads   : the instrumented build's .aux (layout-identical to the real build; tectonic
          does not keep the real build's .aux) -> argv[1] is its directory
          revision-artifacts/phase0/floats.csv, revision-artifacts/inventory_before.csv
Writes  : revision-artifacts/phase0/label_map.csv ; prints the merge pre-checks
"""
import csv, re, sys, pathlib

PH0 = pathlib.Path(__file__).parent
AUX = pathlib.Path(sys.argv[1]) / "scada_ijphm.aux"

aux = AUX.read_text(encoding="utf-8", errors="replace")
lab = {m.group(1): m.group(2) for m in
       re.finditer(r"\\newlabel\{((?:tab|fig|alg):[^}]*)\}\{\{([^}]*)\}\{([^}]*)\}", aux)}
floats = list(csv.DictReader(open(PH0 / "floats.csv", encoding="utf-8")))
with open(PH0 / "label_map.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["label", "kind", "printed_number", "page", "width", "height_bp", "page_equiv", "caption_words"])
    for f in floats:
        kind = {"tab": "Table", "fig": "Figure", "alg": "Algorithm"}[f["label"].split(":")[0]]
        num = lab.get(f["label"], "?")
        w.writerow([f["label"], kind, num, f["page"], f["width"], f["height_bp"], f["page_equiv"], f["caption_words"]])
        print("%-22s %-9s %3s  p%-3s %-6s h=%6s bp  page-eq=%s  cap=%s w" % (
            f["label"], kind, num, f["page"], f["width"], f["height_bp"], f["page_equiv"], f["caption_words"]))

inv = [r for r in csv.DictReader(open(PH0.parent / "inventory_before.csv", encoding="utf-8"))
       if r["item_type"] == "table-cell"]
ALIAS = {"hott2": "hotellingt2", "isofor": "isoforest", "transfad": "transformerad"}


def det(name):
    k = re.sub(r"[^a-z0-9σ]", "", name.split(" / ")[-1].lower())
    return ALIAS.get(k, k)


def cells(label):
    for r in inv:
        if r["group_id"] == label:
            _, row, col = [x.strip() for x in r["location"].split("|")]
            yield row, col, r["value"].replace("‡", "").strip()


# M1: are the Holm table's raw p the same printed values as the sign-test tables?
holm = {(col, det(row)): v for row, col, v in cells("tab:holm")}
sign = {}
for row, col, v in cells("tab:crossds"):
    if col == "p":
        sign[(row.split(" / ")[0].split(" (")[0].split()[0], det(row))] = v
for row, col, v in cells("tab:imssweep"):
    if col == "p":
        sign[("IMS", det(row))] = v
same = [k for k in holm if k in sign and float(holm[k]) == float(sign[k])]
print("\nM1: tab:holm raw-p cells %d; equal to the printed p in tab:crossds (33) + tab:imssweep (11): %d; "
      "unequal/unmatched: %s" % (len(holm), len(same), [(k, holm[k], sign.get(k)) for k in holm if k not in same] or "none"))

# M2: is PH the best raw lead across the tabulated thresholds, and L the tau = 0.10 column?
lds = {}
for row, col, v in cells("tab:tradeoff"):
    if col == "Ld":
        lds.setdefault(det(row), []).append(float(v))
ph = {det(r): float(v) for r, c, v in cells("tab:phrank") if c == "PH"}
Lg = {det(r): float(v) for r, c, v in cells("tab:phrank") if c == "L"}
fb = {det(r): float(v) for r, c, v in cells("tab:farbudget") if "0.10" in c}
print("M2: PH == max(tab:tradeoff Ld):", {d: (v, max(lds.get(d, [float("nan")]))) for d, v in ph.items()},
      "->", all(v == max(lds.get(d, [-1])) for d, v in ph.items()))
print("M2: L == tab:farbudget tau=0.10:", {d: (v, fb.get(d)) for d, v in Lg.items()},
      "->", all(fb.get(d) == v for d, v in Lg.items()))
for label in ("tab:imslead", "tab:farbudget", "tab:phrank", "tab:tradeoff"):
    print("   %-14s rows: %s" % (label, sorted({det(r) for r, c, v in cells(label) if c != "(panel/total row)"})))
