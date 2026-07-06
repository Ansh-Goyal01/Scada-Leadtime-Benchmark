# -*- coding: utf-8 -*-
"""Phase-2 polish fixes for scada_journal.tex (prose/captions only, no numbers)."""
import re, sys, io
from collections import Counter

SRC = r"C:\scada\paper\scada_journal.tex"
s = io.open(SRC, encoding="utf-8").read()
orig = s
rep = []

def lit(name, old, new):
    global s
    c = s.count(old)
    if c != 1:
        rep.append(f"FAIL {name}: found {c}")
        return
    s = s.replace(old, new)
    rep.append(f"ok   {name}")

# 1) Section VI bridging sentence (framing/structure reconciliation)
lit("vi_bridge",
    "We summarize the outcomes first, then support each in turn.\n\n\\textbf{(i) The metric behaves.}",
    "We summarize the outcomes first, then support each in turn. We present IMS first\n"
    "for its raw-waveform mechanism access; XJTU-SY ($n{=}10$) is the primary\n"
    "inferential test.\n\n\\textbf{(i) The metric behaves.}")

# 2) (ii) summary bullet -> point ONGC to Appendix E
lit("ii_ongc_pointer",
    "On the real ONGC turbine the difference is \\textbf{about a minute} ($n{=}1$ case\nstudy, Table~\\ref{tab:ongc_paired});",
    "On the real ONGC turbine the difference is \\textbf{about a minute} ($n{=}1$ case\nstudy, Appendix~E, Table~\\ref{tab:ongc_paired});")

# 3) fig:cross caption -> demote ONGC to case study (Appendix E)
lit("figcross_caption",
    "\\caption{Median run-level lead-time difference (aggregate $-$ decimate) per\n"
    "dataset and detector, annotated with the unit of inference ($n{=}3$ IMS,\n"
    "$n{=}1$ ONGC case study, $n{=}10$ XJTU, $n{=}6$ FEMTO, $n{=}6$ Ferrara). IMS shows a\n"
    "consistent positive trend; ONGC, XJTU, FEMTO, and Ferrara differences are $\\approx$0\n"
    "on this scale. The honest cross-dataset headline is \\emph{non-destruction}. ONGC bars\n"
    "are shown with hatching to distinguish the $n{=}1$ descriptive case study from the\n"
    "inferential datasets (IMS $n{=}3$, XJTU $n{=}10$, FEMTO $n{=}6$, Ferrara $n{=}6$); all\n"
    "seven non-sequence detectors are shown.}",
    "\\caption{Median run-level lead-time difference (aggregate $-$ decimate) per\n"
    "dataset and detector, annotated with the unit of inference ($n{=}3$ IMS,\n"
    "$n{=}10$ XJTU, $n{=}6$ FEMTO, $n{=}6$ Ferrara), plus the $n{=}1$ ONGC case study\n"
    "(Appendix~E). IMS shows a consistent positive trend; the inferential XJTU, FEMTO,\n"
    "and Ferrara differences are $\\approx$0 on this scale. The honest cross-dataset\n"
    "headline is \\emph{non-destruction}. ONGC bars are hatched to mark the $n{=}1$\n"
    "descriptive case study (Appendix~E) as separate from the four inferential\n"
    "datasets; all seven non-sequence detectors are shown.}")

# 4) Appendix E: delete stray leftover subsection heading (keep one clean case study)
lit("appE_stray_heading",
    "\\subsection{Real turbine SCADA (ONGC): a single-asset case study}\n"
    "On genuine 10\\,s industrial SCADA data ending in a real operator shutdown, every",
    "On genuine 10\\,s industrial SCADA data ending in a real operator shutdown, every")

# 5-8) "ten detectors" -> "ten evaluated detectors" (consistency w/ nine-headline framing)
lit("ten_femto_prose",
    "Across all ten detectors (every one runs on the full",
    "Across all ten evaluated detectors (every one runs on the full")
lit("ten_femto_caption",
    "collapsing within-bearing sampling factors. All ten detectors run on\nthe full $n{=}6$ (bearings are long enough",
    "collapsing within-bearing sampling factors. All ten evaluated detectors (nine\nheadline plus Deep SVDD) run on the full $n{=}6$ (bearings are long enough")
lit("ten_ims_prose",
    "gives the run-level test over all ten detectors.",
    "gives the run-level test over all ten evaluated detectors.")
lit("ten_cost_prose",
    "not compute-bound for any of the ten detectors, deep models included;",
    "not compute-bound for any of the ten evaluated detectors, deep models included;")

# integrity: no data row (contains & and ends \\) may change
row = re.compile(r"^(?![ \t]*%).*&.*\\\\[ \t]*$", re.M)
co, cn = Counter(m.group(0).strip() for m in row.finditer(orig)), Counter(m.group(0).strip() for m in row.finditer(s))
delta = (co - cn) + (cn - co)

print("\n".join(rep))
print("data-row delta (must be empty):", dict(delta) if delta else "OK none changed")
if any(r.startswith("FAIL") for r in rep) or delta:
    print("*** NOT WRITING ***"); sys.exit(1)
io.open(SRC, "w", encoding="utf-8", newline="\n").write(s)
print("*** WROTE ***")
