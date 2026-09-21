# Manifest: manuscript float → result file

Every table and figure in `paper/files/scada_ijphm.tex`, mapped to the exact
file under `results/tables/` that backs it. Float numbers are those of the
submitted PDF (23 tables, 6 figures).

**Why this file exists.** Several results exist in more than one arm — a
pre-D-2 *legacy* 445-dimensional feature schema versus the *invariant*
49-dimensional one, and a pre-N-20 versus post-N-20 rerun. The arms give
materially different numbers. Picking the wrong one silently reproduces a
result the paper does not report. Superseded arms have been moved to
`superseded/`; the few still read by code stay here and are flagged below.

Rows marked **[auto]** are machine-checked on every test run by
`paper/verify_tables.py` (via `tests/test_table_numbers.py`), which re-derives
each printed value from the file named here and fails if they disagree.
Rows marked *[doc]* are documented by inspection but not yet auto-checked.

## Tables

| # | Label | Backed by | |
|---|-------|-----------|---|
| 1 | `tab:datasets` | descriptive dataset metadata; no result file | *[doc]* |
| 2 | `tab:imslead` | `benchmark_IMS_leadtime_ci_invariant.csv` (`mode=aggregate`, `factor=1`) | **[auto]** |
| 3 | `tab:onset` | `onset_sensitivity.csv`; decoupled-indicator columns from `rg3_onsets.csv` | *[doc]* |
| 4 | `tab:robust` (a) | `persistence_sensitivity_IMS_invariant.csv` | *[doc]* |
| 4 | `tab:robust` (b) | `d18_gap_injection_multiseed.csv` — mean `lead` over rows with `valid == True`, then over the five gap draws — **not** `gap_injection.csv`, which holds one draw | **[auto]** |
| 5 | `tab:crossds` | `xjtu_sy_runlevel_test.csv`, `femto_runlevel_test_n20.csv`, `ferrara_runlevel_test_n20.csv`, `ims_runlevel_test_invariant.csv` | *[doc]* |
| 6 | `tab:equiv` | `n20_d15_bootstrap_new_11det.csv` — **not** `d15_equivalence_bootstrap.csv` | **[auto]** |
| 7 | `tab:imssweep` | `ims_runlevel_test_invariant.csv`; one-class SVM row from `n20_raw_contrast_old_vs_new.csv` (`arm=new`) | **[auto]** |
| 8 | `tab:holm` | `n20_raw_contrast_old_vs_new.csv` (`arm=new`, `dataset != ONGC`, `sign_test_p`) — **not** `d3_ocsvm_holm_N44_invariant.csv`, which is pre-N-20 | **[auto]** |
| 9 | `tab:perbearing` | `benchmark_XJTU-SY_long.csv` | *[doc]* |
| 10 | `tab:gatedcontrast` | `rf2_gated_contrast_n20.csv` (`metric` in `raw`, `gated_D7`) | *[doc]* |
| 11 | `tab:conformal` | `calibration_IMS.csv`, `calibration_IMS_pooled.csv` | *[doc]* |
| 12 | `tab:farbudget` | `tradeoff_IMS.csv`; one-class SVM from `d3_ocsvm_farbudget_phrank.csv` | *[doc]* |
| 13 | `tab:tradeoff` | `tradeoff_IMS.csv` + `tradeoff_IMS_deepmodels.csv` | **[auto]** |
| 14 | `tab:ablation_general` | `ablation_features_IMS.csv` | *[doc]* |
| 15 | `tab:phrank` | `d3_ocsvm_farbudget_phrank.csv` | *[doc]* |
| 16 | `tab:hyperparams` | `src/config.py` (fixed protocol, not a result file) | *[doc]* |
| 17 | `tab:compute` | `compute_cost_IMS_invariant.csv`, `compute_cost_IMS_extra_invariant.csv` | *[doc]* |
| 18 | `tab:deeparch` | `src/models.py`, `src/deep_baselines.py`, `src/baselines_extra.py`; parameter counts in `deep_model_params.csv` | *[doc]* |
| 19 | `tab:basestats` | feature schema in `src/features.py` (not a result file) | *[doc]* |
| 20 | `tab:d17label` | corrected arm `benchmark_IMS_long_invariant.csv`; original arm `d17_ims_long_originallabel.csv`; both collapsed per Section 4.9 | **[auto]** |
| 21 | `tab:noise` | `noise_snr_IMS_runlevel.csv` | *[doc]* |
| 22 | `tab:denoise` | `denoising_IMS.csv` | *[doc]* |
| 23 | `tab:ongc` | `n20_ongc_minutes.csv` | *[doc]* |

## Figures

| # | Label | Image | Generator | Inputs |
|---|-------|-------|-----------|--------|
| 1 | `fig:health` | `figure1.png` | `paper/make_figures.py::fig_rms_degradation` | `data/processed/2nd_test_features.parquet` |
| 2 | `fig:crossdataset` | `fig_crossdataset.png` | `paper/make_figures.py::fig_crossdataset` | `ims_runlevel_test_invariant.csv`, `xjtu_sy_runlevel_test.csv`, `femto_runlevel_test_n20.csv`, `ferrara_runlevel_test_n20.csv`, `benchmark_ONGC_paired_test_n20.csv` |
| 3 | `fig:sweep` | `fig_sweep.png` | `paper/make_figures.py::fig_leadtime_vs_sampling` | `benchmark_IMS_long_invariant.csv` |
| 4 | `fig:conformal` | `fig_conformal_panels.png` | `paper/make_conformal_panels.py` + `paper/make_panels.py` | `calibration_{IMS,XJTU-SY,FEMTO,ONGC}.csv` |
| 5 | `fig:tradeoffs` | `fig_tradeoff_panels.png` | `paper/make_tradeoff_panels.py` + `paper/make_panels.py` | `tradeoff_IMS.csv`, `tradeoff_IMS_deepmodels.csv`, `tradeoff_XJTU-SY.csv` |
| 6 | `fig:mintrain` | `fig_mintrain.png` | `paper/make_figures.py::fig_training_sweep` | `femto_training_sweep.csv` |

## Provenance rule (N-20)

The N-20 fix landed 2026-09-17 21:56. It changed the **FEMTO, Ferrara and
ONGC** results and was a verified no-op on **IMS and XJTU-SY**. Therefore:

- For FEMTO, Ferrara and ONGC, only a file produced *after* that timestamp is
  canonical. Pre-fix files are in `superseded/`.
- For IMS and XJTU-SY, earlier files remain valid, and the `_invariant` /
  `legacy` feature-schema axis (defect D-2) is the one that matters instead.

`paper/verify_tables.py::check_holm` carries a guard that fails if the N=44
family is ever re-sourced from a pre-fix file: the post-fix family's smallest
raw p is 0.125 (Transformer-AD on FEMTO) and no cell is significant
uncorrected, where the pre-fix file gives 0.031 (Isolation Forest on FEMTO).

## Files kept here that back no float

Still read or written by code, so not moved — but no table or figure in the
manuscript is generated from them:

- `d15_equivalence_bootstrap.csv`, `d15_equivalence_tost.csv` — the **published
  pre-N-20 baseline**, retained because `src/n20_propagate.py::d15_replay_check`
  replays against them to show the N-20 rerun changed no verdict. Ten detectors
  only (no one-class SVM). Table 6 uses `n20_d15_bootstrap_new_11det.csv`.
- `gap_injection.csv`, `gap_injection_far.csv` — the **single-draw** gap sweep.
  `gap_injection.csv` is the originally released file (N-19: its generator was
  lost, so its gap > 0 draw cannot be regenerated); `gap_injection_far.csv` is
  the N-19 reconstruction, which reproduces the gap = 0 arm exactly (78/78
  cells) and so validates the generator. Both are retained as provenance for
  that reconciliation. Table 4(b) uses `d18_gap_injection_multiseed.csv`.
- `benchmark_IMS_long.csv`, `persistence_sensitivity_IMS.csv` — legacy-arm
  inputs still referenced by helper scripts. Both are IMS-only, where the N-20
  fix was a verified no-op, so they remain valid.

See `superseded/README.md` for arms moved out of the way.
