# Response to Review -- audit changes (final pass, Part 5)

Letter: IJPHM-Response-to-Review-FINAL.md. Each change is an exact replacement; the reason column is the evidence. Unlisted text was checked and left unchanged.

## 1. Author box deleted (its three items resolved: Appendix C count -> change 14; Table 4(b) figures -> change 4; release tag -> v1.3.0 here and in submission/SUBMISSION_CHECKLIST.md)

**Old:**

> > **FOR THE AUTHOR — delete this box before sending.**
> >
> > This letter was rebuilt from the final audit. It supersedes `IJPHM-Response-to-Review.md`, which contains stale and false claims.
> >
> > **Confirm against the final PDF before sending:**
> > 1. Appendix C: the number of detectors for which test 3 becomes a guaranteed miss under the original label. The letter says "most detectors" rather than a count — check whether that table has ten or eleven rows before adding one.
> > 2. Table 4(b): the multi-seed gap results as quoted below.
> > 3. The repository claims are true only after you push `main`, cut `v1.2.3`, and create the Release. Do those first.
> >
> > Deliberately **not** cited: em-dash counts and headline-restatement counts. Successive audits measured them differently, and a contestable number invites scrutiny that a described action does not.

**New:**

> *(deleted)*

## 2. Release tag, verifier count and test count (verify_tables.py: 906 values; pytest --collect-only: 181)

**Old:**

> All analyses are reproducible from the public repository at tag v1.2.3. A script in the test suite re-derives 558 printed table values from the released result files and fails on any mismatch.

**New:**

> All analyses are reproducible from the public repository at tag v1.3.0. A script in the 181-test suite re-derives 906 printed values from the released result files and fails on any mismatch.

## 3. Disclosure 1: 78 is the smallest IMS run (test windows 172 / 78 / 506 per run)

**Old:**

> The IMS results were produced on the 445-dimensional path, on 78 test windows.

**New:**

> The IMS results were produced on the 445-dimensional path, on runs with as few as 78 test windows.

## 4. Disclosure 4: 5% claim replaced by the verified statement; 20% verified per chart from d18_gap_injection_multiseed.csv (3sigma +0.83/-0.04, EWMA -0.08/-0.12, CUSUM -0.67/-0.02, IF -0.92/-0.07 h; Hotelling IMS -51.2 h); Table 4(b) prints means only, the ranges are in the text

**Old:**

> Re-running with five independent draws shows the claim holds at 5% missing rows, where no chart's lead changes in any draw. At 20% it holds for the univariate charts but fails for Hotelling T², which collapses in 2 of 5 draws — a single run's alarm survives or does not depending on which rows are removed. Table 4(b) now reports across-draw means with ranges, and the text states the Hotelling T² vulnerability.

**New:**

> Re-running with five independent draws shows the claim holds at 5% missing rows: on IMS, Hotelling T² and EWMA are unchanged in every draw, and no chart's per-draw mean lead moves by more than 0.83 h on either dataset. At 20% it holds for the univariate charts and Isolation Forest, whose across-draw mean lead changes by at most 0.92 h on IMS and XJTU-SY, but fails for Hotelling T² on IMS, which collapses in 2 of 5 draws (across-draw mean 134.9 h, range 58.0–186.1 h, against 186.1 h without gaps) — a single run's alarm survives or does not depending on which rows are removed. Table 4(b) now reports across-draw means, and the text gives the ranges and states the Hotelling T² vulnerability.

## 5. Disclosure 8 (new): ONGC gating finding (Part 1); items 8-11 renumbered 9-12

**Old:**

> ### Figure defects
> 
> **8. The trade-off figure

**New:**

> **8. The ONGC case study reported raw lead as if it were detection quality.** Nine of the eleven detectors alarm 30–35 h before the labeled shutdown, but under the paper's own gated metric at τ = 10% only Hotelling T² (pre-onset false-alarm rate 6.5%) and the RMS-trend baseline (0.1%) have valid alarms; the other eight alarming detectors exceed the budget, at 11.7% (Isolation Forest) to 95.2% (CUSUM). The data-derived onset lies only about 6 h before the shutdown, so their first alarms precede it by 28–29 h and count as pre-onset false alarms. That verdict is itself ambiguous: the onset estimator is systematically late under gradual degradation (the bias analysis Reviewer G requested, Section 4.3), so some of those alarms may be genuine early detection, and with a single asset and no ground-truth defect-initiation time the case study cannot distinguish the two. Appendix D.2 and Section 7.2 now state both readings. The aggregate-versus-decimate contrast on ONGC uses raw lead and is unaffected.
> 
> ### Figure defects
> 
> **9. The trade-off figure

## 6. renumber

**Old:**

> **9. Detectors shared colours.**

**New:**

> **10. Detectors shared colours.**

## 7. renumber

**Old:**

> **10. The ONGC bars in Figure 2

**New:**

> **11. The ONGC bars in Figure 2

## 8. renumber

**Old:**

> **11. The Data and Code Availability section

**New:**

> **12. The Data and Code Availability section

## 9. cross-reference to the renumbered figure items

**Old:**

> surfaced disclosure items 8, 9 and 10,

**New:**

> surfaced disclosure items 9, 10 and 11,

## 10. cross-reference to the renumbered reproducibility item

**Old:**

> Acting on this comment uncovered disclosure item 11.

**New:**

> Acting on this comment uncovered disclosure item 12.

## 11. Smaller corrections: ONGC breakdown verified from n20_rerun_long_ONGC.csv (factor 1); N-29 double rounding added

**Old:**

> The ONGC case study stated that every detector alarmed roughly 35 h ahead, when nine of eleven do, with RMS-trend at about 23 h and Deep SVDD not alarming before failure.

**New:**

> The ONGC case study stated that every detector alarmed roughly 35 h ahead; nine of eleven alarm 30–35 h ahead (seven within 34.9–35.3 h, CUSUM at 33.9 h and Hotelling T² at 30.4 h), RMS-trend at 22.8 h, and Deep SVDD does not alarm before failure (disclosure item 8 gives the gated reading). Two values were double-rounded: the historian-averaging arm of the denoiser comparison (Table 15b) is 75.6 h, not 75.7 h (source 75.647 h), and the one-class SVM's prognostic horizon (Table 2) is 180.2 h, not 180.3 h (source 180.250 h).

## 12. One-class SVM coverage: Tables 10 and 14 carry Deep SVDD but not the one-class SVM

**Old:**

> One-class SVM now appears alongside Deep SVDD in every table covering the additionally-evaluated detectors.

**New:**

> One-class SVM now appears alongside Deep SVDD in the results tables (Tables 2, 5, 6 and 9) and the compute table (Table 11); the feature-group ablation (Table 10) and the relabel contrast (Table 14) report Deep SVDD without it.

## 13. Equivalence method: no TOST p-values or 'untestable' marks exist in the paper; Table 5 uses CI inclusion + sign-test p

**Old:**

> TOST results are reported where the non-zero-difference count supports them; the remaining cells are marked untestable rather than given a p-value that could not have reached significance.

**New:**

> Equivalence is judged by whether each run-level 95% bootstrap interval lies inside ±δ, and the exact sign-test p-value is reported beside each cell (Table 5).

## 14. Appendix C count resolved from Table 14 / Appendix C text: six of the ten detectors

**Old:**

> for most detectors the third test becomes a guaranteed miss and the effective n falls, while others retain n = 3.

**New:**

> for six of the ten detectors in that table the third test becomes a guaranteed miss and the effective n falls, while the other four retain n = 3.

## 15. Reviewer D length passage: counts from the submitted PDF (paper/Scada__IJPHM.pdf: 24 pages, 29 tables, 11 figures) and the final build (22 pages, 15 tables, 6 figures)

**Old:**

> Tables are consolidated from 30 to 23 and figures from 11 to 6, with no result removed.
> 
> I should be direct about the net effect: the paper is 30 pages against 24 as submitted. The reduction in repetition is real and every cut the reviewer named was made, but the revision also adds an equivalence analysis, a gated-metric contrast table, an architecture table, a signal-theoretic section, an onset-estimator analysis, Appendix C, a per-dataset coarsening statement, scoping paragraphs and three related-work paragraphs — all requested by the reviewers. I judged that removing the sensitivity and ablation work to reclaim pages would be the wrong trade.

**New:**

> Tables are consolidated from 29 to 15 and figures from 11 to 6, with no result removed.
> 
> The net effect: the revised paper is 22 pages against 24 as submitted, with 15 tables against 29 and 6 figures against 11. It is shorter although the revision adds an equivalence analysis, a gated-metric contrast table, an architecture table, a signal-theoretic section, an onset-estimator analysis, Appendix C, a per-dataset coarsening statement, scoping paragraphs and three related-work paragraphs — all requested by the reviewers. The pages were recovered by merging tables that reported overlapping results, redrawing figures at print size and removing repetition, not by removing the sensitivity and ablation work: every sentence, number, table cell and citation of the longer intermediate draft is accounted for in the final version.

## 16. Gated-vs-raw power cost: 195 was the pre-N-20 count; post-fix raw non-zero differences = 171 (rf2_gated_contrast_n20.csv / n20_raw_contrast_old_vs_new.csv 'new' arm, four inferential datasets)

**Old:**

> falls from 195 to 98

**New:**

> falls from 171 to 98

## 17. Reviewer F tables: counts updated; merged Table 5 described

**Old:**

> the three per-dataset sign-test tables are one table with a dataset column; the four conformal calibration figures are one four-panel figure. Tables fall from 30 to 23 and figures from 11 to 6, with no result removed.

**New:**

> the three per-dataset sign-test tables, the equivalence table and the Holm table are one table grouped by dataset (Table 5); the four conformal calibration figures are one four-panel figure. Tables fall from 29 to 15 and figures from 11 to 6, with no result removed.

## 18. Holm table: now merged into Table 5 / Table 6 (renumbering map: T8 holm -> T5 caption)

**Old:**

> The Holm correction table, the densest, is restructured from a 45-row list into an 11 × 4 matrix. Its adjusted-p and rejection columns were identical in every row, so they are replaced by a single sentence in the caption.

**New:**

> The Holm correction table, the densest, was a 45-row list. Its raw p-values are now a column of Table 5 (Table 6 for IMS), eleven detectors by four datasets, and its adjusted-p and rejection columns, identical in every row, are replaced by a single sentence in the Table 5 caption.

## 19. Reviewer G onset sensitivity: Isolation Forest's gated IMS median stays +3.43 h under pca1 (rg3_contrast_by_indicator.csv); the gated IMS statement is not in the manuscript

**Old:**

> while on IMS every positive gated median falls to zero under both alternatives. We therefore state that raw-lead non-destruction does not depend on the onset definition, whereas any gated directional pattern on IMS does and is not claimed.

**New:**

> while on IMS the positive gated medians of CUSUM, EWMA and Hotelling T² fall to zero under both alternatives and Isolation Forest's under the kurtosis-only indicator (under the first principal component it is unchanged, at +3.43 h). The manuscript therefore claims only that raw-lead non-destruction does not depend on the onset definition; it claims no gated directional pattern on IMS, which does depend on it.

## 20. Closing: release tag and verifier count

**Old:**

> The analyses are reproducible from the public repository at tag v1.2.3, with a pinned environment and a test suite that includes a script re-deriving 558 printed table values

**New:**

> The analyses are reproducible from the public repository at tag v1.3.0, with a pinned environment and a 181-test suite that includes a script re-deriving 906 printed values

## 21. Layout: the double horizontal rule left by deleting the author box collapsed to one

# Manuscript corrections made during the letter audit

The letter asserted these things of the manuscript; the final PDF did not bear them out, so the
manuscript (not the letter) was corrected, each minimally. Build after all: 22 pages, 0 undefined,
0 overfull; verify_tables all match.

## M1. Sec. 8 did not name the raw-waveform study that Sec. 4.8 ("Section 8 names it as the complementary study") and the letter promise (pre-existing: absent from the 30-page draft too)
**Old (Sec. 8, Future work, end):** > ...and the single real-asset record is one gas-turbine compressor bearing.
**New:** > ...and the single real-asset record is one gas-turbine compressor bearing. The complementary study coarsens the raw waveform itself, where averaging is a low-pass filter on the impulsive transients of an incipient fault (Section 4.8); our claim concerns historian summary statistics and does not cover it.

## M2. "LSTM" never expanded (letter: expanded at first use; not expanded in the submission either)
**Old (Sec. 1):** > deep reconstruction models (an LSTM autoencoder, ...
**New:** > deep reconstruction models (a long short-term memory (LSTM) autoencoder, ...

## M3. "SVM" first used in Sec. 1 but expanded only in Sec. 2.2
**Old (Sec. 1):** > ... and a one-class SVM, on four ...   **(Sec. 2.2):** > the one-class support vector machine (SVM)
**New (Sec. 1):** > ... and a one-class support vector machine (SVM), on four ...   **(Sec. 2.2):** > the one-class SVM

## M4. 5% gap sentence true on IMS only (EWMA moves <= 0.07 h per draw on XJTU-SY)
**Old:** > At 5% missing, Hotelling T2 and EWMA are unchanged in every draw,
**New:** > At 5% missing, Hotelling T2 and EWMA are unchanged in every draw on IMS,

## M5. "every detector" in the gap paragraph: the D18 run also contains RMS-trend (IMS valid 1/3 -> 2/3 in some draws, mean lead +7.4 / +8.4 h), which Table 4b does not report
**Old:** > At 20% every detector on both datasets stays ... / (2/3 for every detector at every gap level ...
**New:** > At 20% every Table 4b detector on both datasets stays ... / (2/3 for every Table 4b detector at every gap level ...

## M6. Internal audit tag in a caption
**Old (Table 4 caption):** > ... five independent gap draws per level (defect D18).
**New:** > ... five independent gap draws per level.

## M7. D.1 operates on the snapshot series (src/robustness.py: transforms on the rms_ch*/kurt_ch* snapshot grid via load_pipeline, coarsened before feature extraction); the paper said "per-window" and did not note the level difference the letter says it notes
**Old:** > We test both on IMS at sampling factor 5, controlling window content so that only the smoothing differs. ... We add zero-mean Gaussian noise to the per-window health statistic at signal-to-noise ratios ...
**New:** > We test both on IMS at sampling factor 5, controlling window content so that only the smoothing differs. Here aggregation and decimation act on the per-snapshot series before windowing, whereas the IMS sweep coarsens the windowed feature vectors (Section 4.8), so this corroborates the mechanism on a related but not identical operation. ... We add zero-mean Gaussian noise to the per-snapshot channel statistics (RMS and kurtosis), scaled per channel, at signal-to-noise ratios ...

# Letter claims verified and left unchanged (evidence)
- 33/33 equivalent; max |CI endpoint| 0.5596 h (n20_d15_bootstrap_new_11det.csv); 5 cells wholly below zero, widest -0.45 h.
- IF on FEMTO post-fix 2+/4-, p = 0.6875 (n20_raw_contrast_old_vs_new.csv, arm new).
- FWER 1-0.95^40 = 0.87, 1-0.95^44 = 0.90; smallest raw p 0.125; Holm 0/44.
- Legacy 3sigma median +18.43 h (benchmark_IMS_long.csv) -> +15.1 h invariant.
- LSTM-AE 99.5th pct test 3: 59.67 h at 4.19%, ten seeds (PDF Sec. 6.1).
- Persistence table 3sigma valid fraction 0.67 (Table 4a).
- CUSUM pre-onset FAR 18.99-19.80% across thresholds (tradeoff_IMS.csv).
- Training sweep: best deep 0.333 vs SPC mean 0.625 at T = 0.5 (femto_training_sweep.csv).
- G1: onset delay identical at persistence 5 and 20 for every slope (re-simulated with src/onset.detect_onset, 6 slopes x 30 seeds), tracks k sigma_b/m.
- G3: multi-bearing gated medians within +-1 h under every indicator (max 0.72 h).
- 20-335 training windows, median 88; 2.0-5.5 x 10^4 parameters; 54,657 / 29,681 / 20,305 / 1,824 parameters.
- Submission (paper/Scada__IJPHM.pdf): 24 pages, 29 tables, 11 figures, "non-destruction" x21, "honest" x18; final: 8 and 0.
- Sec. 7.4 deleted = submission's "Summary of Key Outcomes"; final 7.4 Practical Implications carries the Deep SVDD point.
- ONGC exporter refuses to write on onset mismatch (src/export_ongc_derived.py:123); tests/test_ongc_release.py.
- No early stopping in src/; section/table/figure references re-checked against the final aux.
