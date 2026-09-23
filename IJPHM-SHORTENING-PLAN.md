# IJPHM Manuscript Shortening Plan — 30 pages → 20–21 pages

**Read this file in full before starting. Re-read it at the start of every session.**
Record progress in `IJPHM-PROGRESS.md` after every phase, not at the end.

---

## 0. The goal and the rule that governs everything

**Goal:** reduce the manuscript from 30 pages to 20–21 pages.

**The rule — no content loss.** Every claim, number, correction and reviewer-requested
addition present in the manuscript now must be present after this work. "Shorter"
means the same information expressed once instead of several times, in a denser form.
It never means removing a result, a caveat, a correction or a disclosure.

This rule is made **checkable** in Phase 0 (an inventory is built) and **proved** in
Phase 6 (every inventory item is located in the new manuscript). A phase that cannot
satisfy the inventory does not ship.

**Why length matters here.** IJPHM sets no hard page limit, but its submission
guidelines state that unnecessarily long papers usually do not get a positive response.
Reviewer D also said explicitly: "the paper is much longer than needed." The paper was
24 pages at submission and is 30 now.

---

## 1. Standing constraints — these override everything below

1. **Height, not float count.** In an earlier pass, merging five floats into fewer
   saved zero pages, because the merged floats spanned both columns and occupied the
   same height. Measure the page effect of every change. A merge that does not reduce
   rendered height is reverted.

2. **Do not alter the template.** PHM Society enforces strict formatting and warned
   about it in the decision letter. Do not change body font size, margins, column
   width, line spacing, `\baselinestretch`, section spacing, or the class options.
   Using `\small` or `\footnotesize` *inside tables* is normal and permitted. Do not
   shrink figures below legibility at print size.

3. **N-20 provenance rule.** Every new or regenerated table and figure must read from
   post-N-20 files for FEMTO, Ferrara and ONGC. The provenance rule and guards already
   exist (see the `n20-provenance-rule` memory and `verify_tables.py`). A figure built
   from a pre-fix file is a regression.

4. **No number may live only inside a raster figure.** A reader must be able to find
   every exact value in text, in a table, or as vector text inside a figure. A plot may
   show a value visually only if the exact value is printed somewhere in the paper.
   *Amended 2026-09-23 (author):* this applies to every NEW figure and to any number the
   text cites or a claim depends on. Pre-existing curve figures whose data are in
   MANIFEST-listed result files — Figure 3's curves, Figure 4 panels (b) and (c), Figure 5
   panel (b) — are acceptable as they are. Do NOT add tables to cover them; that adds pages.

5. **Numbers are generated, never typed.** Every new or merged table is produced by a
   script from canonical result files, and `verify_tables.py` is extended to cover it.
   The checked-value count may not fall below 558.

6. **Rule 10 still applies.** Verify on the compiled PDF, not the `.tex`. Render pages
   as images for any layout or figure check. Search concepts with paraphrase lists, not
   single strings.

7. **Commit after each phase**, with the measured page count in the commit message, so
   any phase can be reverted alone.

---

## 2. Protected content — must survive, and must remain findable

These were requested by reviewers or answer a reviewer point. They may be **tightened**
but never removed, and each must still be locatable after the work. The Response to
Review points reviewers at them.

| Item | Content that must survive |
|---|---|
| D6 / F4 | §4.8 per-dataset statement of coarsening level, all five datasets; "not a test of raw-signal averaging" |
| D17 | the ±1 h margin **and its justification** at first use |
| D18 / D16 | bounded margin claim; the five below-zero cells and the widest reaching −0.45 h |
| D19 | Appendix C: both labels side by side, per-run differences, effective n |
| D20 | lifetime asymmetry in §8 **and** abstract **and** conclusion |
| D3 | deep models as rows in the trade-off table; per-threshold statement |
| D4 | one-class SVM in the results tables; N = 44 |
| D1, F1, G6 | the three related-work paragraphs and their six citations |
| F2 | aggregate-vs-decimate under the **gated** metric, visible in the body, with the power cost |
| F3, G4 | deep-model scoping in abstract **and** conclusion; 20–335 windows; 2.0–5.5 × 10⁴ parameters |
| G1 | onset-estimator bias/variance (kσ_b/m, σ_b/m) after Algorithm 1 |
| G2 | §7.3 signal-theoretic argument, including "we claim no conservation result" |
| G3 | disjoint-onset sensitivity result: raw lead invariant, 0.000 h across 99 cells |
| G5 | deep-model architecture table **in the paper** — the reviewer asked for self-containment |
| G7 | Data Availability enumeration of ONGC artifacts, by path |
| G8 | RUL-benchmarking limitation in §8 |
| Corrections | every disclosed defect's corrected result, including the multi-seed gap result and Hotelling T² collapsing in 2 of 5 draws at 20% |

---

## 3. PHASE 0 — Measure. No edits.

1. **Page map.** Compile. For every section and subsection, record the page span and
   word count. For every float, record its page, whether it is single- or full-width,
   and its rendered height as a fraction of a page.
2. **Caption lengths.** Word count of every caption.
3. **Sentence statistics** per section: mean and 90th-percentile sentence length.
4. **Claims and numbers inventory.** From the compiled PDF, build
   `revision-artifacts/inventory_before.csv` with one row per atomic claim and one row
   per distinct printed number, each with section, source location, and the sentence or
   table cell it appears in. Group repeated statements of the same claim under one
   claim ID, recording every location. This is the file Phase 6 proves against.
5. **Redundancy report.** For each claim appearing in more than one location, list the
   locations. This is the map of where repetition lives.
6. **Confirm current labels** for every table and figure and map them to the candidate
   merges in Phase 1. Label names in this plan are best-known and may have drifted.

**Report:** the page map, the float heights ranked largest first, the ten longest
captions, the per-section sentence statistics, and the redundancy report. Then stop and
wait for approval before Phase 1.

---

## 4. PHASE 1 — Consolidate tables that share a row index

Merge only where **both** the row index and the meaning of the columns overlap. Each
merge must carry every value from its sources. Measure height before and after.

### M1 — The cross-dataset statistics table (largest single saving)

**Sources:** the sign-test table (`tab:crossds`), the equivalence table (`tab:equiv`),
the Holm table (`tab:holm`), the gated-contrast table (`tab:gatedcontrast`), and the
ONGC table (`tab:ongc`).

**Why:** all are indexed by dataset × detector. The Holm table's raw p-values are the
same tests as the sign-test p-values — verify this cell by cell before relying on it.
Every Holm-adjusted p is 1.00, so the Holm table reduces to one caption sentence.

**Target:** one table, rows = dataset × detector, columns = median Δ, 95% bootstrap CI,
n₊/n₋, exact sign-test p, equivalence verdict at δ = 1 h, and gated median Δ with its
p. ONGC rows appear as descriptive, marked n = 1, with no test statistics.

**If the merged table is too wide for one column,** split by metric into two
single-column tables that share the row index — raw contrast with CI and equivalence,
and gated contrast — rather than producing one full-width table. Measure both layouts
and keep the shorter.

### M2 — The IMS detector summary

**Sources:** the IMS lead-time table (`tab:imslead`), the FAR-budget table
(`tab:farbudget`), and the prognostic-horizon ranking table (`tab:phrank`).

**Why:** all are indexed by IMS detector. The PH ranking is fully derivable — PH is the
best raw lead across the three tabulated thresholds, and L is the τ = 0.10 column of the
FAR-budget table. Verify this derivation against the files before merging.

**Target:** one table, rows = the eleven detectors, columns = raw lead with 95% CI, best
valid lead at τ = 0.05, 0.10, 0.20, and PH. Show the ranks by ordering the rows or by a
compact rank column. The trade-off table (`tab:tradeoff`) stays separate: it is indexed
by threshold, not by detector alone.

### M3 — Mechanism tables (Appendix D)

**Sources:** the noise-injection table (`tab:noise`) and the denoiser table
(`tab:denoise`). Same experiment family, same factor, same n = 3. Merge into one table
with two panels.

### M4 — Configuration and cost (Appendix A)

**Sources:** the fixed-protocol table (`tab:hyperparams`) and the compute-cost table
(`tab:compute`). Fold compute cost into the protocol table as a compact block, or as
columns if the detector rows align.

**Do not merge the deep-model architecture table (`tab:deeparch`) away.** Reviewer G
asked for it in the paper specifically so the paper is self-contained. It may be
tightened, not absorbed.

### M5 — Conformal calibration

If a conformal calibration table still exists alongside the four-panel conformal
figure, the figure already carries it. Move the exact values into the figure caption as
one compact line, then remove the table.

### Tables that stay

The dataset table, the trade-off table, the per-bearing XJTU table, the robustness
table, the onset table, the single ablation table, the Appendix C relabel table, the
deep-architecture table and the base-statistics table stay. Each may be tightened.

**Report after Phase 1:** tables before and after, pages before and after, and the
height change per merge. Revert any merge that did not reduce height.

---

## 5. PHASE 2 — One headline figure

### F1 — Forest plot of the central result (replaces `fig:crossdataset`)

The cross-dataset bar chart shows medians only. Replace it with a forest plot that shows
the paper's central claim in one view:

- x-axis: run-level aggregate − decimate difference in hours
- y-axis: detector
- panels: IMS, XJTU-SY, FEMTO, Ferrara
- marker: point estimate; bar: 95% bootstrap CI
- a shaded band at ±1 h labelled as the equivalence margin
- ONGC as hollow markers, labelled descriptive (n = 1)
- consistent detector colours from `config.PLOT`, as used elsewhere

Every value it shows exists exactly in the M1 table, so constraint 4 is satisfied. Build
it from post-N-20 files only. Size it to the smallest height that keeps labels legible
at print size, and render it at print size to confirm.

**Optional, only if it saves height:** the prognostic-horizon inversion argument could
be shown as a small single-column slopegraph (PH rank → gated rank, eleven detectors)
in place of the ranking prose. Build it only if it lets the §6.11 prose shrink by more
than the figure costs. Measure.

**Report after Phase 2:** figure count, pages before and after.

---

## 6. PHASE 3 — Caption discipline

A caption states what the float shows and how to read it. Interpretation belongs in the
text. For every caption:

1. Keep: what is plotted or tabulated, units, the meaning of symbols and markers,
   sample sizes, and any convention needed to read it correctly.
2. Remove: restated findings the text already states, and "this shows that…" sentences.
3. Target: 40 words or fewer for most captions; up to about 70 where the float needs
   reading instructions.
4. **Before removing any interpretive sentence from a caption, confirm the same claim
   exists in the body text.** If it exists only in the caption, move it to the text —
   do not delete it.

**Report after Phase 3:** caption word totals before and after, pages before and after.

---

## 7. PHASE 4 — Prose compression

This is the largest and riskiest phase. The inventory from Phase 0 is the constraint.

### Rules

1. **State each finding once, where the evidence is.** A result belongs in the results
   subsection that shows it. The introduction previews it in one clause, the discussion
   interprets it without re-quoting its numbers, the conclusion restates it once.
2. **Do not narrate tables.** Prose states the finding and at most the one number that
   matters, then points to the table. Lists of per-detector or per-run values that
   duplicate a table are removed from the prose, provided the table carries them.
3. **Sentence length.** Target a mean of about 25 words per section; the audit measured
   38. Split multi-clause sentences. Remove parenthetical asides that restate context.
4. **Caveats have one home.** Where the same limitation is stated inline in results and
   again in §8, keep the full statement in one place and reduce the other to a
   cross-reference. The protected items in section 2 keep their required locations.
5. **Remove signposting** — "as discussed above", "we return to this below", "it is
   worth noting that" — unless it resolves a genuine ambiguity.
6. **Do not weaken bounded claims.** A bounding clause such as "within the ±1 h margin"
   or "on the short-lived bearings tested" is content, not padding. Compression must
   never turn a bounded claim into an unbounded one.

### Targets by section

Set per-section word targets from the Phase 0 measurements. Indicative:

| Section | Target reduction | Where the savings are |
|---|---|---|
| §1 Introduction | ~35% | The problem/solution/method/finding arc, the five contributions, and the scope paragraph are three overlapping summaries. Keep the contribution list; compress the arc to a few sentences; fold scope into one paragraph. |
| §2 Related work | ~15% | Tighten; protect the three new paragraphs and their citations. |
| §4 Methods | ~20% | Justifications restated from the introduction. §4.8 is protected. |
| §6 Results | ~30% | Narrated tables and repeated caveats. |
| §7 Discussion | ~30% | Re-quoted results. **§7.1 "What Changed the Story"** describes corrections relative to an unpublished earlier version, which readers cannot see; every correction it lists is described in Methods. Condense it to two or three sentences — do not delete the corrections themselves. §7.3 is protected. |
| §8 Limitations | ~20% | Remove caveats duplicated inline in results. Protected paragraphs stay. |
| Appendices | ~20% | Tighten prose. Protected tables stay. |

**Report after Phase 4:** words and pages per section before and after, and mean
sentence length per section.

---

## 8. PHASE 5 — Layout

Only template-safe adjustments:

- Convert full-width tables to single-column where they fit legibly.
- Use `\small` or `\footnotesize` inside tables where not already used.
- Tune float placement so floats do not strand large white gaps.
- Check that no page ends a column with substantial unused space caused by a float.

No changes to margins, body font, spacing or class options.

---

## 9. PHASE 6 — Prove nothing was lost

1. **Inventory proof.** Build `inventory_after.csv` from the new compiled PDF. For every
   claim ID and distinct number in `inventory_before.csv`, record where it now lives:
   section, table, figure caption, or table cell. Report every item that cannot be
   located. **The count of unlocated items must be zero**, or each one listed for my
   explicit decision. Do not delete an item and report it as relocated.
2. **Protected content.** For each row of the table in section 2, quote the surviving
   passage and its location.
3. **Numbers.** Run `verify_tables.py`. The checked-value count must be at least 558 and
   every value must match. Extend it to cover every new and merged table.
4. **Provenance.** Confirm the new forest plot and every merged table read from post-N-20
   files for FEMTO, Ferrara and ONGC.
5. **Build and render.** Compile. Report page count, undefined references and citations,
   overfull boxes. Render every page as an image: no clipped text, no column overruns,
   no overprinting. Render every figure at print size and confirm legibility.
6. **Test suite.** Run it and report what you observe.

---

## 10. PHASE 7 — Deliverables for the Response to Review

The Response to Review cites section, table and figure numbers, and states page, table
and figure counts. This work changes all of them. Produce:

1. **Renumbering map:** old → new for every section, table and figure, and every label
   that was merged away, with the float it merged into.
2. **Final counts:** pages, tables, figures, compared with the submitted 24 / 30 / 11.
3. **A list of every place the Response to Review cites a number that has now changed.**

---

## 11. Stop rules and escalation

- **Stop at 21 pages.** Once the manuscript is at or below 21 pages with the inventory
  proof clean, stop compressing. Do not trade content for the last page.
- **Stop and ask** if a merge would drop any value, if a protected passage cannot be
  tightened without losing content, if the inventory proof shows an unlocated item that
  you cannot restore, or if a phase increases page count.
- **If the target is not reachable** without content loss after Phases 1–5, stop and
  report the remaining gap with the options. Do not cut content to close it.

### Last-resort tier — OFF unless I explicitly authorise it

Relocating material from the paper to the archived repository is not deletion, but it
does remove it from the paper, and IJPHM states no supplementary-material policy.
**Do not do this without my explicit sign-off.** If Phases 1–5 leave a gap, propose
specific candidates — for example per-run detail that a table summarises — with the
page saving of each, and wait.

---

## 12. Author decisions after Phase 0 (2026-09-23) — binding

- Work on branch `ijphm-shorten`; never touch `main`; do not push. Phases 1-7 run end to end,
  stopping only on a section-11 stop rule. Commit after each phase with the page count.
- Renderer: xpdf `pdftoppm`; if unavailable, report which visual checks could not be done.
- ADD G3 sentence (onset subsection): re-running the benchmark under pca1 and kurt_only leaves
  raw-lead aggregate-minus-decimate differences unchanged, max |deviation| 0.000 h across 99
  dataset x detector x indicator cells. Verify against the RG-3 files first.
- ADD D18 statement (missing-data text): at 20% missing rows Hotelling T2 collapses in 2 of 5
  draws on IMS (mean 134.9 h, range 58.0-186.1 h), driven by a single run; no chart's lead changes
  in any draw at 5%. Verify against `d18_gap_injection_multiseed.csv` first.
- M1: merge crossds + equiv + holm + imssweep + ongc. Do NOT generate per-detector gated values;
  keep the gated contrast per dataset (compact table or per-dataset block, whichever is shorter).
- M2: eleven rows, from `d9_tables_14_22_eleven.csv`. Add the one-class SVM row to tab:tradeoff
  from the D3 trade-off result file. Provenance: IMS only, invariant schema, N-20-unaffected.
- ONGC: all eleven detectors from the post-N-20 ONGC file in M1; fix Appendix D.2's "every
  detector achieves a long warning" (nine of eleven ~34-35 h, RMS-trend ~23 h, Deep SVDD not
  before failure).
- Add a verify_tables.py guard for the XJTU rows of the cross-dataset table.
- Abstract <= 280 words, keeping: the metric, the question, the +-1 h margin with its
  justification, 33 of 33 cells, Holm 0 of 44, D20 lifetime asymmetry, G4 deep-model scoping.
- Phase 4 map = `revision-artifacts/phase0/redundancy_report.md`. Priority: latch-on invalidity
  (once in 4.4 with proof, once in results), PH-vs-gated, the bounded +-1 h sentence, IMS
  +15.1 h, Holm N=44, the n=3 sign-test floor. Protected items keep their required locations.
- Phase 5: recover stranded space on pp. 25, 26, 28, 30; reduce fig:conformal height (e.g. 1x4
  strip) and apply the same discipline to fig:sweep and fig:tradeoffs, verified by rendering.
- Arithmetic: ~2 pp merges+captions, ~2 pp stranded space, ~5 pp (~4,000 words) from Phase 4.
