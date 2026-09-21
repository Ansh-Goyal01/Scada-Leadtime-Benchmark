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

| `d3_ocsvm_holm_N44_invariant.csv` | **Pre-N-20.** The D3 build of the N=44 sign-test family; its FEMTO and Ferrara rows predate the N-20 fix. Gives 0.031 for Isolation Forest on FEMTO, the value Reviewer D flagged; the post-fix family gives 0.688. Table 8 uses `n20_raw_contrast_old_vs_new.csv` (`arm=new`). |
| `d3_ocsvm_holm_N44_legacy.csv` | Same file on the pre-D-2 445-dim arm: stale on both axes. |
| `femto_runlevel_test.csv` | Pre-N-20 FEMTO run-level sign test; replaced by `femto_runlevel_test_n20.csv`. |
| `ferrara_runlevel_test.csv` | Pre-N-20 Ferrara run-level sign test; replaced by `ferrara_runlevel_test_n20.csv`. |
| `benchmark_ONGC_paired_test.csv` | Pre-N-20 ONGC paired test; replaced by `benchmark_ONGC_paired_test_n20.csv`. |
| `rf2_crosscheck_raw_vs_published.csv` | Pre-N-20 RF-2 cross-check; replaced by `rf2_crosscheck_raw_vs_published_n20.csv`. |
| `rf2_gated_contrast.csv` | Pre-N-20 gated contrast; Table 10 uses `rf2_gated_contrast_n20.csv`. |
| `rf2_valid_fraction_agg_vs_dec.csv` | Pre-N-20 validity table; replaced by the `_n20` file. |
| `rf2_valid_fraction_paired.csv` | Pre-N-20 paired validity table; replaced by the `_n20` file. |
| `paired_tests_holm.csv` | Pre-N-20 *and* pre-D-2 forty-test Holm family, superseded by the N=44 family. |
| `paired_tests_holm_invariant.csv` | Pre-N-20 forty-test Holm family on the invariant schema; superseded by the N=44 family. |

Git history is intact — these were moved with `git mv`, not rewritten.

**Note on regeneration.** Several of these are output paths of scripts that are
still runnable (`src/d3_ocsvm.py`, `src/rf2_rg3_gated_contrast.py`,
`src/n20_figure_inputs.py`, `src/stats_rigor.py`). Re-running those scripts
writes the pre-fix name back into `results/tables/`. Nothing in the manuscript
reads them, but if you re-run, check this list before trusting a file that
reappears there.
