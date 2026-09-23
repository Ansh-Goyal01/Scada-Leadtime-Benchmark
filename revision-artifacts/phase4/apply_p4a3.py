"""Phase 4a (third pass).

1. Abstract to <= 280 rendered words (counted on the PDF, conservatively: pdftotext splits
   'n = 10' into three tokens). Required elements kept: metric, question, +-1 h margin with
   its justification (D17), 33 of 33, Holm 0 of 44, D20 asymmetry, G4 deep scoping.
2. 'FEMTO/PRONOSTIA' is an unbreakable 16-character token; the preamble defines
   \\PHMslashbreak for it (F9) but it was never applied, and a rewrite put one at a line end,
   overprinting the right column on p.3 (seen in the render). Apply it in body paragraphs
   (not headings or captions, which are moving arguments).
"""
from p4lib import Doc

d = Doc()
d.para("Bearing anomaly detectors are usually scored by classification accuracy",
       "Bearing anomaly detectors are usually scored by classification accuracy, which ignores how early a warning arrives and at what false-alarm cost. We make lead time the primary evaluation object with a latch-on-resistant, false-alarm-gated metric: warning time counts only when the pre-onset false-alarm rate is within a budget $\\tau$, so a constant-on detector is provably invalid. With it we test whether a SCADA historian's bin-averaged logging destroys lead time relative to decimation. Eleven detectors---four statistical process control (SPC) charts, Isolation Forest, three deep reconstruction autoencoders, a root-mean-square (RMS) trend baseline and two one-class models---run under a controlled sampling sweep on four inferential datasets: XJTU-SY ($n=10$), FEMTO/PRONOSTIA ($n=6$), University of Ferrara ($n=6$) and NASA IMS ($n=3$). On IMS the variance-sensitive charts shift positively ($3\\sigma$ $+15.1$~h) but inconsistently across runs; no test survives Holm correction ($N=44$; 0 of 44). Against a pre-specified $\\pm 1$~h margin, the resolution at which a planner can act, the difference is equivalent to zero in all 33 cells of the three multi-bearing campaigns, none favouring decimation beyond $-0.45$~h; IMS is too wide to decide in 9 of 11 cells and favours aggregation beyond the margin in 2. A single gas-turbine record of the Oil and Natural Gas Corporation (ONGC) cannot be tested. The powered campaigns are short-lived bearings, on which an IMS-sized effect could not appear, so the null bounds the effect at minutes, not hours. On these bearings deep models do not overtake the charts at any training fraction in $[0.20, 0.60]$; long-runway assets remain open. Code and results: \\nburl{https://github.com/Ansh-Goyal01/Scada-Leadtime-Benchmark}.")

lines = d.s.split("\n")
start = next(i for i, ln in enumerate(lines) if ln.startswith("\\section{Introduction}"))
n = 0
for i in range(start, len(lines)):
    ln = lines[i]
    if ln.lstrip().startswith(("\\section", "\\subsection", "\\caption", "%")) or "\\caption{" in ln:
        continue
    if "FEMTO/PRONOSTIA" in ln:
        n += ln.count("FEMTO/PRONOSTIA")
        lines[i] = ln.replace("FEMTO/PRONOSTIA", "FEMTO/\\PHMslashbreak PRONOSTIA")
d.s = "\n".join(lines)
print("slash breaks applied:", n)
d.save()
