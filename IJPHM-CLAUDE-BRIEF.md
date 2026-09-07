# Claude Code operating brief — IJPHM revision

## Context

This repository backs a submitted journal paper: *"A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing Anomaly Detection — and What It Reveals About SCADA-Rate Logging"*, submitted to the International Journal of Prognostics and Health Management.

The editor's decision is **accepted for publication contingent on major revisions**. Reviewer D requested major revisions with another review cycle; Reviewers F and G requested minor revisions and accept once made.

**Deadline: 3 October 2026.** Two files must be uploaded into the existing submission: the revised manuscript, and a separate *"Response to Review"* document. Do not start a new submission.

The manuscript source is `paper/files/scada_ijphm.tex` — **not** `paper/scada_journal.tex`, which is a superseded IEEE version.

Two companion files sit alongside this one and are the authoritative spec:

- **`IJPHM-revision-register.md`** — all 41 reviewer items, deduplicated, each mapped to a verified location in the manuscript, with drafted replacement text and placeholders (`⟦R-n⟧`) marking every value that must come from a pipeline run.
- **`IJPHM-response-letter-draft.md`** — the scaffold for the Response to Review document.
- **`IJPHM-PROGRESS.md`** — **the session state file. Read it before anything else, every session. Update it after every completed item.**

Read the register before doing anything. This brief tells you *how* to work; the register tells you *what* to change.

## The critical fact about this task

The reviewers have this repository and its archived Zenodo snapshot. The major-revision decision was driven largely by a reviewer who cross-checked the manuscript's claims against the manuscript's own tables and found two internal contradictions. That reviewer will do the same again.

So the failure mode that matters is not an unpolished sentence. It is a number in the paper that does not reproduce from a result file in this repo.

## Non-negotiable rules

1. **Never write a number into the manuscript that you did not read from a result file in this repository.** If a value is needed and no result file contains it, write the placeholder `⟦R-n⟧` and stop. Do not estimate it, do not infer it from context, do not carry it over from the previous PDF, do not reconstruct it from a table you saw earlier in the session.
2. **Work on a branch.** Create `ijphm-r1` before the first edit. Do not commit to `main` and do not push to any remote or mint a Zenodo version — the author does that.
3. **Never edit an existing result file, cached feature file, or logged output.** New analyses write new files. If an old result looks wrong, say so; do not fix it silently.
4. **Do not retune hyperparameters, change seeds, or alter the existing detector, onset, or metric implementations.** The paper's headline results must remain bit-reproducible. New analyses are *additions*. If a new analysis appears to require changing existing code, stop and ask.
5. **Do not invent or "recall" citations.** Where the register asks for new references, insert a marked `⟦CITE: …⟧` placeholder describing what is needed. The author verifies and supplies them.
6. **Stop at every gate marked `STOP` below** and report before continuing. Do not run ahead through phases.
7. **Show a diff for every manuscript edit** before applying it. This is a paper under review; silent edits are unacceptable.
8. **Update `IJPHM-PROGRESS.md` the moment an item is finished** — not at the end of the session. Sessions end without warning on context or rate limits. An item completed but not recorded is an item that will be redone or lost. Record: the item ID, what changed, which files, and any number produced together with the result file it came from.

   > **Scope of "no edits".** Whenever an instruction says "no edits", it means **no manuscript, code, or result-file edits**. `IJPHM-PROGRESS.md` is **exempt** — updating it is required and is never blocked by a no-edit instruction. A read-only phase still ends with the progress file written.
9. **Every number that enters the manuscript is logged in the progress file's numbers ledger (§8) with its source file path**, before it is written into the `.tex`.
10. **A negative `grep` of the `.tex` is NOT evidence of absence.** LaTeX macros, math mode, and line wrapping defeat literal search. For any *occurrence sweep* — counting phrases to remove, locating claims, verifying a fix is complete — **compile the PDF, extract its text, and cross-check the counts against the source.** Reconcile any discrepancy before acting on it.

    **Reference counts — re-measured and CORRECTED, session 4.** Extracted with **PyMuPDF** from `paper/files/scada_ijphm.pdf` (25 pp., built 2026-07-08 00:50, one minute after the `.tex` was last saved, so the two correspond) and cross-checked against the source.

    | Target | **Verified count** | Was | Notes |
    |---|---:|---:|---|
    | "never better" | **3** | 3 | agrees in PDF and `.tex` |
    | "never costs" | **2** | 2 | agrees |
    | "does not cost" | **2** | 2 | agrees — **but `pdftotext` reports 1**, see below |
    | "honest" / "honestly" | **18** | 18 | PDF shows 17 until `hon-\nest` is rejoined; `.tex` gives 18 |
    | "non-destruction" | **21** | ~~20~~ | ⚠️ **corrected.** 21 in the PDF *and* 21 in the `.tex` — two independent sources agree the old 20 was one short |
    | em-dashes (rendered) | **180** | 180 | rendered count is right |
    | `---` live in `.tex` | **176** | — | prose sequences actually in the source |
    | `---` inside `.tex` comments | **54** | — | ⚠️ **not rendered.** A naive `grep -c -- '---'` returns **230** and over-reports by 54 |

    **Tooling — this is not interchangeable.**
    - **Use PyMuPDF (`fitz`), not `pdftotext`.** `pdftotext` **fails calibration**: it returns 1 for "does not cost" instead of 2, because its reading order threads a citation through that sentence and splits the phrase. PyMuPDF passes.
    - **Rejoin hyphenation as `-\n` → `-`, never `-\n` → `""`.** Deleting the hyphen destroys genuine compounds: `non-\ndestruction` becomes `nondestruction` and drops out of the count (this is what hides 2 of the 21). Some words need the opposite (`hon-\nest` → `honest`), so **check both forms** when a count comes up one short.
    - For Phase 7's em-dash target, count the **176 live** `---` or the **180 rendered**, never the raw 230.

    **These numbers are a verified FLOOR, not a ceiling.** A `.tex` grep returning fewer is a failed search, not a lower count. And because the 20 above was found to be wrong, **treat every count previously quoted from the rendered PDF as unverified — re-measure it with PyMuPDF before acting on it.** Do not carry a number from this table, or from any earlier session, into an edit decision without re-running the measurement.

    Also beware the reverse failure: piping grep through `cut`/`head` truncates long single-line paragraphs and hides real matches inside them. This manuscript stores whole paragraphs on one line — never judge a match from a truncated prefix.

## Phases

### Phase 0 — Discovery, and the one blocking question. ✅ COMPLETE (session 1)

Findings are recorded in `IJPHM-PROGRESS.md` §5 and §7. **Do not re-derive them.** The answer: no dataset coarsens the raw waveform; IMS is level (c), the other four are level (b).

A new **Phase 0.5** now precedes Phase 1 — see `IJPHM-PROGRESS.md` §9. It covers two verification items found during Phase 0, one of which (defect N-7, the validity gate under missing FAR_pre) may affect already-published numbers and blocks Phase 2 item 1.1.

<details><summary>Original Phase 0 instructions, retained for reference</summary>


Do not edit anything in this phase.

1. Map the repo: where is the LaTeX source, the sweep code, the plotting scripts, the result files, the config, the test suite? Report the layout.
2. Confirm the datasets present on disk (IMS, XJTU-SY, FEMTO/PRONOSTIA, Ferrara, ONGC) and whether the pipeline can currently run end to end.
3. **The blocking question.** Find where the sampling sweep applies the `aggregate` and `decimate` mechanisms. For **each of the five datasets**, determine which of these the code actually does:
   - (a) bin-average / decimate the **raw waveform**, then extract features;
   - (b) bin-average / decimate the **per-snapshot feature series** (one value per snapshot);
   - (c) bin-average / decimate the **windowed feature vectors** after rolling-window summarisation.

   Quote the relevant code for each. Do not generalise from one dataset's path to another — the manuscript's §3 suggests IMS may differ from the rest, and that per-dataset difference is exactly what two reviewers asked to be stated.

`STOP.` Report the answer and wait. The abstract's central claim depends on it, and register items 2.1, 3.2 and the §4.7 rewrite are all blocked on it.

</details>

### Phase 1 — Repo audit against the manuscript's claims. `STOP` at the end.

Still no edits. Two specific questions, both from the major-revision reviewer:

1. **One-class SVM.** §4.5 of the paper says one-class SVM was evaluated. No results table contains it. Does the released code produce OC-SVM results? Does any result file contain them? Answer yes or no with evidence.
2. **Deep autoencoder threshold sweep.** Table 16 (the lead-time vs false-alarm trade-off) omits LSTM-AE, TCN-AE and Transformer-AD, yet §6.1 claims they have no valid operating point "regardless of threshold". Can the existing sweep code produce those rows without modification?

Then, more broadly: list any other claim in the manuscript that you cannot trace to a result file in this repo. This is the highest-value thing you can do in this whole task.

`STOP.` Report and wait.

### Phase 2 — The seven analysis runs

Specs are in the register, Part 1. Implement each as a **new** script that writes a **new** result file, following the existing conventions for seeding, environment pinning and output format. After each run, report the numbers before touching the manuscript.

1. **1.1** — Aggregate-vs-decimate under the *gated* metric (L = 0 where FAR_pre > τ), per dataset × detector: median Δ, n₊/n₋, **tie count**, exact sign-test p, Holm across the same family. Plus valid-alarm fraction under aggregate vs decimate.
2. **1.2** — Equivalence analysis at a pre-specified margin δ. Bootstrap CIs on run-level differences (reuse the existing bootstrap: runs as the resampling unit, B=2000, seed 42), plus TOST by two one-sided exact sign tests. **Corrected session 2:** the sign test drops zero-difference runs, so the one-sided floor is `0.5^(n₊+n₋)` **per detector**, not `0.5^(bearing count)`. TOST needs n₊+n₋ ≥ 5. On XJTU that fails for five of seven detectors (3σ n=4, CUSUM n=3, Hotelling n=2), not just on IMS. Lead with the bootstrap CI; report TOST only where the non-zero count supports it, and show that count beside every result. See register 1.2.
3. **1.3** — The three deep AE rows for Table 16.
4. **1.4** — Full IMS sweep under the **original** 2004-04-08 test-3 failure label, reported side by side with the corrected label, all ten detectors.
5. **1.5** — Aggregate-vs-decimate recomputed with onset from `pca1` and from `kurt_only`; report raw-lead and gated contrasts separately. (Same run as 1.1 — do them together.)
6. **1.6** — Monte Carlo study of the onset estimator: synthetic ramp with known onset, sweep slope and noise, 1000 replicates per cell, report bias and SD. Check against the analytic prediction in the register (bias ≈ kσ_b/m + PΔt, SD ≈ σ_b/m).
7. **1.7** — OC-SVM, only if Phase 1 found it exists. Otherwise this becomes a text deletion.

Add unit tests for any new metric code, in the style of the existing suite. Keep the suite green.

### Phase 3 — Claim corrections in the manuscript

Register Part 2. These are the items that produced the major-revision decision. In order:

1. Remove the universal "decimation is never better" from all six headline locations and replace with the bounded statement naming the Isolation-Forest-on-FEMTO exception. The register lists all seven occurrences with exact phrasing and location; verify each against the source before editing.
2. Rewrite the null-acceptance claim as a bounded equivalence statement using the Phase 2.2 numbers.
3. Add the lifetime-asymmetry scoping paragraph to §8 and mirror one sentence into the abstract and conclusion.
4. Scope the deep-model no-crossover claim in the abstract and conclusion.
5. Remove all 18 self-descriptive statements. The register lists every one with its location. Delete the adjective, keep the fact.

### Phase 4 — New content

Register Part 3. Drafted text is provided for the signal-theoretic argument (§3.2) and the onset-estimator result (§1.6) — adapt it, do not paste blind, and make sure the signal-theoretic version you use matches what Phase 0 established about the coarsening level. Add the deep-model architecture table by transcribing from `config.py` verbatim. Rewrite the ONGC data-availability statement with the real file paths as they exist in the repo. Related-work additions get `⟦CITE⟧` placeholders.

### Phase 5 — Figures

Regenerate Figures 2 and 10. The defect is a character-encoding fault in the plotting scripts: `Δ`, `−`, `σ`, `≈`, `²` are being corrupted in label strings. Fix by switching those labels to matplotlib mathtext, which removes the encoding dependency entirely. Also: delete Figure 10's in-plot title (it contradicts its own caption), and fix the doubled parenthesis in Figure 2's legend (`ONGC (n=1 (case study))`).

Then render all eleven figures and check every axis label, tick label, legend entry and in-plot annotation. Only 2 and 10 are believed affected; confirm that.

### Phase 6 — Cuts and cross-references

Delete Table 21, Table 23 and §7.4; move Tables 15 and 20 to the appendix.

**Before cutting anything**, verify every table and figure uses `\label`/`\ref` rather than a hard-coded number. There are 29 tables and 11 figures; cutting two renumbers most of them. After the cuts, compile twice, grep the log for undefined references, and list every `Table N` / `Figure N` mention in the rendered PDF for the author to check in order.

### Phase 7 — Prose

Both clarity reviewers flagged sentence complexity; one scored clarity 3/Fair partly on it. The manuscript contains 180 em-dashes across 24 pages, which is the main mechanism producing the long sentences. Target under 60. One idea per sentence. Worst offenders first: §6.6's detector-listing paragraph, §6.2's "Onset under a decoupled health indicator", §4.5's Deep SVDD paragraph, §6.13's Deep SVDD failure-mode paragraph, and the introduction's "Method" paragraph.

Do this **after** all content is settled, not before.

### Phase 8 — Verification

Run the full checklist in Part 6 of the register. In particular:

- `grep` the source for `⟦`, `TODO`, `XXX`, `??` — zero hits.
- `grep -i "never\|always\|every dataset\|all detectors"` in abstract, introduction, discussion, conclusion — every hit individually justified.
- The coarsening statement from Phase 0 must read identically in abstract, introduction, §4.7 and conclusion.
- Re-read the abstract and introduction against Tables 7, 8, 9, 10 and 11 specifically. That is the exact check that produced the major-revision decision.

Then fill in the response letter scaffold, marking clearly anything you could not complete.

## Things to escalate rather than decide

Stop and ask the author on any of these:

- Phase 0 finds coarsening is at the feature level, which would narrow the paper's central claim.
- Any existing result fails to reproduce.
- A new analysis contradicts a published result in the paper.
- OC-SVM turns out not to exist in the repo (the fix is a deletion, but the author should confirm).
- The equivalence margin δ — propose, do not assume.
- Anything requiring a change to existing detector, onset or metric code.