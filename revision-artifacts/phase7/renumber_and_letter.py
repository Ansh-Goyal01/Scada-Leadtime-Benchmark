"""Phase 7: renumbering map (old -> new) and the Response-to-Review citations that changed.

Old numbers: revision-artifacts/phase0/label_map.csv (30-page build).
New numbers: revision-artifacts/phase6/measure/scada_ijphm.aux (22-page build).
Letter    : IJPHM-response-letter-draft.md (scanned for Table/Figure/Section/page refs and
            for values changed by this work).
Writes    : revision-artifacts/phase7/renumbering_map.md
"""
import csv, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
RA = ROOT / "revision-artifacts"
old = {r["label"]: (r["kind"], r["printed_number"]) for r in csv.DictReader(open(RA / "phase0/label_map.csv", encoding="utf-8"))}
aux = (RA / "phase6/measure/scada_ijphm.aux").read_text(encoding="utf-8", errors="replace")
new = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{((?:tab|fig|alg|sec):[^}]*)\}\{\{([^}]*)\}", aux)}
MERGED = {"tab:imslead": "tab:imsdet", "tab:farbudget": "tab:imsdet", "tab:phrank": "tab:imsdet",
          "tab:equiv": "tab:crossds", "tab:holm": "tab:crossds (caption)", "tab:imssweep": "tab:imsongc",
          "tab:ongc": "tab:imsongc", "tab:conformal": "fig:conformal (caption)", "tab:compute": "tab:hyperparams (b)",
          "tab:noise": "tab:mechanism (a)", "tab:denoise": "tab:mechanism (b)"}
L = ["# Renumbering map (old 30-page build -> new 22-page build)", "",
     "| Old | Label | New | Note |", "|---|---|---|---|"]
old_to_new = {}
for lab, (kind, num) in old.items():
    if lab in new:
        L.append("| %s %s | `%s` | %s %s | %s |" % (kind, num, lab, kind, new[lab], "" if num == new[lab] else "renumbered"))
        old_to_new[(kind, num)] = "%s %s" % (kind, new[lab])
    else:
        tgt = MERGED[lab]
        base = tgt.split()[0]
        k2 = "Figure" if base.startswith("fig") else "Table"
        L.append("| %s %s | `%s` | merged into %s %s | %s |" % (kind, num, lab, k2, new.get(base, "?"), tgt))
        old_to_new[(kind, num)] = "%s %s (%s)" % (k2, new.get(base, "?"), tgt)
L += ["", "Sections: unchanged numbering (no section added or removed); Section 7.1 condensed.",
      "Counts: tables %d -> %d, figures %d -> %d, algorithm 1 -> 1." % (
          sum(1 for k, _ in old.values() if k == "Table"), sum(1 for l in new if l.startswith("tab:")),
          sum(1 for k, _ in old.values() if k == "Figure"), sum(1 for l in new if l.startswith("fig:")))]

letter = (ROOT / "IJPHM-response-letter-draft.md").read_text(encoding="utf-8").split("\n")
PAT = re.compile(r"\b(Table|Tables|Fig\.|Figure|Figures)\s*~?(\d+)|(\d+)\s*pages|\b(180\.3|75\.7|34[-–]35|fourth|seven non-sequence)\b")
L += ["", "## Response-to-Review lines citing a number that has changed", "",
      "Old numbering in the letter refers to the 30-page build unless stated; check each line.", ""]
for i, ln in enumerate(letter, 1):
    hits = []
    for m in PAT.finditer(ln):
        if m.group(1):
            kind = "Figure" if m.group(1).startswith("Fig") else "Table"
            key = (kind, m.group(2))
            now = old_to_new.get(key)
            if now and now != "%s %s" % key:
                hits.append("%s %s -> %s" % (kind, m.group(2), now))
        elif m.group(3):
            hits.append("%s pages -> now 22 pages" % m.group(3))
        elif m.group(4):
            hits.append("value '%s' changed (N-29 / ONGC / 11-detector PH ranking)" % m.group(4))
    if hits:
        L.append("- L%d: %s  | `%s`" % (i, "; ".join(hits), ln.strip()[:140]))
(RA / "phase7/renumbering_map.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[:40]))
print("... letter lines flagged:", sum(1 for x in L if x.startswith("- L")))
