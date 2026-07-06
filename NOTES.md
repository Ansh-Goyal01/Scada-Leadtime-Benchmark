# NOTES — flagged decisions & ambiguities (IJPHM reframe)

Nothing here is a numeric change. These are judgment calls, deviations, and things the
user should be aware of. No number in the paper was left un-sourced.

## 1. Deep SVDD demotion — Option B (confirmed with user)
STEP 6 says "remove Deep SVDD rows from main-body tables." I demoted it from the
**headline count** (now nine) and added the requested appendix note + FEMTO caveat, but I
**kept Deep SVDD's released numbers in every result table** instead of deleting/relocating
them. Reason: in the trade-off (`tab:tradeoff`), FAR-budget (`tab:farsens`) and PH-ranking
(`tab:phrank`) tables, Deep SVDD is the paper's near-zero-false-alarm deployable operating
point (14.8 h at <=0.6 % pre-onset FAR; at tau=0.05 the only within-budget detector besides
the naive RMS-trend). Stripping it would push the strict-budget recommendation onto the
naive baseline — weakening a genuine result and conflicting with the ABSOLUTE RULES ("do
not weaken … preserve honesty"). This is the one place the reframe departs from a literal
reading of STEP 6; it is the "best for the paper" choice you approved. If you instead want
Deep SVDD physically stripped from the trade-off tables, say so and I'll do the row-moves
and rewrite the strict-budget recommendation prose.

## 2. `paper/` is gitignored — commit & baseline implications
`.gitignore:42` is `paper/` ("kept local for now, not published"), so `paper/scada_journal.tex`
was **never committed**. Consequences:
- **STEP-14 `git diff --word-diff` is not applicable** (no HEAD baseline). The equivalent,
  stronger proof is the transform's row-integrity gate, which ran against the true original
  bytes and confirmed **273/273** table data rows byte-identical. See CHANGES.md section 2.
- **Committing the reframe requires `git add -f`.** I committed the deliverables to the
  `ijphm-reframe` branch with a forced add of the paper files, and did **not merge to main**
  and did **not push** — because "kept local / not published" conflicts with a normal push.
  **Decision for you:** if you want this pushed to `origin/ijphm-reframe`, tell me; I left it
  local so the paper isn't published against the `.gitignore` intent.
- The pre-existing working-tree changes in `src/` (`config.py`, `datasets.py`,
  `stats_rigor.py`, `feature_coarsening_ablation.py`, `loaders/`, `training_sweep.py`) and
  the modified `.gitignore` were present at session start and are **unrelated to the reframe**;
  I did not touch or commit them.

## 3. New floats are provenance-clean (no new experimental numbers)
- `tab:taustar_grid` (STEP 10): every cell is tau*=rho/k clipped to [0,1], computed directly
  from Eq. (6); k,rho in {1e2,1e3,1e4}. Nothing experimental.
- `fig:farbudget` (STEP 11): plots only the values already in Table XVII (`tab:farsens`) at
  the three budgets tau in {0.05,0.10,0.20} it already reports. No intermediate tau invented.
  Generator: `paper/make_far_budget_fig.py` (values hardcoded verbatim from the table so the
  figure cannot diverge from it).

## 4. `sec:mechanism` label
The mechanism block moved to Appendix D. All `\ref{sec:mechanism}` usages were replaced with
the literal text "Appendix D" (a starred appendix has no reliable section number). The
`\label{sec:mechanism}` is retained on the Appendix D header but is now unused — harmless,
kept only as a safety anchor. Log confirms no undefined reference.

## 5. In-table "ten detectors" wording
A few table captions (e.g. `tab:femto_paired`, `tab:ims_ci`) still say "ten detectors" /
"all ten" because that accurately describes the number of rows in those tables (the full
evaluated set). This is reconciled with the "nine headline" framing by the detector-list
note and the Holm caption footnote, both of which state that the full evaluated set is ten
= nine headline + the additionally-evaluated Deep SVDD. Not a numeric change.

## 6. `fig:cross` (Fig. 3) unchanged
Per STEP 5, ONGC is kept in the cross-dataset figure because its bars are already
hatched/separated to mark the n=1 case study (stated in the figure caption). The figure and
its caption were left intact (no numbers/labels changed).

## 7. Minor
- "eight minutes" appears once in the abstract but greps as 0 tokens only because it wraps
  across a line break in the source — the phrase (pre-existing) is present.
- The compile emits routine underfull/overfull `\hbox`/`\vbox` warnings (typographic only)
  and `TU/ptm` font-shape warnings (tectonic substituting Times shapes); neither affects
  correctness, references, or the 23-page output.
