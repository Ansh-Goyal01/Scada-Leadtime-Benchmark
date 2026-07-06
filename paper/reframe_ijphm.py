# -*- coding: utf-8 -*-
"""
IJPHM reframe transform for paper/scada_journal.tex.

Design rule (ABSOLUTE): never retype a table cell. Long/number-bearing blocks are
CAPTURED from the source via regex and MOVED verbatim; only pure-prose spans are
rewritten. At the end we assert that every original data row (a line containing
'&' and ending with '\\\\') still exists in the output with >= its original count,
so no numeric cell can have been altered or dropped (new rows may be added).
"""
import re, sys, io
from collections import Counter

SRC = r"C:\scada\paper\scada_journal.tex"
s = io.open(SRC, encoding="utf-8").read()
orig = s
report = []

def lit(name, old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        report.append(f"FAIL literal {name}: found {c}, expected {n}")
        return
    s = s.replace(old, new)
    report.append(f"ok   literal {name}")

def capture(name, pattern):
    m = re.search(pattern, s, re.DOTALL)
    if not m:
        report.append(f"FAIL capture {name}: no match")
        return None
    report.append(f"ok   capture {name} ({len(m.group(0))} chars)")
    return m.group(0)

def cut(name, pattern):
    global s
    m = re.search(pattern, s, re.DOTALL)
    if not m:
        report.append(f"FAIL cut {name}: no match")
        return None
    blk = m.group(0)
    s = s[:m.start()] + s[m.end():]
    report.append(f"ok   cut {name} ({len(blk)} chars)")
    return blk

def rx_sub(name, pattern, repl, n=1):
    global s
    new_s, c = re.subn(pattern, repl, s, flags=re.DOTALL)
    if c != n:
        report.append(f"FAIL rx_sub {name}: replaced {c}, expected {n}")
        return
    s = new_s
    report.append(f"ok   rx_sub {name}")

# ------------------------------------------------------------------ STEP 1 title
rx_sub("title",
    r"\\title\{Lead-Time-Centric Evaluation of Bearing Anomaly Detectors:\nA Multi-Dataset SCADA Study\}",
    (r"\\title{A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing"
     "\n" r"Anomaly Detection --- and What It Reveals About SCADA-Rate Logging}"))

lit("markboth",
    r"{Goyal: Lead-Time-Centric Evaluation of Bearing Anomaly Detectors}",
    r"{Goyal: A False-Alarm-Gated Lead-Time Metric for Bearing Anomaly Detection}")

# ------------------------------------------------------------------ STEP 2 abstract
NEW_ABSTRACT = r"""\begin{abstract}
Anomaly detectors for rolling-element-bearing prognostics are usually judged by
classification accuracy, which answers \emph{whether} a fault is detected but not
\emph{how early}, nor at what false-alarm cost. We argue that the operationally
decisive quantity is \emph{lead time}---the warning interval before failure---and
we make it the primary object of evaluation through a \emph{latch-on--resistant,
false-alarm-gated} metric. Warning time is credited only when the false-alarm rate
over a data-anchored, leakage-free \emph{pre-onset} region is within a stated
budget $\tau$; we prove by construction (and by a released unit test) that a
degenerate ``latch-on'' detector, which would otherwise score maximal lead time,
is invalidated, while a detector that fires just after the true degradation onset
scores valid at zero false-alarm rate. A formal comparison against the Saxena
prognostic horizon shows the gate is decisive: on IMS the ungated horizon ranks
first exactly the detectors---Hotelling $T^2$, Isolation Forest, and EWMA---that
have \emph{no} valid operating point at a $10\%$ budget, whereas the gated metric
identifies the deployable choice (3$\sigma$), so the two rankings invert at the
top. We then apply the metric to a question of direct industrial relevance: does
the coarse, \emph{bin-averaged} logging of a SCADA historian destroy detection
lead time relative to simple decimation? Using nine detectors---four SPC charts
(3$\sigma$, EWMA, CUSUM, Hotelling $T^2$), Isolation Forest, three deep
reconstruction autoencoders (LSTM, TCN, Transformer), and an RMS-trend
baseline, with Deep SVDD additionally evaluated---under a controlled sweep that
holds window content and alarm persistence constant, we test this across four
inferential run-to-failure datasets: XJTU-SY ($n{=}10$), FEMTO/PRONOSTIA
($n{=}6$), University of Ferrara ($n{=}6$), and NASA IMS ($n{=}3$), with
bootstrap confidence intervals and run-level significance tests. The metric
correctly refuses to manufacture a positive effect. On the large multi-bearing
sets the aggregate-vs-decimate difference is null (median $|$diff$|$ at most eight
minutes, with Isolation Forest even \emph{reversing sign} on FEMTO); on IMS it
shows a \emph{consistent positive trend}---the same sign across all three runs for
every magnitude detector (3$\sigma$ median $+18.4$\,h; Isolation Forest
$+12.2$\,h; EWMA $+5.8$\,h; CUSUM $+5.4$\,h; Hotelling $T^2$ $+4.6$\,h)---but with
only $n{=}3$ independent runs this does not reach significance (exact sign test
floors at $p{=}0.25$) and does not survive multiple-comparison correction. Across
the $N{=}40$ detector$\times$dataset family \textbf{nothing survives Holm
correction} (smallest adjusted $p{=}1.00$). The defensible cross-dataset
conclusion is \textbf{non-destruction}: coarse SCADA-rate logging does not cost
bearing-fault warning time, and averaging is at worst neutral and may stabilize
the health signal. A real single-asset gas-turbine SCADA record
(aggregate-vs-decimate under a minute) is reported as a case study in the appendix
and excluded from the inferential family. We additionally validate a conformal
detector for distribution-free false-alarm control, present a
lead-time--vs--false-alarm trade-off analysis, and report feature-group and
spectral ablations showing that time-domain amplitude/impulsiveness statistics
carry the prognostic signal on IMS. The contribution is a metric that is
statistically honest by construction, together with a reproducible methodology and
an honest, counter-intuitive null result rather than a guaranteed positive effect.
\end{abstract}"""
rx_sub("abstract", r"\\begin\{abstract\}.*?\\end\{abstract\}", lambda m: NEW_ABSTRACT)

# ------------------------------------------------------------- STEP 3+4 contributions
NEW_CONTRIB = r"""\textbf{Contributions.} We make five contributions.
\begin{enumerate}
\item A \emph{latch-on--resistant, false-alarm-gated, onset-relative lead-time
metric}. Warning time is credited only when the false-alarm rate over a
data-anchored, leakage-free pre-onset region is within a stated budget. We
prove---by construction and by a unit test that is part of the released code---that
a constant-on (latch-on) detector is scored invalid, while a detector that fires
just after the true degradation onset scores valid at zero false-alarm rate. We do
not claim the metric is unconditionally ungameable; we discuss residual gaming
surfaces in Section~\ref{sec:threats}.
\item A \emph{formal proof that gating changes the answer}. We give, to our
knowledge, the first formal comparison showing that an ungated prognostic-horizon
metric (the Saxena PH) produces a different and operationally misleading detector
recommendation relative to the false-alarm-budgeted metric
(Section~\ref{sec:saxena}, Tables~\ref{tab:latchon} and~\ref{tab:phrank}): on IMS
the detectors PH ranks first by raw lead---Hotelling $T^2$, Isolation Forest, and
EWMA---each have no valid operating point at a $10\%$ false-alarm budget, whereas
our metric correctly identifies 3$\sigma$ as the deployable choice.
\item A \emph{controlled SCADA-sampling methodology} that holds window content and
alarm persistence constant, so that any lead-time difference between the
historian's \emph{aggregate} mechanism and simple \emph{decimation} reflects
genuine information loss rather than a window-counting artifact of coarser time
grids.
\item A \emph{multi-dataset null result that is statistically honest by
construction}. Across XJTU-SY ($n{=}10$), FEMTO/PRONOSTIA ($n{=}6$), University of
Ferrara ($n{=}6$), and NASA IMS ($n{=}3$), with bootstrap confidence intervals and
run-level significance tests that treat the run---not the within-run sampling
factor---as the unit of inference, SCADA-rate aggregation does \emph{not} destroy
lead time---and on IMS shows a consistent positive trend for the
variance-sensitive control charts---while decimation is never better; nothing
survives Holm correction across the $N{=}40$ family.
\item \emph{Validation}: wiring and empirical validation of a conformal detector
for distribution-free false-alarm control, a lead-time--vs--false-alarm trade-off
analysis, feature-group and spectral ablations that localize the prognostic signal
to time-domain statistics on IMS, and a characterization of deep reconstruction
models (LSTM-AE, TCN-AE, Transformer-AD) showing they do not become competitive
with SPC charts within the tested training-fraction range $[0.20, 0.60]$ on
short-lived bearings; whether a crossover exists on long-runway assets remains
open (Section~\ref{sec:mindata}).
\end{enumerate}

\textbf{Scope of claims.} The empirical results are for rolling-element bearings
under approximately steady operating conditions; we make no claim of transfer to
gearboxes, blades, or variable-speed machinery. The sampling question is
specifically \emph{bin-averaged} historian storage versus \emph{decimated}
storage. The metric itself is failure-mode-agnostic: it applies wherever a
run-to-failure trajectory and a stationary normal region exist."""
rx_sub("contributions",
    r"\\textbf\{Contributions\.\} We make five contributions\.\n\\begin\{enumerate\}.*?\\end\{enumerate\}",
    lambda m: NEW_CONTRIB)

# ------------------------------------------------- STEP 5/6 intro method + finding
rx_sub("intro_method",
    r"applied to \\textbf\{ten\ndetectors\} \(SPC charts, Isolation Forest, four deep autoencoders\) across\n\\textbf\{five run-to-failure datasets\}---NASA IMS, a real ONGC gas-turbine SCADA\nrecord, ten XJTU-SY bearings, six FEMTO/PRONOSTIA bearings, and six University of\nFerrara bearings---with",
    lambda m: (r"applied to \textbf{nine detectors} (four SPC charts, Isolation Forest, three"
     "\n" r"deep reconstruction autoencoders, and an RMS-trend baseline; Deep SVDD"
     "\n" r"additionally evaluated) across \textbf{four inferential run-to-failure"
     "\n" r"datasets}---XJTU-SY ($n{=}10$), FEMTO/PRONOSTIA ($n{=}6$), University of Ferrara"
     "\n" r"($n{=}6$), and NASA IMS ($n{=}3$), plus a real single-asset ONGC gas-turbine"
     "\n" r"SCADA record analyzed as a case study (Appendix~E)---with"))

rx_sub("intro_finding",
    r"The folklore is \\textbf\{refuted on all five datasets\}:\nhistorian-style aggregation does \\emph\{not\} destroy lead time\. On IMS it shows a\nconsistent positive \\emph\{trend\} \(not significant at \$n\{=\}3\$\); on ONGC, XJTU,\nFEMTO, and Ferrara the difference is negligible\. The defensible cross-dataset conclusion is\n\\textbf\{non-destruction\}---decimation is never better, and averaging is at worst\nneutral\.",
    lambda m: (r"The folklore is \textbf{refuted on every dataset tested}: historian-style"
     "\n" r"aggregation does \emph{not} destroy lead time. On the large multi-bearing sets"
     "\n" r"(XJTU-SY, FEMTO, Ferrara) the difference is negligible; on IMS it shows a"
     "\n" r"consistent positive \emph{trend} (not significant at $n{=}3$); the single-asset"
     "\n" r"turbine record agrees (case study, Appendix~E). The defensible cross-dataset"
     "\n" r"conclusion is \textbf{non-destruction}---decimation is never better, and averaging"
     "\n" r"is at worst neutral."))

# --------------------------------------------------------- STEP 5 datasets opening
rx_sub("datasets_open",
    r"We use five run-to-failure datasets spanning controlled-lab, real-industrial,\nand cross-condition regimes.*?statistical power a three-run rig cannot\.",
    lambda m: (r"We use four inferential run-to-failure datasets spanning controlled-lab and"
     "\n" r"cross-condition regimes, together with a single-asset real-historian case study"
     "\n" r"(Table~\ref{tab:datasets}). They were chosen so that the central sampling claim"
     "\n" r"is tested under genuinely different conditions: a high-rate raw-waveform rig"
     "\n" r"where aggregation can be simulated faithfully (IMS), two multi-bearing campaigns"
     "\n" r"(XJTU-SY and FEMTO/PRONOSTIA) that supply the statistical power a three-run rig"
     "\n" r"cannot, a second modern constant-condition rig (Ferrara), and---as a case study"
     "\n" r"only---a real historian stream that already \emph{is} SCADA-rate data (ONGC,"
     "\n" r"Appendix~E)."))

# --------------------------------------------------------- STEP 7 relabel -> App C
RELABEL = capture("relabel_justif",
    r"A subtlety we correct\nhere is the failure-label of the third test:.*?It is the labeling we use throughout\.")
if RELABEL:
    lit("relabel_replace", RELABEL,
        (r"IMS test~3's failure label is set as documented in the released repository; the"
         "\n" r"justification appears in Appendix~C."))

# --------------------------------------------------------- STEP 5 ONGC desc -> App E
ONGC_DESC = cut("ongc_desc",
    r"\\textbf\{ONGC\.\} The ONGC record is a real Solar-Turbine.*?it is\nthe historian\.\n\n")

# --------------------------------------------------------- STEP 8 mechanism -> App D
MECH = cut("mechanism_subsec",
    r"\\subsection\{Mechanism: SCADA averaging or generic smoothing\?\}\n\\label\{sec:mechanism\}\n.*?(?=\\subsection\{Conformal calibration\})")

# --------------------------------------------------------- STEP 5 ONGC subsec -> App E
ONGC_SUB = cut("ongc_subsec",
    r"\\subsection\{Real turbine SCADA \(ONGC\): a single-asset case study\}\n.*?(?=\\subsection\{Generalization to XJTU-SY)")

ONGC_CALIB = cut("ongc_calib_fig",
    r"\\begin\{figure\}\[t\]\n\\centering\n\\includegraphics\[width=0\.86\\columnwidth\]\{figs/fig_calibration_ongc\.png\}\n.*?\\label\{fig:calib_ongc\}\n\\end\{figure\}\n")

# --------------------------------------------------------- STEP 9 relocate IMS block
BLOCK_IMS = cut("ims_aggdec_subsec",
    r"\\subsection\{Aggregate vs decimate on IMS: a consistent positive trend\}\n.*?(?=\\subsection\{Generalization to XJTU-SY)")
if BLOCK_IMS:
    BLOCK_IMS = BLOCK_IMS.replace(
        "We test this smoothing hypothesis directly in\nSection~\\ref{sec:mechanism}.",
        "We test this smoothing hypothesis directly in\nAppendix~D.")
    lit("reinsert_ims_block",
        r"\subsection{Multiple-comparison correction}",
        BLOCK_IMS + r"\subsection{Multiple-comparison correction}")

# --------------------------------------------------------- STEP 9 primary-dataset line
lit("primary_dataset_sentence",
    r"\section{Methodology}",
    (r"XJTU-SY ($n{=}10$) is our primary inferential dataset; IMS ($n{=}3$) is retained"
     "\n" r"for its raw-waveform access, which permits the faithful aggregate/decimate"
     "\n" r"simulation and the mechanism analysis (Appendix~D)."
     "\n\n" r"\section{Methodology}"))

# --------------------------------------------------------- STEP 6 detectors -> nine
lit("detectors_intro",
    r"We evaluate ten detectors under one fixed hyperparameter protocol:",
    r"The headline set comprises nine detectors, evaluated under one fixed hyperparameter protocol:")

lit("remove_deepsvdd_item",
    "\\item \\textbf{Deep SVDD} \\cite{ruff2018}: a one-class deep model; an MLP encoder\nmaps normal data toward a fixed center, and the squared distance to that center\nis the anomaly score.\n",
    "")

DEEPSVDD_NOTE = ("\\end{itemize}\n\n"
    r"\textbf{Additionally evaluated (not in the headline nine).} We also evaluate Deep"
    "\n" r"SVDD~\cite{ruff2018}---a one-class deep model whose MLP encoder maps normal data"
    "\n" r"toward a fixed center, scoring a window by its squared distance to that"
    "\n" r"center---and one-class SVM~\cite{scholkopf2001}. Deep SVDD produced no valid"
    "\n" r"alarm on any FEMTO bearing at any training fraction (Section~\ref{sec:mindata})"
    "\n" r"and is omitted from the headline set; its full numbers are retained in the"
    "\n" r"result tables throughout and summarized in Appendix~F. We keep it visible"
    "\n" r"because it is the low-false-alarm operating point under the gated metric"
    "\n" r"(Section~\ref{sec:saxena}, Table~\ref{tab:farsens}).")
lit("deepsvdd_note",
    "scores a window by its reconstruction error.\n\\end{itemize}",
    "scores a window by its reconstruction error.\n" + DEEPSVDD_NOTE)

lit("remove_ocsvm_line",
    " One-class\nSVM \\cite{scholkopf2001} is also implemented but kept out of the headline. All\nnon-conformal",
    " All\nnon-conformal")

# --------------------------------------------------------- STEP 6 Holm footnote
lit("holm_footnote",
    "On FEMTO and Ferrara all ten detectors run\non the full $n{=}6$.}",
    ("On FEMTO and Ferrara all ten detectors run\non the full $n{=}6$. The $N{=}40$ "
     "family is the full evaluated set of ten detectors\n(the nine headline detectors "
     "plus the additionally-evaluated Deep SVDD) across the\nfour inferential datasets, "
     "retained exactly as originally computed.}"))

# --------------------------------------------------------- STEP 5 Table I caption+row
lit("datasets_caption",
    "\\caption{Datasets used in this study. ``Role'' indicates the function each\ndataset plays in the argument.}",
    ("\\caption{Datasets used in this study. ``Role'' indicates the function each\ndataset "
     "plays in the argument. The four inferential datasets supply the run-level\nstatistics; "
     "ONGC is a single-asset case study (Appendix~E) and Paderborn is\nexcluded.}"))

lit("datasets_ongc_row",
    "ONGC                    & real turbine SCADA & 10\\,s historian   & 1 \\\\",
    "ONGC                    & case study (App.~E) & 10\\,s historian   & 1 \\\\")

lit("imsci_caption_count",
    "IMS mean detection lead time (hours) at full resolution, all ten\ndetectors,",
    "IMS mean detection lead time (hours) at full resolution, all ten evaluated\ndetectors (the nine headline detectors plus Deep SVDD),")

# =================================================== STEP 12 discussion/threats/concl
lit("disc_whatchanged_three",
    "original claim that SCADA averaging destroys lead time is refuted on all three\ndatasets, and",
    "original claim that SCADA averaging destroys lead time is refuted on every\ndataset tested, and")

lit("disc_mechanism_sentence",
    ("Our mechanism test\n(Section~\\ref{sec:mechanism}) confirms this directly: the aggregate advantage\n"
     "grows monotonically as injected noise rises, and an ordinary moving-average or\n"
     "Kalman smoother on the decimated stream recovers the same lead time---so the\n"
     "effect is generic health-signal smoothing, not historian averaging\nspecifically."),
    ("The IMS trend is reproduced by an ordinary moving-average or Kalman filter on the\n"
     "decimated stream (Appendix~D), indicating a generic low-pass-smoothing mechanism\n"
     "rather than historian averaging specifically."))

ONGC_DISC = (
    r"\textbf{The single-asset turbine case study.} The one real historian record in"
    "\n" r"our study---an ONGC gas-turbine low-pressure-compressor bearing logged at a"
    "\n" r"10\,s SCADA rate and ending in a genuine operator shutdown---has every detector"
    "\n" r"alarm roughly $35$\,h ahead of the labeled failure, with an aggregate-vs-decimate"
    "\n" r"difference of at most about a minute for every detector. Because it is a single"
    "\n" r"asset ($n{=}1$) we draw \emph{no} inference from it and exclude it from the"
    "\n" r"inferential family; we report it in full as a case study in Appendix~E. It is"
    "\n" r"nonetheless the cleanest illustration of the practical question---it uses no"
    "\n" r"simulated coarsening---and is consistent with non-destruction."
    "\n\n" r"\subsection{Practical implications}")
lit("ongc_discussion_para",
    r"\subsection{Practical implications}",
    ONGC_DISC)

lit("summary_fivedatasets",
    "\\textbf{(1)~Non-destruction holds on all\nfive datasets:} SCADA bin-averaging never costs lead time relative to\ndecimation.",
    "\\textbf{(1)~Non-destruction holds on all four inferential\ndatasets (and the single-asset case study):} SCADA bin-averaging never costs lead\ntime relative to decimation.")

lit("summary_ongc",
    "effect is null:} ONGC ($n{=}1$) differs by \\textbf{$\\le1$\\,min}, and XJTU-SY",
    "effect is null:} the single-asset ONGC case study differs by \\textbf{$\\le1$\\,min},\nand XJTU-SY")

lit("threats_fivedatasets",
    "The five datasets, while deliberately diverse,\nare all rolling-element bearings;",
    "The datasets, while deliberately diverse, are all rolling-element bearings;")

lit("conclusion_datasets",
    ("Across a controlled laboratory dataset, a real\nturbine SCADA record, ten XJTU-SY "
     "run-to-failure bearings, six\nFEMTO/PRONOSTIA run-to-failure bearings, and six "
     "University of Ferrara\nrun-to-failure bearings, coarse aggregation does\nnot "
     "destroy lead time"),
    ("Across four inferential run-to-failure datasets---XJTU-SY ($n{=}10$),\n"
     "FEMTO/PRONOSTIA ($n{=}6$), University of Ferrara ($n{=}6$), and NASA IMS\n"
     "($n{=}3$)---together with a real single-asset turbine SCADA case study\n"
     "(Appendix~E), coarse aggregation does not destroy lead time"))

# =================================================== STEP 10 tau* grid (arithmetic)
TAUSTAR_TABLE = r"""
\begin{table}[t]
\caption{The break-even budget $\tau^{\ast}=\rho/k$ from Eq.~\eqref{eq:taustar}
(clipped to $[0,1]$), over failure-to-inspection cost ratios
$\rho\in\{10^2,10^3,10^4\}$ and pre-onset window counts $k\in\{10^2,10^3,10^4\}$.
The chosen $\tau{=}0.10$ sits inside this range across the mid-to-high cost ratios
typical of rolling-element bearings, which is why it is a conservative central
choice. Every entry is computed directly from Eq.~\eqref{eq:taustar}; no
experimental quantity enters.}
\label{tab:taustar_grid}
\centering
\footnotesize
\setlength{\tabcolsep}{8pt}
\begin{tabular}{@{}lccc@{}}
\toprule
 & $\rho{=}10^2$ & $\rho{=}10^3$ & $\rho{=}10^4$ \\
\midrule
$k{=}10^2$ & 1.00 & 1.00 & 1.00 \\
$k{=}10^3$ & 0.10 & 1.00 & 1.00 \\
$k{=}10^4$ & 0.01 & 0.10 & 1.00 \\
\bottomrule
\end{tabular}
\end{table}
"""
lit("taustar_ref",
    "so \\eqref{eq:taustar} places the break-even budget at\n$\\tau^{\\ast}\\!\\sim\\!0.1$--$1$: our $\\tau{=}0.10$ is the \\emph{conservative} end of that\nrange",
    "so \\eqref{eq:taustar} places the break-even budget at\n$\\tau^{\\ast}\\!\\sim\\!0.1$--$1$ (Table~\\ref{tab:taustar_grid}): our $\\tau{=}0.10$ is the\n\\emph{conservative} end of that range")
lit("taustar_table_insert",
    "Eq.~\\eqref{eq:taustar} is offered so a practitioner can\nsubstitute their own.",
    "Eq.~\\eqref{eq:taustar} is offered so a practitioner can\nsubstitute their own.\n" + TAUSTAR_TABLE)

# =================================================== STEP 11 FAR-budget figure
FARFIG = r"""
\begin{figure}[t]
\centering
\includegraphics[width=0.94\columnwidth]{figs/fig_far_budget_detector.png}
\caption{Best \emph{valid} lead time per detector as a function of the false-alarm
budget $\tau$ on IMS, plotted directly from the operating points of
Table~\ref{tab:farsens}. Each line is one detector; a value of $0$ means no
operating point within budget. The recommended detector changes with $\tau$:
3$\sigma$ wins at $\tau\ge0.10$, while at a strict $\tau{=}0.05$ only the low-FAR
Deep SVDD and the RMS-trend floor remain valid.}
\label{fig:farbudget}
\end{figure}
"""
lit("farfig_ref",
    ("The non-destruction conclusion\nis computed on raw lead and is unaffected "
     "by $\\tau$.}\n\\label{tab:farsens}"),
    ("The non-destruction conclusion\nis computed on raw lead and is unaffected "
     "by $\\tau$. Fig.~\\ref{fig:farbudget} plots\nthese best-valid-lead curves.}\n\\label{tab:farsens}"))
lit("farfig_env",
    "RMS-trend        & \\textbf{34.7} & 34.7 & 34.7 \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}",
    "RMS-trend        & \\textbf{34.7} & 34.7 & 34.7 \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}\n" + FARFIG)

# =================================================== assemble & insert appendices
def sn(x):
    return x if x else ""

APP = []
APP.append(r"\section*{Appendix C: IMS Test-3 Relabeling Justification}")
APP.append(sn(RELABEL))
APP.append("")
APP.append(r"\section*{Appendix D: Mechanism --- Generic Smoothing vs Historian Averaging}")
APP.append(sn(MECH).rstrip())
APP.append("")
APP.append(r"\section*{Appendix E: Supplementary --- Single-Asset Case Study (ONGC)}")
APP.append(r"\label{app:ongc}")
APP.append(sn(ONGC_DESC).rstrip())
APP.append("")
APP.append(sn(ONGC_SUB).rstrip())
APP.append(sn(ONGC_CALIB).rstrip())
APP.append("")
APP.append(r"\section*{Appendix F: Additional Detector --- Deep SVDD}")
APP.append(
    r"Deep SVDD~\cite{ruff2018} is evaluated alongside the nine headline detectors but"
    "\n" r"is not part of the headline set. It produced no valid alarm on any FEMTO bearing"
    "\n" r"at any training fraction (Table~\ref{tab:trainsweep}) and is omitted from the"
    "\n" r"headline count for that reason. Its numbers are retained, unchanged, throughout"
    "\n" r"the paper: the aggregate-vs-decimate results in"
    "\n" r"Tables~\ref{tab:ims_paired},~\ref{tab:xjtu_paired},~\ref{tab:femto_paired},"
    "\n" r"and~\ref{tab:ferrara_paired}; the $N{=}40$ Holm family in Table~\ref{tab:holm};"
    "\n" r"and its low-false-alarm operating point---$14.8$\,h of valid lead at $\le0.6\%$"
    "\n" r"pre-onset FAR---in Tables~\ref{tab:farsens},~\ref{tab:tradeoff},"
    "\n" r"and~\ref{tab:phrank}, where it is the recommended choice for operators with a"
    "\n" r"near-zero nuisance-alarm tolerance. We retain it in the statistical family"
    "\n" r"exactly as originally computed so that no $p$-value or family size changes.")
APP.append("")
APPENDIX_TEXT = "\n".join(APP) + "\n\n"

lit("insert_appendices",
    r"\section*{Data and Code Availability}",
    APPENDIX_TEXT + r"\section*{Data and Code Availability}")

# =================================================== INTEGRITY CHECK
row_re = re.compile(r"^(?![ \t]*%).*&.*\\\\[ \t]*$", re.MULTILINE)
orig_rows = Counter(m.group(0).strip() for m in row_re.finditer(orig))
new_rows  = Counter(m.group(0).strip() for m in row_re.finditer(s))

# Intended non-numeric edit: ONGC datasets-table Role label. The Runs count '1' and
# rate '10 s' are preserved; only the free-text Role changes. Whitelist it, but assert
# the replacement row (with '1') is present so the count is provably preserved.
ONGC_OLD_ROW = r"ONGC                    & real turbine SCADA & 10\,s historian   & 1 \\".strip()
ONGC_NEW_ROW = r"ONGC                    & case study (App.~E) & 10\,s historian   & 1 \\".strip()
if ONGC_OLD_ROW in orig_rows:
    del orig_rows[ONGC_OLD_ROW]
if new_rows[ONGC_NEW_ROW] < 1:
    report.append("FAIL ongc_row_check: replacement ONGC datasets row missing")

missing = []
for row, cnt in orig_rows.items():
    if new_rows[row] < cnt:
        missing.append((cnt, new_rows[row], row))

fails = [r for r in report if r.startswith("FAIL")]

print("=== OP REPORT ===")
for r in report:
    print(r)
print(f"\n=== INTEGRITY: {len(orig_rows)} distinct orig data rows ===")
if missing:
    print(f"MISSING/ALTERED {len(missing)} rows:")
    for cnt, got, row in missing[:60]:
        print(f"  orig x{cnt} -> new x{got}: {row}")
else:
    print("OK: every original data row present with >= original count.")
print(f"Net new data rows (expect tau* grid = 3): {sum(new_rows.values()) - sum(orig_rows.values())}")

if fails or missing:
    print("\n*** NOT WRITING (failures present). Fix and re-run. ***")
    sys.exit(1)

io.open(SRC, "w", encoding="utf-8", newline="\n").write(s)
print("\n*** WROTE", SRC, "***")
