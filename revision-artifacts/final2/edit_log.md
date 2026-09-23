
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
