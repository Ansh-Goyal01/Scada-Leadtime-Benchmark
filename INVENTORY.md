# INVENTORY — current structure of `paper/scada_journal.tex`

Snapshot taken on branch `ijphm-reframe` BEFORE any reframing edits, so that every
structural move can be verified later. Source: `paper/scada_journal.tex` (2456 lines,
IEEEtran journal class, embedded `thebibliography`). No external `.bib`.

Build: `tools/tectonic.exe -X compile scada_journal.tex` (via `paper/build_pdf.sh`).

## Sections (in current order)

| # | Section | Line |
|---|---------|------|
| — | Title / Author / Abstract / Keywords | 35–99 |
| I | Introduction (incl. Problem/Solution/Method/Finding + 5 Contributions) | 101 |
| II | Related Work (A–E) | 218 |
| III | Datasets (IMS, ONGC, XJTU-SY, FEMTO, Ferrara; incl. IMS relabel para) | 303 |
| IV | Methodology (A problem, B feature schema, C onset, D metric, E detectors, F conformal, G sweep, H stat protocol) | 398 |
| V | Experimental Setup | 635 |
| VI | Results (A–O, see below) | 647 |
| VII | Discussion (A what changed, B why IMS trend, C practical, D summary) | 2078 |
| VIII | Limitations and Threats to Validity | 2156 |
| IX | Conclusion and Future Work | 2240 |
| A | Appendix A: Reproducibility Settings | 2267 |
| B | Appendix B: 49-Dim Invariant Feature Space | 2352 |
| — | Data and Code Availability | 2399 |
| — | Bibliography (thebibliography, 33 entries) | 2424 |

### Results subsections (current order)
- A. Lead time and CIs on IMS (686)
- B. Sensitivity of the onset definition (753) — incl. short-bearing, decoupled-indicator, persistence, missing-data
- C. Aggregate vs decimate on IMS: consistent positive trend (920)
- D. Real turbine SCADA (ONGC): single-asset case study (998)
- E. Generalization to XJTU-SY n=10 (1033)
- F. Generalization to FEMTO/PRONOSTIA n=6 (1104)
- G. Generalization to University of Ferrara n=6 (1154)
- H. Multiple-comparison correction (Holm, N=40) (1197) — incl. per-bearing heterogeneity
- I. Mechanism: SCADA averaging or generic smoothing? (1336)
- J. Conformal calibration (1460)
- K. Lead-time-vs-false-alarm trade-off (1560) — incl. FAR-budget sensitivity, tau* cost-ratio (Eq 6)
- L. Feature-group ablation (1709)
- M. Spectral vs time-domain features, per run (1840)
- N. Comparison with the Saxena prognostic horizon (1897)
- O. Minimum training data for deep anomaly detectors (2002)

## Tables (IEEE auto-number = source order)

| Tbl | Label | Caption topic | Line | Reframe action |
|-----|-------|---------------|------|----------------|
| I | tab:datasets | Datasets used (6 rows incl. Paderborn excluded) | 378 | edit: "four inferential + case study" framing |
| II | tab:ims_ci | IMS raw lead + 95% CI, 10 detectors | 707 | Deep SVDD stays (gated-vs-raw story) |
| III | tab:onset | Onset sensitivity to k on IMS | 766 | unchanged |
| IV | tab:onsetdef | Onset under 3 health indicators | 832 | unchanged |
| V | tab:persist | Alarm-persistence sensitivity | 865 | unchanged |
| VI | tab:gaps | Missing-data robustness | 898 | unchanged |
| VII | tab:ims_paired | IMS run-level agg-vs-dec (table*) | 957 | Deep SVDD row → Deep SVDD appendix |
| VIII | tab:ongc_paired | ONGC descriptive diffs (n=1) | 1013 | → Appendix (ONGC case study) |
| IX | tab:xjtu_paired | XJTU n=10 sign test | 1060 | Deep SVDD row → appendix |
| X | tab:femto_paired | FEMTO n=6 sign test | 1125 | Deep SVDD row → appendix |
| XI | tab:ferrara_paired | Ferrara n=6 sign test | 1170 | Deep SVDD row → appendix |
| XII | tab:holm | Holm N=40 family | 1222 | KEEP INTACT (N=40), add footnote |
| XIII | tab:xjtu_perbearing | XJTU per-bearing summary | 1303 | unchanged |
| XIV | tab:noise | IMS noise injection (mechanism) | 1407 | → Appendix D (mechanism) |
| XV | tab:denoise | IMS denoiser comparison (mechanism) | 1434 | → Appendix D (mechanism) |
| XVI | tab:calib | Conformal IMS FAR vs alpha | 1486 | unchanged |
| XVII | tab:farsens | FAR-budget sensitivity (best valid lead per detector, tau 0.05/0.10/0.20) | 1610 | source for new STEP-11 figure |
| XVIII | tab:tradeoff | IMS lead-vs-FAR trade-off | 1663 | Deep SVDD stays |
| XIX | tab:coarsen | Feature-group frac by coarsening | 1768 | unchanged |
| XX | tab:ablation | IMS feature-group ablation (IF) | 1791 | unchanged |
| XXI | tab:ablation_spc | Ablation across detectors | 1813 | Deep SVDD stays (col) |
| XXII | tab:spectral | Spectral ablation per run | 1853 | Deep SVDD stays |
| XXIII | tab:latchon | Latch-on vs gated metric | 1920 | promote (metric proof) |
| XXIV | tab:phrank | PH vs L detector rankings | 1965 | promote (metric proof) |
| XXV | tab:trainsweep | Training-fraction sweep FEMTO (table*) | 2043 | Deep SVDD stays (col) |
| XXVI | tab:hparams | Fixed hyperparameters | 2272 | unchanged (Appendix A) |
| XXVII | tab:cost | Per-detector compute cost | 2326 | Deep SVDD stays |
| XXVIII | tab:featbase | 6 base statistics | 2372 | unchanged (Appendix B) |

## Figures (source order)

| Fig | Label | File | Line | Reframe action |
|-----|-------|------|------|----------------|
| 1 | fig:rms | fig_rms_degradation.png | 743 | unchanged |
| 2 | fig:sampling | fig_leadtime_vs_sampling.png | 988 | unchanged |
| 3 | fig:cross | fig_crossdataset.png | 1090 | keep (ONGC bars hatched/separated per caption) |
| 4 | fig:calib | fig_calibration.png | 1503 | unchanged |
| 5 | fig:calib_xjtu | fig_calibration_xjtu.png | 1513 | unchanged |
| 6 | fig:calib_femto | fig_calibration_femto.png | 1540 | unchanged |
| 7 | fig:calib_ongc | fig_calibration_ongc.png | 1550 | → Appendix (ONGC case study) |
| 8 | fig:tradeoff | fig_tradeoff.png | 1690 | unchanged |
| 9 | fig:tradeoff_xjtu | fig_tradeoff_xjtu.png | 1699 | unchanged |
| 10 | fig:mindata | fig_training_sweep.png | 2067 | unchanged |
| NEW | fig:farbudget | fig_far_budget_detector.png (to generate, STEP 11) | — | from tab:farsens data |

## Equations
- (1) h(t)=max(z_b[RMS], z_b[kurt]) — line 443
- (2) t_o=min{...} `eq:onset` — line 451
- (3) L=max(0,(t_f-FAT)/3600) — line 497
- (4) FAR_pre — line 503
- (5) validity: L>0 ∧ FAR_pre≤τ `eq:valid` — line 509
- (6) τ* ≈ ρ/k `eq:taustar` — line 646 (source for new STEP-10 grid table)

Algorithm 1 `alg:onset` — line 462.

## Detector set (current)
Ten detectors: RMS-trend, 3σ, EWMA, CUSUM, Hotelling T², Isolation Forest, **Deep SVDD**,
LSTM-AE, TCN-AE, Transformer-AD. (One-class SVM implemented but already out of headline.)
Reframe → nine headline (drop Deep SVDD from the count); Deep SVDD "additionally evaluated."
