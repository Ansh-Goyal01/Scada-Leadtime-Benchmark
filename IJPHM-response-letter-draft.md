# Response to Reviewers — Draft Scaffold

*Manuscript: "A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing Anomaly Detection — and What It Reveals About SCADA-Rate Logging"*
*International Journal of Prognostics and Health Management*

---

## How to use this file

Every reviewer point gets its own numbered entry with three parts: the reviewer's comment (quoted verbatim), the response, and the specific change with section/table/page numbers **of the revised manuscript**. Fill the `⟦…⟧` placeholders only after the corresponding revision is actually made — never in advance.

**Two rules that decide how this reads.**

1. **Never claim a change you have not made.** Reviewer D cross-checked your claims against your own tables and found two mismatches; that reviewer will cross-check this letter against the revised manuscript. One overstated "we have added" undoes the goodwill from forty correct ones.
2. **Where you decline, say so plainly and give the reason.** Reviewers respect a defended decision far more than a silent omission. You have at least two legitimate declines available (see 3.2 and the raw-lead defence in 1.2).

Keep the letter to the point. No thanking beyond one line, no restating the paper's contributions.

---

## Opening

> We thank the three reviewers for reviews that were unusually specific and, in several cases, caught genuine inconsistencies between what the paper did and what it claimed. The revision addresses every point raised. Four changes are substantive enough to flag at the outset:
>
> 1. **Section 4.7 has been rewritten** to state, per dataset, the level at which the aggregate and decimate operations are applied, and the abstract, introduction, and conclusion have been aligned with it (Reviewer D, Reviewer F).
> 2. **The headline claim has been rewritten** from a null-acceptance statement to a bounded equivalence statement, now supported by an explicit equivalence analysis at a pre-specified operational margin (Reviewer D).
> 3. **The claim that "decimation is never better" has been removed** throughout, because it was never supported. It is replaced by a bound on the operational margin: no cell shows decimation superior beyond ±1 h. Separately, the Table 8 counterexample the reviewer cited turned out to be an artifact of a resampling defect we found and fixed (Reviewer D; see D19).
> 4. **The aggregate-versus-decimate comparison is now also reported under the gated metric**, not only on raw lead time (Reviewer F).
>
> The manuscript is ⟦N⟧ pages shorter. All new analyses are in the released repository and a new Zenodo version has been minted: ⟦DOI⟧. Changes are marked in the revised manuscript.

---

## Reviewer D — Major revisions

### D1. False-alarm cost in the wider anomaly-detection literature
> "It would have been good to also at least slightly touch on the extensive false positive related costs discussed in other fields including general anomaly detection publications. The Numenta Anomaly Benchmark (Lavin & Ahmad 2015) comes to mind."

**Response.** Added. ⟦Describe the added paragraph, and state specifically what the gate shares with NAB — an asymmetric cost profile penalising false positives and rewarding early detection — and how it differs: NAB folds cost into a weighted score, whereas our gate makes the false-alarm constraint a validity condition rather than a term traded off against lead time.⟧
**Change.** §2.1, ⟦paragraph⟧; references added: ⟦…⟧.

### D2. Small sample sizes; circularity in the 3σ recommendation
> "the number and size of the datasets tested is small… the 3σ deployment recommendation inherits an acknowledged circularity between the onset definition and the detectors' features."

**Response.** Both stand. We have strengthened the treatment rather than restated the acknowledgement: §8 now scopes the conclusion by bearing lifetime (see D21), and the circularity is now probed empirically — the aggregate-versus-decimate contrast is recomputed under two onset indicators disjoint from the amplitude basis (Reviewer G, point 3).
**Change.** §8 ⟦…⟧; new Table ⟦…⟧.

### D6. Deep reconstruction models omitted from the threshold sweep
> "the deep reconstruction models are stated to have no valid operating point 'regardless of threshold' (Section 6.1) but are omitted from the threshold sweep in Table 16."

**Response.** Correct, and the claim was unsupported as written. We have run the three deep reconstruction models through the same threshold sweep and added them to Table 16 ⟦R-3⟧, so the statement in §6.1 is now backed by the evidence rather than asserted.
**Change.** Table 16 (three rows added); §6.1 ⟦…⟧.

### D7. One-class SVM described as evaluated but never reported
> "one-class SVM is described as evaluated (Section 4.5) but appears in no results table. It should be reported or the mention removed."

**Response.** One-class SVM is now reported rather than merely mentioned; it joins Deep SVDD in the "additionally evaluated" tier, which makes §4.5's existing claim true rather than requiring its removal. Adding one-class SVM widens the correction family from N = 40 to N = 44 and raises the uncorrected family-wise error rate from approximately 0.87 to approximately 0.90. No hypothesis is rejected at either family size; the smallest raw p-value remains 0.031 (Isolation Forest on FEMTO) with a Holm-adjusted p of 1.00. The reviewer's requested addition therefore widens the evidence base without altering any conclusion.
**Change.** §4.5; Table 11 recomputed at N = 44; §6.4 family size and FWER; result tables gain the one-class SVM row.

### D9. Coarsening described inconsistently *(shared with F4)*
> "Section 4.7 describes the coarsening operation inconsistently… The authors should state, for each dataset, at which level the aggregate and decimate operations are applied, and align the framing in the introduction and abstract with it."

**Response.** The reviewer is right, and the two descriptions in §4.7 did correspond to different operations. New §4.7.1 states, per dataset, the level at which each operation is applied ⟦R-1⟧, and the contradictory sentence has been removed. The abstract, introduction, and conclusion now use one consistent framing.
> ⚠️ **If the answer is that coarsening is applied at the feature level, add this sentence — do not omit it:** "We have also narrowed the framing accordingly: the operation tested is historian-style aggregation of the summary series, not bin-averaging of the raw waveform, and the abstract and introduction no longer describe the result as a refutation of the raw-signal-averaging folklore."
**Change.** New §4.7.1 and Table ⟦…⟧; abstract; §1 ⟦…⟧; §9.

### D10. Sentence complexity *(shared with F6)*
> "the sentence structures are unnecessarily complex almost throughout, which makes the methodology harder to follow than it needs to be."

**Response.** The manuscript has been through a full simplification pass. Em-dash constructions, which were the main source of the compounding, are reduced from 180 to ⟦N⟧; long multi-clause sentences in §4.5, §4.7, §6.2, §6.6, and §6.13 have been split.
**Change.** Throughout.

### D13. Abbreviations *(shared with F7)*
> "SCADA is never expanded… the bearing characteristic frequencies BPFO, BPFI, BSF, and FTF are named but never expanded."

**Response.** Both corrected. We also swept the manuscript for other unexpanded abbreviations and expanded SPC, ROC–AUC, CUSUM, LSTM, SVDD, PCA, FFT, and ONGC at first use.
**Change.** §1; §4.2; abstract.

### D14 / D15. Tables 21 and 23
> "Table 21 may be unnecessary: its results are true by construction and already described in the text. Table 23 duplicates the Figure 10 results."

**Response.** Both removed. The latch-on and oracle results are now stated in a single sentence in §6.12; Figure 10 carries the training-fraction result alone. All cross-references and table numbering have been updated.
**Change.** Tables 21 and 23 deleted; §6.12 ⟦…⟧; §6.13 ⟦…⟧.

### D16. Figure 10 in-plot title
> "The Figure 10 title is misleading, since the deep models never match the SPC charts in the tested range; the caption states this correctly, so the in-plot title contradicts its own caption and should be removed."

**Response.** Removed. The figure now carries no in-plot title and the LaTeX caption is the sole description.
**Change.** Figure 10.

### D17. Malformed figure labels
> "the x and y labels in Figure 2 are malformed, and the Figure 10 legend is malformed. The authors should regenerate both figures and check the remaining figures for similar issues."

**Response.** Both figures have been regenerated. The cause was a character-encoding fault in the plotting script that corrupted `Δ`, `−`, `σ`, `≈`, and `²` in label strings; these are now rendered through matplotlib mathtext, which removes the encoding dependency. We also corrected a doubled parenthesis in the Figure 2 legend. As requested, we checked all eleven figures for the same fault; Figures 2 and 10 were the only ones affected.
**Change.** Figures 2 and 10 regenerated.

### D18. Null-acceptance without an equivalence test
> "the headline 'does not cost warning time' is a null-acceptance claim made without an equivalence test; it should be reworded as a bounded no-detectable-difference statement or supported formally."

**Response.** We have done both. The claim is reworded as a bounded statement throughout, and it is now supported by an equivalence analysis at a pre-specified operational margin of δ = 1 h, chosen because a maintenance planner cannot act on sub-hour differences in warning time. On the three multi-bearing datasets the run-level difference is equivalent to zero within that margin ⟦R-2⟧. On IMS we state explicitly that equivalence cannot be established: the exact one-sided sign test at n = 3 floors at p = 0.125, so no margin can reach α = 0.05, exactly as significance cannot be reached in the other direction.
**Change.** Abstract; §4.8 ⟦…⟧; new Table ⟦…⟧; §7; §9.

### D19. "Decimation is never better" contradicted by Table 8
> "the introduction's 'decimation is never better' is contradicted by the paper's own Table 8 (Isolation Forest on FEMTO, negative in six of six runs - the most sign-consistent result in the study)."

**Response.** The reviewer is right, and the answer has two independent parts.

*First, the universal claim is removed because it was never supported.* "Decimation is never better" asserts an absence of negative differences, and no analysis in the paper established that. It is removed from every place it appeared: the abstract, the introduction's finding and contribution statements, the discussion, the summary of key outcomes, and the conclusion. In its place we state a bound phrased around the pre-specified ±1 h operational margin: **no dataset × detector cell shows decimation superior beyond ±1 h** ⟦R-2, R-19⟧. We deliberately do not claim that no cell favours decimation. In five cells the run-level 95% interval lies wholly below zero (Isolation Forest on XJTU-SY; 3σ, LSTM-AE, RMS-trend and Transformer-AD on FEMTO), and the manuscript now names them. All five lie inside the margin; the widest reaches −0.44 h (3σ on FEMTO) ⟦R-19⟧. This removal stands on its own and does not depend on the second point.

*Second, the specific counterexample the reviewer identified was an artifact of a defect in our pipeline, which we found and fixed while answering this review.* On the three datasets with sub-minute native logging (FEMTO, University of Ferrara, ONGC), the aggregation arm rounded its bin width to whole minutes with a one-minute floor, while the decimation arm kept every k-th sample. At the same nominal factor, aggregation was therefore coarser than decimation: up to 12× on Ferrara (5 s native), 6× on FEMTO and ONGC (10 s). That is exactly the confound §4.7 says the controlled sweep removes. We corrected the resampling so both arms land on the same effective interval, verified that the IMS and XJTU-SY results are unchanged to the byte (their native spacing is a whole number of minutes), and re-ran the three affected datasets. Under the corrected pipeline, Isolation Forest on FEMTO is **2 positive / 4 negative runs (median −0.07 h, p = 0.688)**, no longer sign-consistent. Its bootstrap interval now includes zero (−0.18 h, [−0.49, +0.03]). FEMTO's sign-consistent detectors are now LSTM-AE and Transformer-AD, both negative and non-significant ⟦R-19⟧. The paper's conclusions survive the correction: the Holm verdict is 0 of 44 before and after, and the ±1 h equivalence holds in all 30 multi-bearing cells before and after (33 of 33 with the one-class SVM) ⟦R-19⟧. Tables 8, 9 and 11, the ONGC table and Figure 2 were regenerated, and the full defect record (N-20) is in the repository.

We are grateful for this comment in particular: pursuing it is what exposed the defect.
**Change.** Abstract; §1 (finding, contribution 4); §6.4 and Table 8; §6.5 and Table 9; Table 11; §7 (discussion, summary); §9; Appendix D.2 table; Figure 2.

### D20. IMS test-3 relabelling
> "The IMS test-3 failure relabel is author-chosen and affects one of the three runs carrying the paper's only directional trend; results under the original label should be shown."

**Response.** Added. Appendix C now reports the full IMS sweep under both labels side by side ⟦R-4⟧. We state the consequence plainly rather than only in our own favour: ⟦under the original label, test 3 is a guaranteed miss for every detector, its aggregate−decimate difference is zero, and it is therefore excluded from the sign-test count by the rule stated in §4.8 — so IMS effectively falls to n = 2 and the exact sign test floors at p = 0.50. The direction of the trend is unchanged; the number of runs supporting it is not.⟧ We retain the corrected label as the primary analysis for the reasons given in Appendix C, but the reader can now see the alternative in full.
**Change.** Appendix C; new Table ⟦…⟧.

### D21. Scope of the non-destruction conclusion
> "the non-destruction conclusion should be scoped: the datasets providing statistical power are short-lived bearings on which the effect could never exceed minutes, while the long-runway case rests on three runs."

**Response.** This is a fair structural criticism and it is now stated as such in the paper rather than left for the reader to derive. §8 has a new paragraph making the asymmetry explicit: the datasets supplying power comprise bearings of 0.7–8.9 h total lifetime, on which an effect of the magnitude observed on IMS could not have been observed even if present, so the null on those campaigns bounds the effect at the scale of minutes; the only dataset with a runway long enough to express such an effect has n = 3. The conclusion is correspondingly scoped: non-destruction is established at short lifetimes with good power, and is consistent with — but does not establish — non-destruction at the multi-week lifetimes typical of industrial assets.
**Change.** §8 ⟦…⟧; abstract; §9.

### D22. Length and repetition
> "the paper is much longer than needed: the headline finding is restated many times, Table 21 and Table 23 can be cut, Section 7.4 duplicates Section 6's summaries."

**Response.** §7.4 has been deleted in full, Tables 21 and 23 removed, and ⟦Tables 15 and 20 moved to the appendix⟧. Occurrences of the phrase "non-destruction" are reduced from 20 to ⟦N⟧. The manuscript is ⟦N⟧ pages shorter.
**Change.** §7.4 deleted; Tables ⟦…⟧.

### D23. Self-descriptive statements
> "the self-descriptive statements ('statistically honest by construction,' 'the metric correctly refuses…') should be removed and the methods allowed to speak for themselves."

**Response.** Removed. All eighteen instances of self-characterisation, including both phrases quoted, have been deleted or rewritten to state the fact without the adjective.
**Change.** Throughout.

### D8. Future work
> "more and longer bearing run-to-failure datasets are needed, especially to extend the conclusions to long-life bearings… A similar effort on other bearing types may also be relevant."

**Response.** §8 now names both requirements explicitly alongside the existing power analysis, which quantifies the minimum campaign size (n ≈ 6 at d = 1.2 to n ≈ 17 at d = 0.7).
**Change.** §8; §9.

---

## Reviewer F — Minor revisions

### F1. Classical change-detection literature
> "The literature review could be slightly expanded toward classical change-detection methods, where detection delay and false-alarm constraints have also been studied."

**Response.** Added, and it sharpens the positioning rather than diluting it. ⟦Describe: the delay-versus-false-alarm trade-off is the founding problem of quickest change detection; the distinction is that this literature constrains the false-alarm rate when *designing* a detector, whereas the gate imposes it when *scoring* one — which is why the gate can invalidate a detector that a delay-only criterion ranks first.⟧
**Change.** §2.2 ⟦…⟧; references added ⟦…⟧.

### F2. Aggregation result should also be shown under the gated metric
> "the main SCADA aggregation conclusion appears to rely mainly on raw lead-time differences, while the paper itself argues that lead time without a false-alarm constraint may be misleading… It would strengthen the work to also show the aggregation-versus-decimation results directly under the proposed gated metric."

**Response.** Added — the reviewer identified a real tension between the paper's argument and its own headline analysis. The aggregate-versus-decimate contrast is now reported under the gated metric alongside the raw-lead contrast ⟦R-1 table⟧, together with the valid-alarm fraction under each mechanism.

We retain raw lead as the *primary* contrast, and now give the reason explicitly rather than leaving it implicit: the gated quantity depends on the onset through FAR_pre, whereas the raw-lead difference contains no onset term and is therefore invariant to the onset definition (§6.2). Reporting both makes the dependence visible. ⟦State the outcome honestly, including the power loss: gating produces many exact zeros, so the gated test has strictly less power than the raw-lead test; report the tie counts.⟧
**Change.** New §6.6a and Table ⟦…⟧; §4.8 ⟦…⟧; §7.

### F3. Scope of deep-model conclusions
> "The conclusions about deep models should also be kept within the tested conditions, since some of the datasets provide quite limited training data for these models."

**Response.** Agreed and now stated at every point the claim appears — abstract, §6.13, and §9 — scoped both to the bearing lifetimes tested (0.7–8.9 h) and to the training-fraction range evaluated (0.20–0.60). We also note explicitly that the finding is a statement about this data regime, not about the model class.
**Change.** Abstract; §6.13; §9.

### F4. Per-dataset aggregation level
> "It would help if the paper stated more clearly for each dataset whether aggregation is performed on the raw vibration signal, the sampled data, or the extracted features."

**Response.** See D9 — new §4.7.1 states this per dataset in a table.

### F5. Soften the non-destruction statements
> "Some of the stronger statements about 'non-destruction' could also be softened, since several statistical comparisons are not significant and the available sample sizes are limited."

**Response.** See D18 and D19. The claim is now bounded rather than universal, supported by an equivalence analysis, and the one contrary result is named wherever the conclusion is stated.

### F8. Move secondary tables to supplementary
> "there are many tables, and some of the secondary results could be moved to supplementary material to make the main paper more focused."

**Response.** ⟦Tables 15 and 20 have been moved to the appendix; Tables 21 and 23 removed entirely per Reviewer D.⟧ The main text now carries ⟦N⟧ tables.
**Change.** ⟦…⟧

### F9. Table density
> "some tables are quite dense and would benefit from slightly improved formatting or simplification."

**Response.** Table 11 is now grouped by dataset with rule separators, and the uniformly-"no" rejection column has been replaced by a single statement in the caption. Tables 16, 19, and 24 have been similarly grouped, and numeric columns are decimal-aligned.
**Change.** Tables 11, 16, 19, 24.

---

## Reviewer G — Minor revisions

### G1. Onset estimator properties
> "Provide a brief theoretical or simulation analysis of the onset estimator's properties (bias/variance under abrupt vs. gradual degradation)."

**Response.** Added as a new appendix subsection. We give a first-order analytic result — the terminal-excursion rule fires when the ramp clears the band kσ_b and persists for P samples, so bias ≈ kσ_b/m + PΔt and standard deviation ≈ σ_b/m in the ramp slope m — and verify it by Monte Carlo over abrupt and gradual regimes ⟦R-6⟧. Both quantities scale inversely with the ramp slope: the estimator is near-unbiased and low-variance for abrupt degradation and systematically late for gradual degradation.

This also explains a pattern already present in the results: IMS test 1 (abrupt) agrees across all three onset indicators at ~98–99% of span, while the slow-degrading tests 2 and 3 move substantially (Table 4). That behaviour is now a predicted consequence of the estimator rather than an unexplained observation.
**Change.** New Appendix ⟦…⟧; §4.3 ⟦…⟧; §8.

### G2. Signal-theoretic grounding
> "Add a signal-theoretic argument (e.g., sufficient statistics, aliasing) grounding why bin-averaging preserves prognostic information for the studied signal class."

**Response.** Added ⟦§…⟧, on two grounds. First, aggregation is exact for the second moment: the mean square over a union of disjoint bins equals the mean of the per-bin mean squares, so the aggregated amplitude series is a sufficient statistic for the block variance under a locally stationary Gaussian model, and no second-moment information is lost at any coarsening factor. This exactness does not extend to higher-order statistics, so impulsiveness features are genuinely altered while amplitude features are not. Second, bin-averaging is an anti-alias filter followed by downsampling, whereas decimation omits the filter; since the degradation content lies far below the post-coarsening Nyquist rate while measurement noise is broadband, decimation folds noise into the band occupied by the trend and aggregation attenuates it first.

Two predictions follow, both consistent with results already reported: the advantage should concentrate in amplitude- and variance-sensitive detectors and be weakest for spike-robust ones, and it should grow with the noise floor — which is what Appendix D.1's noise injection shows.
**Change.** New §⟦…⟧; §7.2 ⟦…⟧.

### G3. Sensitivity under a disjoint onset indicator
> "Include a sensitivity check showing that the aggregate-vs-decimate difference is stable under a disjoint onset indicator (e.g., PCA-first-component), or bound the claim if it is not."

**Response.** Added ⟦R-5⟧. The contrast is recomputed with onset from the first principal component and from a kurtosis-only indicator, both disjoint from the amplitude basis shared with the magnitude detectors. We report the raw-lead and gated contrasts separately and state which is invariant: the raw-lead difference contains no onset term and is invariant by construction, while the gated difference depends on the onset through FAR_pre and does move ⟦quantify⟧. Where it moves, we bound the claim accordingly.
**Change.** New Table ⟦…⟧; §6.2 ⟦…⟧; §8.

### G4. Scope the deep-model no-crossover claim
> "Explicitly scope the deep-model 'no crossover' claim to short-lived bearings in the abstract and conclusion."

**Response.** Done. The abstract, which previously did not state the claim at all, now states it in scoped form; the conclusion's crossover sentence is scoped to short-lived bearings. §6.13 and the introduction's contribution list were already scoped to the 0.20–0.60 training range and are unchanged.
**Change.** Abstract; §9.

### G5. Deep-model architecture table
> "Add a concise architecture/hyper-parameter table for the deep reconstruction models (LSTM-AE, TCN-AE, Transformer-AD) so the paper is fully self-contained without requiring inspection of the code."

**Response.** Added as Table ⟦…⟧ in Appendix A: layer counts, latent and hidden widths, kernel sizes and dilation schedule, attention heads and model dimension, sequence length, optimiser, learning rate, batch size, epochs, early-stopping rule, loss, and parameter counts, for all three reconstruction models and for Deep SVDD. All values are transcribed from the released `config.py`.
**Change.** Appendix A, Table ⟦…⟧.

### G6. Positioning against time-aware and uncertainty-aware evaluation
> "expand the related-work discussion to better position the gated metric against other recent time-aware or uncertainty-aware evaluation approaches."

**Response.** Added ⟦…⟧ at the end of §2.1, connecting the gated metric to the time-aware prognostic metrics already discussed and to uncertainty-aware evaluation, and stating what the gate adds: the false-alarm constraint enters as a validity condition on the score rather than as a separately reported quantity or a weighting term.
**Change.** §2.1 ⟦…⟧; references ⟦…⟧.

### G7. ONGC derived artifacts
> "Clarify in the Data Availability statement exactly which derived ONGC artifacts are released for reproducibility."

**Response.** The statement now enumerates the released artifacts by name ⟦R-9⟧ — the derived health-indicator series, the per-detector lead-time and pre-onset-FAR result files, the conformal calibration series behind Figure 11, and the sampling-sweep rows behind Table 29 — and states what is withheld (raw waveforms, channel-level measurements, asset identifiers). We also restate that no inferential claim depends on ONGC.
**Change.** Data and Code Availability.

### G8. External anchoring against the RUL literature; restricted scope
> "The main shortfalls are the limited external anchoring against the existing RUL literature and the restricted scope to steady-condition bearings."

**Response.** Both accepted as limitations rather than resolved, and now stated as such. §2.2 already explains why published RUL scores on the truncated FEMTO and XJTU test copies are not directly comparable to gated lead time on complete run-to-failure trajectories; we have added a sentence acknowledging that this is a limitation of the present benchmark and not only a justification, and identifying re-evaluation of published architectures under the gated metric as future work requiring their original code. The restriction to approximately steady operating conditions is stated in the scope paragraph of §1 and in §8.
**Change.** §2.2 ⟦…⟧; §8 ⟦…⟧.

---

## Closing

> We have made every change requested. The two points on which we have retained the original approach — ⟦list them, e.g. raw lead as the primary contrast, and the corrected IMS test-3 label as the primary analysis⟧ — are now argued explicitly in the manuscript, with the alternative reported in full alongside so the reader can judge.
>
> All new analyses are reproducible from the released repository; a new archived version has been minted at ⟦DOI⟧, and every number in the revised manuscript is generated from the released result files.