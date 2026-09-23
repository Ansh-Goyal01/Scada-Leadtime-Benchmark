"""Measure the CURRENT manuscript with the Phase 0 method (instrumented copy, validated
text-identical to the real build) into revision-artifacts/<outdir>/.

Run: python revision-artifacts/tools/measure_now.py phase3/measure
Prints: pages, caption words total, float page-equivalents, prose words.
"""
import csv, os, pathlib, shutil, subprocess, sys, tempfile
import pypdf

ROOT = pathlib.Path(__file__).resolve().parents[2]
P0 = ROOT / "revision-artifacts" / "phase0"


def main(rel):
    out = ROOT / "revision-artifacts" / rel
    out.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="instr-"))
    py = sys.executable
    subprocess.run([py, str(P0 / "instrument.py"), str(tmp)], check=True, capture_output=True)
    r = subprocess.run([str(ROOT / "tools" / "tectonic.exe"), "-X", "compile", "--keep-intermediates",
                        "scada_ijphm.tex"], cwd=tmp, capture_output=True, text=True, errors="replace")
    if r.returncode:
        sys.exit("instrumented build failed:\n" + r.stdout[-2000:])
    a = pypdf.PdfReader(str(tmp / "scada_ijphm.pdf"))
    b = pypdf.PdfReader(str(ROOT / "paper/files/scada_ijphm.pdf"))
    diff = [i for i, (p, q) in enumerate(zip(a.pages, b.pages), 1) if p.extract_text() != q.extract_text()]
    if len(a.pages) != len(b.pages) or diff:
        sys.exit("instrumented copy NOT identical to real build: pages %d/%d differ %s" % (
            len(a.pages), len(b.pages), diff))
    shutil.copy2(tmp / "scada_ijphm.mpos", out / "positions.mpos")
    shutil.copy2(tmp / "scada_ijphm.aux", out / "scada_ijphm.aux")
    env = dict(os.environ, MEASURE_OUT=str(out), PYTHONIOENCODING="utf-8")
    subprocess.run([py, str(P0 / "measure.py")], check=True, env=env)
    fl = list(csv.DictReader(open(out / "floats.csv", encoding="utf-8")))
    pm = list(csv.DictReader(open(out / "page_map.csv", encoding="utf-8")))
    print("PAGES", len(b.pages), "| captions", sum(int(f["caption_words"]) for f in fl), "words over",
          len(fl), "floats | float page-equiv %.2f" % sum(float(f["page_equiv"]) for f in fl),
          "| prose words (excl refs)", sum(int(x["words"]) for x in pm if x["title"] != "References"))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
