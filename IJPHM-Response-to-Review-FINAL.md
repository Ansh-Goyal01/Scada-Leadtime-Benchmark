# Response to Review

**Manuscript:** A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing Anomaly Detection — and What It Reveals About SCADA-Rate Logging

**Author:** Ansh Goyal

---

## Opening

I thank the three reviewers for reviews that were unusually specific. Several comments identified genuine mismatches between what the paper did and what it claimed. Following them up meant opening the code, and that uncovered further defects of the same kind that no reviewer had seen. All are disclosed below.

Every point raised has been addressed. The changes that alter what the paper claims are:

1. **Section 4.8 now states, per dataset, the level at which the aggregate and decimate operations are applied**, and the introduction is aligned with it (Reviewers D and F).
2. **The headline is now a bounded equivalence statement rather than an accepted null**, supported by a pre-specified ±1 h margin: equivalence holds in 33 of 33 detector × dataset cells on the three multi-bearing campaigns (Reviewer D).
3. **The claim that "decimation is never better" has been removed throughout.** Investigating the contradiction Reviewer D found uncovered a resampling defect, disclosed as item 2 below.
4. **The aggregate-versus-decimate comparison is now also reported under the gated metric** (Reviewer F).
5. **The IMS results have been re-baselined onto the feature space that Section 4.2 describes as the paper's methodology.** This is disclosed as item 1 below.

The correction family is now N = 44. No hypothesis is rejected at any family size, and the non-destruction conclusion is unchanged.

All analyses are reproducible from the public repository at tag v1.3.0. A script in the 181-test suite re-derives 1040 printed values from the released result files and fails on any mismatch.

---

## Defects found during revision and disclosed voluntarily

None of the following was raised by a reviewer. Each was present in the submitted manuscript, was found while following up a reviewer's comment, and is corrected. I report them because the reviewers' central concern — that the paper claim exactly what the evidence supports — applies equally to defects they did not happen to see.

### Defects that changed results

**1. The headline dataset used a feature scheme the paper argues against.** Section 4.2 argues that a 445-dimensional, channel-count-dependent feature space is ill-posed at p ≫ n, and presents a 49-dimensional invariant space as the methodology. The IMS results were produced on the 445-dimensional path, on runs with as few as 78 test windows. All IMS results are re-baselined onto the invariant space. The 3σ run-level median moves from +18.4 h to +15.1 h, and the direction is no longer consistent across the three runs, so the submitted abstract's "consistent positive trend" is withdrawn. The Holm verdict is unchanged under both schemes.

**2. A resampling defect coarsened the two arms unequally.** The aggregation bin width was rounded to whole minutes with a one-minute floor. On FEMTO, Ferrara and ONGC, whose native spacing is sub-minute, the aggregate and decimate arms therefore ran at different effective logging intervals at the same nominal factor. Section 4.7 states that the controlled sweep holds everything constant except the logging interval; this defect sat inside that exact mechanism. It is fixed. IMS and XJTU-SY have integer-minute spacing, so the rounding was a no-op there, and both reproduce byte-identically after the fix, which confirms the correction is scoped. On the three affected datasets, every factor-1 row and every decimate row is unchanged; only aggregate rows at factor > 1 moved. The defect handicapped the aggregate arm, so the observed equivalence held despite it.

**3. The training-fraction sweep did not vary the training fraction.** The sweep changed a configuration value the pipeline never read, so all five settings ran at the same split; a released column records the number of training windows as constant across the sweep. What varied was the onset anchor. This is fixed and the sweep re-run. The conclusion is unchanged and now actually tested: no crossover appears in [0.20, 0.60].

**4. The robustness claim for historian gaps rested on one random draw.** The submitted manuscript stated that dropping a fifth of the historian's records does not cost the control charts their warning time, from a single random draw of which rows to remove. Re-running with five independent draws shows the claim holds at 5% missing rows: on IMS, Hotelling T² and EWMA are unchanged in every draw, and no chart's per-draw mean lead moves by more than 0.83 h on either dataset. At 20% it holds for the univariate charts and Isolation Forest, whose across-draw mean lead changes by at most 0.92 h on IMS and XJTU-SY, but fails for Hotelling T² on IMS, which collapses in 2 of 5 draws (across-draw mean 134.9 h, range 58.0–186.1 h, against 186.1 h without gaps) — a single run's alarm survives or does not depending on which rows are removed. Table 4(b) now reports across-draw means, and the text gives the ranges and states the Hotelling T² vulnerability.

### Claims that did not match the evidence

**5. A claim about the deep models was refuted rather than merely unsupported.** Section 6.1 stated that the deep reconstruction models flood the pre-onset region "regardless of threshold." Running them through the threshold sweep, as Reviewer D asked, showed this is false: LSTM-AE attains a valid operating point at the 99.5th percentile on the third IMS test, with 59.7 h of lead at 4.19% pre-onset false-alarm rate, unchanged across ten random seeds. The claim is corrected. The deployment recommendation is unaffected.

**6. Several result tables had no generating script, and one value could not be reproduced.** The persistence-sensitivity, gap-injection, compute-cost and onset-indicator tables existed as committed files with no code that produced them. Generators are now released. The persistence table reported a 3σ valid-alarm fraction of 1.00 that the released data does not support — it gives 0.67 — and the conclusion drawn from it is withdrawn.

**7. A sentence named the wrong detector as its worked example.** The text stated that EWMA attains the highest raw lead in the trade-off table, where it does not. The gating argument is unaffected and is stronger with the correct detector: Hotelling T² genuinely has the highest raw lead among the control charts and no valid operating point at any tested threshold.

**8. The ONGC case study reported raw lead as if it were detection quality.** Nine of the eleven detectors alarm 30–35 h before the labeled shutdown, but under the paper's own gated metric at τ = 10% only Hotelling T² (pre-onset false-alarm rate 6.5%) and the RMS-trend baseline (0.1%) have valid alarms; the other eight alarming detectors exceed the budget, at 11.7% (Isolation Forest) to 95.2% (CUSUM). The data-derived onset lies only about 6 h before the shutdown, so their first alarms precede it by 28–29 h and count as pre-onset false alarms. That verdict is itself ambiguous: the onset estimator is systematically late under gradual degradation (the bias analysis Reviewer G requested, Section 4.3), so some of those alarms may be genuine early detection, and with a single asset and no ground-truth defect-initiation time the case study cannot distinguish the two. Appendix D.2 and Section 7.2 now state both readings. The aggregate-versus-decimate contrast on ONGC uses raw lead and is unaffected.

**9. Validity counts included alarms the gate could not evaluate.** Where the onset estimator places the onset at or before the first scored window, the pre-onset region is empty and the false-alarm rate is undefined. The submitted manuscript's XJTU-SY counts, and its per-bearing table, counted such alarms as valid whenever their lead was positive, and one bearing with no detectable onset was scored by a positional criterion the paper did not state. Equation 5 now states the rule explicitly — such alarms are excluded from the validity denominator — and every count is restated under it. The XJTU-SY figure of 209/450 becomes 48 of 230 scoreable evaluations, 220 being excluded (170 with an empty pre-onset region, 50 on the bearing with no detectable onset); in the per-bearing table five of the ten bearings cannot be scored at full resolution, and the total becomes 6/25 rather than 20/50. The same rule moves the pooled persistence fractions and the XJTU-SY gap columns of Table 4 and the smallest training fraction of the deep-model sweep; the FEMTO count and the gated contrast already applied it. No aggregate-versus-decimate result is affected, since those are computed on raw lead.

### Figure defects

**10. The trade-off figure omitted the detectors its argument depends on.** It plotted five of the seven detectors in its source file. The missing two were CUSUM and Deep SVDD, and Deep SVDD's low-false-alarm operating point is the basis of the complementary recommendation in Sections 6.9 and 7.4.

**11. Detectors shared colours.** A second, divergent colour table meant that EWMA and LSTM-AE were drawn in the same colour, as were Hotelling T² and Deep SVDD. All eleven detectors now have distinct colours. Eleven categories cannot be made fully dichromat-safe by hue alone; I have not added a redundant encoding.

**12. The ONGC bars in Figure 2 were drawn 60 times too small**, owing to a unit conversion applied twice in the plotting script.

### The reproducibility statement

**13. The Data and Code Availability section made claims that were false of the public repository.** The result tables were excluded from version control, so the statement that every table and figure is generated from released result files was untrue of what a reader could obtain. The statement also claimed that a derived ONGC series was released when it was not, gave a stale test count, and cited a file that did not exist. All result files are now released, with a manifest mapping each table and figure to its source file and superseded files separated from current ones. The ONGC derived artifacts are generated by a released exporter, and a released test recomputes the published ONGC degradation onset from those files alone, touching no proprietary input. Each claim was verified from a clean clone of the public repository rather than the working tree.

### Smaller corrections

A caption claimed ten evaluated detectors against a nine-row table. A caption claimed valid-alarm fractions were unchanged under injected gaps while showing one that changed. The ONGC case study stated that every detector alarmed roughly 35 h ahead; nine of eleven alarm 30–35 h ahead (seven within 34.9–35.3 h, CUSUM at 33.9 h and Hotelling T² at 30.4 h), RMS-trend at 22.8 h, and Deep SVDD does not alarm before failure (disclosure item 8 gives the gated reading). Two values were double-rounded: the historian-averaging arm of the denoiser comparison (Table 15b) is 75.6 h, not 75.7 h (source 75.647 h), and the one-class SVM's prognostic horizon (Table 2) is 180.2 h, not 180.3 h (source 180.250 h). Section 6.2 stated that the default onset moves by less than two percent of run span on every IMS run as k varies; on the second test it moves 5.4 percentage points (60.4% to 65.8% of span), and the text now gives the spread per run.

---

# Reviewer D

> "It would have been good to also at least slightly touch on the extensive false positive related costs discussed in other fields including general anomaly detection publications. The Numenta Anomaly Benchmark (Lavin & Ahmad 2015) comes to mind."

**Response.** Added to §2.1. The Numenta Anomaly Benchmark scores streaming detectors under a profile that rewards early detection and penalises false positives, making the same commitment our gate makes in a different domain. The paragraph states the structural difference: that benchmark folds both into a weighted score, so a detector can trade false alarms against earliness, whereas our budget is a validity condition, and an alarm outside it earns no credit that a longer lead can offset.

---

> "the number and size of the datasets tested is small… and the 3σ deployment recommendation inherits an acknowledged circularity between the onset definition and the detectors' features."

**Response.** Both stand, and the treatment is strengthened. Section 8 now states the structural asymmetry of the evidence directly: the campaigns supplying statistical power are bearings of 0.7–8.9 h lifetime, on which an effect of the magnitude seen on IMS could not have appeared, so the null there bounds the effect at the scale of minutes. The only dataset with a long enough runway has n = 3. We claim non-destruction at short lifetimes, and consistency with — not demonstration of — non-destruction at industrial lifetimes. A scoped sentence appears in the abstract and conclusion as well.

The circularity has been probed empirically at Reviewer G's request. The contrast was recomputed under two onset indicators that do not share the magnitude detectors' amplitude basis, and the raw-lead differences are exactly invariant — maximum absolute deviation 0.000 h across 99 cells.

---

> "the deep reconstruction models are stated to have no valid operating point 'regardless of threshold' (Section 6.1) but are omitted from the threshold sweep in Table 16. This evidence should be shown or the claim softened"

**Response.** We ran the sweep rather than softening the claim, and it showed the claim was false; see disclosure item 5. The three deep models are now rows in the trade-off table, and the text states what was measured at each threshold.

---

> "one-class SVM is described as evaluated (Section 4.5) but appears in no results table. It should be reported or the mention removed."

**Response.** Reported. The code produced the results; they had not been included. One-class SVM now appears alongside Deep SVDD in the results tables (Tables 2, 5, 6 and 9) and the compute table (Table 12); the feature-group ablation (Table 10) and the relabel contrast (Table 14) report Deep SVDD without it.

Adding it widens the correction family from N = 40 to N = 44 and raises the uncorrected family-wise error rate from approximately 0.87 to approximately 0.90. No hypothesis is rejected at either family size, and the smallest raw p-value is 0.125. The requested addition widens the evidence base without altering any conclusion.

It also sharpens Section 6.11. With all eleven detectors ranked, the seven that the prognostic horizon ranks highest all have no valid operating point at a 10% budget, and 3σ — which that metric ranks eighth — is the deployable choice.

---

> "Section 4.7 describes the coarsening operation inconsistently: 'before feature extraction' in one sentence and 'resamples at the feature level' two sentences later… The authors should state, for each dataset, at which level the aggregate and decimate operations are applied, and align the framing in the introduction and abstract with it."

**Response.** The reviewer is correct: the two descriptions corresponded to different operations on different datasets. Both sentences are removed, and a new Section 4.8 states the level per dataset. IMS coarsens the windowed feature vectors; XJTU-SY, FEMTO, Ferrara and ONGC coarsen the per-snapshot feature series. No dataset coarsens the raw waveform.

We have also narrowed the framing, as the reviewer's overall evaluation anticipated. The introduction had described the concern in terms of waveform averaging destroying impulsive transients — a different operation from the one tested. It now separates the two: averaging a raw waveform is a low-pass filter and does attenuate incipient-fault transients, which we neither test nor dispute; the question that governs historian design is whether bin-averaging the summary statistics a historian actually stores costs warning time relative to keeping every k-th summary. The ONGC record is the clearest case, since its channels are the historian stream and no coarsening is simulated. Raw-waveform coarsening is named in Section 8 as the complementary study. The practical-implications paragraph of Section 7.4 is aligned with Section 4.8 in the same way: it compares bin-averaged summary statistics with keeping every f-th stored value, bounded to the ±1 h margin on the datasets tested, and no longer refers to decimated raw samples.

---

> "the headline 'does not cost warning time' is a null-acceptance claim made without an equivalence test; it should be reworded as a bounded no-detectable-difference statement or supported formally."

**Response.** Both. The claim is bounded throughout, and supported by an equivalence analysis at a margin of δ = 1 h, stated and justified at first use: a maintenance planner cannot act on sub-hour differences in warning time.

Equivalence holds in 33 of 33 detector × dataset cells across XJTU-SY, FEMTO and Ferrara, using two-sided bootstrap confidence intervals on run-level differences; no interval endpoint exceeds 0.56 h. No cell shows decimation superior beyond the margin. On IMS, equivalence cannot be established and we say so: the exact one-sided sign test at n = 3 floors at p = 0.125, so no margin can reach α = 0.05, just as significance cannot be reached in the other direction. Equivalence is judged by whether each run-level 95% bootstrap interval lies inside ±δ, and the exact sign-test p-value is reported beside each cell (Table 5).

---

> "the introduction's 'decimation is never better' is contradicted by the paper's own Table 8"

**Response.** The reviewer is right, and we thank them for catching a contradiction between two sections of the same manuscript. The universal claim is removed wherever it appeared.

Two facts, stated independently. First, the claim is removed because it was never supported by the evidence, regardless of any particular counterexample. Second, investigating the specific counterexample uncovered the resampling defect in disclosure item 2; with it corrected, Isolation Forest on FEMTO is 2+/4−, p = 0.688, and no longer sign-consistent.

The replacement is bounded around the margin rather than around an absence of negative cells, because five cells have intervals lying entirely below zero. No cell shows decimation superior beyond ±1 h, and the widest of those five intervals reaches only −0.45 h.

---

> "The IMS test-3 failure relabel is author-chosen… results under the original label should be shown."

**Response.** Added to Appendix C, with the full sweep under both labels side by side.

We lead with the result that runs against our own framing. Under the original label, the third test's aggregate-minus-decimate difference for the 3σ chart is exactly zero and drops out under the zero-difference rule of Section 4.9, leaving two positive runs and none negative. The withdrawn claim that aggregation shortens lead time in no run would therefore have been true under the original label, and is false only under the corrected one. The relabelling made the paper's own claim harder to support.

The effect on sample size is detector-dependent: for six of the ten detectors in that table the third test becomes a guaranteed miss and the effective n falls, while the other four retain n = 3. No IMS detector reaches significance under either label, since the best attainable floor is p = 0.25.

---

> "the non-destruction conclusion should be scoped: the datasets providing statistical power are short-lived bearings on which the effect could never exceed minutes, while the long-runway case rests on three runs."

**Response.** Done; see the response on dataset size above. The asymmetry is stated in Section 8, the abstract and the conclusion.

---

> "the paper is much longer than needed: the headline finding is restated many times, Table 21 and Table 23 can be cut, Section 7.4 duplicates Section 6's summaries"

**Response.** Every named item is done. Table 21 is deleted and replaced by one sentence; Table 23 is deleted and the figure carries the result alone; Section 7.4 is deleted in full. Section 6's opening summary list, which previewed subsections that immediately follow, is also deleted. The five-cell exception, which had been enumerated in full four times, now appears once, in the results where the cells are reported. The term "non-destruction" falls from 21 occurrences to 8. Tables are consolidated from 29 to 15 and figures from 11 to 6, with no result removed.

The net effect: the revised paper is 22 pages against 24 as submitted, with 15 tables against 29 and 6 figures against 11. It is shorter although the revision adds an equivalence analysis, a gated-metric contrast table, an architecture table, a signal-theoretic section, an onset-estimator analysis, Appendix C, a per-dataset coarsening statement, scoping paragraphs and three related-work paragraphs — all requested by the reviewers. The pages were recovered by merging tables that reported overlapping results, redrawing figures at print size and removing repetition, not by removing the sensitivity and ablation work: no result from the submitted version has been removed; the results that changed are the corrections disclosed above.

---

> "the self-descriptive statements ('statistically honest by construction,' 'the metric correctly refuses…') should be removed"

**Response.** Removed. Both phrases are gone, and all eighteen instances of "honest" or "honestly" are deleted or rewritten to state the fact without the adjective.

---

> "SCADA is never expanded… BPFO, BPFI, BSF, and FTF are named but never expanded."

**Response.** Both corrected. A sweep of the manuscript found further unexpanded abbreviations, which are now expanded at first use, including SPC, CUSUM, EWMA, LSTM, TCN, SVDD, SVM, PCA, FFT, RMS, MLP, ROC–AUC and ONGC.

---

> "The Figure 10 title is misleading… the in-plot title contradicts its own caption and should be removed."

**Response.** Removed, and in-plot titles are removed from every figure for the same reason: a title inside the plot duplicates the caption and can drift out of step with it.

---

> "the x and y labels in Figure 2 are malformed, and the Figure 10 legend is malformed. The authors should regenerate both figures and check the remaining figures for similar issues."

**Response.** Both regenerated. The cause was a character-encoding fault in the plotting scripts that corrupted Δ, −, σ, ≈ and ²; these now render through mathtext. A doubled parenthesis in Figure 2's legend is also fixed.

Checking the remaining figures, as asked, surfaced disclosure items 10, 11 and 12, together with a clipped axis label, annotations that overlapped plotted series, and percentile labels that were illegible where curves cross. All are fixed and were verified by rendering each figure at print size.

---

> "the sentence structures are unnecessarily complex almost throughout"

**Response.** A simplification pass has been made through the methodology and results, splitting the longest multi-clause sentences and removing the parenthetical asides that produced most of the compounding.

---

> "more and longer bearing run-to-failure datasets are needed, especially to extend the conclusions to long-life bearings… A similar effort on other bearing types may also be relevant."

**Response.** Both named explicitly in Section 8, alongside the existing power analysis, which quantifies the minimum campaign size.

---

> "Typos: None identified."

**Response.** No action required. A proofreading pass was made in any case. It found and fixed a LaTeX accent artifact and several lines where text overran its column into the neighbouring one; the rendered manuscript now has no text outside its column.

---

# Reviewer F

> "The literature review could be slightly expanded toward classical change-detection methods, where detection delay and false-alarm constraints have also been studied."

**Response.** Added to §2.2. Pairing detection delay with a false-alarm constraint is the founding formulation of sequential change detection: Lorden (1971) posed the minimax problem, and Moustakides (1986) showed that Page's CUSUM chart is exactly optimal under it. The distinction worth drawing is that this theory constrains the false-alarm rate when a detector is *designed*, whereas our gate imposes it when a detector is *scored*, against a rate measured on the data. The two can disagree on our own results: CUSUM, whose optimality theory this is, has no valid operating point on IMS at a 10% budget, because its pre-onset false-alarm rate stays between 19.0% and 19.8% across every threshold we sweep.

---

> "the main SCADA aggregation conclusion appears to rely mainly on raw lead-time differences, while the paper itself argues that lead time without a false-alarm constraint may be misleading… It would strengthen the work to also show the aggregation-versus-decimation results directly under the proposed gated metric."

**Response.** The reviewer identified a real tension between the paper's argument and its own headline analysis. A new table reports the aggregate-versus-decimate contrast under both the raw and the gated metric, per dataset. The conclusion is unchanged: no hypothesis is rejected under either.

We retain raw lead as the primary contrast and now give the reason explicitly. The gated quantity depends on the onset through the pre-onset false-alarm rate, whereas the raw-lead difference contains no onset term and is invariant to the onset definition — which Reviewer G's sensitivity check now confirms by measurement. We also report the cost: gating produces exact ties, so the number of non-zero paired differences falls from 171 to 98 and the gated test is strictly less powerful.

---

> "The conclusions about deep models should also be kept within the tested conditions, since some of the datasets provide quite limited training data for these models."

**Response.** Agreed, and now stated in the abstract, Section 6.12 and the conclusion. The scoping is quantitative: across FEMTO bearings and training fractions the runs provide between 20 and 335 normal training windows, with a median of 88 at the default split, while the models carry 2.0–5.5 × 10⁴ parameters. The comparison is made where the deep models are structurally disadvantaged, and the text says so.

---

> "It would help if the paper stated more clearly for each dataset whether aggregation is performed on the raw vibration signal, the sampled data, or the extracted features."

**Response.** Addressed by the new Section 4.8; see the corresponding response to Reviewer D.

---

> "Some of the stronger statements about 'non-destruction' could also be softened"

**Response.** Addressed by the equivalence analysis and the removal of the universal claim. The term itself now appears 8 times, down from 21.

---

> "a careful proofreading would still be useful… Some sentences are quite long and could be simplified."

**Response.** Done; see the responses to Reviewer D on sentence complexity and typos.

---

> "terms such as SCADA, SPC, BPFO (+ may be some more) should be checked and expanded when they first appear."

**Response.** Done, including the further abbreviations a full sweep identified.

---

> "there are many tables, and some of the secondary results could be moved to supplementary material"

**Response.** Rather than move them, we consolidated. Four ablation tables reporting the same finding are now one; the three per-dataset sign-test tables, the equivalence table and the Holm table are one table grouped by dataset (Table 5); the four conformal calibration figures are one four-panel figure. Tables fall from 29 to 15 and figures from 11 to 6, with no result removed.

---

> "some tables are quite dense and would benefit from slightly improved formatting or simplification."

**Response.** The Holm correction table, the densest, was a 45-row list. Its raw p-values are now a column of Table 5 (Table 6 for IMS), eleven detectors by four datasets, and its adjusted-p and rejection columns, identical in every row, are replaced by a single sentence in the Table 5 caption. The rendered manuscript now has no table extending beyond its column.

---

# Reviewer G

> "Provide a brief theoretical or simulation analysis of the onset estimator's properties (bias/variance under abrupt vs. gradual degradation)."

**Response.** Added to Section 4.3, after Algorithm 1, as an analytic result checked by simulation. The terminal-excursion rule fires when the health indicator clears the band μ_b + kσ_b, so for a degradation ramp of slope m the estimator is late by approximately kσ_b/m, with a standard deviation of order σ_b/m. Both scale inversely with the ramp slope: the estimator is near-unbiased and stable under abrupt degradation, and systematically late and more variable under gradual degradation.

One detail was corrected during this work. The persistence requirement does not add to the delay, because the rule returns the start of the last sustained excursion rather than the point at which persistence is satisfied. Simulation confirms the delay is the same at persistence 5 and 20 for every ramp slope.

The result explains a pattern already present in the submitted manuscript: the abrupt first IMS test agrees across all three health indicators, while the slow-degrading second and third tests move substantially.

---

> "Add a signal-theoretic argument (e.g., sufficient statistics, aliasing) grounding why bin-averaging preserves prognostic information for the studied signal class."

**Response.** Added as Section 7.3. Bin-averaging by a factor f is a moving-average filter followed by downsampling — an anti-alias filter, then decimation — whereas plain decimation omits the filter. The degradation content lies far below the post-coarsening Nyquist rate even at the coarsest factor, while measurement noise is broadband, so decimation folds noise into the band occupied by the trend and aggregation attenuates it first. The prediction concerns the noise floor rather than any particular detector, and Appendix D.1 tests it: the advantage rises monotonically with injected noise, from −0.35 h at the native level to +6.60 h at 10 dB, and is recovered by an ordinary moving-average or Kalman filter on the decimated stream.

The section adds a structural point: the window mean and linear-trend slope are linear functionals of the underlying series, so block-averaging commutes with them up to the weighting of the window overlap, whereas the standard deviation, maximum and cross-channel coherence are not linear. Aggregation therefore preserves amplitude and trend descriptors more faithfully than dispersion and extremal ones.

We stop short of a conservation result and say so. The detectors monitor a scalar collapse of the full feature vector rather than any individual statistic, and the window overlap makes even the linear summaries a non-uniformly weighted average. We also note that Appendix D.1 coarsens at the snapshot level while the IMS sweep coarsens at the feature level, so the mechanism is corroborated on a related but not identical operation.

---

> "Include a sensitivity check showing that the aggregate-vs-decimate difference is stable under a disjoint onset indicator (e.g., PCA-first-component), or bound the claim if it is not."

**Response.** Added. The full benchmark was re-run under two alternative onset indicators — the first principal component and a kurtosis-only indicator — both disjoint from the amplitude basis of the magnitude detectors.

The raw-lead differences are exactly invariant, with maximum absolute deviation 0.000 h across 99 dataset × detector × indicator cells. This confirms by measurement what the manuscript previously argued by construction.

The gated differences do move, and we bound the claim accordingly. The three multi-bearing campaigns stay within ±1 h under every indicator, while on IMS the positive gated medians of CUSUM, EWMA and Hotelling T² fall to zero under both alternatives and Isolation Forest's under the kurtosis-only indicator (under the first principal component it is unchanged, at +3.43 h). The manuscript therefore claims only that raw-lead non-destruction does not depend on the onset definition; it claims no gated directional pattern on IMS, which does depend on it.

---

> "Explicitly scope the deep-model 'no crossover' claim to short-lived bearings in the abstract and conclusion."

**Response.** Done in both, and the claim is now tested rather than asserted: disclosure item 3 describes a defect that had prevented the training fraction from varying at all. With the sweep corrected, no crossover appears anywhere in [0.20, 0.60]; the best deep-model valid-alarm fraction is 0.333 against a control-chart baseline of 0.625 at the same training fraction.

The corrected sweep also surfaced something the frozen split had hidden: the control charts do best at the smallest training fraction, because on these short bearings the test window shrinks as the training fraction grows. That is now reported.

---

> "Add a concise architecture/hyper-parameter table for the deep reconstruction models… so the paper is fully self-contained without requiring inspection of the code."

**Response.** Added to Appendix A for LSTM-AE, TCN-AE, Transformer-AD and Deep SVDD: layer structure, widths, kernel sizes and dilations, attention heads, sequence length, optimiser, learning rate, batch size, epochs, dropout, loss, seed and measured parameter counts (54,657, 29,681, 20,305 and 1,824). Values are transcribed from the released configuration and model constructors.

Two footnotes record findings from the transcription: no model uses early stopping — each runs its full epoch budget — and the LSTM-AE dropout setting has no effect, since recurrent dropout applies only between stacked layers and the encoder and decoder each have one layer.

---

> "expand the related-work discussion to better position the gated metric against other recent time-aware or uncertainty-aware evaluation approaches."

**Response.** Added to §2.1. Tatbul et al. (2018) generalise precision and recall from points to ranges with a tunable positional bias, so early detection within an anomalous interval can be rewarded, and Wu and Keogh (2023) argue that widely used benchmarks admit trivial solutions and overstate progress. The paragraph states where our metric differs: rather than a score on a bounded scale, the gated lead time is a physical quantity — hours of warning — that a maintenance planner can act on, and the false-alarm constraint enters as a gate on validity rather than as a weight inside the score.

---

> "Clarify in the Data Availability statement exactly which derived ONGC artifacts are released for reproducibility."

**Response.** The statement now names the released ONGC artifacts file by file, and states what is withheld: raw waveforms, channel-level measurements and asset identifiers. The released health indicator is a single baseline-standardised scalar aggregated over all four channels, so no per-channel value or absolute vibration amplitude can be recovered from it.

Acting on this comment uncovered disclosure item 13. The guarantee is now a test rather than a claim: a released test recomputes the published ONGC degradation onset from the released files alone, and the exporter refuses to write output if the onset does not reproduce. This was verified from a clean clone of the public repository.

---

> "The main shortfalls are the limited external anchoring against the existing RUL literature and the restricted scope to steady-condition bearings."

**Response.** Both are accepted as limitations and now stated as such. Section 8 has a paragraph acknowledging that the gated metric is not benchmarked against the RUL-estimation literature. Section 2.2 explains why published RUL scores on the deliberately truncated test copies of FEMTO and XJTU-SY are not directly comparable to gated lead time on complete run-to-failure trajectories, and identifies re-evaluating published architectures under the gated metric as future work requiring their original code. The restriction to approximately steady operating conditions is stated in Section 1 and in Section 8.

---

> "The paper scores highly on clarity of presentation… No substantive corrections are required on these points."

**Response.** I am grateful for the assessment. Reviewer D's clarity score was lower, and I have acted on Reviewer D's specific points — abbreviations, figure defects and sentence complexity — as improvements in their own right.

---

## Closing

Every point raised by the three reviewers has been addressed. Two original choices are retained — raw lead as the primary aggregate-versus-decimate contrast, and the corrected IMS test-3 label as the primary analysis — and each is now argued explicitly in the manuscript, with the alternative reported in full beside it.

The revision also corrects defects that no reviewer identified. I report them in full because the standard the reviewers applied — that the paper claim exactly what the evidence supports — does not depend on which defects happened to be visible from outside.

The analyses are reproducible from the public repository at tag v1.3.0, with a pinned environment and a 181-test suite that includes a script re-deriving 1040 printed values from the released result files and an assertion that the ONGC case study reproduces from released files alone.
