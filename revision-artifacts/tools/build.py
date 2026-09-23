"""Compile the manuscript and report what every phase must measure.

Compiles paper/files/scada_ijphm.tex with tools/tectonic.exe into paper/files (the
shipped PDF), then reports: page count (from the PDF, never the .log), undefined
references/citations, multiply-defined labels, and UNIQUE overfull boxes (tectonic
runs several passes, so raw counts are multiples -- see the emergencystretch memory).

Run: python revision-artifacts/tools/build.py
"""
import pathlib, re, subprocess, sys
import pypdf

ROOT = pathlib.Path(__file__).resolve().parents[2]
FILES = ROOT / "paper" / "files"


def main():
    out = subprocess.run([str(ROOT / "tools" / "tectonic.exe"), "-X", "compile", "scada_ijphm.tex"],
                         cwd=FILES, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = out.stdout + out.stderr
    if out.returncode != 0:
        print(log[-3000:])
        sys.exit("BUILD FAILED")
    pages = len(pypdf.PdfReader(str(FILES / "scada_ijphm.pdf")).pages)
    undef_ref = sorted(set(re.findall(r"Reference `([^']+)' .*undefined", log)))
    undef_cit = sorted(set(re.findall(r"Citation `([^']+)' .*undefined", log)))
    multi = sorted(set(re.findall(r"Label `([^']+)' multiply defined", log)))
    over = sorted(set(re.findall(r"(\S+\.tex):(\d+): Overfull \\hbox \(([\d.]+)pt too wide\)", log)),
                  key=lambda t: (t[0], int(t[1])))
    print("PAGES %d" % pages)
    print("undefined refs %d %s" % (len(undef_ref), undef_ref))
    print("undefined cites %d %s" % (len(undef_cit), undef_cit))
    print("multiply-defined labels %d %s" % (len(multi), multi))
    print("unique overfull hboxes %d %s" % (len(over), ["%s:%s +%spt" % o for o in over]))
    vbox = sorted(set(re.findall(r"(\S+\.tex:\d+): Overfull \\vbox \(([\d.]+)pt too high\)", log)))
    print("unique overfull vboxes %d %s" % (len(vbox), vbox))
    return pages


if __name__ == "__main__":
    main()
