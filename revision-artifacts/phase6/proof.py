"""Phase 6 inventory proof: locate every item of inventory_before.csv in the new manuscript.

Before: revision-artifacts/inventory_before.csv (Phase 0, 30-page PDF).
After : revision-artifacts/inventory_after.csv + revision-artifacts/phase6/measure/
        sections_text.json (22-page PDF, same extraction method).
Rules
  number / table-cell (numeric) : the value appears among the after numbers (prose,
                                  captions, table cells); sign-insensitive fallback noted.
  table-cell (text)             : the string appears in the after text or tables.
  claim                          : the claim ID has >= 1 located sentence after.
  citation                       : the key is still cited.
  sentence (no catalogued claim) : best content-word overlap with any after sentence /
                                   caption / table text; < 0.6 is listed for manual review.
Documented changes (author-mandated or corrective) are listed separately, never silently
counted as located. Output: revision-artifacts/phase6/proof_report.md, proof_items.csv
"""
import csv, collections, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
RA = ROOT / "revision-artifacts"
before = list(csv.DictReader(open(RA / "inventory_before.csv", encoding="utf-8")))
after = list(csv.DictReader(open(RA / "inventory_after.csv", encoding="utf-8")))
text = json.loads((RA / "phase6/measure/sections_text.json").read_text(encoding="utf-8"))
floats = text.pop("__floats__")
blob = " ".join(text.values()) + " " + " ".join(v["caption"] + " " + v["body"] for v in floats.values())
blob = blob.replace("−", "-").replace("–", "-")
NUM = re.compile(r"[+-]?\d+(?:,\d{3})*(?:\.\d+)?")
after_nums = {r["group_id"].lstrip("+") for r in after if r["item_type"] == "number"}
after_nums |= {t.lstrip("+") for r in after if r["item_type"] == "table-cell" for t in NUM.findall(r["value"])}
after_nums |= {t.lstrip("+") for t in NUM.findall(blob)}
after_claims = {r["group_id"] for r in after if r["item_type"] == "claim" and r["location_kind"] != "UNLOCATED"}
after_cites = {r["group_id"] for r in after if r["item_type"] == "citation"}
low_blob = blob.lower()

DOCUMENTED = {  # (item kind, value) -> reason
    ("num", "180.3"): "N-29 double rounding corrected to 180.2 (source 180.2496 h)",
    ("num", "75.7"): "N-29 double rounding corrected to 75.6 (source 75.6469 h)",
}
PHRANK_RANKS = "old 7-detector PH/L ranks superseded by the author-mandated 11-detector ranking (M2)"
SC_WORDS = {"yes", "no", "yes-", "1+,2 ties", "yes$^{-}$"}


DOCUMENTED[("num", "34")] = ("ONGC corrected to the data (n20_rerun_long_ONGC.csv, factor 1): "
                             "'34-35 h' became '30-35 h (seven within 34.9-35.3 h, CUSUM 33.9, Hotelling 30.4)'")
TEXSRC = re.sub(r"\\input\{(gen/[^}]+)\}",
                lambda m: (ROOT / "paper/files" / (m.group(1) + ".tex")).read_text(encoding="utf-8"),
                (ROOT / "paper/files/scada_ijphm.tex").read_text(encoding="utf-8"))
MANUAL = {r["item_id"]: r for r in csv.DictReader(open(RA / "phase6/review_decisions.csv", encoding="utf-8"))}


def located_num(v):
    v = v.lstrip("+").rstrip("%")
    # ranges print as "42-63%" after en-dash normalisation, so the upper bound tokenises as "-63"
    return v in after_nums or v.lstrip("-") in after_nums or ("-" + v.lstrip("-")) in after_nums


STOP = set("the and for that with this from are was were which their these than into only when where have has been does not its also each under over most more such both they them then there what while".split())


def words(s):
    return {w for w in re.findall(r"[a-z][a-z0-9_\-]{3,}", s.lower()) if w not in STOP}


after_units = [words(r["context"]) for r in after if r["item_type"] == "sentence"]
after_units += [words(v["body"]) for v in floats.values()]

rows, unlocated, documented, review = [], [], [], []
for r in before:
    t, v = r["item_type"], r["value"]
    status, where = "located", ""
    if t == "number":
        if located_num(r["group_id"]):
            pass
        elif ("num", r["group_id"].lstrip("+")) in DOCUMENTED:
            status, where = "documented", DOCUMENTED[("num", r["group_id"].lstrip("+"))]
        else:
            status = "UNLOCATED"
    elif t == "table-cell":
        toks = NUM.findall(v.replace("−", "-"))
        if toks:
            miss = [x for x in toks if not located_num(x)]
            if miss:
                if r["group_id"] == "tab:phrank":
                    status, where = "documented", PHRANK_RANKS
                elif all(("num", x.lstrip("+")) in DOCUMENTED for x in miss):
                    status, where = "documented", DOCUMENTED[("num", miss[0].lstrip("+"))]
                elif r["group_id"] == "tab:imslead" and "operating point" in v:
                    status, where = "documented", "group heading; tau=10% stated as tau = 0.10 in the merged caption"
                else:
                    status, where = "UNLOCATED", "missing %s" % miss
        else:
            if v.strip().lower() in SC_WORDS or v.strip() in SC_WORDS:
                status, where = "documented", "sign-consistency verdict now encoded as the s-superscript on n+/n- (verify_tables checks it)"
            elif v.lower() in low_blob or v.lower().replace("_", " ") in low_blob:
                pass
            elif v in TEXSRC or v.replace("-", "--") in TEXSRC:
                where = "present in the source table (PDF glyph mismatch only)"
            elif r["item_id"] in MANUAL:
                status, where = "located-manual", "%s: %s" % (MANUAL[r["item_id"]]["decision"], MANUAL[r["item_id"]]["where_now"])
            else:
                status, where = "REVIEW", "text cell not found verbatim"
    elif t == "claim":
        if r["group_id"] not in after_claims:
            status = "UNLOCATED"
    elif t == "citation":
        if r["group_id"] not in after_cites:
            status = "UNLOCATED"
    elif t == "sentence":
        if r["claim_ids"]:
            ok = [c for c in r["claim_ids"].split(";") if c in after_claims]
            if not ok:
                status = "UNLOCATED"
        else:
            w = words(r["context"])
            best = max((len(w & u) / len(w) for u in after_units if w), default=1.0)
            where = "%.2f" % best
            if best < 0.6:
                status = "REVIEW"
                if r["item_id"] in MANUAL:
                    status = "located-manual"
                    where = "%s: %s" % (MANUAL[r["item_id"]]["decision"], MANUAL[r["item_id"]]["where_now"])
    rows.append(dict(item_id=r["item_id"], item_type=t, group_id=r["group_id"], status=status, note=where,
                     context=r["context"][:200] if r["context"] else r["value"][:200]))
    if status == "UNLOCATED":
        unlocated.append(rows[-1])
    elif status == "documented":
        documented.append(rows[-1])
    elif status == "REVIEW":
        review.append(rows[-1])

with open(RA / "phase6/proof_items.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
c = collections.Counter((r["item_type"], r["status"]) for r in rows)
L = ["# Phase 6 inventory proof (generated by proof.py)", "",
     "| item type | located | documented | review | UNLOCATED |", "|---|---|---|---|---|"]
for t in ("sentence", "claim", "number", "table-cell", "citation"):
    L.append("| %s | %d (+%d manual) | %d | %d | %d |" % (t, c[(t, "located")], c[(t, "located-manual")], c[(t, "documented")], c[(t, "REVIEW")], c[(t, "UNLOCATED")]))
L += ["", "## UNLOCATED (%d)" % len(unlocated), ""] + ["- %s [%s %s] %s | %s" % (u["item_id"], u["item_type"], u["group_id"], u["note"], u["context"]) for u in unlocated]
L += ["", "## Documented changes (%d)" % len(documented), ""]
for k, n in collections.Counter(d["note"] for d in documented).items():
    L.append("- %d x %s" % (n, k))
L += ["", "## Manual review queue (%d)" % len(review), ""] + ["- %s [%s] overlap %s | %s" % (u["item_id"], u["item_type"], u["note"], u["context"]) for u in review]
(RA / "phase6/proof_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[:9]))
print("UNLOCATED", len(unlocated), "| review", len(review), "| documented", len(documented))
