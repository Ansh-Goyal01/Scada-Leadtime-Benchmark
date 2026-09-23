
## Part 1 layout: per-bearing paragraph

- OLD: they differ only where valid detectors disagree, which happens on none of the scoreable bearings here. Only 5 of the ten bearings are scoreable at full resolution: Bearing1\_2 has no detectable onset, and on Bearing1\_3, 1\_5, 2\_2 and 2\_5 the onset precedes the first scored window.
- NEW: they differ only where valid detectors disagree, which happens on none of the five scoreable bearings (Table~\ref{tab:perbearing} marks the other five and why).

## Part 2: internal tracking IDs removed from Data Availability

- OLD: (the pre-D-2 legacy feature schema, or the pre-N-20 rerun)
- NEW: (an earlier feature schema, or results computed before the aggregation bin width was corrected)

- OLD: together with the full post-N-20 sampling sweep
- NEW: together with the full sampling sweep

- OLD: both of which are the pre-N-20 arm, retained as provenance
- NEW: both of which were computed before the aggregation bin width was corrected, retained as provenance

- OLD: the aggregate-vs-decimate contrast is taken from the post-N-20 files named above
- NEW: the aggregate-vs-decimate contrast is taken from the corrected files named above

## Part 3: abstract equivalence wording, IMS equivalence sentence in S6.6

- OLD: none favouring decimation beyond $-0.45$~h; IMS is too wide to decide in 9 of 11 cells and favours aggregation beyond the margin in 2.
- NEW: every 95\% interval lying inside $\pm 0.6$~h; IMS is too wide to decide in 9 of 11 cells, favours aggregation beyond the margin for CUSUM, and touches it for Hotelling $T^2$ (lower bound exactly $+1.00$~h).

- OLD: The powered campaigns are short-lived bearings
- NEW: The campaigns that supply this statistical power are short-lived bearings

- OLD: the defensible reading is a null result with a positive median direction for the magnitude-monitoring detectors.
- NEW: the defensible reading is a null result with a positive median direction for the magnitude-monitoring detectors. Against the $\pm 1$~h margin the IMS intervals are too wide to decide for nine of the eleven detectors; CUSUM's lies wholly above it ([$+4.15$, $+4.67$]~h), favouring aggregation beyond the margin, and Hotelling $T^2$'s lower bound sits exactly on it ([$+1.00$, $+81.74$]~h).

## Part 4: factual corrections

- OLD: Across $k \in \{3,4,5\}$ the default onset moves by less than two percent of run span on every run (Table~\ref{tab:onset}).
- NEW: Across $k \in \{3,4,5\}$ the default onset moves by less than 0.1 percentage points of run span on test~1, 1.6 on test~3 and 5.4 on the slow-degrading test~2 (Table~\ref{tab:onset}).

- OLD: For practitioners, storing bin-averaged vibration at SCADA rates, the default behavior of most historians, does not inherently sacrifice bearing-fault warning time relative to keeping decimated raw samples, and may improve it for control-chart detectors on noisy long-runway data.
- NEW: For practitioners, storing bin-averaged summary statistics at SCADA rates, the default behavior of most historians, rather than keeping every $f$-th stored value changed bearing-fault warning time by less than the $\pm 1$~h margin on every multi-bearing campaign tested (Section~\ref{sec:femto}), and may improve it for control-chart detectors on noisy long-runway data.

- OLD: The deep sequence models are data-starved: across bearings and training fractions the runs furnish between 20 and 335 normal training windows (median 88 at the default split).
- NEW: The deep sequence models are data-starved: across FEMTO bearings and training fractions the runs furnish between 20 and 335 normal training windows (median 88 at the default split), and the largest IMS run 631.

- OLD: but its numbers are reported in every result table because
- NEW: but its numbers are reported in the main result tables because

- OLD: per-bearing results in Tables~\ref{tab:crossds} and \ref{tab:perbearing} flag these cases explicitly rather than silently discarding them.
- NEW: the per-bearing results of Table~\ref{tab:perbearing} report these bearings individually rather than discarding them.

- OLD: their pre-onset FAR sitting at 19.0--22.1\% across the swept thresholds,
- NEW: their pre-onset FAR sitting at 19.0--22.1\% across the tabulated thresholds (Table~\ref{tab:tradeoff}),

- OLD: ; an earlier single-draw run reported a 128.1~h collapse already at 5\%, a property of that draw that we do not state.
- NEW: .

- OLD: The folklore is refuted on every dataset tested:
- NEW: The folklore is not supported on any dataset tested:

- OLD: with its dataset-dependent direction explicit, as more valuable than a tidy but unsupported positive claim.
- NEW: with its dataset-dependent direction explicit.

- OLD: the direction of any residual effect is dataset-specific noise,
- NEW: the direction of any residual effect varies by dataset,

- OLD: every run-level median difference is within $\pm5$~min, no detector is sign-consistent across the six
- NEW: every run-level median difference is within $\pm1$~min, no detector is sign-consistent across the six

- OLD: from $-0.35$~h at the native noise level to $+6.6$~h at 10~dB,
- NEW: from $-0.35$~h at the native noise level to $+6.60$~h at 10~dB,

- OLD: (late by approximately $k\sigma_b/m$; Algorithm~\ref{alg:onset})
- NEW: (Section~\ref{sec:onset})

- OLD: \subsection{Leakage-Free Degradation Onset}
- NEW: \subsection{Leakage-Free Degradation Onset}
\label{sec:onset}

- OLD: The IMS (NASA), XJTU-SY, and FEMTO/\PHMslashbreak PRONOSTIA run-to-failure datasets are publicly available from their original providers;
- NEW: The IMS (NASA), XJTU-SY, FEMTO/\PHMslashbreak PRONOSTIA and University of Ferrara run-to-failure datasets are publicly available from their original providers;

- OLD: retained as provenance for the indicator comparison; no number reported here depends on them, and the aggregate-vs-decimate contrast is taken from the corrected files named above.
- NEW: retained as provenance for the indicator comparison; the invariance they establish compares onset indicators within one arm, so it does not depend on that correction, and the aggregate-vs-decimate contrast is taken from the corrected files named above.

## Part 5: email, abbreviations, Figure 5 and Table 10 captions

- OLD: {\email{anshgoyal500@gmail.com}}
- NEW: {\email{anshgoyal5500@gmail.com}}

- OLD: The IEEE PHM 2012 challenge and later remaining-useful-life (RUL) studies
- NEW: The IEEE PHM 2012 challenge and later RUL studies

- OLD: the $3\sigma$ rule, the exponentially weighted moving average (EWMA) \cite{roberts1959control}
- NEW: the $3\sigma$ rule, the EWMA chart \cite{roberts1959control}

- OLD: the Saxena prognostic horizon (PH) \cite{saxena2008metrics,saxena2010metrics}:
- NEW: the Saxena prognostic horizon \cite{saxena2008metrics,saxena2010metrics}:

- OLD: where they fit legibly. Up and to the left is better.}
- NEW: where they fit legibly. Up and to the left is better. The deep reconstruction models and the one-class SVM, above the budget at every threshold, appear in Table~\ref{tab:tradeoff} only.}

- OLD: by feature group, for the six non-sequence detectors.}
- NEW: by feature group, for the six non-sequence detectors. EW: EWMA; CU: CUSUM; DS: Deep SVDD; IF: Isolation Forest.}

## Part 5 layout: drop the FloatBarrier that left p17's second column 40% empty

- OLD: '\\FloatBarrier\n\\section*{Acknowledgments}'
- NEW: '\\section*{Acknowledgments}'

## Part 5 layout: test without the FloatBarrier before the Discussion

- OLD: '\\FloatBarrier\n\\section{Discussion}'
- NEW: '\\section{Discussion}'

(reverted: no page effect; the barrier keeps Results floats ahead of the Discussion)

## Part 5 layout: tighten wording added in Parts 1-5 (no fact removed)

- OLD: At $T=0.20$ the onset of Bearing2\_2 precedes the first scored window, so its ten cells are not scoreable (Eq.~\ref{eq:valid}). Valid-alarm fractions are over $n=6$ bearings ($n=5$ at $T=0.20$), with an N/A counted as no valid alarm, the conservative choice;
- NEW: Valid-alarm fractions are over $n=6$ bearings, or five at $T=0.20$, where Bearing2\_2's onset precedes the first scored window (Eq.~\ref{eq:valid}); an N/A counts as no valid alarm, the conservative choice;

- OLD: count as no valid alarm; at $T=0.20$ fractions are over five bearings, Bearing2\_2 being not scoreable (Eq.~\ref{eq:valid}).}
- NEW: count as no valid alarm; $T=0.20$ is over five bearings (Section~\ref{sec:mintrain}).}

- OLD: windows; pooled fractions are over the 13 scoreable aggregate evaluations (test~2 at $f \in \{10,20\}$ has an empty pre-onset region).
- NEW: windows, pooled over the 13 scoreable aggregate evaluations (Eq.~\ref{eq:valid}).

- OLD: XJTU-SY Bearing1\_3, 1\_5, 2\_2 and 2\_5 are not scoreable at full resolution and are excluded; --: no valid alarm on the six that remain.}
- NEW: XJTU-SY: the four bearings not scoreable at full resolution (Table~\ref{tab:perbearing}) are excluded; --: no valid alarm on the other six.}

## Part 5 layout: appendix floats read at the start of their sections

Tables 11-15 moved (source only, order kept) to the start of Appendix A, A, B, C and D.1 respectively.

## Part 5 layout: Appendix A table* read before the single-column table (renumbers 11<->12)
