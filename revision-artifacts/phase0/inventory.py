"""Phase 0 claims-and-numbers inventory (Phase 6 reruns this on the new PDF).

Reads   : revision-artifacts/phase0/sections_text.json  (from measure.py, PDF text)
          paper/files/scada_ijphm.tex                    (table cells, citations)
          revision-artifacts/phase0/claims_catalog.py
Writes  : revision-artifacts/inventory_before.csv  (or the path given as argv[1])
          revision-artifacts/phase0/redundancy_report.md
          revision-artifacts/phase0/table_cell_crosscheck.txt

Row types in the CSV
  sentence   every body/caption sentence of the PDF (the fallback unit of content)
  claim      one row per (claim_id, sentence) match; group_id = claim_id
  number     one row per numeric token printed in a sentence; group_id = normalised value
  table-cell one row per tabular cell (from the .tex, cross-checked against the PDF)
  citation   one row per cited key; group_id = key
"""
import csv, json, re, sys, collections, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from measure import sentences                   # same splitter as the sentence statistics
from claims_catalog import CLAIMS

ROOT = pathlib.Path(__file__).resolve().parents[2]
PH0 = ROOT / "revision-artifacts/phase0"
import os
MEAS = pathlib.Path(os.environ.get("MEASURE_OUT", PH0))   # sections_text.json in, reports out
TEX = ROOT / "paper/files/scada_ijphm.tex"
OUT_CSV = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "revision-artifacts/inventory_before.csv"
NEW_CITES = {"lavin2015nab", "tatbul2018", "wu2023flawed", "lorden1971", "moustakides1986", "pollak1985"}


def norm(s):
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = re.sub(r"(\d) \.(\d)", r"\1.\2", s)          # '0 .05' -> '0.05' (math spacing)
    return re.sub(r"\s+", " ", s).strip()


CITE_PAREN = re.compile(r"\([^()]*\b(?:19|20)\d{2}[a-z]?(?:[;,][^()]*)?\)")
CITE_BARE = re.compile(r"(?<=[A-Za-z.]) \((?:19|20)\d{2}[a-z]?\)")
XREF = re.compile(r"\b(?:Section|Sections|Table|Tables|Figure|Eq\.|Appendix|Algorithm)\s*\(?[A-D]?\d+(?:\.\d+)?[a-d]?\)?"
                  r"(?:(?:,| and| or)\s*\(?[A-D]?\d+(?:\.\d+)?[a-d]?\)?)*")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?\b|\b\d{2}:\d{2}\b")
NUM = re.compile(r"(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+(?:\.\d+)?)?%?")


def numbers_in(s):
    """Printed data values in a sentence: dates, times, numbers (signed where the sign is a sign)."""
    s = CITE_BARE.sub("", CITE_PAREN.sub("", s))
    s = XREF.sub(" ", s)
    out = [m.group(0) for m in DATE.finditer(s)]
    s = DATE.sub(" ", s)
    for m in NUM.finditer(s):
        tok, i = m.group(0), m.start()
        after = s[m.end():m.end() + 2]
        if (tok == "3" and after.lstrip().startswith("σ")) or \
           (tok == "2" and s[max(0, i - 2):i].rstrip().endswith(("T", "ℓ"))):
            continue                                       # 3σ, Hotelling T², ℓ2 are names
        if i >= 1 and s[i - 1] in "+-±" and (i < 2 or not s[i - 2].isalnum()):
            tok = s[i - 1] + tok
        out.append(tok)
    return out


def tex_text():
    """Manuscript with \input{gen/...} expanded (Phase 1+ tables live in gen/)."""
    src = TEX.read_text(encoding="utf-8")
    return re.sub(r"\\input\{(gen/[^}]+)\}", lambda m: (TEX.parent / (m.group(1) + ".tex")).read_text(encoding="utf-8"), src)


def strip_tex(c):
    c = re.sub(r"\\(multicolumn|multirow)\{[^}]*\}\{[^}]*\}\{", "{", c)
    c = re.sub(r"\\shortstack\[\w\]\{([^}]*)\}", lambda m: m.group(1).replace("\\\\", " "), c)
    c = re.sub(r"\\(textbf|emph|texttt|textit|mathrm|text)\{", "{", c)
    for a, b in ((r"\,", " "), ("\\ ", " "), ("{,}", ","), (r"\%", "%"), (r"\_", "_"), (r"\checkmark", "✓"),
                 (r"\ddagger", "‡"), (r"\dagger", "†"), (r"\sigma", "σ"), (r"\alpha", "α"),
                 (r"\Delta", "Δ"), (r"\mu", "μ"), (r"\lambda", "λ"), (r"\ll", "≪")):
        c = c.replace(a, b)
    c = re.sub(r"\\[a-zA-Z]+\*?", " ", c)
    c = re.sub(r"[{}$^]", "", c).replace("--", "-").replace("~", " ")
    return re.sub(r"\s+", " ", c).strip()


def tex_tables():
    """Yield (label, rowname, colname, cell) for every non-empty tabular cell."""
    tex = tex_text()
    for m in re.finditer(r"\\begin\{(table\*?)\}(.*?)\\end\{\1\}", tex, re.S):
        body = m.group(2)
        label = re.search(r"\\label\{([^}]*)\}", body).group(1)
        for t in re.finditer(r"\\begin\{tabular\}\{(?:[^{}]|\{[^}]*\})*\}(.*?)\\end\{tabular\}", body, re.S):
            header, group = None, ""
            # \shortstack{A\\B} holds a '\\' that is not a row break: flatten it first
            tab = re.sub(r"\\shortstack\[\w\]\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
                         lambda s: s.group(1).replace("\\\\", " "), t.group(1))
            for r in re.split(r"\\\\", tab):
                r = re.sub(r"\\hline|\\cmidrule(\([^)]*\))?\{[^}]*\}", "", r).strip()
                if not r or r.startswith("%"):
                    continue
                raw_cells = re.split(r"(?<!\\)&", r)
                cells = [strip_tex(c) for c in raw_cells]
                first = raw_cells[0].strip()
                if len(cells) > 1 and "\\textbf" in r and ("\\textbf" in first or not first):
                    header = cells                   # header row: bold first cell, or empty + bold
                    continue
                if len(cells) == 1:
                    group = cells[0]
                    yield label, group, "(panel/total row)", cells[0]
                    continue
                if "\\multirow" in r:
                    group, cells[0] = cells[0], ""
                two_labels = bool(header) and len(header) > 1 and header[0].lower() in ("data", "dataset") \
                    and header[1].lower() in ("method", "detector")
                row = cells[1] if two_labels else cells[0]
                rowname = "%s / %s" % (group, row) if group and row else (row or group)
                for j, c in enumerate(cells[2 if two_labels else 1:], 2 if two_labels else 1):
                    if c:
                        col = header[j] if header and j < len(header) else "col%d" % j
                        yield label, rowname, col, c


def main():
    data = json.loads((MEAS / "sections_text.json").read_text(encoding="utf-8"))
    floats = data.pop("__floats__")
    rows = []

    units = []
    for si, (title, text) in enumerate(data.items()):
        if title != "References":
            units += [("S%02d.%03d" % (si, k), "body", title, s) for k, s in enumerate(sentences(norm(text)), 1)]
    for label, parts in floats.items():
        units += [("%s.cap%02d" % (label, k), "caption", label, s) for k, s in enumerate(sentences(norm(parts["caption"])), 1)]

    compiled = [(cid, tag, stmt, [re.compile(p, re.I) for p in pats]) for cid, tag, stmt, pats in CLAIMS]
    hits = collections.defaultdict(list)
    for sid, kind, loc, s in units:
        ids = [cid for cid, _, _, pats in compiled if any(p.search(s) for p in pats)]
        for cid in ids:
            hits[cid].append((sid, kind, loc, s))
        rows.append(dict(item_id=sid, item_type="sentence", group_id="", value="", section=loc,
                         location_kind=kind, location=loc, context=s, claim_ids=";".join(ids), protected=""))
        for n, tok in enumerate(numbers_in(s), 1):
            rows.append(dict(item_id="%s.n%02d" % (sid, n), item_type="number", group_id=tok.lstrip("+"),
                             value=tok, section=loc, location_kind=kind, location=loc, context=s,
                             claim_ids="", protected=""))
    for cid, tag, stmt, _ in compiled:
        for sid, kind, loc, s in hits.get(cid) or [("NONE", "UNLOCATED", "", "")]:
            rows.append(dict(item_id="%s@%s" % (cid, sid), item_type="claim", group_id=cid, value=stmt,
                             section=loc, location_kind=kind, location=loc, context=s, claim_ids=cid, protected=tag))

    cross, per_table = [], collections.defaultdict(list)
    for n, (label, rname, col, cell) in enumerate(tex_tables(), 1):
        per_table[label].append(cell)
        rows.append(dict(item_id="%s.c%03d" % (label, n), item_type="table-cell", group_id=label, value=cell,
                         section="table", location_kind="table-cell", location="%s | %s | %s" % (label, rname, col),
                         context=rname, claim_ids="", protected="G5" if label == "tab:deeparch" else
                         ("D19" if label == "tab:d17label" else ("D3/D4" if label in ("tab:tradeoff", "tab:crossds", "tab:holm", "tab:imslead") else ""))))
    numre = r"[+-]?\d+(?:,\d{3})*(?:\.\d+)?"
    for label, cells in per_table.items():
        tex_n = collections.Counter(t.lstrip("+") for c in cells for t in re.findall(numre, norm(c)))
        pdf_n = collections.Counter(t.lstrip("+") for t in re.findall(numre, norm(floats[label]["body"])))
        miss = tex_n - pdf_n
        cross.append("%-22s cells=%3d numeric-tokens=%4d missing-in-PDF-float-text=%d %s" % (
            label, len(cells), sum(tex_n.values()), sum(miss.values()), dict(miss) if miss else ""))
    (MEAS / "table_cell_crosscheck.txt").write_text("\n".join(cross) + "\n", encoding="utf-8")

    cur = "Front matter"
    for i, ln in enumerate(TEX.read_text(encoding="utf-8").split("\n"), 1):
        h = re.match(r"\s*\\(?:sub)?section\*?\{([^}]*)", ln)
        cur = h.group(1) if h else cur
        for m in re.finditer(r"\\cite[A-Za-z]*\{([^}]*)\}", ln):
            for key in (k.strip() for k in m.group(1).split(",")):
                rows.append(dict(item_id="cite:%s@tex%d" % (key, i), item_type="citation", group_id=key, value=key,
                                 section=cur, location_kind="citation", location="tex:%d" % i, context="",
                                 claim_ids="", protected="D1/F1/G6" if key in NEW_CITES else ""))

    cols = ["item_id", "item_type", "group_id", "value", "section", "location_kind", "location", "context", "claim_ids", "protected"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    write_report(rows, compiled, hits)


def write_report(rows, compiled, hits):
    counts = collections.Counter(r["item_type"] for r in rows)
    nsent = counts["sentence"]
    mapped = sum(1 for r in rows if r["item_type"] == "sentence" and r["claim_ids"])
    L = ["# Phase 0 redundancy report (generated by inventory.py; do not hand-edit)", "",
         "Rows: " + ", ".join("%s %d" % kv for kv in sorted(counts.items())) + ".",
         "Sentences matched to >= 1 catalogued claim: %d / %d (%.0f%%). Unmatched sentences remain in "
         "the inventory as sentence units." % (mapped, nsent, 100 * mapped / nsent), "",
         "## Catalogued claims stated in more than one location", "",
         "Location = section (body) or float label (caption). A pattern hit is a candidate; read the "
         "sentence in inventory_before.csv before cutting anything.", ""]
    nloc = lambda cid: len({h[2] for h in hits.get(cid, [])})
    for cid, tag, stmt, _ in sorted(compiled, key=lambda c: (-nloc(c[0]), c[0])):
        locs = collections.Counter(h[2] for h in hits.get(cid, []))
        if len(locs) > 1:
            L.append("- **%s**%s %s — **%d locations / %d sentences**: %s" % (
                cid, " [%s]" % tag if tag else "", stmt, len(locs), sum(locs.values()),
                "; ".join(("%s ×%d" % kv) if kv[1] > 1 else kv[0] for kv in locs.items())))
    L += ["", "## Catalogued claims in exactly one location", "",
          ", ".join(c[0] for c in compiled if nloc(c[0]) == 1), "",
          "## Catalogued claims NOT located by their patterns", ""]
    L += ["- %s%s %s" % (c[0], " [%s]" % c[1] if c[1] else "", c[2]) for c in compiled if nloc(c[0]) == 0] or ["(none)"]
    L += ["", "## Distinctive numbers printed in three or more locations", "",
          "Tokens with >= 3 digits, excluding 0.00/1.00-type values; body sections and captions only "
          "(table cells are listed per table in the CSV).", ""]
    numloc = collections.defaultdict(set)
    for r in rows:
        if r["item_type"] == "number" and len(re.sub(r"\D", "", r["group_id"])) >= 3 \
                and r["group_id"] not in {"0.00", "1.00", "0.000", "1.000"}:
            numloc[r["group_id"]].add(r["location"])
    for v, locs in sorted(numloc.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(locs) >= 3:
            L.append("- `%s` — %d: %s" % (v, len(locs), "; ".join(sorted(locs))))
    (MEAS / "redundancy_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(dict(counts), "mapped %d/%d" % (mapped, nsent))


if __name__ == "__main__":
    main()
