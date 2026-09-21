# Superseded result files

These files are kept for provenance. **No table or figure in the manuscript is
generated from any of them**, and no code reads them. They were moved out of
`results/tables/` so a replicator cannot pick one by mistake — several differ
materially from the arm the paper reports.

Two revisions produced the split:

- **D-2 (channel-invariant features).** The original 445-dimensional
  per-channel feature space was replaced by the 49-dimensional
  channel-invariant schema of Section 4.2 and Appendix B. Files without
  `_invariant` in the name are the pre-D-2 arm.
- **N-20 (training-fraction fix).** A parameter bug meant the training
  fraction was not actually varied. Files named `*_old` are the pre-fix arm.

| File | Why superseded |
|------|----------------|
| `ims_runlevel_test.csv` | Pre-D-2 legacy arm. Gives a 3σ IMS median of 18.43 h; the paper reports 15.10 h from `ims_runlevel_test_invariant.csv`. |
| `benchmark_IMS_aggregate.csv` | Pre-D-2 arm of the IMS aggregate benchmark; replaced by `benchmark_IMS_aggregate_invariant.csv`. |
| `benchmark_IMS_leadtime_ci.csv` | Pre-D-2 arm of the IMS lead-time CIs; Table 2 uses `benchmark_IMS_leadtime_ci_invariant.csv`. |
| `benchmark_IMS_paired_test.csv` | Pre-D-2 arm of the IMS paired tests; replaced by the `_invariant` file. |
| `compute_cost_IMS_legacy.csv` | Pre-D-2 compute costs, measured on the 445-dim feature space; Table 17 uses `compute_cost_IMS_invariant.csv`. |
| `persistence_sensitivity_IMS_legacy.csv` | Pre-D-2 persistence sweep; Table 4(a) uses `persistence_sensitivity_IMS_invariant.csv`. |
| `n20_d15_bootstrap_old.csv` | Pre-N-20 equivalence bootstrap; superseded by `n20_d15_bootstrap_new_11det.csv`. |
| `n20_d15_tost_old.csv` | Pre-N-20 equivalence TOST; superseded by `n20_d15_tost_new_11det.csv`. |
| `n20_d15_bootstrap_new.csv` | Post-N-20 but ten detectors only, before the one-class SVM joined the family. Table 6 needs all eleven, so it uses the `_11det` file. |
| `n20_d15_tost_new.csv` | Same ten-detector limitation; superseded by `n20_d15_tost_new_11det.csv`. |

Git history is intact — these were moved with `git mv`, not rewritten.
