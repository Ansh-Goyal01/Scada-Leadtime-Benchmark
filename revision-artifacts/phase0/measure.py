"""Phase 0 measurement of the compiled IJPHM manuscript (no edits).

Inputs : paper/files/scada_ijphm.pdf (the real build) and
         revision-artifacts/phase0/positions.mpos (\\pdfsavepos markers from the
         instrumented copy built by instrument.py; its per-page text was verified
         identical to the real build, so the positions apply to it).
Outputs: revision-artifacts/phase0/floats.csv, page_map.csv, sections_text.json
Run    : python revision-artifacts/phase0/measure.py   (Phase 6 reruns it on the new PDF)
"""
import csv, json, re, statistics, pathlib
import pypdf

ROOT = pathlib.Path(__file__).resolve().parents[2]
PDF = ROOT / "paper/files/scada_ijphm.pdf"
TEX = ROOT / "paper/files/scada_ijphm.tex"
import os
OUT = pathlib.Path(os.environ.get("MEASURE_OUT", ROOT / "revision-artifacts/phase0"))  # positions.mpos in, csv/json out
SP_TO_BP = 72.0 / 72.27 / 65536.0
PT_TO_BP = 72.0 / 72.27
TEXTHEIGHT_BP = 650.43 * PT_TO_BP
COLW_BP, TEXTW_BP = 243.91125 * PT_TO_BP, 505.89 * PT_TO_BP
COL_SPLIT_BP = 300.0                 # left column x = 54 bp, right column x = 315 bp
BODY_TOP, BODY_BOTTOM = 726.0, 70.0  # excludes running head (~748) and folio (~42)
TEXTFLOATSEP, DBLTEXTFLOATSEP = 16.0, 18.0   # PHMSociety.cls, pt
COLS = ((50.0, 300.0), (300.0, 562.0))      # crop x-ranges of the two columns
P1_TITLE_BOTTOM = 540.0                      # p.1 full-width title block is above this
P1_FOOTNOTE_TOP = 110.0                      # p.1 licence footnote (8 pt) is below this, left column
OVERFLOW_BP = 25.0                           # left-column tables overrun by up to 21.5 pt (F9 residue)
HEAD_GAP_BP = 9.0                            # marker = first body baseline; heading sits above +9 bp


def load_marks():
    marks = []
    for ln in (OUT / "positions.mpos").read_text().splitlines():
        p = ln.split(";")
        if p[0] != "PAGEHEIGHT":
            marks.append(dict(tag=p[0], page=int(p[2]),
                              x=int(p[3]) * SP_TO_BP, y=int(p[4]) * SP_TO_BP))
    return marks


def tex_structure():
    tex = TEX.read_text(encoding="utf-8").split("\n")
    heads = {}
    for i, ln in enumerate(tex, 1):
        m = re.match(r"\s*\\(section|subsection)(\*?)\{(.*)$", ln)
        if m:
            title = re.split(r"\}\s*(\\label|$)", m.group(3))[0]
            heads[i] = (m.group(1), title)
    # floats may live in \input{gen/...} files: scan the expanded source (order is all
    # that matters for floats; heading line numbers above stay those of the main file)
    expanded = re.sub(r"\\input\{(gen/[^}]+)\}",
                      lambda mm: (TEX.parent / (mm.group(1) + ".tex")).read_text(encoding="utf-8"),
                      "\n".join(tex)).split("\n")
    floats, cur = [], None
    env_re = re.compile(r"\\begin\{(figure\*?|table\*?|algorithm)\}")
    for i, ln in enumerate(expanded, 1):
        m = env_re.search(ln)
        if m:
            cur = dict(env=m.group(1), line=i, label=None)
        if cur and cur["label"] is None:
            lm = re.search(r"\\label\{((?:tab|fig|alg):[^}]*)\}", ln)
            if lm:
                cur["label"] = lm.group(1)
        if cur and ("\\end{%s}" % cur["env"]) in ln:
            floats.append(cur)
            cur = None
    return heads, floats


def build_floats(marks, float_src):
    caps = [m for m in marks if m["tag"] in ("CB", "CE")]
    out = []
    for n, fl in enumerate(float_src, 1):
        t = next(m for m in marks if m["tag"].startswith("FT-") and m["tag"].endswith("-%d" % n))
        e = next(m for m in marks if m["tag"].startswith("FE-") and m["tag"].endswith("-%d" % n))
        wide = fl["env"].endswith("*")
        x0 = 54.0 if (wide or t["x"] < COL_SPLIT_BP) else 315.0
        x1 = x0 + (TEXTW_BP if wide else COLW_BP)
        cb = sorted((c for c in caps if c["page"] == t["page"] and x0 - 2 <= c["x"] <= x1
                     and e["y"] - 2 <= c["y"] <= t["y"] + 2), key=lambda c: -c["y"])
        h = t["y"] - e["y"]
        sep = (DBLTEXTFLOATSEP if wide else TEXTFLOATSEP) * PT_TO_BP
        out.append(dict(n=n, label=fl["label"], env=fl["env"], src_line=fl["line"],
                        page=t["page"], width="full" if wide else "single",
                        top=t["y"], bottom=e["y"], x0=x0, x1=x1, height_bp=h,
                        frac_textheight=h / TEXTHEIGHT_BP,
                        page_equiv=(h + sep) * (2 if wide else 1) / (2 * TEXTHEIGHT_BP),
                        cap=(cb[0]["y"], cb[-1]["y"]) if len(cb) >= 2 else None))
    return out


def crop_text(regions):
    """Text of each region (page, x0, y0, x1, y1) in bp, origin bottom-left.

    xpdf pdftotext 4.00 has no crop flags and pypdf mis-orders math-mode runs
    ('+0.030' comes out as '+0' '.030' interleaved), so: write one cropped copy
    of the page per region (MediaBox = CropBox = region) and let xpdf, which
    discards text outside the box and orders glyphs correctly, extract each.
    """
    import subprocess, tempfile
    from pypdf.generic import RectangleObject
    reader = pypdf.PdfReader(str(PDF))
    writer = pypdf.PdfWriter()
    for (pg, x0, y0, x1, y1) in regions:
        page = writer.add_page(reader.pages[pg - 1])
        box = RectangleObject([x0, y0, x1, y1])
        page.mediabox = box
        page.cropbox = box
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "regions.pdf"
        writer.write(str(tmp))
        out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(tmp), "-"], capture_output=True,
                             text=True, encoding="utf-8", check=True).stdout
    pages = out.split("\f")
    assert len(pages) >= len(regions), (len(pages), len(regions))
    return [re.sub(r"\s+", " ", t).strip() for t in pages[:len(regions)]]


def heading_re(title):
    """Match a rendered heading at the END of a text piece.

    Letters only, any non-letters between them: survives numbering, math
    ('$n=10$' -> 'n = 10') and small caps ('R EPRODUCIBILITY')."""
    letters = re.sub(r"[^A-Za-z]", "", re.sub(r"\\[a-zA-Z]+", "", title))
    return re.compile(r"(?:\b\d+(?:\.\d+)*\.?\s*)?" + r"[\W\d_]*".join(map(re.escape, letters))
                      + r"[\W\d_]*$", re.I)


def join_lines(parts):
    """Join extracted lines into running text, undoing end-of-line hyphenation."""
    text = ""
    for ln in parts:
        if text.endswith("-") and ln[:1].islower():
            text = text[:-1] + ln
        else:
            text = (text + " " + ln) if text else ln
    return re.sub(r"\s+", " ", text).strip()


ABBREV = r"(?<!\be\.g)(?<!\bi\.e)(?<!\bet al)(?<!\bvs)(?<!\bcf)(?<!\bEq)(?<!\bFig)(?<!\bSec)(?<!\bApp)(?<!\bIso)"


def sentences(text):
    parts = re.split(ABBREV + r"(?<=[.!?])[\"”’)]*\s+(?=[A-Z(“\"$\[])", text)
    return [s for s in (p.strip() for p in parts) if len(words(s)) >= 3]


def words(s):
    return [w for w in s.split() if re.search(r"[A-Za-z0-9]", w)]


def p90(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.9 * (len(xs) - 1))))] if xs else 0


def main():
    marks = load_marks()
    heads, float_src = tex_structure()
    floats = build_floats(marks, float_src)

    secs = [dict(line=0, level="front", title="Front matter: title, abstract, keywords",
                 key=(1, 0, -1e9))]
    for m in marks:
        if m["tag"].startswith("S-"):
            sl = int(m["tag"][2:])
            col = 0 if m["x"] < COL_SPLIT_BP else 1
            y = m["y"] + HEAD_GAP_BP          # keeps the first body line with its section
            secs.append(dict(line=sl, level=heads[sl][0], title=heads[sl][1], y=y,
                             key=(m["page"], col, -y)))
    secs.sort(key=lambda s: s["key"])
    refs = dict(line=-1, level="section*", title="References", key=None)

    def sec_of(k):
        best = secs[0]
        for s in secs:
            if s["key"] <= k:
                best = s
        return best

    regions, owners = [], []          # owners: ("sec", line, page) | ("float", label, part)
    npages = len(pypdf.PdfReader(str(PDF)).pages)
    regions.append((1, 50.0, P1_TITLE_BOTTOM, 562.0, BODY_TOP)); owners.append(("sec", 0, 1))
    for p in range(1, npages + 1):
        for col, (cx0, cx1) in enumerate(COLS):
            top = P1_TITLE_BOTTOM if p == 1 else BODY_TOP
            bottom = P1_FOOTNOTE_TOP if (p == 1 and col == 0) else BODY_BOTTOM
            blocked = sorted((f["bottom"] - 4, f["top"] + 4) for f in floats if f["page"] == p and
                             (f["width"] == "full" or (f["x0"] < COL_SPLIT_BP) == (col == 0)))
            free, hi = [], top
            for b_lo, b_hi in sorted(blocked, key=lambda b: -b[1]):
                if b_hi < hi:
                    free.append((max(b_hi, bottom), hi))
                hi = min(hi, b_lo)
            free.append((bottom, hi))
            cuts = sorted((s["y"] for s in secs[1:] if s["key"][0] == p and s["key"][1] == col), reverse=True)
            for lo, hi in free:
                if hi - lo < 2:
                    continue
                edges = [hi] + [c for c in cuts if lo < c < hi] + [lo]
                for a, b in zip(edges, edges[1:]):
                    s = sec_of((p, col, -(a - 0.5)))
                    regions.append((p, cx0, b, cx1, a)); owners.append(("sec", s["line"], p))
    for f in floats:
        ovf = OVERFLOW_BP if f["width"] == "single" and f["x0"] < COL_SPLIT_BP else 6.0
        fx0, fx1, lo, hi = f["x0"] - 3, f["x1"] + ovf, f["bottom"] - 3, f["top"] + 3
        if f["cap"]:
            c_hi, c_lo = f["cap"][0] + 3, f["cap"][1] - 3
            regions.append((f["page"], fx0, c_lo, fx1, c_hi)); owners.append(("float", f["label"], "caption"))
            for a, b in ((hi, c_hi), (c_lo, lo)):
                if a - b > 4:
                    regions.append((f["page"], fx0, b, fx1, a)); owners.append(("float", f["label"], "body"))
        else:
            regions.append((f["page"], fx0, lo, fx1, hi)); owners.append(("float", f["label"], "body"))

    body = {s["line"]: [] for s in secs + [refs]}
    pages = {s["line"]: set() for s in secs + [refs]}
    ftext = {f["label"]: {"caption": [], "body": []} for f in floats}
    head_res = [heading_re(t) for _, t in heads.values()]
    for (kind, key, extra), txt in zip(owners, crop_text(regions)):
        if not txt:
            continue
        if kind == "float":
            ftext[key][extra].append(txt)
            continue
        for _ in range(4):                       # strip trailing heading(s) of the next section
            m = next((m for r in head_res for m in [r.search(txt)] if m), None)
            if not m:
                break
            txt = txt[:m.start()].rstrip()
        sec = next(s for s in secs if s["line"] == key)
        if sec["title"].startswith("Data and Code"):
            parts = re.split(r"R ?EFERENCES", txt, maxsplit=1)
            if sec["title"].startswith("Data and Code") and len(parts) == 2:
                body[key].append(parts[0]); pages[key].add(extra)
                body[-1].append(parts[1]); pages[-1].add(extra)
                continue
            if sec["title"].startswith("Data and Code") and body[-1]:
                body[-1].append(txt); pages[-1].add(extra)
                continue
        body[key].append(txt)
        pages[key].add(extra)

    order = secs[:]
    da = next(i for i, s in enumerate(order) if s["title"].startswith("Data and Code"))
    order.insert(da + 1, refs)
    rows, dump = [], {}
    for s in order:
        text = join_lines(body[s["line"]])
        sl = [len(words(x)) for x in sentences(text)]
        pg = sorted(pages[s["line"]])
        rows.append(dict(src_line=s["line"], level=s["level"], title=s["title"],
                         page_start=pg[0] if pg else "", page_end=pg[-1] if pg else "",
                         words=len(words(text)), sentences=len(sl),
                         mean_sent=round(statistics.mean(sl), 1) if sl else "",
                         p90_sent=p90(sl)))
        dump[s["title"]] = text
    for f in floats:
        f["caption_words"] = len(words(join_lines(ftext[f["label"]]["caption"])))
        f["caption_text"] = join_lines(ftext[f["label"]]["caption"])
        f["body_text"] = join_lines(ftext[f["label"]]["body"])

    with open(OUT / "page_map.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    cols = ["n", "label", "env", "width", "page", "height_bp", "frac_textheight",
            "page_equiv", "caption_words", "src_line"]
    with open(OUT / "floats.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for f in floats:
            w.writerow({**f, "height_bp": round(f["height_bp"], 1),
                        "frac_textheight": round(f["frac_textheight"], 3),
                        "page_equiv": round(f["page_equiv"], 3)})
    dump["__floats__"] = {f["label"]: {"caption": f["caption_text"], "body": f["body_text"]} for f in floats}
    (OUT / "sections_text.json").write_text(json.dumps(dump, indent=1, ensure_ascii=False), encoding="utf-8")
    print("sections", len(rows), "floats", len(floats), "pages", len(pypdf.PdfReader(str(PDF)).pages))


if __name__ == "__main__":
    main()
