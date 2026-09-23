"""Phase 4g -- final tightening (22 pages, last page ~60% full).

- tab:deeparch (G5, stays in the paper): the five rows identical for all four models
  (Adam, 10^-3, 32, 42, early stopping none) move into one caption sentence; every value
  and the explicit 'no early stopping' statement survive.
- tab:imsdet caption trimmed (PH is defined in Section 6.11; the single-run caveat is the
  Section 6.1 LSTM-AE sentence).
- Data Availability: first sentence tightened; the G7 ONGC path enumeration is untouched.
"""
import pathlib
from p4lib import Doc

d = Doc()
for row in ("Optimiser & Adam & Adam & Adam & Adam \\\\", "Learning rate & $10^{-3}$ & $10^{-3}$ & $10^{-3}$ & $10^{-3}$ \\\\",
            "Batch size & 32 & 32 & 32 & 32 \\\\", "Early stopping & none & none & none & none \\\\",
            "Seed & 42 & 42 & 42 & 42 \\\\"):
    lines = d.s.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln.strip() == row]
    assert len(hits) == 1, (len(hits), row)
    del lines[hits[0]]
    d.s = "\n".join(lines)
d.sub("Parameters are counted at the 49-dimensional input (Appendix~B). Deep SVDD scores single windows.}",
      "Parameters are counted at the 49-dimensional input (Appendix~B). All four use the Adam optimiser at learning rate $10^{-3}$, batch size 32 and seed 42, with no early stopping. Deep SVDD scores single windows.}")
d.sub("All code---detectors, the leakage-free onset, the gated metric, the sampling sweep, the conformal wrapper, the run-level statistical harness, and the noise/denoiser mechanism test---is released with a pinned environment (requirements.lock.txt, Python 3.13) and a test suite that asserts the metric's resistance to the latch-on exploit, the leakage-free onset, and the run-level sign-test/Holm machinery.",
      "All code (detectors, leakage-free onset, gated metric, sampling sweep, conformal wrapper, run-level statistical harness and the noise/denoiser mechanism test) is released with a pinned environment (requirements.lock.txt, Python 3.13) and a test suite asserting the metric's resistance to the latch-on exploit, the leakage-free onset and the run-level sign-test/Holm machinery.")
d.save()

gen = pathlib.Path(__file__).resolve().parents[2] / "paper/make_shortened_tables.py"
g = gen.read_text(encoding="utf-8")
old = ("IMS, all eleven detectors, in prognostic-horizon order (PH rank 1--11). Raw: mean ungated lead (h) at full resolution and the default 97.5th-percentile threshold, with 95\\%% bootstrap CI over the $n=3$ runs. PH: Saxena prognostic horizon, the best raw lead over the 95th, 99th and 99.5th percentiles. $L_\\tau$: best lead at an operating point whose pre-onset FAR, \\emph{averaged across the three runs}, is within budget $\\tau$ (0.0 = none), so a zero does not exclude a valid point on a single run.")
new = ("IMS, all eleven detectors in prognostic-horizon order (PH rank 1--11). Raw: mean ungated lead (h) at full resolution and the default 97.5th-percentile threshold, with 95\\%% bootstrap CI over the $n=3$ runs. PH: best raw lead over the 95th, 99th and 99.5th percentiles. $L_\\tau$: best lead at an operating point whose pre-onset FAR, \\emph{averaged across the three runs}, is within $\\tau$ (0.0 = none).")
assert g.count(old) == 1
gen.write_text(g.replace(old, new), encoding="utf-8")
print("imsdet caption trimmed")
