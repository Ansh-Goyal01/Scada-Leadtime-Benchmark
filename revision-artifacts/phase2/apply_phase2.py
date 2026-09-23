"""Phase 2 manuscript edit: the forest plot (paper/make_forest.py -> fig_forest.pdf)
replaces the cross-dataset bar chart. Label fig:crossdataset is kept (same role).
Every replacement is asserted to match exactly once.
"""
import pathlib

TEX = pathlib.Path(__file__).resolve().parents[2] / "paper/files/scada_ijphm.tex"
s = TEX.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


sub("\\includegraphics[width=\\textwidth]{fig_crossdataset}",
    "\\includegraphics[width=\\textwidth]{fig_forest.pdf}")
sub("\\caption{Median run-level lead-time difference (aggregate $-$ decimate) per dataset and detector, annotated with the unit of inference ($n=3$ IMS, $n=10$ XJTU, $n=6$ FEMTO, $n=6$ Ferrara), plus the $n=1$ ONGC case study (Appendix~D.2). IMS shows a positive median shift for most magnitude detectors, not consistent across its three runs; the inferential XJTU, FEMTO, and Ferrara differences are ${\\approx}0$ on this scale. The cross-dataset headline is a null result. ONGC bars are hatched to mark the $n=1$ descriptive case study as separate from the four inferential datasets.}",
    "\\caption{Run-level aggregate$-$decimate lead-time difference (h) per detector; the unit of inference is in each panel title. XJTU-SY, FEMTO, Ferrara: mean (dot) and 95\\% bootstrap CI over runs (Table~\\ref{tab:crossds}). IMS, on a wider scale: the three per-run differences and their median (diamond). ONGC: the descriptive $n=1$ median (hollow), a case study outside the four inferential datasets (Appendix~D.2). IMS and ONGC values are in Table~\\ref{tab:imsongc}. Shaded: the $\\pm 1$~h equivalence margin.}")
sub("a positive but non-significant median shift on IMS that is not consistent across its three runs, and null effects on ONGC and XJTU.",
    "a positive but non-significant median shift on IMS that is not consistent across its three runs, and null effects on XJTU-SY, FEMTO, Ferrara and ONGC, every interval inside the $\\pm 1$~h margin.")
TEX.write_text(s, encoding="utf-8")
print("Phase 2 edits applied")
