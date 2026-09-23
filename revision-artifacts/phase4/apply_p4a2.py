"""Phase 4a (second pass): abstract to <= 280 words; remove the overfull 'Test/Validation'
token. Every abstract element required by the plan stays: the metric, the question, the
+-1 h margin with its justification (D17), 33 of 33, Holm 0 of 44, the lifetime asymmetry
(D20) and the deep-model scoping (G4). Items dropped from the abstract are stated in the
body: smallest adjusted p = 1.00 (Sec. 6.7), '3-sigma on FEMTO' for -0.45 h (Sec. 6.4).
"""
from p4lib import Doc

d = Doc()
d.para("Anomaly detectors for rolling-element-bearing prognostics are usually scored",
       "Bearing anomaly detectors are usually scored by classification accuracy, which ignores how early a warning arrives and at what false-alarm cost. We make lead time the primary evaluation object with a latch-on-resistant, false-alarm-gated metric: warning time counts only when the pre-onset false-alarm rate is within a stated budget $\\tau$, so a constant-on detector is provably invalid. With it we ask whether the bin-averaged logging of a SCADA historian destroys lead time relative to decimation. Eleven detectors (four statistical process control (SPC) charts, Isolation Forest, three deep reconstruction autoencoders, a root-mean-square (RMS) trend baseline and two one-class models) are evaluated under a controlled sampling sweep on four inferential run-to-failure datasets: XJTU-SY ($n=10$), FEMTO/PRONOSTIA ($n=6$), University of Ferrara ($n=6$) and NASA IMS ($n=3$). On IMS the variance-sensitive charts show a positive median shift ($3\\sigma$ $+15.1$~h) that is inconsistent across runs; no test survives Holm correction across the $N=44$ family (0 of 44). Against a pre-specified $\\pm 1$~h margin, the resolution at which a maintenance planner can act, the aggregate-minus-decimate difference is equivalent to zero in all 33 dataset $\\times$ detector cells of the three multi-bearing campaigns, and no interval favours decimation beyond $-0.45$~h. On IMS the intervals are too wide at $n=3$ to decide in 9 of 11 cells and favour aggregation beyond the margin in 2; an $n=1$ gas-turbine record of the Oil and Natural Gas Corporation (ONGC) cannot be tested. The powered campaigns are short-lived bearings, on which an effect of the IMS magnitude could not appear, so the null bounds the effect at the scale of minutes, not hours. On these bearings deep models do not overtake the charts at any training fraction in $[0.20, 0.60]$; long-runway assets remain open. Code and results: \\nburl{https://github.com/Ansh-Goyal01/Scada-Leadtime-Benchmark}.")
d.sub("RUL-error score on deliberately truncated Test/Validation copies.",
      "RUL-error score on deliberately truncated Test and Validation copies.")
d.save()
