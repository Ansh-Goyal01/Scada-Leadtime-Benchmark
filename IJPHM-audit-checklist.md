# IJPHM — Reviewer Concern Audit Checklist

> **READ THIS FIRST.** Reviewer quotes describe the SUBMITTED manuscript.
> They are not ground truth about current results. Never alter data or a table
> to match a reviewer's description.
>
> A quote is evidence of what the reviewer read, not of what is true now. When a
> quoted number disagrees with the current result files, the default conclusion is
> that the result changed after submission — not that the current result is wrong.
> Check the file provenance first (`results/tables/MANIFEST.md`), and if the number
> moved because a defect was fixed, the item is closed by *explaining* the change,
> never by reproducing the old value. Editing a result to satisfy a reviewer quote
> has already caused one regression in this revision (see D18).

Every actionable request from the three reviews, quoted verbatim, with a concrete
pass/fail test against the current manuscript.

**41 items: Reviewer D 23, Reviewer F 9, Reviewer G 9.** Three require no action
and are marked NO-ACTION; they still need a one-line confirmation in the report.

## Rules for the audit

1. **Test against the compiled PDF text, not the `.tex` source.** Macros, math mode
   and line wrapping defeat literal source search. Where a test says "PDF", extract
   with PyMuPDF and join hyphenation both ways (`-\n` → `-` and `-\n` → ``).
2. **Figure tests require rendering the page as an image.** A text-layer check
   cannot detect a malformed label, an obscured legend, or a clipped string.
3. **Report what you measure, not what the progress file says was done.** This audit
   exists because an item can be recorded as complete and still not be in the file —
   it has already happened once in this revision.
4. Three verdicts only: **PASS** (test satisfied), **FAIL** (test not satisfied),
   **PARTIAL** (satisfied in some locations but not all — list which).
5. For every FAIL or PARTIAL, quote the offending text with its line number.

---

# REVIEWER D — major revisions, another review cycle

### D1
> "It would have been good to also at least slightly touch on the extensive false positive related costs discussed in other fields including general anomaly detection publications. The Numenta Anomaly Benchmark (Lavin & Ahmad 2015) comes to mind."

**Test:** Lavin & Ahmad 2015 cited in the PDF body and present in the bibliography. The citing passage discusses false-alarm cost outside bearing prognostics.

### D2
> "the number and size of the datasets tested is small, as the author correctly acknowledges, the observed trend cannot be established as significant at these sample sizes — and the 3σ deployment recommendation inherits an acknowledged circularity between the onset definition and the detectors' features."

**Test:** Both acknowledged in the limitations section. The circularity must be probed empirically, not only stated — locate the analysis and confirm it reports a measured result.

### D3
> "the deep reconstruction models are stated to have no valid operating point 'regardless of threshold' (Section 6.1) but are omitted from the threshold sweep in Table 16. This evidence should be shown or the claim softened"

**Test:** The phrase "regardless of threshold" returns zero from the PDF. LSTM-AE, TCN-AE and Transformer-AD appear as rows in the trade-off table. The replacement sentence states what was measured per threshold.

### D4
> "one-class SVM is described as evaluated (Section 4.5) but appears in no results table. It should be reported or the mention removed."

**Test:** Either one-class SVM appears in results tables, or every claim that it was evaluated is removed. List every table it appears in. If reported, the correction family size must be consistent everywhere.

### D5
> "more and longer bearing run-to-failure datasets are needed, especially to extend the conclusions to long-life bearings, which are typical in industrial applications. A similar effort on other bearing types may also be relevant."

**Test:** Both named explicitly in future work — long-life bearings, and other bearing types.

### D6
> "Section 4.7 describes the coarsening operation inconsistently: 'before feature extraction' in one sentence and 'resamples at the feature level' two sentences later… The authors should state, for each dataset, at which level the aggregate and decimate operations are applied"

**Test:** No sentence in the PDF describes coarsening at two different levels. A per-dataset statement exists covering all five datasets. Report the exact wording.

### D7
> "the sentence structures are unnecessarily complex almost throughout, which makes the methodology harder to follow than it needs to be."

**Test:** Count rendered em-dashes in the PDF (baseline in the submitted version: 167). Report the count. Identify the five longest sentences in the methodology and results sections by word count.

### D8 — NO-ACTION
> "Typos: None identified."

**Test:** Confirm no new typos introduced. Check for LaTeX artifacts: acute accents from `\'`, doubled parentheses, mojibake, clipped strings.

### D9
> "SCADA is never expanded. Spell out 'Supervisory Control and Data Acquisition' at first use"

**Test:** "Supervisory Control and Data Acquisition" appears in the PDF at or before the first body use of SCADA.

### D10
> "the bearing characteristic frequencies BPFO, BPFI, BSF, and FTF are named but never expanded. Expand each once at first use in Section 4.2."

**Test:** All four expansions present at first use. Quote the sentence.

### D11
> "Table 21 may be unnecessary: its results are true by construction and already described in the text."

**Test:** The latch-on/oracle table is absent from the source. Its content is carried by prose. No stale cross-reference to it remains.

### D12
> "Table 23 duplicates the Figure 10 results."

**Test:** The training-fraction table is absent. The corresponding figure remains. No stale cross-reference.

### D13
> "The Figure 10 title is misleading… the in-plot title contradicts its own caption and should be removed."

**Test:** Render the figure as an image. Confirm no in-plot title. Confirm the caption does not claim the deep models match the control charts.

### D14
> "the x and y labels in Figure 2 are malformed"

**Test:** Render as an image and read the axis labels. In the submitted version they rendered as `î"` for Δ and `â^'` for the minus sign. Confirm both render correctly, and that tick labels show `3σ` and `Hot. T²`.

### D15
> "the Figure 10 legend is malformed"

**Test:** Render as an image. Confirm the legend renders `3σ` correctly and that the `≈` in any in-plot annotation is correct.

### D16
> "The authors should regenerate both figures and check the remaining figures for similar issues."

**Test:** Render EVERY figure at high resolution and inspect axis labels, tick labels, legend entries and in-plot annotations. Report per figure. Also confirm no legend obscures plotted data and no two series share a colour.

### D17
> "the headline 'does not cost warning time' is a null-acceptance claim made without an equivalence test; it should be reworded as a bounded no-detectable-difference statement or supported formally."

**Test:** The bare phrase and its paraphrases return zero. An equivalence analysis exists with a stated margin, and the margin is justified before results are reported. Confirm the claim is bounded wherever it appears — abstract, introduction, discussion, conclusion.

### D18
> "the introduction's 'decimation is never better' is contradicted by the paper's own Table 8 (Isolation Forest on FEMTO, negative in six of six runs)"

**Test:** "never better", "never costs", "does not cost" and their paraphrases return zero from the PDF. List the paraphrase set searched before searching. Confirm the replacement claim is phrased around the margin, not around an absence of negative cells.

> **Do not act on the quoted numbers.** The Isolation Forest on FEMTO result the
> reviewer quotes was an artifact of defect N-20. Post-fix it is 2+/4-, p = 0.688.
> Do not restore the reviewer's values.
>
> Provenance: `n20_raw_contrast_old_vs_new.csv` holds both arms for this cell.
> `arm=old` (pre-N-20) is median $-0.137$~h, 0+/6-, sign-consistent, p = 0.031 --
> exactly the "negative in six of six runs" the reviewer describes, so the quote was
> accurate about the submitted PDF. `arm=new` (post-N-20, canonical) is median
> $-0.065$~h, 2+/4-, not sign-consistent, p = 0.688. Table 8 and Table 5 must read
> `arm=new`; `paper/verify_tables.py::check_holm` fails if either is re-pointed at a
> pre-fix file. An earlier pass "corrected" 18 of Table 8's p-values back toward the
> pre-fix arm to match this quote; that regression was reverted in commit f5afe70.
>
> The D18 item itself is still live, but it is a *wording* test only: the phrase
> "decimation is never better" must not appear, and the replacement must be phrased
> around the $\pm 1$~h operational margin rather than around an absence of negative
> cells. Five cells do lie wholly below zero (Table 6); that is expected and is not
> a defect to be edited away.

### D19
> "The IMS test-3 failure relabel is author-chosen and affects one of the three runs carrying the paper's only directional trend; results under the original label should be shown."

**Test:** Results under the original label appear in the manuscript, with both labels shown side by side, and the effect on effective sample size is stated.

### D20
> "the non-destruction conclusion should be scoped: the datasets providing statistical power are short-lived bearings on which the effect could never exceed minutes, while the long-runway case rests on three runs."

**Test:** A passage states this asymmetry explicitly. A scoped version appears in the abstract and conclusion, not only in the limitations section.

### D21
> "the paper is much longer than needed: the headline finding is restated many times, Table 21 and Table 23 can be cut, Section 7.4 duplicates Section 6's summaries"

**Test:** The summary subsection is absent. Count how many times the headline finding is stated across abstract, introduction, results, discussion and conclusion — report the count and the locations. Report table count, figure count and page count against the submitted 30 / 11 / 24.

### D22
> "the self-descriptive statements ('statistically honest by construction,' 'the metric correctly refuses…') should be removed and the methods allowed to speak for themselves."

**Test:** Both quoted phrases return zero. Count "honest"/"honestly" (submitted: 18) and "non-destruction" (submitted: 21). Search for other self-characterisation: "correctly refuses", "by construction" used as praise, "exemplary", "rigorous", "we are careful to".

### D23
> "The Figure 10 in-plot title must be corrected as it currently contradicts its own caption."

**Test:** Covered by D13; confirm independently.

---

# REVIEWER F — minor revisions

### F1
> "The literature review could be slightly expanded toward classical change-detection methods, where detection delay and false-alarm constraints have also been studied."

**Test:** The change-detection literature is cited and positioned. Confirm citations resolve.

### F2
> "the main SCADA aggregation conclusion appears to rely mainly on raw lead-time differences, while the paper itself argues that lead time without a false-alarm constraint may be misleading… It would strengthen the work to also show the aggregation-versus-decimation results directly under the proposed gated metric."

**Test:** The aggregate-versus-decimate contrast is reported under the gated metric, in the manuscript body, not only in the repository. Confirm the reason for retaining raw lead as primary is stated explicitly.

### F3
> "The conclusions about deep models should also be kept within the tested conditions, since some of the datasets provide quite limited training data for these models."

**Test:** Every deep-model conclusion is scoped to the tested conditions. Locate each and confirm. The training-data limitation should be quantified, not only asserted.

### F4
> "It would help if the paper stated more clearly for each dataset whether aggregation is performed on the raw vibration signal, the sampled data, or the extracted features."

**Test:** Same as D6.

### F5
> "Some of the stronger statements about 'non-destruction' could also be softened, since several statistical comparisons are not significant and the available sample sizes are limited."

**Test:** Same as D17 and D18. Additionally report the occurrence count of the term.

### F6
> "a careful proofreading would still be useful to correct a few minor wording and consistency issues. Some sentences are quite long and could be simplified for easier reading."

**Test:** Same as D7 plus D8.

### F7
> "terms such as SCADA, SPC, BPFO (+ may be some more) should be checked and expanded when they first appear."

**Test:** SCADA, SPC, BPFO, BPFI, BSF, FTF expanded at first use. Sweep the PDF for any remaining unexpanded abbreviation and list them.

### F8
> "there are many tables, and some of the secondary results could be moved to supplementary material to make the main paper more focused."

**Test:** Report the table count against the submitted 30 and state what changed.

### F9
> "some tables are quite dense and would benefit from slightly improved formatting or simplification."

**Test:** Identify the densest table and confirm it was reorganised. Render every table page and confirm no column spills into the neighbouring text column.

---

# REVIEWER G — minor revisions

### G1
> "Provide a brief theoretical or simulation analysis of the onset estimator's properties (bias/variance under abrupt vs. gradual degradation)."

**Test:** An analysis exists giving bias and variance behaviour, distinguishing abrupt from gradual degradation.

### G2
> "Add a signal-theoretic argument (e.g., sufficient statistics, aliasing) grounding why bin-averaging preserves prognostic information for the studied signal class."

**Test:** Such an argument exists. Confirm it does not overclaim — any exactness or conservation claim must be checked against what the detectors actually consume.

### G3
> "Include a sensitivity check showing that the aggregate-vs-decimate difference is stable under a disjoint onset indicator (e.g., PCA-first-component), or bound the claim if it is not."

**Test:** The check is reported with at least one disjoint indicator, and the claim is bounded where the result is not stable.

### G4
> "Explicitly scope the deep-model 'no crossover' claim to short-lived bearings in the abstract and conclusion."

**Test:** The scoping appears in **both** the abstract and the conclusion. Confirm separately for each.

### G5
> "Add a concise architecture/hyper-parameter table for the deep reconstruction models (LSTM-AE, TCN-AE, Transformer-AD) so the paper is fully self-contained without requiring inspection of the code."

**Test:** The table exists and covers all three named models. Test the stated purpose directly: could a reader reimplement from the table alone, without opening the code? List anything missing.

### G6
> "expand the related-work discussion to better position the gated metric against other recent time-aware or uncertainty-aware evaluation approaches."

**Test:** Such a discussion exists and states what the gated metric adds. Confirm citations resolve.

### G7
> "Clarify in the Data Availability statement exactly which derived ONGC artifacts are released for reproducibility."

**Test:** The statement enumerates artifacts specifically. **Verify every cited path resolves in a clean clone of the public repository at the released tag** — not in the working tree. Confirm the paths render fully in the PDF without clipping.

### G8
> "Limitations lie mainly in the still-heuristic nature of the onset definition, the limited external benchmarking against the RUL literature, and the restricted scope (steady-condition bearings)."

**Test:** All three stated as limitations.

### G9 — NO-ACTION
> "The paper scores highly on clarity of presentation… No substantive corrections are required on these points."

**Test:** Confirm nothing done for Reviewer D's clarity items made presentation worse.

---

## Cross-cutting checks

These are not reviewer requests, but a reviewer will notice them.

**X1. Internal consistency.** Every number in the abstract and introduction must match the table it summarises. Reviewer D found two such contradictions in the submitted version; this is the check they ran.

**X2. Cross-references.** Zero undefined references or citations. Every `Table N` / `Figure N` mention resolves to the intended float — verify by reading the rendered PDF in order, not by trusting `\ref`.

**X3. Numbers trace to files.** Spot-check fifteen numbers at random against released result files.

**X4. Claim-vs-table check.** For each of the main results tables, read the prose that describes it and confirm every claim matches the table's contents.

**X5. Reproducibility statement.** Every claim in the Data and Code Availability section must be true of the **public repository**, not the working tree.
