
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
