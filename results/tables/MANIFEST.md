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
| 5 | `tab:crossds` | `xjtu_sy_runlevel_test.csv`, `femto_runlevel_test_n20.csv`, `ferrara_runlevel_test_n20.csv`, `ims_runlevel_test_invariant.csv`; the eleventh (one-class SVM) row of each block from `n20_raw_contrast_old_vs_new.csv` (`arm=new`) | **[auto]** (FEMTO/Ferrara blocks) |
| 6 | `tab:equiv` | `n20_d15_bootstrap_new_11det.csv` — **not** `d15_equivalence_bootstrap.csv` | **[auto]** |
| 7 | `tab:imssweep` | `ims_runlevel_test_invariant.csv`; one-class SVM row from `n20_raw_contrast_old_vs_new.csv` (`arm=new`) | **[auto]** |
| 8 | `tab:holm` | `n20_raw_contrast_old_vs_new.csv` (`arm=new`, `dataset != ONGC`, `sign_test_p`) — **not** `d3_ocsvm_holm_N44_invariant.csv`, which is pre-N-20 | **[auto]** |
| 9 | `tab:perbearing` | `benchmark_XJTU-SY_long.csv` | *[doc]* |
| 10 | `tab:gatedcontrast` | `rf2_gated_contrast_n20.csv` (`metric` in `raw`, `gated_D7`) -- **not** `SOURCES` in `src/rf2_rg3_gated_contrast.py`, which reads the pre-N-20 long files | **[auto]** |
| 11 | `tab:conformal` | `calibration_IMS.csv`, `calibration_IMS_pooled.csv` | *[doc]* |
| -- | `fig:conformal` c/d | `calibration_{FEMTO,ONGC}.csv`, `calibration_{FEMTO,ONGC}_pooled.csv` -- N-20-invariant, see the proof below | **[auto]** |
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
| 23 | `tab:ongc` | `n20_ongc_minutes.csv`, column `new_min` -- **not** `old_min`, which is the pre-N-20 arm | **[auto]** |

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

The N-20 fix landed 2026-09-17 21:56. It replaced the aggregate resampling
interval `max(1, round(base_min * factor))` whole minutes with native spacing
x factor in seconds, so it moved only the datasets whose native spacing is
sub-minute: **FEMTO** and **ONGC** (10 s) and **Ferrara** (5 s). It was a
verified no-op on **IMS** and **XJTU-SY**, whose native spacing is already a
whole number of minutes.

### What the fix did and did not touch

Because the fix changed only the *aggregate* interval arithmetic, and because
`src/sampling.py:166` records that "factor=1 is identical across modes (no
downsampling)" -- at factor 1 the resampler is never entered at all -- the fix
partitions every sweep row into three classes:

| rows | status under N-20 |
|------|-------------------|
| `mode=aggregate, factor=1` | **unchanged** |
| `mode=decimate`, any factor | **unchanged** |
| `mode=aggregate, factor>1` | **changed** |

**This is measured, not assumed.** `paper/verify_tables.py::check_n20_rule`
joins each pre-fix `benchmark_<DS>_long.csv` to its post-fix
`n20_rerun_long_<DS>_main.csv` on
`(dataset, run, seed, short_name, mode, factor)` and compares
`effective_interval_min`, `lead_time_hours`, `detection_delay_hours`,
`far_preonset_pct`, `lead_norm` and `valid_alarm`. Over all 1300 matched rows
(600 FEMTO + 600 Ferrara + 100 ONGC) every `aggregate, factor=1` and every
`decimate` cell is identical, and every `aggregate, factor>1` group differs.
The check also asserts that converse, so the rule fails loudly if a regenerated
file ever stops obeying it.

### The consequence

- An artifact computed from **factor-1 rows alone** is N-20-invariant, and its
  pre-fix file remains canonical.
- An artifact that reads **any aggregate row at factor > 1** -- including
  anything that collapses over all factors -- must come from a post-fix file.
- For IMS and XJTU-SY earlier files remain valid regardless, and the
  `_invariant` / `legacy` feature-schema axis (defect D-2) is the one that
  matters instead.

`paper/verify_tables.py::check_holm` carries a guard that fails if the N=44
family is ever re-sourced from a pre-fix file: the post-fix family's smallest
raw p is 0.125 (Transformer-AD on FEMTO) and no cell is significant
uncorrected, where the pre-fix file gives 0.031 (Isolation Forest on FEMTO).

## FEMTO / Ferrara / ONGC file-by-file classification

Every file for the three N-20-affected datasets, with the rows its consumer
actually reads, what it backs, and whether it is canonical. "Invariant" means
proven N-20-invariant under the rule above, so the pre-fix file stays canonical.

| File | Rows its consumer reads | Backs | Verdict |
|------|-------------------------|-------|---------|
| `n20_rerun_long_{FEMTO,Ferrara,ONGC}.csv` | all modes, all factors, 11 detectors | Section 6.2 `211/660`; ONGC release | **canonical (post-fix)** |
| `n20_rerun_long_<DS>_main.csv` | all modes, all factors, 10 detectors | the invariance measurement above | **canonical (post-fix)** |
| `femto_runlevel_test_n20.csv`, `ferrara_runlevel_test_n20.csv` | all modes, all factors | Table 5, Figure 2 | **canonical (post-fix)** |
| `n20_raw_contrast_old_vs_new.csv` (`arm=new`) | all modes, all factors | Table 5 (OC-SVM row), Table 7, Table 8 | **canonical (post-fix)** |
| `n20_d15_bootstrap_new_11det.csv`, `n20_d15_tost_new_11det.csv` | all modes, all factors | Table 6 | **canonical (post-fix)** |
| `rf2_gated_contrast_n20.csv` | all modes, all factors | Table 10, Section 6.9 | **canonical (post-fix)** |
| `n20_ongc_minutes.csv` (`new_min`) | all modes, all factors | Table 23 | **canonical (post-fix)** |
| `benchmark_ONGC_{aggregate,leadtime_ci}_n20.csv` | derived from `n20_rerun_long_ONGC.csv` | ONGC data-availability release | **canonical (post-fix)** |
| `benchmark_ONGC_paired_test_n20.csv` | all modes, all factors | Figure 2, ONGC release | **canonical (post-fix)** |
| `femto_training_sweep{,_long}.csv` | `load_pipeline` at `mode="none", factor=1` | Figure 6, Sections 4.11 and 6.13 | **invariant** (and in fact regenerated post-fix, 2026-09-20) |
| `onset_sensitivity_{FEMTO,XJTU-SY}.csv` | `load_pipeline` at `mode="none", factor=1` | Section 4.6 short-bearing onset stability | **invariant** |
| `calibration_{FEMTO,ONGC}.csv`, `calibration_{FEMTO,ONGC}_pooled.csv` | `load_pipeline` at `mode="none", factor=1` | Figure 4c/4d, Section 6.11 | **invariant** -- proof below |
| `d3_ocsvm_leadtime_ci.csv`, `d3_ocsvm_tradeoff{,_long}.csv` | `factor==1 & mode=="aggregate"` (`src/d3_ocsvm.py:243,250`) | OC-SVM factor-1 derivations | **invariant** |
| `benchmark_{FEMTO,Ferrara}_long.csv` | `factor==1 & mode=="aggregate"` by `src/d3_ocsvm.py`; **all** factors by `src/d15_equivalence.py` and `src/rf2_rg3_gated_contrast.py::SOURCES` | **no manuscript float and no manuscript number** | pre-fix; retained only as the published pre-N-20 baseline |
| `benchmark_ONGC_long.csv` | all modes, all factors | **no longer released** -- the ONGC availability statement now names `n20_rerun_long_ONGC.csv`; still read by `tests/test_ongc_release.py` and `src/export_ongc_derived.py` | pre-fix; retained only as the published pre-N-20 baseline |
| `benchmark_{FEMTO,Ferrara,ONGC}_{aggregate,leadtime_ci}.csv` | no code consumer | **nothing** | pre-fix; superseded by the `_n20` forms for ONGC, unused for FEMTO/Ferrara |
| `benchmark_{FEMTO,Ferrara}_paired_test.csv` | no code consumer | **nothing** | pre-fix; unused |
| `d3_ocsvm_benchmark_long.csv` | `factor==1 & mode=="aggregate"` only | OC-SVM factor-1 derivations (invariant). Its `aggregate, factor>1` rows are pre-fix and must not be read | pre-fix file, invariant slice only |

### Invariance proof for the calibration files

`calibration_{FEMTO,ONGC}[_pooled].csv` were last written 2026-09-17 04:02,
before the fix, and are kept as canonical. The proof is stronger than the
factor-1 rule rather than an appeal to it:
`src/calibration.py::calibration_for_run` calls
`load_pipeline(run_name, dataset=dataset)` with **no downsample arguments**, so
it runs at the signature defaults `downsample_mode="none",
downsample_factor=1` (`src/__init__.py:164-165`) and never enters the
resampling code the fix changed. Consistently with that, neither file carries a
`mode`, `factor` or `effective_interval_min` column at all, so no resampled row
can reach them. `paper/verify_tables.py::check_calibration_invariance` asserts
exactly that structural property, and fails if a future rerun ever adds such a
column -- at which point this invariance claim must be redone rather than
assumed. The same check re-derives the four numbers the files back: FEMTO
pre-onset FAR 0.08--0.56 at alpha = 0.05 with pooled 0.27, and ONGC 0.016,
0.030, 0.096 at alpha = 0.01, 0.02, 0.05.

The same code-path argument covers `onset_sensitivity_{FEMTO,XJTU-SY}.csv`
(`src/onset_sensitivity.py:75`) and `femto_training_sweep{,_long}.csv`
(`src/training_sweep.py:85`), both of which also call `load_pipeline` without
downsample arguments.

### Section 6.2, "211/660"

The sentence "Across all eleven evaluated detectors ... 211/660 evaluations
yield a valid alarm" spans both modes and all five factors, so it is **not**
factor-1 only and cannot come from a pre-fix file. It is backed by
`n20_rerun_long_FEMTO.csv` -- 660 rows, 11 detectors, 211 valid. **The number
is correct; what was missing was the pointer.** The pre-fix pair that used to
supply it, `benchmark_FEMTO_long.csv` (191/600, ten detectors) plus the FEMTO
slice of `d3_ocsvm_benchmark_long.csv` (2/60), gives **193/660**.
`paper/verify_tables.py::check_femto_valid` pins both arms and asserts they
differ, so re-pointing the number at the pre-fix pair fails.

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
- `benchmark_{FEMTO,Ferrara,ONGC}_{long,aggregate,leadtime_ci}.csv` and
  `benchmark_{FEMTO,Ferrara}_paired_test.csv` — the **published pre-N-20
  baseline** for the three affected datasets. None backs a float or a number;
  see the file-by-file classification above for which rows of each are still
  safe to read (the `factor=1, aggregate` and `decimate` rows) and which are
  not (`aggregate` at `factor > 1`).

See `superseded/README.md` for arms moved out of the way.
