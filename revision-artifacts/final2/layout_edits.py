"""Part 5 layout: set the four appendix tables in \\footnotesize, as the body tables
(Tables 3, 5, 6) already are. No content changes; every edit is guarded."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
GEN = ROOT / "paper" / "make_shortened_tables.py"
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
SMALL, FOOT = "\\small", "\\footnotesize"


def swap(path, label):
    s = path.read_bytes().decode("utf-8")
    i = s.find("\\label{" + label + "}")
    assert i > 0, label
    j = s.rfind("\\begin{table", 0, i)
    head_end = s.find("\n", j)
    head = s[j:head_end]
    assert head.count(SMALL) == 1, (label, head)
    s = s[:j] + head.replace(SMALL, FOOT) + s[head_end:]
    path.write_bytes(s.encode("utf-8"))
    print("footnotesize:", label)


for label in ("tab:mechanism", "tab:hyperparams"):
    swap(GEN, label)
for label in ("tab:deeparch", "tab:basestats"):
    swap(TEX, label)
