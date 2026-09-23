"""Phase 0 roll-up: per top-level section words/pages/sentence stats, and caption ranking.

Reads revision-artifacts/phase0/{page_map.csv, floats.csv, sections_text.json};
writes revision-artifacts/phase0/section_rollup.csv and prints both tables.
"""
import csv, json, statistics, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from measure import sentences, words, p90

PH0 = pathlib.Path(__file__).parent
pm = list(csv.DictReader(open(PH0 / "page_map.csv", encoding="utf-8")))
texts = json.loads((PH0 / "sections_text.json").read_text(encoding="utf-8"))
texts.pop("__floats__")
fl = list(csv.DictReader(open(PH0 / "floats.csv", encoding="utf-8")))

groups, cur = [], None
for r in pm:
    if r["level"] != "subsection":
        cur = dict(title=r["title"], rows=[])
        groups.append(cur)
    cur["rows"].append(r)

NAMES = {"Front matter: title, abstract, keywords": "Abstract + title"}
out, prose_sl = [], []
for g in groups:
    text = " ".join(texts[r["title"]] for r in g["rows"])
    sl = [len(words(s)) for s in sentences(text)]
    if g["title"] != "References":
        prose_sl += sl
    pages = [int(r[k]) for r in g["rows"] for k in ("page_start", "page_end") if r[k]]
    out.append(dict(section=NAMES.get(g["title"], g["title"]),
                    pages="%d-%d" % (min(pages), max(pages)) if pages else "",
                    words=len(words(text)), sentences=len(sl),
                    mean_sent=round(statistics.mean(sl), 1) if sl else "", p90_sent=p90(sl)))
with open(PH0 / "section_rollup.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
for o in out:
    print("%-58s %6s %6s %4s %5s %4s" % (o["section"][:58], o["pages"], o["words"], o["sentences"],
                                         o["mean_sent"], o["p90_sent"]))
print("TOTAL prose words (excl. references): %d; sentences %d; mean %.1f; p90 %d" % (
    sum(o["words"] for o in out if o["section"] != "References"), len(prose_sl),
    statistics.mean(prose_sl), p90(prose_sl)))
print("Captions: total %d words over %d captions" % (sum(int(f["caption_words"]) for f in fl), len(fl)))
for f in sorted(fl, key=lambda f: -int(f["caption_words"]))[:10]:
    print("   %-20s %4s words" % (f["label"], f["caption_words"]))
