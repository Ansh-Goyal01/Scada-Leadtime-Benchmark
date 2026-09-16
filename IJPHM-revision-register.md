# IJPHM Revision Register — *A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric…*

**Editor decision: accepted for publication contingent on major revisions.** Reviewer D — major revisions, another review cycle. Reviewers F and G — minor revisions, accept once made.

**Deadline: 3 October 2026** (4 weeks from the 5 September 2026 decision letter).

**Two files must be uploaded**, per the editor: the revised manuscript, and a separate *"Response to Review"* document as an additional file. Do **not** start a new submission — upload into the existing one.

**53 items total:** 41 from the three reviewers (Parts 0-5 below) plus **12** defects found during execution — 9 in Phase 0, and N-10/N-11/N-12 in Phase 0.5(A) (see `IJPHM-PROGRESS.md` §7; N-12 is High).

**Status legend**
- `TEXT` — pure wording; replacement drafted here; no numbers needed.
- `RUN` — needs a number out of your pipeline. Placeholder `⟦R-n⟧` marks where it goes. **Never fill a placeholder by estimation.**
- `DECIDE` — a judgement call only you can make; blocks other items.

**Placeholder rule.** Every `⟦R-n⟧` must be replaced by a value emitted by a released script and committed to the repo before submission. A reviewer with your Zenodo snapshot can check any of them.

---

## PART 0 — Resolve this first. Everything downstream depends on it.

### 0.1 `DECIDE` — At what level is coarsening applied? (D9, F4)

This is the single most important item in the review. Reviewer D:

> "Section 4.7 describes the coarsening operation inconsistently: 'before feature extraction' in one sentence and 'resamples at the feature level' two sentences later. These are different experiments, and an independent implementer cannot tell which one to build."

**Verified in the PDF.** Section 4.7 contains both, ~4 lines apart:
- "We coarsen the time grid by a factor f ∈ {1, 2, 5, 10, 20} **before feature extraction** under two mechanisms:"
- "Our controlled sweep resamples **at the feature level** so that window content and alarm persistence are held constant."

Section 3 adds a third data point: for IMS, "Because the waveforms are raw, the aggregate/decimate sweep can be applied faithfully **at the signal level**."

**Why this is load-bearing and not cosmetic.** D's sharpest sentence in the overall evaluation:

> "the folklore the paper claims to refute concerns raw-signal averaging."

If coarsening happens on the *feature* series, then bin-averaging RMS values is not the same operation as bin-averaging the waveform, and the paper does not refute the folklore as the abstract and introduction state it. Your claim would narrow to: *historian-rate aggregation of summary statistics does not destroy lead time* — still publishable and still useful, but a different claim.

**Action:** open the sweep code and determine, **per dataset**, which of these three is actually implemented:
- (a) bin-average / decimate the **raw waveform**, then extract features;
- (b) bin-average / decimate the **per-snapshot feature series** (RMS, kurtosis, … one value per snapshot);
- (c) bin-average / decimate the **windowed feature vectors** after rolling-window summarisation.

Most likely answer given the dataset descriptions: **(a) or (b) on IMS** (raw waveforms available) and **(b) or (c) on XJTU/FEMTO/Ferrara/ONGC** (snapshot or historian data only). If so, that per-dataset split *is* the answer both reviewers asked for, and it is a perfectly respectable one — you just have to say it.

**Deliverable:** a new short subsection **4.7.1 "At what level coarsening is applied"** with a table:

| Dataset | Native record | `aggregate` applied to | `decimate` applied to |
|---|---|---|---|
| IMS | 20.48 kHz raw waveform | ⟦R-1⟧ | ⟦R-1⟧ |
| XJTU-SY | 1.28 s snapshots @ 1/min | ⟦R-1⟧ | ⟦R-1⟧ |
| FEMTO | 0.1 s snapshots @ 1/10 s | ⟦R-1⟧ | ⟦R-1⟧ |
| Ferrara | 5 s snapshots, contiguous | ⟦R-1⟧ | ⟦R-1⟧ |
| ONGC | 10 s historian scalars | ⟦R-1⟧ | ⟦R-1⟧ |

Then **delete** the contradicting phrase in §4.7 (keep one description only) and **align four places**: abstract, introduction "Method" paragraph, §4.7, conclusion.

> **Blocks:** items 0.2, 2.1, 3.2, and the theory paragraph in 3.2. Do this before writing anything else.

### 0.2 `DECIDE` — Does §6.1's "regardless of threshold" survive? (D6)

> "the deep reconstruction models are stated to have no valid operating point 'regardless of threshold' (Section 6.1) but are omitted from the threshold sweep in Table 16. This evidence should be shown or the claim softened."

**Verified.** §6.1 reads: "their pre-onset FAR ranges from 48% on test 3 to 100% on test 1, far above the τ = 10% budget **regardless of threshold**." Table 16's rows are: 3σ, EWMA, CUSUM, Hotelling T², Iso. Forest, Deep SVDD, RMS-trend. The three deep AEs are absent.

Two options, in order of preference:
1. **Run it** — add LSTM-AE, TCN-AE, Transformer-AD rows to Table 16 at the 95th/99th/99.5th percentiles (item 1.3). This converts an unsupported universal into evidence and is cheap.
2. Soften to: "at every threshold percentile evaluated (Table 16)". Only if (1) is impossible.

Take option 1. It is a stronger paper and it directly answers a major-revision reviewer.

---

## PART 1 — Analyses requiring a pipeline run

Seven runs. All use existing data; none needs new datasets. Commit each script and its output table to the repo before resubmission.

### 1.1 `RUN` — Aggregate-vs-decimate under the **gated** metric (F2) — *highest value*

Reviewer F raised this twice, in two separate sections:

> "the main SCADA aggregation conclusion appears to rely mainly on raw lead-time differences, while the paper itself argues that lead time without a false-alarm constraint may be misleading… It would strengthen the work to also show the aggregation-versus-decimation results directly under the proposed gated metric."

This is the most consequential *scientific* gap in the review, and it is embarrassing if left unanswered: your entire thesis is that ungated lead time misleads, and your headline result is computed on ungated lead time. §6.2 defends this ("computed on raw lead time … which contains no onset term, so non-destruction is invariant to the onset definition by construction") — that defence is *correct but incomplete*. Keep it, and add the gated result alongside.

**Spec.** Recompute the run-level `aggregate − decimate` contrast on the gated lead `L` (Eq. 5), i.e. `L = 0` wherever `FAR_pre > τ = 0.10`. Emit, per dataset × detector:

- median Δ (h), `n₊ / n₋`, **tie count** (gating creates many exact zeros), exact two-sided sign test p, Holm-adjusted p across the same N = 40 family.
- A companion table: **valid-alarm fraction under aggregate vs. decimate** — gating can flip validity even where raw lead is unchanged, and this is the interesting quantity.

**Expected outcome to prepare for:** far more ties, so lower power, so the gated result will likely be "no detectable difference, with even less power than the raw-lead analysis." That is a fine result. Report it, note the power loss explicitly, and keep raw lead as the primary contrast *with a stated reason* (it is onset-independent, per §6.2) rather than by silence.

New table → **§6.6a**, referenced from the abstract and §7.

### 1.2 `RUN` — Equivalence bound to replace the null-acceptance claim (D18, F5)

> "the headline 'does not cost warning time' is a null-acceptance claim made without an equivalence test; it should be reworded as a bounded no-detectable-difference statement or supported formally."

Do both — the bound is cheap and it is far stronger than rewording alone.

**Spec.**
1. Pre-specify an equivalence margin **δ** and justify it operationally, not statistically. Suggested: **δ = 1 h**, on the grounds that a maintenance planner cannot act on sub-hour differences in warning time (mobilising a crew, ordering parts). State δ *before* reporting results and say it was chosen on operational grounds.
2. **Lead with this.** Per dataset × detector on the run-level differences, report the **two-sided 95% bootstrap CI** (you already bootstrap runs, B=2000, seed 42 — reuse it). Equivalence is established where the CI lies entirely inside (−δ, +δ). The bootstrap is the primary instrument; TOST is supporting evidence where the sample supports it.
3. Formal TOST via two one-sided exact sign tests — **only where the non-zero count supports it.**

   > ⚠️ **CORRECTED (session 2). The earlier arithmetic here was wrong** and is superseded. It read the floor as `0.5^n` with *n = bearing count* (n=10 XJTU, n=6 FEMTO/Ferrara, n=3 IMS), concluding TOST was infeasible on IMS alone.
   >
   > **The sign test excludes zero-difference runs** (the paper's own rule, §4.8). So the minimum attainable one-sided p is **`0.5^(n₊+n₋)` per detector**, not `0.5^(bearing count)`. Since TOST requires *both* one-sided tests to reject at α = 0.05, it is feasible only where **n₊ + n₋ ≥ 5**.
   >
   > **Worked example, XJTU** (counts read from Table `tab:xjtu`, `scada_ijphm.tex:406-412`):
   >
   > | Detector | n₊/n₋ | n₊+n₋ | floor `0.5^n` | feasible at α=0.05 |
   > |---|---|---:|---:|---|
   > | 3σ | 3/1 | 4 | 0.0625 | ✗ |
   > | EWMA | 2/2 | 4 | 0.0625 | ✗ |
   > | CUSUM | 1/2 | 3 | 0.125 | ✗ |
   > | Hotelling T² | 2/0 | 2 | 0.25 | ✗ |
   > | Iso. Forest | 2/7 | 9 | 0.00195 | ✓ |
   > | Deep SVDD | 3/2 | 5 | 0.03125 | ✓ |
   > | RMS-trend | 2/2 | 4 | 0.0625 | ✗ |
   >
   > So on XJTU — the dataset previously assumed to be comfortably powered at "n=10" — **TOST is infeasible for five of seven detectors.** The problem is far broader than IMS.
   >
   > **Compute the FEMTO and Ferrara floors from the run-level result files during this item.** Do **not** infer them from the p-values in Table `tab:holm`; that is exactly the estimation rule 1 forbids.

   Report the per-detector non-zero count beside every TOST result so the floor is visible, and state plainly where equivalence could not be tested rather than reporting a non-rejection as if it were a null finding.

**Resulting claim shape (replaces "does not cost")** — *rewritten in session 2; the previous version presumed TOST would succeed on all three multi-bearing datasets, which the corrected floor does not support:*

> "We report bootstrap confidence intervals on the run-level difference for every dataset × detector (⟦R-2⟧). Where the interval lies entirely inside ±1 h we describe the difference as equivalent to zero at that margin. Formal TOST is reported only for the detectors whose non-zero run count reaches n₊+n₋ ≥ 5 (⟦R-2⟧); for the remainder — including most XJTU detectors and all of IMS — the exact test cannot reach α = 0.05 at any margin, and we report the interval alone rather than a non-rejection."

> ⚠️ **Item 2.1's drafted abstract text inherits this.** Its clause "on the three multi-bearing campaigns the run-level difference is equivalent to zero within a ±1 h operational margin" presumes an equivalence result that may not survive. **Revisit 2.1 once the CIs are computed** — do not paste it as drafted.

### 1.3 `RUN` — Deep AE rows in the threshold sweep (D6)

Add LSTM-AE, TCN-AE, Transformer-AD to Table 16 at the 95th/99th/99.5th percentiles (lead + pre-onset FAR, dagger where FAR > τ). Then §6.1's "regardless of threshold" becomes supported. → `⟦R-3⟧`

### 1.4 `RUN` — IMS test-3 under the **original** failure label (D20)

> "The IMS test-3 failure relabel is author-chosen and affects one of the three runs carrying the paper's only directional trend; results under the original label should be shown."

**Spec.** Rerun the IMS sweep with the original 2004-04-08 label. Report in Appendix C: per-run aggregate−decimate differences and the sign test for all ten detectors under both labels, side by side.

**Anticipate the result and pre-write the honest reading.** Under the old label, test 3 is a guaranteed miss for every detector (`L = 0`), so its aggregate−decimate difference is 0, it drops out of the sign-test count (your own rule in §4.8 excludes zero-difference runs), and **IMS effectively falls to n = 2**. The exact sign test at n = 2 floors at p = 0.50. So the correct statement becomes: *the direction of the IMS trend is unchanged under the original label, but the run count supporting it drops from 3 to 2.* That is a weaker but truthful position, and stating it yourself is far better than having a second-round reviewer derive it. → `⟦R-4⟧`

Also strengthen the Appendix C argument with the one fact that is already in your favour and currently understated: the relabel makes the run **harder**, not easier, and the contrast is computed *within* each run so the label cannot inflate it. That is already there — keep it, but lead with the side-by-side table.

### 1.5 `RUN` — Aggregate-vs-decimate under a disjoint onset indicator (G3)

> "Include a sensitivity check showing that the aggregate-vs-decimate difference is stable under a disjoint onset indicator (e.g., PCA-first-component), or bound the claim if it is not."

You have half of this: **Table 4** already reports onset *position* under `rms_kurt`, `kurt_only`, `pca1`. What is missing is the *contrast* recomputed under each.

**Spec.** Recompute the run-level aggregate−decimate difference — **both raw and gated** (couples to 1.1) — with onset from `pca1` and from `kurt_only`. Raw-lead differences should be exactly invariant (no onset term). The **gated** differences will move, because validity depends on `FAR_pre`, which depends on the onset. Report both and say precisely which is invariant and which is not. → `⟦R-5⟧`

This item and 1.1 are the same run. Do them together.

### 1.6 `RUN` — Onset estimator bias and variance (G1)

> "Provide a brief theoretical or simulation analysis of the onset estimator's properties (bias/variance under abrupt vs. gradual degradation)."

**Spec — Monte Carlo, no real data needed.** Synthesise `h(t) = μ_b + σ_b·ε(t) + m·max(0, t − t_o*)` with known true onset `t_o*`; sweep ramp slope `m` (abrupt → gradual) and noise `σ_b`; 1000 replicates per cell; run Algorithm 1 unchanged; report bias `E[t̂_o − t_o*]` and SD.

**First-order prediction to check your simulation against** (state it in the paper as the analytic result, verified by simulation):

> The terminal-excursion rule fires when the ramp clears the band `β = μ_b + kσ_b` and persists for `P` samples, so
> **bias ≈ kσ_b/m + P·Δt** and **SD ≈ σ_b/m**.

Both are **inversely proportional to the ramp slope**. So: near-zero bias and near-zero variance for abrupt degradation (m → ∞, bias → P·Δt = the persistence delay alone); systematically **late** and more variable for gradual degradation. This explains, from first principles, a pattern already in your results — IMS test 1 (abrupt) agrees across all three onset definitions at ~98–99% of span (Table 4), while the slow-degrading tests 2 and 3 move a lot. Presenting that as a *predicted* consequence rather than an anomaly is a substantial strengthening. → `⟦R-6⟧`

### 1.7 `RUN` or `TEXT` — One-class SVM (D7)

> "one-class SVM is described as evaluated (Section 4.5) but appears in no results table. It should be reported or the mention removed."

**Verified.** Two mentions: §2.2 (related work, fine — it is a citation) and §4.5: "We also evaluate Deep SVDD … **and one-class SVM** (Schölkopf et al., 2001)." No OC-SVM row exists in any table.

**Check the repo first.** If the released code produces OC-SVM results, add the rows everywhere Deep SVDD appears (Tables 2, 7, 8, 9, 11, 14, 16, 22) and note the family size changes from N = 40 to N = 44 with Holm recomputed. If it does not, **delete the §4.5 clause** — leave the §2.2 citation. Do not claim an evaluation that is not in the snapshot; that is exactly the class of mismatch this reviewer is checking for.

Simplest safe path: delete, unless the numbers already exist. → `⟦R-7⟧`

---

## PART 2 — Claim corrections (text only, drafted)

### 2.1 `TEXT` — "decimation is never better" contradicts your own Table 8 (D19)

> ⚠️ **PARTLY STALE — decision D-2 (session 3). The item stands; one drafted sentence does not.**
>
> The drafted **abstract** replacement says *"we detect **no aggregation penalty on any dataset**, and on the three multi-bearing campaigns the run-level difference is equivalent to zero…"*. Under the invariant re-baseline that clause is **false on IMS**: 3σ (−1.0 h on 3rd_test), EWMA (−3.9 h on 1st_test) and Isolation Forest (−0.7 h on 1st_test) each have a run where aggregation yields *less* lead than decimation. Replace with a per-run-honest formulation, e.g. *"no dataset shows a median aggregation penalty, though individual IMS runs go both ways."*
>
> The rhetorical frame **"One detector runs the other way — Isolation Forest on FEMTO"** now understates the picture. FEMTO's IsoForest is still the only *sign-consistent* counter-result (median −0.14 h, 0/6, raw p = 0.031) and remains the strongest single counter-evidence, so the item's core argument is intact — but IMS is no longer uniformly positive, and a reviewer reading the new Table 10 will find three "no" entries in the S-c. column. State it rather than let them find it.
>
> **NOT stale:** the seven occurrence locations, the global replacement rule, and the FEMTO numbers — FEMTO was never on the legacy path. The ⟦R-2⟧ margin placeholder is unaffected.


> "the introduction's 'decimation is never better' is contradicted by the paper's own Table 8 (Isolation Forest on FEMTO, negative in six of six runs — the most sign-consistent result in the study)."

**Verified — and it is worse than E states, because the universal appears seven times in three different forms.** Exact locations found in the PDF:

| # | Phrase | Location |
|---|---|---|
| 1 | "while decimation is never better; nothing survives Holm correction" | Intro, Contribution 4 |
| 2 | "non-destruction—decimation is never better, and averaging is at worst neutral" | Intro, "Finding" paragraph |
| 3 | "while decimation is never better" | Conclusion |
| 4 | "SCADA bin-averaging never costs lead time relative to decimation" | §7.4 (1) |
| 5 | "coarse aggregation never costs warning time" | §7.2 |
| 6 | "SCADA-rate aggregation does not cost bearing-fault warning time" | **Abstract** |
| 7 | "dropping a fifth of the historian's records does not cost the control charts their warning time" | §6.2, missing-data |

Items 1–6 are the contradiction. (#7 is a different claim about gaps — leave it, it is defensible.)

**Verified counter-evidence in your own Table 8:** Isolation Forest on FEMTO — median Δ = **−0.14 h**, `n₊/n₋ = 0/6`, sign-consistent **yes**, raw p = **0.031** (the smallest raw p in the entire study). Your §6.4 text even calls this out — "the one detector that is sign-consistent on FEMTO, Isolation Forest, trends negative" — so the paper contradicts itself between §6.4 and the introduction. E found it. Fix all six.

**Global replacement rule:** delete every universal quantifier ("never", "every", "all", "does not cost") from the headline and replace with the bounded statement + the named exception.

**Drafted replacements:**

*Abstract (#6):*
> "The defensible cross-dataset conclusion is bounded rather than universal: we detect no aggregation penalty on any dataset, and on the three multi-bearing campaigns the run-level difference is equivalent to zero within a ±1 h operational margin (⟦R-2⟧). One detector runs the other way — Isolation Forest on FEMTO trends negative in 6 of 6 runs (median −0.14 h, raw p = 0.031) — so we do not claim that decimation is never preferable; that difference does not survive Holm correction across the N = 40 family."

*Intro, Contribution 4 (#1) and Finding (#2):*
> "…SCADA-rate aggregation does not destroy lead time. We stop short of the stronger claim that decimation is never better: on FEMTO, Isolation Forest is sign-consistently negative across all six runs (Table 8, median −0.14 h), the most sign-consistent single result in this study, though it does not survive multiple-comparison correction. The replicated conclusion is therefore non-destruction with a bounded residual difference, not a uniform aggregation advantage."

*§7.2 (#5) and §7.4 (#4) and Conclusion (#3):* apply the same construction. If §7.4 is cut (item 4.4), #4 disappears with it.

### 2.2 `TEXT` — Scope the non-destruction conclusion (D21, F5, G8)

> ⚠️ **STALE NUMBER + WEAKENED ARGUMENT — decision D-2 (session 3). Do not paste the drafted paragraph as written.**
>
> **1. The cited range is wrong.** The drafted §8 paragraph says *"an aggregation effect of the magnitude observed on IMS (**medians of 4.6–18.4 h**)"*. Those were the five legacy Table 10 medians (Hotelling 4.6 … 3σ 18.4). Under the invariant re-baseline the same five are 3σ **15.10**, CUSUM **4.27**, Iso. Forest **3.43**, EWMA **2.10**, Hotelling T² **1.17** — so the range becomes **1.2–15.1 h**. Source: `results/tables/ims_runlevel_test_invariant.csv`.
>
> **2. The argument itself weakens at the lower bound, and this matters.** The paragraph's force comes from the claim that an IMS-magnitude effect *"could not have been observed"* on bearings whose lifetimes are 0.7–8.9 h. At 4.6 h that was compelling. At **1.17 h (Hotelling T²)** and **2.10 h (EWMA)** it is no longer true: a 1–2 h effect is perfectly observable on a 6.8 h Ferrara or 7.8 h FEMTO bearing. **Rewrite the argument to rest on the upper end of the range, not the whole of it** — e.g. *"an effect of the size seen on 3σ (15.1 h) could not have been observed on them"* — and drop the implication that the entire IMS effect range is physically excluded on the short campaigns. Overstating this is the same species of unsupported universal that item 2.1 exists to remove, so leaving it would be self-defeating.
>
> **3. One clause gets stronger, not weaker.** *"the only dataset with a runway long enough to express such an effect, IMS, has n = 3 and cannot reach significance"* is now doubly supported: at n=3 the sign test floors at p=0.25, **and** under the invariant schema six of the ten IMS raw p-values are 1.00 because the runs are no longer sign-concordant. Cite both.
>
> **NOT stale:** the lifetime figures (XJTU 52–533 min, FEMTO 1.4–7.8 h, Ferrara 0.7–6.8 h), the structural asymmetry argument, and the future-work ask.


> "the non-destruction conclusion should be scoped: the datasets providing statistical power are short-lived bearings on which the effect could never exceed minutes, while the long-runway case rests on three runs."

This is the sharpest structural criticism in the review and it is correct. Your power comes from XJTU (52–533 min), FEMTO (1.4–7.8 h), Ferrara (0.7–6.8 h) — bearings on which a multi-hour aggregation effect is *physically impossible*, so a null there is nearly guaranteed by construction. The one dataset with a long runway (IMS) has n = 3.

**Add to §8 (Limitations), as its own paragraph, and mirror one sentence into the abstract and conclusion:**

> "A structural asymmetry limits what the cross-dataset null can establish. The three datasets that supply statistical power — XJTU-SY, FEMTO, and Ferrara — comprise bearings whose total lifetimes are 0.7–8.9 h, so an aggregation effect of the magnitude observed on IMS (medians of 4.6–18.4 h) could not have been observed on them even if it were present: the null on these campaigns bounds the effect at the scale of minutes, not at the scale of the IMS trend. Conversely, the only dataset with a runway long enough to express such an effect, IMS, has n = 3 and cannot reach significance. Our result therefore establishes non-destruction at short lifetimes with good power, and is consistent with — but does not establish — non-destruction at the multi-week lifetimes typical of industrial assets. Resolving the long-runway case requires a multi-run, long-lifetime campaign, which we identify as the key open requirement in Section 8."

This converts a weakness a reviewer would otherwise use against you into a stated scope boundary, and it sets up your future-work ask.

### 2.3 `TEXT` — Scope the deep-model "no crossover" claim (G4, F3)

> "Explicitly scope the deep-model 'no crossover' claim to short-lived bearings in the abstract and conclusion."

**Verified state:** §6.13 and Intro Contribution 5 are *already* scoped ("on short-lived bearings", "within the tested training-fraction range [0.20, 0.60]"). The **conclusion** is scoped as future work. The **abstract does not mention the claim at all**.

So G4 needs less than it appears. Two small edits:
- **Abstract:** add one sentence, already scoped: "On the short-lived bearings tested (0.7–8.9 h), deep reconstruction models do not overtake statistical process control charts at any training fraction in [0.20, 0.60]; whether a crossover exists on long-runway assets is left open."
- **Conclusion:** insert "on short-lived bearings" into the existing crossover sentence.
- Also add F3's condition once: the datasets provide limited training data for deep models, so the finding is a statement about this regime, not about the model class.

### 2.4 `TEXT` — Remove self-descriptive statements (D23)

> "the self-descriptive statements ('statistically honest by construction,' 'the metric correctly refuses…') should be removed and the methods allowed to speak for themselves."

**Verified counts in the PDF: "honest"/"honestly" ×16, "non-destruction" ×20, "correctly" ×9.**

Every "honest" instance, located:

| Where | Phrase |
|---|---|
| Abstract | "The metric **correctly refuses** to manufacture a positive effect." |
| Intro Contribution 4 | "A multi-dataset null result that is **statistically honest by construction**." |
| Conclusion | "an **honest**, counter-intuitive empirical result" |
| §6.1 | "this is the **honest** consequence of n = 3" |
| §6.2 | "We flag the two **honest** exceptions rather than hide them" |
| §6.2 | "The result is **honest** and two-sided" |
| §6.2 | "which we report **honestly**" |
| §6.3 | "an **honest** consequence of short runs" |
| §6.6 | "at the **honest** unit of inference" |
| §6.7 | "the **honest** family of hypotheses" |
| §6.7 | "This is the **honest** face of the metric" |
| §6.8 | "**honestly** flagged uncalibrated rather than silently passed" |
| §6.8 | "confirms the pattern and its **honest** limits" |
| §7.2 | "The **honest** synthesis is therefore not 'averaging helps'" |
| §7.4 | "The **honest**, replicated headline is therefore non-destruction" |
| Fig. 2 caption | "The **honest** cross-dataset headline is non-destruction" |
| App. D.1 | "We state its weight **honestly**" |
| §4.5 | "The deep sequence models carry an **honest** caveat" |

**Rule:** delete the adjective, keep the fact. "The honest unit of inference (n = 3 runs)" → "The unit of inference (n = 3 runs)". "We flag the two honest exceptions rather than hide them" → "Two bearings are exceptions:". "This is the honest face of the metric: it refuses to credit warning time on bearings that genuinely give none" → "The metric credits no warning time on bearings that provide none." Reducing "non-destruction" from 20 to roughly 6 occurrences also does most of D22's length work for free.

Note this is not a style quibble — a reviewer reading "statistically honest by construction" next to an unsupported universal ("never better") reads the self-description as a substitute for the evidence. Removing it makes the paper read as more rigorous, not less.

---

## PART 3 — New content to write

### 3.1 `TEXT` — Related work: three additions

**(a) False-alarm cost in the general anomaly-detection literature (D1).** E named the source:
> "The Numenta Anomaly Benchmark (Lavin & Ahmad 2015) comes to mind."

Add to §2.1, ~4 sentences. NAB is the right anchor: it scores streaming anomaly detectors with an explicitly asymmetric cost profile that penalises false positives and rewards early detection — structurally the same commitment as your gate, in a different domain. Say so, and say what is different: NAB folds cost into a single weighted score, while your gate makes the false-alarm constraint a *validity condition* rather than a term to be traded off. **Verify the citation yourself before adding it** — I have not fetched it and you should not cite from my description.

**(b) Classical change detection (F1).** F is right that this strengthens your novelty positioning rather than threatening it: the trade-off between detection delay and false-alarm rate is the founding problem of quickest change detection (Page's CUSUM, Lorden's minimax delay under a mean-time-to-false-alarm constraint, Pollak, Moustakides' optimality result, Basseville & Nikiforov's monograph). You already cite Page (1954) for CUSUM. Add ~4 sentences to §2.2 positioning your gate as the *evaluation-side* analogue of the ARL₀ constraint: change-detection theory constrains the false-alarm rate when **designing** a detector; you impose it when **scoring** one, which is why the gate can invalidate a detector that a delay-only metric ranks first. Verify each citation before adding.

**(c) Time-aware and uncertainty-aware evaluation (G6).** §2.1 covers Saxena/Goebel well and §2.3 covers conformal prediction. What is missing is the bridge: position the gated metric against more recent evaluation frameworks that incorporate timing and uncertainty. ~3 sentences at the end of §2.1.

> All three are additions of a paragraph each. Total: under 400 words. Do not let this balloon — E already says the paper is too long.

### 3.2 `TEXT` — Signal-theoretic grounding (G2) — *draft below, but gated on item 0.1*

> "Add a signal-theoretic argument (e.g., sufficient statistics, aliasing) grounding why bin-averaging preserves prognostic information for the studied signal class."

This is the most valuable addition available to you: it converts your empirical mechanism story (§7.2, Appendix D.1) into a stated reason, and it is free — no new runs.

**⚠️ Which version you can write depends entirely on item 0.1.** The sufficient-statistic argument holds for aggregation of the *feature/mean-square* series. If your sweep aggregates the *raw waveform*, the second argument below does not apply and you must use the aliasing argument alone.

**Draft (feature-series version) — new §4.7.2 or a subsection of §7.2:**

> "Two properties of the signal class explain why bin-averaged storage retains prognostic information.
>
> *Aggregation is exact for the second moment.* The mean square of a signal over a union of disjoint bins is the mean of the per-bin mean squares. The bin-averaged mean-square series is therefore not an approximation of the full-rate one but is exactly the mean-square over the coarsened window, and it is a sufficient statistic for the block variance under a locally stationary Gaussian model. No second-moment information is lost by aggregation at any factor f. This exactness does not extend to the higher-order statistics: the mean of per-bin kurtoses is not the kurtosis of their union, so impulsiveness features are genuinely altered by aggregation while amplitude features are not.
>
> *Decimation aliases; aggregation does not.* Bin-averaging by a factor f is a length-f moving-average filter followed by downsampling — an anti-alias filter followed by decimation. Plain decimation is the same downsampling with the filter omitted. The prognostic content of the health statistic lives at the degradation timescale, hours, far below the post-coarsening Nyquist rate even at f = 20; measurement noise in the same series is broadband. Decimation therefore folds out-of-band noise into the low-frequency band occupied by the degradation trend, inflating the variance of the health statistic without changing its mean, while aggregation attenuates that noise by approximately 1/f before downsampling. For a detector that alarms when the statistic crosses μ_b + kσ_b, a lower noise variance means the threshold is crossed earlier and held more persistently — the mechanism observed in Section 7.2 and confirmed in Appendix D.1.
>
> Two predictions follow, both testable against results already reported. First, the aggregation advantage should concentrate in amplitude- and variance-sensitive detectors and be weak or absent for impulse-driven and spike-robust ones — consistent with the observed ordering (3σ, EWMA, Hotelling T² positive; Isolation Forest weakest and sign-reversed on FEMTO). Second, the advantage should grow as the noise floor rises, which is what the noise-injection experiment of Appendix D.1 shows. The mechanism is thus generic low-pass filtering with an exactness property specific to the amplitude family, not a property of historian averaging as such."

That last paragraph is important: it makes your Isolation-Forest-negative-on-FEMTO result **predicted by the theory** rather than an inconvenient exception, which turns D19's contradiction into a strength.

### 3.3 `TEXT` — Deep model architecture table (G5)

> "Add a concise architecture/hyper-parameter table for the deep reconstruction models (LSTM-AE, TCN-AE, Transformer-AD) so the paper is fully self-contained without requiring inspection of the code."

**Verified gap.** Table 24 currently gives only: "Deep models seq-len 30, 40–50 epochs" and "Transformer d_model=32, 2 heads, 2 layers". That is not reproducible on its own.

New **Table 24b** in Appendix A, one row per model, columns: layers/blocks, hidden or latent width, kernel size and dilation schedule (TCN), heads and d_model (Transformer), sequence length, optimiser, learning rate, batch size, epochs, early-stopping rule, loss, parameter count. Also add Deep SVDD (encoder MLP widths, centre initialisation, ν). **Transcribe from `config.py`, verbatim — do not reconstruct from memory of the architecture.** → `⟦R-8⟧`

### 3.4 `TEXT` — ONGC derived artifacts in Data Availability (G7, D5)

> "Clarify in the Data Availability statement exactly which derived ONGC artifacts are released for reproducibility."

Current text says "the derived health-indicator series and the figures/tables it produces are included". Replace with an explicit enumeration — file names and paths as they appear in the repo:

> "For the ONGC case study the raw historian record is proprietary and cannot be redistributed. The following derived artifacts are released and are sufficient to regenerate every ONGC number in this paper: ⟦R-9: list exact paths — health-indicator series, per-detector lead-time and pre-onset-FAR result files, the conformal calibration series behind Figure 11, and the sampling-sweep result rows behind Table 29⟧. Raw waveforms, channel-level measurements, and asset identifiers are withheld. No inferential claim in this paper depends on ONGC."

**Verify each path exists in the Zenodo snapshot before submitting.**

### 3.5 `TEXT` — Future work (D8)

> "more and longer bearing run-to-failure datasets are needed, especially to extend the conclusions to long-life bearings, which are typical in industrial applications. A similar effort on other bearing types may also be relevant."

§8 already has the power analysis (n ≈ 6 to 17 needed) and the loader-templates offer. Add two sentences naming (a) long-life industrial bearings specifically, and (b) other bearing types and geometries. This costs nothing and closes the item.

---

## PART 4 — Presentation and formatting

### 4.1 `RUN` — Regenerate Figures 2 and 10 (D17, D16)

**Verified by rasterising and inspecting both pages. The root cause is a single bug, and it is not a font problem — it is UTF-8 bytes decoded as cp1252 (mojibake) in the plotting script's label strings.**

**Figure 2 (page 10) — confirmed defects:**
- y-axis label renders as `Median run-level lead-time î" (aggregate â^' decimate), h` — the `Δ` became `î"` and the minus sign `−` became `â^'`.
- x-axis tick labels render as `3ĺf` (should be `3σ`) and `Hot. TÂ²` (should be `Hot. T²`).
- Legend entry reads `ONGC (n=1 (case study))` — doubled parenthesis. Fix to `ONGC (n=1, case study)`.

**Figure 10 (page 18) — confirmed defects:**
- Legend renders `3ĺf` and `Hot. TÂ²` — same mojibake.
- In-plot annotation renders `SPC baseline ã‰ 0.67` — the `≈` is mangled.
- **In-plot title reads "Minimum training data for deep models to match SPC charts on FEMTO/PRONOSTIA (n=6 bearings)"** — which asserts a match that the caption correctly denies ("never reach it — no crossover"). E is right that the plot contradicts its own caption. **Delete the in-plot title entirely** and let the LaTeX caption carry it; that is house style for IJPHM anyway.

**Fix:** in the plotting script, either use matplotlib mathtext (`r'$3\sigma$'`, `r'Hot. $T^2$'`, `r'$\Delta$'`, `r'$\approx$'`, `'-'` for the minus) or ensure the source file is read/written as UTF-8 end to end. Mathtext is the safer choice — it removes the encoding dependency completely.

**Remaining figures: I checked all of them.** Extracted the embedded text of Figures 1, 3, 4, 5, 6, 7, 8, 9, 11 — `σ`, `λ`, `T²`, `α` all render correctly there. **Only Figures 2 and 10 are affected.** Still eyeball the regenerated PDF at 200% before submitting, and say in the response letter that you checked all figures, since E explicitly asked you to.

### 4.2 `TEXT` — Abbreviations (D13, F7)

| Abbrev. | Expansion | First use / action |
|---|---|---|
| **SCADA** | Supervisory Control and Data Acquisition | **Never expanded anywhere in the paper — verified.** Appears in the title and abstract. Expand at first body use in §1: "Industrial Supervisory Control and Data Acquisition (SCADA) historians…" |
| **SPC** | statistical process control | First use is the **abstract** ("four SPC charts"). Expand there. §2.2 spells it out — keep. |
| **BPFO / BPFI / BSF / FTF** | ball pass frequency outer race / inner race / ball spin frequency / fundamental train frequency | §4.2 — named but never expanded. Expand all four at that single point. |
| **ROC–AUC** | receiver operating characteristic – area under the curve | §1, not expanded |
| **CUSUM** | cumulative sum | Abstract; expanded only in §4.5. Add at abstract or §1. |
| **LSTM** | long short-term memory | §4.5 gives "LSTM autoencoder" but not the expansion |
| **SVDD** | support vector data description | §4.5, never expanded |
| **PCA / FFT** | principal component analysis / fast Fourier transform | §4.2, §4.5 |
| **ONGC** | Oil and Natural Gas Corporation | Abstract and throughout — never expanded |
| **RUL** | remaining useful life | ✓ expanded §2.1 — no action |
| **CBM / PHM** | ✓ expanded §1 — no action |

F said "check the others" — the table above is the full sweep.

### 4.3 `TEXT` — Cut Table 21 (D14)

> "Table 21 may be unnecessary: its results are true by construction and already described in the text."

Agreed. Replace with one sentence in §6.12:

> "Evaluated on the three IMS runs, a constant-on detector earns the entire record as prognostic horizon (164–1073 h) while flooding the pre-onset region (FAR_pre ≈ 1), so the gated metric scores it invalid on every run (L = 0); the oracle firing just after t_o⁺ is the mirror image, at zero pre-onset false alarms and the maximum achievable lead (12.9, 62.5, 44.5 h)."

*(Numbers above are transcribed from your Table 21 — re-verify against the table before pasting.)*

### 4.4 `TEXT` — Cut Table 23 and §7.4 (D15, D22)

- **Table 23** duplicates Figure 10 — cut, keep the regenerated figure, and point §6.13's text at the figure alone.
- **§7.4 "Summary of Key Outcomes"** duplicates §6's per-section summaries and restates the headline a fifth time — cut entirely. This is D's clearest length win and it removes one of the six "never costs" instances (item 2.1 #4) for free.
- **F8** additionally suggests moving dense secondary tables to supplementary. Candidates, in order: Table 19 (feature-group × detector validity), Table 18 (feature group × coarsening factor), Table 20 (per-run spectral ablation), Table 15 (break-even budget grid — pure arithmetic from Eq. 6, no experimental content). Moving Tables 15 and 18–20 to an appendix would cut ~1.5 pages without losing a single result. Recommend doing at least Table 15 and Table 20.

### 4.5 `TEXT` — Cross-reference repair after the cuts ⚠️

Cutting Tables 21 and 23 renumbers everything after them. **Verified inbound references that will go stale:**

- Intro, Contribution 2: "(Section 6.12, **Tables 21 and 22**)"
- §2.1: "(Section 6.12, **Tables 21 and 22**)"
- §6.13: "The result (**Table 23**, Figure 10)"
- Every reference to Tables 24–29 shifts by two.

**Strong recommendation:** before making any cuts, confirm every table and figure uses `\label{}`/`\ref{}` rather than a hard-coded number. This paper has 29 tables and 11 figures; a single stale cross-reference in a resubmission to a reviewer who has already caught two internal inconsistencies is exactly the wrong impression to make. After the cuts, compile twice and grep the log for undefined references, then read every `Table N` and `Figure N` mention in the PDF once, in order.

### 4.6 `TEXT` — Sentence complexity (D10, F6)

Both reviewers flagged this; E scored clarity **3 / Fair** partly on it.

**Concrete measurement: the paper contains 180 em-dashes across 24 pages** (~7.5 per page). That single count is most of the problem — em-dash asides are how the long sentences get built.

**Targets:**
- Reduce em-dashes to under 60. Most become a full stop or a comma.
- One idea per sentence. Where a sentence has two em-dash asides, it is at least two sentences.
- Worst offenders to rewrite first (all verified as long, multi-clause constructions): §6.6's detector-listing paragraph; §6.2 "Onset under a decoupled health indicator"; §4.5's Deep SVDD paragraph; §6.13's Deep SVDD failure-mode paragraph; the Intro "Method" paragraph.

Do this pass **last**, after all content is settled, in one sitting, reading aloud.

### 4.7 `TEXT` — Table density (F9)

> "some tables are quite dense and would benefit from slightly improved formatting or simplification."

Table 11 (40 rows) is the main one. Options: group by dataset with `\midrule` separators and a subheading row per dataset; drop the "Rej.?" column, since every entry is "no" and one sentence in the caption says it better; right-align numerics on the decimal point. Tables 16, 19, 24 also benefit from `\midrule` grouping.

---

## PART 5 — Items requiring no change (state this in the response letter)

- **D12** — "Typos: None identified." No action.
- **G9** — "The paper scores highly on clarity of presentation… No substantive corrections are required." No action. *(Note: G and E disagree on clarity, 4 vs 3. Address D's version; G's assessment costs you nothing.)*
- **D2 / G8 onset circularity** — already acknowledged in §8 and probed in Table 4. Reinforced by items 1.5 and 1.6.
- **D4** — "not all models could be evaluated on all bearing runs" — already handled via explicit N/A cells (§4.5, §6.3). Point to it.
- **F3 / G8 indirect RUL comparison** — §2.2's "Relation to published FEMTO/XJTU results" already explains why RUL scores are not comparable. Point to it and add one sentence acknowledging it as a limitation rather than only a justification.

---

## PART 6 — Pre-submission verification

Run every one of these before uploading. Do not skip any.

1. **No unfilled placeholders.** `grep` the source for `⟦`, `TODO`, `XXX`, `??`.
2. **Every number traces to a released result file.** Reviewers have the repo and the Zenodo snapshot. Spot-check ten numbers at random against the released tables.
3. **Repo and Zenodo updated first, paper second.** New scripts for items 1.1–1.7 committed, environment still pinned, test suite still green, new Zenodo version minted. The paper's DOI reference must point at a snapshot that actually contains the new analyses.
4. **No universals left.** `grep -i "never\|always\|every dataset\|all detectors\|cannot be"` in the abstract, introduction, discussion, and conclusion. Each hit must be individually justified.
5. **Cross-references.** Compile twice; zero undefined references; read every `Table N` / `Figure N` mention in order against the rendered PDF.
6. **Figures.** Open the PDF at 200% and read every axis label, tick label, legend entry, and in-plot annotation in all 11 figures.
7. **Abbreviations.** Every entry in the §4.2 table above expanded at first use, once.
8. **Consistency sweep.** The coarsening-level statement from item 0.1 must read identically in the abstract, introduction, §4.7, and conclusion.
9. **Internal contradiction check.** Re-read the abstract and introduction *against Tables 7, 8, 9, 10, 11* specifically. That is the exact check Reviewer D performed, and it is the one that produced the major-revision decision.
10. **Response letter complete** — every one of the 41 items answered, including the ones you declined.