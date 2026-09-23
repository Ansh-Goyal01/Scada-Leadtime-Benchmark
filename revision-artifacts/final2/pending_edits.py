"""Guarded manuscript edits: every old string must occur exactly once. Overwritten per batch;
each batch's old/new text is appended to revision-artifacts/final2/edit_log.md.
"""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
LOG = ROOT / "revision-artifacts" / "final2" / "edit_log.md"
TAB = ROOT / "results" / "tables"
BATCH = "Part 4: factual corrections"

# --- measured values, never typed
o = pd.read_csv(TAB / "onset_sensitivity.csv")
o = o[(o.kind == "rms_kurt") & (o.method == "terminal")]
spread = o.groupby("run").onset_pct.agg(lambda s: s.max() - s.min())
assert spread["1st_test"] < 0.1 and f"{spread['3rd_test']:.1f}" == "1.6" and f"{spread['2nd_test']:.1f}" == "5.4"
w = pd.read_csv(TAB / "femto_training_sweep_long.csv").drop_duplicates(["bearing", "train_fraction"])
assert (w.n_train_windows.min(), w.n_train_windows.max()) == (20, 335)
assert w[w.train_fraction == 0.5].n_train_windows.median() == 88
c = pd.read_csv(TAB / "n20_raw_contrast_old_vs_new.csv")
fer = c[(c.arm == "new") & (c.dataset == "Ferrara")]
assert len(fer) == 11 and fer.median_diff_h.abs().max() * 60 < 1.0          # 0.875 min
t = pd.read_csv(TAB / "tradeoff_IMS.csv")
ew = t[t.short_name == "ewma"].far_preonset_pct_mean
assert round(ew.max(), 1) == 24.6                                             # full sweep exceeds 22.1

EDITS = [
    # S6.2 onset stability (Table 3): test 2 moves 5.4 points
    (r"Across $k \in \{3,4,5\}$ the default onset moves by less than two percent of run span on every run "
     r"(Table~\ref{tab:onset}).",
     r"Across $k \in \{3,4,5\}$ the default onset moves by less than 0.1 percentage points of run span on "
     rf"test~1, {spread['3rd_test']:.1f} on test~3 and {spread['2nd_test']:.1f} on the slow-degrading test~2 "
     r"(Table~\ref{tab:onset})."),
    # S7.4 practical implications, aligned with S4.8
    (r"For practitioners, storing bin-averaged vibration at SCADA rates, the default behavior of most "
     r"historians, does not inherently sacrifice bearing-fault warning time relative to keeping decimated raw "
     r"samples, and may improve it for control-chart detectors on noisy long-runway data.",
     r"For practitioners, storing bin-averaged summary statistics at SCADA rates, the default behavior of most "
     r"historians, rather than keeping every $f$-th stored value changed bearing-fault warning time by less "
     r"than the $\pm 1$~h margin on every multi-bearing campaign tested (Section~\ref{sec:femto}), and may "
     r"improve it for control-chart detectors on noisy long-runway data."),
    # S4.5 training-window range is FEMTO's
    (r"The deep sequence models are data-starved: across bearings and training fractions the runs furnish "
     r"between 20 and 335 normal training windows (median 88 at the default split).",
     r"The deep sequence models are data-starved: across FEMTO bearings and training fractions the runs "
     r"furnish between 20 and 335 normal training windows (median 88 at the default split), and the largest "
     r"IMS run 631."),
    # S4.5 Deep SVDD is absent from Tables 4b and 7
    (r"but its numbers are reported in every result table because",
     r"but its numbers are reported in the main result tables because"),
    # S4.3 caveat
    (r"per-bearing results in Tables~\ref{tab:crossds} and \ref{tab:perbearing} flag these cases explicitly "
     r"rather than silently discarding them.",
     r"the per-bearing results of Table~\ref{tab:perbearing} report these bearings individually rather than "
     r"discarding them."),
    # S6.9 EWMA's full sweep reaches 24.6%
    (r"their pre-onset FAR sitting at 19.0--22.1\% across the swept thresholds,",
     r"their pre-onset FAR sitting at 19.0--22.1\% across the tabulated thresholds (Table~\ref{tab:tradeoff}),"),
    # S6.2 missing data: a run no reviewer saw
    (r"; an earlier single-draw run reported a 128.1~h collapse already at 5\%, a property of that draw that "
     r"we do not state.",
     r"."),
    # S1
    (r"The folklore is refuted on every dataset tested:",
     r"The folklore is not supported on any dataset tested:"),
    (r"with its dataset-dependent direction explicit, as more valuable than a tidy but unsupported positive "
     r"claim.",
     r"with its dataset-dependent direction explicit."),
    # S6.4
    (r"the direction of any residual effect is dataset-specific noise,",
     r"the direction of any residual effect varies by dataset,"),
    # S6.5 Ferrara: post-correction medians are within 1 min
    (r"every run-level median difference is within $\pm5$~min, no detector is sign-consistent across the six",
     r"every run-level median difference is within $\pm1$~min, no detector is sign-consistent across the six"),
    # Appendix D.1 / D.2
    (r"from $-0.35$~h at the native noise level to $+6.6$~h at 10~dB,",
     r"from $-0.35$~h at the native noise level to $+6.60$~h at 10~dB,"),
    (r"(late by approximately $k\sigma_b/m$; Algorithm~\ref{alg:onset})",
     r"(Section~\ref{sec:onset})"),
    (r"\subsection{Leakage-Free Degradation Onset}",
     r"\subsection{Leakage-Free Degradation Onset}" "\r\n" r"\label{sec:onset}"),
    # Data Availability: Ferrara is public; the decoupled-indicator reruns
    (r"The IMS (NASA), XJTU-SY, and FEMTO/\PHMslashbreak PRONOSTIA run-to-failure datasets are publicly "
     r"available from their original providers;",
     r"The IMS (NASA), XJTU-SY, FEMTO/\PHMslashbreak PRONOSTIA and University of Ferrara run-to-failure "
     r"datasets are publicly available from their original providers;"),
    (r"retained as provenance for the indicator comparison; no number reported here depends on them, and the "
     r"aggregate-vs-decimate contrast is taken from the corrected files named above.",
     r"retained as provenance for the indicator comparison; the invariance they establish compares onset "
     r"indicators within one arm, so it does not depend on that correction, and the aggregate-vs-decimate "
     r"contrast is taken from the corrected files named above."),
]


def main():
    s = TEX.read_bytes().decode("utf-8")
    for old, new in EDITS:
        assert s.count(old) == 1, (s.count(old), old[:80])
        s = s.replace(old, new)
    TEX.write_bytes(s.encode("utf-8"))
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"\n## {BATCH}\n")
        for old, new in EDITS:
            fh.write(f"\n- OLD: {old}\n- NEW: {new}\n")
    print(f"{BATCH}: applied {len(EDITS)}")


if __name__ == "__main__":
    main()
