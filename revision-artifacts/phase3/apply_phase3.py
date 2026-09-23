"""Phase 3 -- caption discipline. A caption states what is shown and how to read it;
interpretation lives in the text. Each removed interpretive sentence was confirmed to
exist in the body (see the notes beside each edit); caption-only content is MOVED to the
text, never deleted. Every replacement is asserted to match exactly once.

Edits the manuscript and the caption strings in paper/make_shortened_tables.py.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "paper/files/scada_ijphm.tex"
GEN = ROOT / "paper/make_shortened_tables.py"


def sub(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:90])
    return s.replace(old, new)


t = TEX.read_text(encoding="utf-8")
g = GEN.read_text(encoding="utf-8")

# ---------------------------------------------------------------- captions in the .tex
t = sub(t, "\\caption{Datasets used in this study. ``Role'' indicates the function each dataset plays in the argument. The four inferential datasets supply the run-level statistics; ONGC is a single-asset case study (Appendix~D.2) and Paderborn is excluded.}",
        "\\caption{Datasets. ``Role'' is the function each plays in the argument: the four inferential datasets supply the run-level statistics, ONGC is a single-asset case study (Appendix~D.2) and Paderborn is excluded.}")
# onset: stability to k, decoupled shift, headline unaffected -> all stated in Sec. 6.2 text
t = sub(t, " The default onset is stable to $k$; it shifts materially under the decoupled indicators on the slow-degrading tests 2 and 3, but the headline is computed on raw lead and is unaffected by this choice.}", "}")
# robust: interpretation stated in Sec. 6.2; the "3.4 h / 0.37 h" bound moves to the text below
t = sub(t, "\\caption{Robustness of the IMS and XJTU-SY results. (a) Alarm persistence on IMS: run-level median aggregate$-$decimate lead-time difference (h) and the $3\\sigma$ valid-alarm fraction (at full resolution, and pooled over the five sampling factors) at persistence $\\in \\{1,3,5,10\\}$ windows. The median direction is stable; the pooled $3\\sigma$ valid-alarm fraction halves by persistence 10. (b) Historian gaps: mean valid lead time (h) under random gaps of 0\\%, 5\\% and 20\\%, averaged over the runs on which the alarm is valid and then over \\emph{five independent gap draws} per level (defect D18): one draw cannot separate a gap effect from the draw. Valid-alarm fractions are unchanged across gap levels and across draws on IMS (2/3 for each detector at every level); on XJTU-SY they move by at most two bearings across draws. Only one cell is materially draw-dependent: Hotelling $T^2$ on IMS at 20\\%, which ranges from 58.0 to 186.1~h over the five draws. Every other cell varies by less than 3.4~h on IMS and 0.37~h on XJTU-SY across draws.}",
        "\\caption{Robustness on IMS and XJTU-SY. (a) Alarm persistence on IMS: run-level median aggregate$-$decimate lead-time difference (h) and the $3\\sigma$ valid-alarm fraction, at full resolution and pooled over the five sampling factors, at persistence $\\in \\{1,3,5,10\\}$ windows. (b) Historian gaps: mean valid lead time (h) under random gaps of 0\\%, 5\\% and 20\\%, averaged over the runs with a valid alarm and then over \\emph{five independent gap draws} per level (defect D18).}")
t = sub(t, "and move by at most two bearings on XJTU-SY.",
        "and move by at most two bearings on XJTU-SY; apart from Hotelling $T^2$ on IMS at 20\\%, every cell of Table~\\ref{tab:robust}b varies across draws by less than 3.4~h on IMS and 0.37~h on XJTU-SY.")
t = sub(t, "\\caption{Detection lead time vs effective SCADA logging interval on IMS (controlled sweep, mean across runs). Aggregation (left) preserves lead time as the interval coarsens far better than decimation (right), where the variance-sensitive detectors collapse at coarse rates.}",
        "\\caption{Detection lead time vs effective SCADA logging interval on IMS (controlled sweep, mean across runs): aggregation (left) and decimation (right).}")
# conformal: every panel's interpretation is in Sec. 6.8
t = sub(t, "\\caption{Conformal calibration: empirical pre-onset FAR vs target $\\alpha$; points on or below the diagonal satisfy the distribution-free guarantee. (a) IMS: test 1 violates it because its near-failure onset leaves no genuinely stationary normal region. (b) XJTU-SY: bearings with a substantial stationary pre-onset region honor the bound; those with only one or two pre-onset windows cannot support a finite-sample guarantee and are flagged uncalibrated. (c) FEMTO/PRONOSTIA: no bearing honors the bound at $\\alpha=0.05$, because the short, non-stationary pre-onset regions of these 1.4--7.8~h bearings cannot support it. (d) ONGC turbine ($n=1$ case study, Appendix~D.2): the real historian stream tracks the diagonal closely, a modest 1.5--2$\\times$ above target, consistent with a mostly-stationary normal region. \\ConformalPanelA}",
        "\\caption{Conformal calibration: empirical pre-onset FAR vs target $\\alpha$ for (a) IMS, (b) XJTU-SY, (c) FEMTO/PRONOSTIA and (d) the ONGC turbine ($n=1$ case study, Appendix~D.2). Points on or below the diagonal satisfy the distribution-free guarantee; bearings with only one or two pre-onset windows are flagged uncalibrated. \\ConformalPanelA}")
t = sub(t, "\\caption{Lead-time vs pre-onset-FAR trade-off (threshold percentile swept, mean across runs); up-and-to-the-left is better. (a) IMS: Hotelling $T^2$ and Isolation Forest dominate the achievable frontier---highest lead at the lowest attainable FAR; the RMS-trend baseline collapses at low FAR. (b) The ten XJTU-SY bearings: the same qualitative shape at the shorter absolute lead times these short-lived bearings permit, showing that the operating-point selection generalizes.}",
        "\\caption{Lead-time vs pre-onset-FAR trade-off, threshold percentile swept (mean across runs): (a) IMS, (b) the ten XJTU-SY bearings. Up and to the left is better.}")
t = sub(t, "\\caption{Feature-group ablation generalized beyond Isolation Forest: valid-alarm fraction (mean over the three IMS runs) by group. Time-domain amplitude features are best for every detector; for the SPC charts rms\\_only is uniquely ($3\\sigma$, EWMA) or jointly best, and spectral/envelope/all collapse them to 0.33.}",
        "\\caption{Feature-group ablation on IMS: valid-alarm fraction (mean over the three runs) by feature group, for the six non-sequence detectors.}")
t = sub(t, "\\caption{Valid-alarm fraction vs.\\ training fraction on FEMTO ($n=6$). SPC charts (blue) sit at the top throughout, peaking at the smallest training fraction and declining slightly thereafter as the test window shrinks; the deep reconstruction models (red) and Deep SVDD lie below the SPC baseline (dashed, ${\\approx}0.62$) at every training fraction and never reach it---no crossover. The three N/A cells at $T=0.20$, all on Bearing3\\_1, which forms only 20 training windows, are counted as no valid alarm.}",
        "\\caption{Valid-alarm fraction vs.\\ training fraction $T$ on FEMTO ($n=6$): SPC charts in blue, deep reconstruction models in red, Deep SVDD separately; dashed: the SPC baseline (${\\approx}0.62$). The three N/A cells at $T=0.20$ (Bearing3\\_1, 20 training windows) count as no valid alarm.}")
t = sub(t, "\\caption{Deep-model architectures and training protocol, transcribed from the released\n\t\\texttt{config.py} and model definitions. All four are trained with Adam at a fixed learning\n\trate with no per-dataset tuning and no early stopping: every model runs its full epoch budget.\n\tParameter counts are measured at the $49$-dimensional invariant feature width (Appendix~B).\n\tDeep SVDD scores individual windows and so takes no sequence length.}",
        "\\caption{Deep-model architectures and training protocol, from the released \\texttt{config.py} and model definitions; no per-dataset tuning, and every model runs its full epoch budget. Parameters are counted at the 49-dimensional input (Appendix~B). Deep SVDD scores single windows.}")
# d17label: the last sentence is stated in Appendix C ("no median flips sign", "neither label")
t = sub(t, " Both arms are computed on the 49-dimensional invariant feature schema so that the contrast isolates the label alone. No median changes sign between labels, and no detector reaches $\\alpha=0.05$ under either label.}",
        " Both arms use the 49-dimensional invariant feature schema, so the contrast isolates the label.}")

# ---------------------------------------------------------------- caption-only content -> text
t = sub(t, "(59.7~h of lead at 4.19\\% pre-onset FAR, unchanged across ten random seeds)",
        "(59.67~h of lead at 4.19\\% pre-onset FAR, unchanged across ten random seeds, although its pre-onset FAR averaged across the three runs is 62.00\\%, which is why the across-run gate of Table~\\ref{tab:imsdet} scores it 0.0)")
t = sub(t, "with no interval endpoint reaching $\\pm 0.6$~h.",
        "with no interval endpoint reaching $\\pm 0.6$~h, so the margin is cleared with room to spare.")

# ---------------------------------------------------------------- generated-table captions
g = sub(g, "Run-level aggregate$-$decimate lead-time contrast on the three multi-bearing campaigns, all eleven detectors, collapsing the five within-run sampling factors to one difference per run. Med.\\ and Mean: run-level median and mean difference (h), with the 95\\%% bootstrap CI over runs; $n_+/n_-$ counts non-zero runs only ($^{\\mathrm{s}}$: sign-consistent, every non-zero run of one sign); $p$: exact two-sided sign test. A cell is equivalent when its CI lies inside $[-\\delta,+\\delta]$, $\\delta = 1$~h: all 33 of 33 are, and no endpoint reaches $\\pm 0.6$~h, clearing the margin with an order of magnitude to spare. $^\\ddagger$: length-30 sequence models, $n=3$ on XJTU-SY. Holm--Bonferroni over the $N=44$ family (these 33 tests and the eleven IMS tests of Table~\\ref{tab:imsongc}; ONGC, $n=1$, excluded): no raw $p$ is below 0.05, the smallest is 0.125 (Transformer-AD, FEMTO), and every adjusted $p$ is 1.00, so no hypothesis is rejected. IMS is equivalent in no cell at $n=3$ (intervals too wide) and ONGC is untestable at $n=1$; neither enters the equivalence family.",
        "Run-level aggregate$-$decimate lead-time contrast on the three multi-bearing campaigns, collapsing the five sampling factors to one difference per run. Med., Mean: run-level median and mean difference (h), with the 95\\%% bootstrap CI over runs; $n_+/n_-$: non-zero runs ($^{\\mathrm{s}}$: all of one sign); $p$: exact two-sided sign test. $^\\ddagger$: length-30 sequence models, $n=3$ on XJTU-SY. Equivalent at $\\delta=1$~h when the CI lies inside $[-\\delta,+\\delta]$: all 33 cells. Holm over $N=44$ (these 33 tests and the eleven IMS tests of Table~\\ref{tab:imsongc}): every adjusted $p$ is 1.00. IMS and ONGC are outside the equivalence family.")
g = sub(g, " ONGC: descriptive median over the five sampling factors, in minutes; no inference. Every ONGC difference is about a minute or less.}",
        " ONGC: descriptive median over the five sampling factors, in minutes; no inference.}")
g = sub(g, " $\\bar{n}_{\\text{eff}}$: mean effective sample size once zero-difference runs are dropped. Under both metrics no hypothesis survives Holm correction across the $N=44$ family.}",
        " $\\bar{n}_{\\text{eff}}$: mean effective sample size once zero-difference runs are dropped.}")
g = sub(g, "IMS, all eleven detectors, rows in prognostic-horizon order (PH rank 1--11). Raw: mean ungated lead (h) at full resolution and the default 97.5th-percentile threshold, with 95\\%% bootstrap CI over the $n=3$ runs. PH: Saxena prognostic horizon, the best raw lead over the 95th, 99th and 99.5th percentiles, with no false-alarm constraint. $L_\\tau$: best lead at an operating point whose pre-onset FAR, \\emph{averaged across the three runs}, is within budget $\\tau$ (0.0 = none). $^\\dagger$: no valid operating point at $\\tau=0.10$; the long raw leads of these detectors come from flooding the pre-onset region. The gated ranking at $\\tau=0.10$ is $3\\sigma$, RMS-trend, Deep SVDD, then the eight detectors tied at $L=0$. $^\\ast$: RMS-trend is valid only at the loosest threshold and on one of three runs. Because the gate uses the across-run mean, a zero here does not exclude a valid point on one run: LSTM-AE has a mean pre-onset FAR of 62.00\\%% at the 99.5th percentile but 4.19\\%% FAR and 59.67~h of valid lead on \\texttt{3rd\\_test} alone (Table~\\ref{tab:tradeoff}).",
        "IMS, all eleven detectors, in prognostic-horizon order (PH rank 1--11). Raw: mean ungated lead (h) at full resolution and the default 97.5th-percentile threshold, with 95\\%% bootstrap CI over the $n=3$ runs. PH: Saxena prognostic horizon, the best raw lead over the 95th, 99th and 99.5th percentiles. $L_\\tau$: best lead at an operating point whose pre-onset FAR, \\emph{averaged across the three runs}, is within budget $\\tau$ (0.0 = none), so a zero does not exclude a valid point on a single run. $^\\dagger$: no valid operating point at $\\tau=0.10$. Gated order at $\\tau=0.10$: $3\\sigma$, RMS-trend, Deep SVDD, then eight tied at 0. $^\\ast$: valid only at the loosest threshold and on one of three runs.")
g = sub(g, " The three deep reconstruction models and the one-class SVM are included so that the ``no valid operating point'' claim can be checked per threshold: all twelve of their entries are daggered. LSTM-AE's 99.5th-percentile entry is daggered on the across-run mean (62.0\\%%) although it is within budget on \\texttt{3rd\\_test} alone.}",
        " The three deep reconstruction models and the one-class SVM are listed so the ``no valid operating point'' claim can be checked per threshold: all twelve of their entries are daggered.}")
g = sub(g, " its mean, and the runs with a positive sign; a directional trend that cannot be significance-tested at $n=3$.",
        " its mean, and the runs with a positive sign.")
g = sub(g, " training time and inference in $\\mu$s per window, every one $\\ll$ the 10~s SCADA polling interval.}",
        " training time and inference in $\\mu$s per window.}")

TEX.write_text(t, encoding="utf-8")
GEN.write_text(g, encoding="utf-8")
print("Phase 3 caption edits applied")
