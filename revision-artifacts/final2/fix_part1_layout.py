"""Part 1 layout follow-up: Table 7 width after the unit headers; drop a redundant sentence."""
import pathlib

TEX = pathlib.Path(__file__).resolve().parents[2] / "paper" / "files" / "scada_ijphm.tex"
s = TEX.read_bytes().decode("utf-8")
NL = "\r\n"
EDITS = [
    ("\t\\label{tab:perbearing}" + NL + "\t\\begin{tabular}{l c r c r r}",
     "\t\\label{tab:perbearing}" + NL + "\t\\setlength{\\tabcolsep}{3.5pt}" + NL + "\t\\begin{tabular}{l c r c r r}"),
    (r"as is a run with no detectable onset. Every validity count in Section~\ref{sec:results} is over "
     r"scoreable evaluations, with the exclusions stated.",
     r"as is a run with no detectable onset."),
]
for old, new in EDITS:
    assert s.count(old) == 1, (s.count(old), old[:60])
    s = s.replace(old, new)
TEX.write_bytes(s.encode("utf-8"))
print("ok", len(EDITS))
