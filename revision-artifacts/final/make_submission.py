"""Final pass, Part 7 -- build the submission/ PDFs.

  submission/scada_ijphm_revised.pdf  copy of the verified build paper/files/scada_ijphm.pdf
  submission/response_to_review.pdf   IJPHM-Response-to-Review-FINAL.md -> HTML (markdown-it)
                                      -> PDF (headless Chrome --print-to-pdf), author box removed

Run: python revision-artifacts/final/make_submission.py [scratch_dir]
"""
import pathlib, re, shutil, subprocess, sys, tempfile

import pypdf
from markdown_it import MarkdownIt

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "submission"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CSS = """
@page { size: Letter; margin: 22mm 20mm 20mm 20mm; }
body { font-family: "Times New Roman", Times, serif; font-size: 11pt; line-height: 1.38; color: #111; }
h1 { font-size: 17pt; margin: 0 0 10pt; }
h2 { font-size: 13pt; margin: 16pt 0 6pt; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; }
p { margin: 5pt 0; text-align: justify; }
blockquote { margin: 10pt 0 6pt; padding: 4pt 10pt; border-left: 3px solid #888; background: #f4f4f4;
             font-style: italic; page-break-inside: avoid; }
blockquote p { margin: 2pt 0; }
hr { border: 0; border-top: 1px solid #bbb; margin: 12pt 0; }
ol, ul { margin: 4pt 0 4pt 18pt; padding: 0; }
li { margin: 2pt 0; }
"""


def strip_author_box(md):
    """Drop any '> **FOR THE AUTHOR' blockquote (its '>' lines and the blank line after it)."""
    out, skipping = [], False
    for line in md.split("\n"):
        if line.startswith("> **FOR THE AUTHOR"):
            skipping = True
        if skipping:
            if line.startswith(">"):
                continue
            skipping = False
            if not line.strip():
                continue
        out.append(line)
    return "\n".join(out)


def main(scratch):
    OUT.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "paper" / "files" / "scada_ijphm.pdf", OUT / "scada_ijphm_revised.pdf")

    md = strip_author_box((ROOT / "IJPHM-Response-to-Review-FINAL.md").read_text(encoding="utf-8"))
    assert "FOR THE AUTHOR" not in md
    body = MarkdownIt("commonmark").render(md)
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>Response to Review</title>"
            "<style>%s</style></head><body>%s</body></html>" % (CSS, body))
    page = pathlib.Path(scratch) / "response_to_review.html"
    page.write_text(html, encoding="utf-8")
    target = OUT / "response_to_review.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=%s" % target, page.as_uri()], check=True, timeout=120,
                   capture_output=True)

    for f in (OUT / "scada_ijphm_revised.pdf", target):
        r = pypdf.PdfReader(f)
        text = re.sub(r"\s+", " ", " ".join(p.extract_text() for p in r.pages))
        print("%-28s %2d pages %8d bytes" % (f.name, len(r.pages), f.stat().st_size))
        if f == target:
            assert "FOR THE AUTHOR" not in text
            for s in ("v1.3.0", "1040", "181", "22 pages", "only Hotelling T",
                      "Validity counts included alarms the gate could not evaluate", "48 of 230"):
                assert s in text, s


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp())
