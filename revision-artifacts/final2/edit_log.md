
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
