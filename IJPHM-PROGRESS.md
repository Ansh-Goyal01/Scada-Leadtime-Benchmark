# IJPHM REVISION — PROGRESS TRACKER

> **READ THIS FILE FIRST, BEFORE ANY OTHER FILE, AT THE START OF EVERY SESSION.**
> It is the single source of truth for what is done, what is not, and what is blocked.
> **UPDATE IT AFTER EVERY COMPLETED ITEM** — not at the end of a session. A session can
> end without warning (context limit, rate limit, crash). If an item is finished and not
> recorded here, it will be redone or lost.

---

## 0. ✅ MANUSCRIPT UNFROZEN — CLAUDE OWNS THE `.tex` AGAIN (2026-09-17, session 6)

> **The external-revision handoff of 2026-09-09 is CANCELLED.** `paper/files/scada_ijphm.tex` is
> no longer frozen. The freeze commit `8e619e3` stays in history as a diff anchor only.
>
> **New division of labour (author instruction, session 6):**
>
> | Who | Does what |
> |---|---|
> | **Claude (in repo)** | **Owns the `.tex`** and all mechanical work: cuts, merges, abbreviations, figure regeneration, compilation (`tools/tectonic.exe`), verification (PyMuPDF sweep) |
> | **Author (outside)** | Drafts **prose blocks** and hands them over **as text to insert**. Insert them verbatim; do not rewrite them |
>
> **All brief rules still apply**, including rule 6 (show a diff before every manuscript edit) and
> **rule 10 (a negative search proves nothing)**. **Rule 10 now also covers tool-presence checks:**
> probe the filesystem before concluding that a tool is absent (see the toolchain note below).
> Rule 7 stands: record every completed item here immediately.
>
> *Superseded (kept for history): the 2026-09-09 freeze, which limited the in-repo role to
> figures, measurements, rebuilds and sweeps, and expected the `.tex` back as complete
> replacement files. The "Replacement-landing checklist" below is retained. Steps 2–5 of it are
> still the right verification after any manuscript edit pass.*

### ✅ Build toolchain: `tools/tectonic.exe` (corrected 2026-09-09)

**The build engine is `tools/tectonic.exe`, Tectonic 0.16.9, committed in-repo. No MiKTeX or
TeX Live install is needed. Job 3 is NOT blocked.**

⚠️ **Correction — do not repeat this mistake.** An earlier note in this section claimed no TeX
engine existed, based on `command -v pdflatex/xelatex/lualatex/latexmk/tectonic` returning
nothing in both shells. **That was a false negative.** `command -v` searches `PATH` only, and
`tools/tectonic.exe` is a repo-local binary that is not on `PATH`. Always probe the filesystem
directly (`ls tools/`, `find . -iname '*tectonic*'`) before concluding a tool is missing — the
same "a negative search proves nothing" logic as brief rule 10, applied to executables instead
of manuscript strings.

Corroborating evidence that tectonic is the engine: the last build log records
`Output written on scada_ijphm.xdv`, and tectonic wraps **XeTeX**, whose native output is
`.xdv`. A plain-`pdflatex` build would not produce an `.xdv` at all.

Build inputs (verified complete, 2026-09-09): `PHMSociety.cls`, `ijphm.bib`, and **11** `.png`
figures in `paper/files/` — 11 files on disk, 11 `\includegraphics` calls in the frozen `.tex`,
each referenced exactly once. No orphans, none missing. (An earlier draft of this section said
12 figures; the correct count is 11.)

`tools/paper/build/` exists but is **empty** — no prior build artifact survives there, so the
"26 pages" from an earlier tectonic run cannot be re-verified without recompiling. Treat page
count as unmeasured until the next build.

### Freeze baseline — what "the frozen file" precisely is

| | |
|---|---|
| **Frozen file** | `paper/files/scada_ijphm.tex` |
| **Lines at freeze** | 1160 |
| **SHA-256 at freeze** | `a2e498de76c115cb455b4614c92fa64ec0067f9980cd5f6923dedfa294cd7454` |
| **Git state at freeze** | ✅ **COMMITTED** as `8e619e3` on `ijphm-r1` (2026-09-09) — *"chore: freeze manuscript at external-revision handoff (SHA a2e498de)"*. Was `d2ec5d6` + 34/4 uncommitted; author authorised the baseline commit. |
| **Exported for upload** | `scada_ijphm_current.tex` (repo root) — `cmp`-verified byte-identical |
| **Last successful build** | 2026-09-19, **24 pages** (tectonic 0.16.9, counted from the PDF page tree). The 2026-07-08 "25 pages" came from a frozen XeLaTeX `.log`; tectonic writes no `.log`, so that file never updated. Do **not** grep the `.log`. |

✅ **Resolved 2026-09-09.** The baseline is now committed as `8e619e3`, so the freeze point is
recoverable and there is an exact diff anchor for every incoming replacement. The commit captured
session 4's FWER `≈ 0.90` fix (`tex:510`), the `tab:d17label` D-17 original-label table and its
three surrounding paragraphs (`tex:1051+`), the `tab:farbudget` mean-vs-per-run gate caption, the
`tab:missing` valid-fraction caption, and the empty-pre-onset-region clause at `tex:216` — all of
which had existed only in the working tree.

Post-commit verification: working-tree `sha256sum` **and** the stored blob
(`git cat-file blob HEAD:paper/files/scada_ijphm.tex`) both hash to `a2e498de…cd7454`. Content
unchanged by the commit, as required by the freeze.

⚠️ **SHA-verification caveat.** `core.autocrlf=true` and there is no `.gitattributes`. The blob is
stored LF, but a fresh `git checkout` writes **CRLF** to the working tree, which yields a
*different* `sha256sum` for semantically identical content. When re-verifying the freeze, hash the
**blob** (`git cat-file blob …`), not the working file, or a false mismatch will look like
tampering.

`scada_ijphm_current.tex` was exported byte-identical **after** those edits, so whatever the author
uploaded externally does include them — the external revision is not working from a stale base.

### Replacement-landing checklist (run on every incoming `.tex`)

1. `sha256` + `wc -l` the incoming file; diff it against the frozen baseline and **report the
   diff before committing** — replacement files are committed, but never blind.
2. Confirm no `⟦R-n⟧` / `⟦CITE: …⟧` placeholders survived (rule 1, rule 5).
3. Rebuild with `tools/tectonic.exe` (see toolchain note above).
4. PyMuPDF-sweep the PDF. Rule 10 reference counts, verified on the 2026-07-08 build:
   "never better" ×3 · "never costs" ×2 · "does not cost" ×2 · "honest"/"honestly" ×18 ·
   "non-destruction" ×20 · em-dashes ×180. **Re-baseline these on the first new build** — they
   are two months and five commits stale.
5. Record the outcome here immediately (rule 7).

---

## 1. Status snapshot

| | |
|---|---|
| **Paper** | *A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing Anomaly Detection — and What It Reveals About SCADA-Rate Logging* |
| **Venue** | International Journal of Prognostics and Health Management (IJPHM) |
| **Decision** | **Accepted for publication contingent on major revisions** (5 Sep 2026) |
| **Reviewers** | D — major revisions, another cycle · F — minor · G — minor |
| **Deadline** | **3 October 2026** |
| **Deliverables** | (1) revised manuscript, (2) separate *"Response to Review"* document. Upload into the **existing** submission — do not start a new one. |
| **Manuscript source** | `paper/files/scada_ijphm.tex` (1160 lines) — ✅ **UNFROZEN 2026-09-17, Claude owns it (§0)** — **not** `paper/scada_journal.tex`, which is the superseded IEEE version |
| **Branch** | `ijphm-r1` — ✅ created and checked out |
| **Current phase** | Phase 0 ✅ · Phase 0.5**(A)** ✅ · Phase 0.5**(B)** ✅ **corrected session 3** · D-2 cascade measured (§5C) · **Reviewer D run items D2/D3/D15/D17 ✅ session 4 (§5G)** · remaining Phase 1 audit ⬜ · **⛔ manuscript FROZEN — in-repo role is now figures / measurements / rebuild+sweep only (§0)** |
| **Last updated** | 2026-09-17 — session 6 (unfrozen; RF-2 + RG-3 done; results preserved, §5O) |

### Companion files
- `IJPHM-CLAUDE-BRIEF.md` — standing rules and phase plan. Rules are non-negotiable.
- `IJPHM-revision-register.md` — full spec for all 41 reviewer items, with drafted text.
- `IJPHM-response-letter-draft.md` — scaffold for the Response to Review document.

---

## 2. The rules, condensed (full versions in the brief)

1. **Never write a number into the manuscript that was not read from a result file in this repo.** No estimating, no inferring, no carrying over from the old PDF. If a number is needed and no file has it, leave `⟦R-n⟧` and stop.
2. Work on branch `ijphm-r1`. Never commit to `main`, never push, never mint a Zenodo version.
3. Never edit an existing result file, cache, or logged output. New analyses write new files.
4. Never retune hyperparameters, change seeds, or alter existing detector / onset / metric code without explicit sign-off.
5. Never invent citations. Use `⟦CITE: …⟧` placeholders.
6. Stop at every gate. Show a diff before every manuscript edit.
7. **Record every completed item in this file immediately.** A "no edits" instruction **never** covers this file — "no edits" means no manuscript, code, or result-file edits. This file is exempt; a read-only phase still ends with it written.
8. **Sweep the CONCEPT, not one phrase** (session 6): list the paraphrases of a claim first, then search each in the `.tex` and the PyMuPDF text (brief rule 10 extension). Tool presence: probe the filesystem, not only `PATH`.
9. **A negative `grep` of the `.tex` proves nothing.** Macros, math mode and line wrapping defeat literal search; and truncating grep output (`cut`, `head`) hides matches inside this manuscript's very long single-line paragraphs. For any occurrence sweep, **compile the PDF, extract its text, cross-check against the source, and reconcile before acting.** Verified PDF counts: "never better" ×3 · "never costs" ×2 · "does not cost" ×2 · "honest"/"honestly" ×18 · "non-destruction" ×20 · em-dashes ×180. Fewer than these from a `.tex` grep = failed search. Full rule: brief rule 10.

---

## 3. Session log — append only, newest last

### Session 1 — 2026-09-05
- Phase 0 executed. Repo mapped, all five datasets confirmed on disk, pipeline reproduces committed values (XJTU Bearing1_3 smoke test matched `benchmark_XJTU-SY_long.csv` to the digit).
- **Blocking question answered** — see §5 below.
- 9 additional defects found — see §7 below.
- No edits made. No branch created. `main` untouched.
- Test suite: 92 pass, 1 fail (`test_diagnostic_console.py::test_metropt_loads_with_expected_parameters` — MetroPT air-compressor dataset, touches no paper number; benign).

### Session 2 — 2026-09-05
- **Phase 0.5(A) executed and complete.** Findings in §5A below — do not re-derive.
- N-7 resolved: the FAR gate is *skipped by design* when `FAR_pre` is NaN. 295 rows across the corpus carry a valid alarm that was never gated. Published counts reproduce exactly but do not match Eq. 5 as written.
- New defects **N-10**, **N-11**, **N-12** (N-12 High — `Bearing1_2` legacy-metric substitution).
- Author decisions taken: **D-7 DECIDED** (three-outcome validity) and **D-8 DECIDED** (no-onset fallback is a correctness bug; code change signed off, scoped to that branch).
- Register item 1.2 arithmetic corrected — TOST floor is per-detector `0.5^(n₊+n₋)`, not `0.5^(bearing count)`. Same error fixed in the brief's Phase 2 list. **N-6 superseded.**
- No manuscript, code, or result-file edits. No branch created. `main` untouched.
- File renamed `IJPHM-progess.md` → **`IJPHM-PROGRESS.md`**; references updated in the brief and register.
- **New brief rule 10** (mirrored as condensed rule 8 above): a negative `.tex` grep is not evidence of absence — compile the PDF and cross-check. Prompted by a real miss this session, recorded in §5A.4.
- **Phase 0.5(B) executed and complete.** Findings §5B. New file `results/tables/benchmark_IMS_long_invariant.csv` (300 rows). Code: `feature_mode` added to `load_pipeline_controlled` + `run_benchmark` (default `"legacy"`, published path verified reproducible); new runner `src/ims_schema_check.py`. **D-2 measured but still open** — direction survives, magnitude does not.
- New defect **N-13** (console cp1252 encoding crashes released scripts on Windows — same root cause as the Figure 2/10 mojibake).
- Test suite re-run after the code change: **only failure is the pre-existing N-9** (`test_metropt_loads_with_expected_parameters`, `assert 'real' == 'fixture'`). No new failures, 1 skip.

### Session 3 — 2026-09-05
- **Two corrections and one new measurement, per author instruction. No manuscript, code-path, or result-file edits; `main` untouched; no branch created.**
- **CORRECTION 1 — §5B recomputed under the paper's own convention.** Session 2 collapsed factors by the **median** and reported a **pooled 15-pair Wilcoxon**; §4.8 (`tex:252`) and Table 10's caption (`tex:491`) specify the **mean**, and §4.8 explicitly disavows the pooled test. New `src/d2_convention_recompute.py`. **Legacy column reproduces published Table 10 exactly** (all 10 detectors, all 3 per-run diffs, all medians, all p) and the **N=40 Holm family reproduces** (smallest raw p 0.031 FEMTO/IsoForest, Holm 1.000, 0/40). Corroborated by `results/tables/ims_runlevel_test.csv`. **No separate defect — the pipeline is sound, the session-2 comparison script was not.**
- **The corrected result reverses session 2's conclusion.** Sign-consistency does **not** survive the schema change: 3σ, EWMA and Iso. Forest each flip one run negative. `tex:480` ("in no run does aggregation shorten their lead time") and the abstract's "consistent positive trend" become false as written. 3σ median +18.4 → **+15.1 h**. Holm verdict unchanged (0/40). §5B.2/5B.3/5B.4 struck through and marked superseded.
- **CORRECTION 2 — N-14 logged, severity High.** D-2 is not only a robustness question: if IMS ran at 445 dims, §4.2 does not describe the headline dataset — same class as §4.7, which Reviewer D has flagged three times. §5B.0.3.
- **NEW MEASUREMENT — D-2 cascade quantified, §5C.** New `src/d2_cascade_audit.py` (read-only). Structural bound found: the legacy schema is reachable **only** via `load_pipeline_controlled` (`sampling.py:365`), called from only `benchmark.py:164` and `sampling.py:547`; every other IMS analysis uses `load_pipeline` → `FEATURES["mode"]="invariant"` and is already on the endorsed schema. **Onset verified schema-independent: `t_onset`/`t_fail`/`max_lead_hours` identical on 300/300 paired rows.** Result: **11 artifacts move, 17 do not, 2 need a rerun.**
- **New defect N-15 (High), found while regenerating Table 5** — the published 3σ valid-alarm fraction of **1.00 at every persistence** does not reproduce; the released data give **0.67** under every denominator and both schemas. `persistence_sensitivity_IMS.csv` has **no generating script in the repo**. Schema-independent, so it is not a D-2 consequence.
- Ledger: **R-13 corrected**, **R-14** and **R-15** added.

### Session 3 (continued) — D-2 DECIDED, route (b), executed
- **D-2 decided by the author: re-baseline IMS onto the invariant schema.** Rationale recorded in §4. Brief rule 4 sign-off granted, scoped to the IMS controlled-sweep path.
- **Code change** (§5F.1): `feature_mode` default `"legacy"` → `"config"` on `load_pipeline_controlled` and `run_benchmark`, so `FEATURES["mode"]` governs. Legacy path kept reachable and **now tested for the first time** — new `tests/test_feature_mode.py`, 7 tests, all pass, including that legacy still yields 445 dims with p > n and that downsampling geometry is schema-independent. Suite: 99 pass, 1 skip, 1 pre-existing benign failure (N-9); **no new failures**.
- **N-15 FIXED** (§5D). Wrote the missing generator `src/persistence_sweep_ims.py`; regenerated Table 5 at persistence {1,3,5,10} → `persistence_sensitivity_IMS_invariant.csv`. **The published "3σ valid-alarm fraction = 1.00 at every persistence" is not reproduced — it is 0.67**, and was 0.67 in the originally released data too. **§6.2's conclusion does NOT survive**: validity falls 0.67 → 0.33 across coarsening factors as persistence goes 1 → 10, and the sign-consistency claim fails for 3σ (p=3) and EWMA (p=1,3,5). Three separate sentences at `tex:357` must be rewritten.
- **All 11 changed artifacts regenerated** (§5F.2) using the repo's own generators; two independent §4.8 implementations agree to the digit. Published files deliberately **not** overwritten (N-3: `results/` is gitignored).
- **Claim-delta inventory produced** (§5E): 18 prose claims, Tables 2/5/10/11/25, Figures 2/3, with old value, new value and `.tex` line number. Explicit "unchanged" list for the response letter.
- **Legacy-schema control run for N-15** (§5D.2b): the new generator reproduces the published Table 5's **three median rows to the digit** on the legacy schema but returns **0.67, not 1.00**, for the valid-alarm row. This isolates the defect to that one column and rules out schema, convention, and generator error — and validates the generator as authentic. **Correction applied to §5D.3 and §5E rows P12/P13:** the sign-consistency and Isolation-Forest sentences were **correct as published** and break only under D-2; only the 1.00 valid-fraction claim is an authoring defect. An earlier version of §5D.3 ran the two together.
- **Table 25 timings delivered** (§5E.7): first pass was contaminated by CPU contention and was deleted; redone as a **paired legacy→invariant run on an idle machine**, 5 repeats each. Invariant is faster on every detector — SPC inference 2.5–13.8×, Hotelling T² training 13.1×, Iso. Forest only 1.1–1.2×. **Report the ratio, not the absolutes**: this machine runs the legacy pass 4–13× slower than the published column, which is hardware, not schema.
- **Register annotated**: items **2.1** and **2.2** marked partly stale. 2.2's cited "medians of 4.6–18.4 h" → **1.2–15.1 h**, and its "could not have been observed" argument must be re-based on the upper end only, since a 1.2 h effect *is* observable on a 6.8 h bearing.

### Session 4 — 2026-09-06 — Reviewer D run-dependent items (D2, D3, D15, D17)

Branch `ijphm-r1` (already created, checked out). **No manuscript edit made.** Every run wrote
a new result file; no published result file was modified. Findings in **§5G**.

- **D15** ✅ equivalence evidence at δ = 1 h — `src/d15_equivalence.py` → `d15_equivalence_bootstrap.csv`, `d15_equivalence_tost.csv`. Equivalence established on XJTU-SY, FEMTO, Ferrara (30/30 cells); **not** established on IMS under either schema. §5G.1, ledger R-2.
- **D2** ✅ deep models in the Table 16 sweep — `src/d2_deep_tradeoff.py` → `tradeoff_IMS_deepmodels{,_long}.csv`. ⚠️ **`tex:275`'s "regardless of threshold" is FALSE**: LSTM-AE attains a valid operating point at the 99.5th percentile on `3rd_test`. New defect **N-16**. §5G.2, ledger R-3.
- **D3** ✅ one-class SVM — **answer is YES, the released code produces OC-SVM results.** Detector implemented at `models.py:378`, dispatched at `:623`, configured at `config.py:166`, listed in `benchmark.py:50`'s `_DETERMINISTIC`; absent only from `EXPERIMENT["methods_to_run"]`. So §4.5's clause is **runnable, not fabricated** — the fix is a run, not the deletion D-5 assumed. Runner `src/d3_ocsvm.py`. §5G.3, ledger R-7.
- **D17** ✅ original 2004-04-08 test-3 label — `src/d17_original_label.py`, label patched **in memory** (context manager), `config.py` untouched. **No median flips sign; best p = 0.25 under both labels.** Test 3 is a guaranteed miss for **6 of 10** detectors, not all ten — the register's pre-written anticipation is wrong and must be rewritten. §5G.4, ledger R-4.

**Session 4 continued — D-4/D-5/D-9 decided, three follow-ups done:**
- **Seed check** ✅ `src/d2_seed_check.py` — N-16 holds at **10/10 seeds**, FAR 4.19% every time,
  despite training loss varying 0.0027–0.0040. **Not a seed artifact**; caveat discharged. §5G.2.
- **N=40 → N=44 inventory** ✅ **§5H** — **16 atomic edits** (not the ~8 estimated), reconciled
  PDF 16 = tex 16. `pdftotext` fails calibration; **use PyMuPDF**. Brief rule 10 corrected.
- **Consolidated claim-delta inventory** ✅ **§5I** — collision sentences given combined
  requirements (`tex:275` carries four drivers).
- **D-9 rebuild** ✅ **§5J** — Tables 14/22 at eleven detectors. **§6.9's 3σ recommendation HOLDS.**
  LSTM-AE attains **no** valid point in Table 14 at any τ (mean FAR 62.00%) — consistent with N-16,
  which is a per-run/per-threshold claim.
- **Table 25 completion** ✅ **§5K** — OC-SVM and RMS-trend timed; **new defect N-17**; deep-model
  parameter counts captured for G5 (ledger R-8).

**Result-file families written this session, no published file touched** (verified by mtime):
`d15_equivalence_*` (2), `tradeoff_IMS_deepmodels*` (2), `d3_ocsvm_*` (7), `d17_*` (2),
`d2_seed_check_lstmae.csv`, `d9_tables_14_22_eleven.csv`, `compute_cost_IMS_extra_invariant.csv`,
`deep_model_params.csv` — **17 files**.

**Every remaining Reviewer D item is text-only; the author drafts them.**

**Verification done before trusting the baselines:** published Table 16 reproduces to the digit
from `tradeoff_IMS.csv`; the register's worked XJTU n₊/n₋ counts reproduce exactly from
`run_level_diffs`. **N-13 confirmed live** — `pd.read_csv` + `print` of any detector name crashes
with `UnicodeEncodeError` on the default Windows console; every new script carries the
`sys.stdout.reconfigure` guard.

---

### Session 6 — 2026-09-17 — UNFREEZE; RF-2 + RG-3; results preservation

- **Manuscript UNFROZEN** (author instruction). Claude owns the `.tex`; prose arrives as text to insert. §0 rewritten, memory updated.
- **RF-2 (1.1) and RG-3 (1.5) done in one pass**, §5O. New result files only; no published file or manuscript touched.
- **Preservation:** N-3 negation in `.gitignore`; all result files committed; D-2 code (`d873e58`) and 15 revision scripts (`960f711`) committed. §5O.5.
- **Session 6b:** paired validity (§5O.6); **N-20 found (High, open)**; N-21 (Table 4 = 4th orphan); **D-2 re-baseline applied to the manuscript + Table 11 at 44 rows** (§5O.9, `20658e5`, `6bb3f74`).
- **Session 6e:** **cuts batch** (§5O.12): A 26 → 25 pp (`7397708`), B 25 → 25 pp (`8d7fd10`); D-2 residue `fb34a96`.
- **Session 6d:** **N-20 manuscript pass applied** (§5O.11, `394cd96`): 81 cells, exception removed at 6 sites (concept-swept), Figure 2 regenerated (+ ONGC ÷60 bug), D-2 residue at 398/929/956/516; D19 response rewritten; brief rule 10 extended.
- **Session 6c:** **D-10 authorised; N-20 fixed** (`src/__init__.py`), IMS and XJTU-SY verified unchanged, FEMTO/Ferrara/ONGC re-run and propagated (§5O.10). No manuscript edit.
- **New findings for the manuscript pass:** Tables 10/11 still carry legacy IMS values (D-2 swap not applied); Table 11 has 40 rows under an N=44 caption; Table 4 had no generator (now reproduced); the gated IMS contrast is onset-dependent.

## 4. Open decisions awaiting the author

| # | Decision | Status | Author's answer |
|---|---|---|---|
| D-1 | Accept the narrowed claim (historian-rate aggregation of **summary statistics**), rather than running a new raw-waveform experiment | ✅ **decided** | **Accept the narrowing.** Do not run raw-waveform coarsening. Reframe as a distinction between two operations, lead the claim from ONGC (where its channels *are* the historian record, so no simulation gap exists), and list raw-waveform coarsening as future work. |
| D-2 | IMS path asymmetry — level (c) and 445-dim legacy schema, versus level (b) and 49-dim invariant elsewhere | ✅ **DECIDED — route (b): re-baseline IMS onto the invariant schema** (session 3) | **Author's rationale:** under the paper's own §4.8 convention, sign-consistency does **not** survive the schema change on **any of the three trend-carrying detectors**, so the only directional claim in the paper exists **solely under the 445-dim schema that §4.2 argues is ill-posed**. Reporting it from that schema is **indefensible in a second review round** (defect **N-14**). The Holm verdict is unchanged at **0/40 under both schemas**, so the **non-destruction headline — the paper's actual conclusion — is unaffected**. The cascade is bounded at **11 artifacts**, mostly regenerable from the existing invariant CSV. **Sign-off (brief rule 4):** may change existing code and regenerate published result files, **scoped to the IMS controlled-sweep path only**; `FEATURES["mode"]` governs `load_pipeline_controlled` instead of defaulting to legacy; **the legacy path stays reachable and tested** so the published numbers remain reproducible for the response letter. Prior "awaiting decision" record: | **Session-2 measurement was computed under the wrong convention and its conclusion is reversed — see §5B.0.** Under the paper's own protocol (mean collapse, run-level sign test, Holm): **sign-consistency does NOT survive** — 3σ, EWMA and Iso. Forest each flip one run negative, so `tex:480`'s "in no run does aggregation shorten their lead time" and the abstract's "consistent positive trend" become false as written. 3σ median +18.4 → **+15.1 h**. Holm verdict unchanged (0/40 either way). **Cascade measured, §5C: 11 artifacts move, 17 do not, 2 need a rerun.** Also now carries **N-14 (High)** — this is not only a robustness question: if IMS ran at 445 dims, §4.2 does not describe the headline dataset. Nothing swapped in. **The call is still open.** |
| D-3 | What the Zenodo archive actually contains | ⬜ **open** | Author to check the live Zenodo record. Blocks the ⟦R-n⟧ verification premise and the Data Availability statement. |
| D-4 | Equivalence margin δ (proposed: 1 h, on maintenance-planning grounds) | ✅ **DECIDED — δ = 1 h CONFIRMED** (session 4) | **Author confirmed δ = 1 h.** Margin was pre-specified on operational grounds (a maintenance planner cannot act on sub-hour differences in warning time — mobilising a crew, ordering parts) and fixed **before** any result was read; state that ordering explicitly in the manuscript. Results computed at this margin in §5G.1 / ledger R-2. Equivalence established on XJTU-SY, FEMTO and Ferrara (30/30 cells); established on **no** IMS cell under either schema; ONGC untestable at n=1. |
| D-5 | One-class SVM: report or delete | ✅ **DECIDED — REPORT** (session 4) | **The "delete the §4.5 clause" option was predicated on the detector not existing. It does** — `models.py:378` + `:623` + `config.py:166`; absent only from `methods_to_run`. **Author's decision: REPORT OC-SVM, in the "additionally evaluated" tier alongside Deep SVDD** (`tex:235`), which **makes §4.5's existing claim true rather than requiring deletion**. **Author's rationale, CORRECTED session 4 after D-9:** the rationale as first recorded said OC-SVM ranks **first on PH**. That held only against Table 22's *then-current* seven-row set (180.2 > Hotelling's 176.9). Under **D-9** the deep rows join Tables 14 and 22, so the accurate statement is: **OC-SVM ranks first among the non-deep detectors on PH, fourth overall of eleven** (behind LSTM-AE 199.6, TCN-AE 185.4, Transformer-AD 184.0), **and last-equal on gated L (0.0)**. **The inversion argument is strengthened, not weakened** — and it is **SEVEN-way, not four-way**: measured in §5J, **the top seven detectors by PH all score L = 0**, and the deployable chart **3σ ranks EIGHTH of eleven on PH while ranking FIRST on L**. (The published seven-row Table 22 is only a three-way inversion with 3σ 4th.) Statistically free: Holm recomputed at **N=44 → 0/44 rejections**, verdict and non-destruction headline unchanged. Numbers in §5G.3 / ledger R-7. **Consequence:** the family size changes 40 → 44 in **every** location — full inventory §5H. |
| D-6 | Template check — the editor's letter says "PHM Conference Paper template" but this is the journal; the source uses `\documentclass[IJPHM,2026,0]{PHMSociety}` | ⬜ open | Verify against the IJPHM author guidelines; query the editor if ambiguous. |
| D-7 | How validity is defined when `FAR_pre` is undefined (N-7) — strict Eq. 5, documented carve-out, or exclusion | ✅ **decided** | **Three-outcome validity: valid / invalid / unscoreable.** *Unscoreable* = pre-onset region empty, `FAR_pre` undefined. Unscoreable rows are **excluded from validity denominators** and reported explicitly. **Amend Eq. 5** in the manuscript to define this. **AND** report the strict-convention figures alongside (unscoreable counted as invalid), because a reviewer running Eq. 5 literally against the released CSVs lands on 73/450 — that number must appear in the paper. |
| D-8 | `Bearing1_2` no-onset fallback — documentation gap or correctness bug | ✅ **decided** | **Correctness bug.** The fallback must stop writing legacy FAR into `far_preonset_pct` and legacy VLT into `valid_alarm` under onset-relative column names. **Emit NaN plus an explicit `no_onset` flag instead.** `Bearing1_2` is **unscoreable for all onset-relative quantities** and comes out of Table 12's validity columns with a stated flag. Its **raw lead-time contribution to Tables 7 and 11 is unaffected and stays.** Requires changing existing metric code — **brief rule 4 sign-off granted, scoped to this fallback branch only** (`src/lead_time.py:234-240` and the `benchmark.py:130` warning). |
| D-10 | N-20: fix the aggregation resampling target so aggregate and decimate land on the same effective logging interval | ✅ **AUTHORISED (session 6, rule-4 sign-off)** | **Scope:** `src/__init__.py:207` and anything strictly required to make aggregate and decimate land on the same effective interval at the same nominal factor. **Not** detector, onset or metric code, seeds, or hyperparameters. **Fix:** resample at native spacing × factor in the native unit (seconds when sub-minute) instead of rounding to whole minutes. **Author's rationale:** §4.7 states the controlled sweep holds everything constant so that only the effective logging interval varies, isolating information loss from the window-counting confound. On FEMTO, Ferrara and ONGC it does not: the minute-rounding floor coarsens aggregate harder than decimate at the same factor. That is a defect in the exact mechanism the paper claims to have eliminated, so it cannot ship. **Mandatory check:** IMS (600 s native) and XJTU-SY (60 s native) must reproduce byte-identically; if either moves, stop. Then rerun FEMTO/Ferrara/ONGC and report before any manuscript edit. **Add N-20 to the Response to Review disclosure list** (with N-15, N-17, N-18, N-21). |
| D-9 | Do Tables 14 (`tab:farbudget`) and 22 (`tab:phrank`) gain the three deep reconstruction rows and one-class SVM, alongside Table 16? *(The author labelled this "D-6"; **D-6 is already in use** for the template check, which remains open — recorded as D-9 to keep the register unambiguous.)* | ✅ **DECIDED — YES, both tables gain all four rows** (session 4) | **Author's rationale:** the **four-way inversion is a stronger demonstration of §6.12's thesis** than the single-detector version — **the top SEVEN detectors by prognostic horizon all score L = 0**, and the deployable choice **3σ ranks EIGHTH of eleven on PH while ranking FIRST on L** — a seven-way inversion. *(The rationale as first stated said "top four … ranks fifth"; the rebuild in §5J measured **seven / eighth**. The decision is unaffected and the demonstration is stronger. **Use seven-way / eighth everywhere, including the Response to Review.**)* **Consistency also requires it**: D2 puts the deep models in Table 16, and Tables 14, 16 and 22 all draw on the **same trade-off data**, so a detector present in one must be present in all three. Rebuilt tables in §5J. |

---

## 5. Phase 0 findings — RESOLVED, do not re-derive

**The blocking question is answered. No dataset coarsens the raw waveform.**

Every loader funnels through `_snapshot_stats` (`src/datasets.py:147-164`), which collapses each waveform block to six scalars per channel at **ingest**, cached to parquet. `RunBundle.snapshot_df` — the only thing the sweep ever sees — is already a feature series on all five datasets. The sweep never opens a waveform file.

| Dataset | `aggregate` / `decimate` applied to | Level | Code path |
|---|---|---|---|
| **IMS** | windowed feature vectors (block mean / every k-th) | **(c)** | `load_pipeline_controlled`, `src/sampling.py:414-424`, `downsample_features` at `:326-362` |
| XJTU-SY | per-snapshot feature series | (b) | `load_pipeline`, `src/__init__.py:197-212` |
| FEMTO | per-snapshot feature series | (b) | same |
| Ferrara | per-snapshot feature series | (b) | same |
| ONGC | the historian series itself | (b) | same |

`aggregate` = `df.resample(freq).mean()` (`src/preprocessing.py:182-188`); `decimate` = `df.iloc[::k]`.
IMS is routed separately and **only** IMS: `src/benchmark.py:115-117`.

**Confirmed empirically.** Row counts by stage: on path (b) the snapshot series thins with the factor (984 → 493 → 198 → 99 → 50); on path (c) it stays at 984 at every factor and only the feature stream thins (195 → 98 → 39 → 20 → 10).

**Corroborated by the result files.** `control=True` only in `benchmark_IMS_long.csv`; `False` in all four others. `window_floored`: IMS 0/300, XJTU 500/900, FEMTO 360/600, Ferrara 360/600, ONGC 60/100.

**Why the asymmetry exists:** the controlled path was built as a reviewer fix (`src/sampling.py:307-323`, "reviewer W7 fix") to remove the window-flooring confound, and was only ever wired up for IMS. Historical, not physical.

### What this does and does not change

**Does not change the abstract's core question.** The abstract asks whether *"the bin-averaged logging of a SCADA historian"* destroys lead time, and §1 correctly states that historians *"store decimated or time-averaged summaries."* Historians store summaries; the sweep coarsens summaries. Consistent.

**Two sentences overreach and must be fixed:**
- §1's folklore sentence — "averaging destroys the kurtosis and crest-factor transients" — describes *waveform* averaging, which was not tested.
- `scada_ijphm.tex:128` — "Because the waveforms are raw, the aggregate/decimate sweep can be applied faithfully at the signal level," asserted of IMS, which is the **only** dataset at level (c). This is false as implemented and is a third internal contradiction of the same species Reviewer D already found twice.

**The §4.7 pair Reviewer D flagged (`:241` "before feature extraction" / `:246` "at the feature level") is confirmed verbatim.** Both readings are individually true — of different datasets. That is the honest resolution and is exactly the per-dataset statement Reviewers D and F asked for.

**Register item 3.2's drafted signal-theory argument does not survive as written** and must be rewritten per path:
- The claimed exactness ("mean square over a union of bins = mean of per-bin mean squares") holds for `var_ch{i}`, which is present, but **not** for `rms_ch{i}` — the mean of square roots is not the square root of the mean.
- The rescue is stronger than the original claim: by Jensen, the mean of RMS values is an **underestimate** of the union RMS, so aggregation can only understate amplitude, never inflate it. The observed aggregation advantage therefore cannot be an artifact of the averaging operation.
- On path (c) the averaged quantities are window summaries (`wmean`, `wstd`, `wmax`, `wslope`); bin-averaging a max or a slope is exact for nothing. Say so.
- **The aliasing half of the argument survives intact on both paths.**

---

## 5A. Phase 0.5(A) findings — RESOLVED, do not re-derive

**Resolves N-7.** Audit was read-only against the committed `results/tables/benchmark_*_long.csv`. No repo file was modified.

### 5A.1 What the code does when `FAR_pre` is NaN

**The gate is skipped by explicit, commented design.** `valid_alarm` is not defaulted true — the *gate term* short-circuits to pass, leaving validity resting on `lead_time > 0` alone.

`src/lead_time.py:228-233`:

```python
# NaN FAR (no pre-onset window to score) does not by itself invalidate the alarm.
far_ok        = (far_preonset != far_preonset) or (far_preonset <= far_budget)
valid_alarm   = (lead_time > 0) and far_ok
```

`far_preonset != far_preonset` is the NaN self-inequality idiom — true **only** for NaN.

The NaN has exactly one origin, `src/lead_time.py:141-146`: `compute_FAR_preonset` returns NaN iff `n == |{t < t_onset}| == 0`, i.e. **no test timestamp falls strictly before the onset**. The onset estimator placed onset at or before the first scored window, so there is no apparently-normal region to score.

**This diverges from the manuscript.** Eq. 5 (`scada_ijphm.tex:214-219`) defines validity as `L > 0 ∧ FAR_pre ≤ τ` with **no NaN carve-out**, anywhere. A reader implementing Eq. 5 literally gets different numbers than the repo produces. The carve-out is defensible in principle — you cannot score a FAR over an empty region — but its effect is that on those rows the metric provides **zero latch-on resistance**, which is the paper's title claim.

### 5A.2 Three distinct routes to a NaN — they mean different things

| Route | Condition | Effect on `valid_alarm` |
|---|---|---|
| **R1** "honest N/A" filler | `benchmark.py:223-244` — detector produced no result | forced `False` — harmless |
| **R2** no pre-onset window | onset exists; no test sample precedes it | **gate skipped** — `lead > 0` alone decides |
| **R3** run has no onset at all | `t_onset is None` → `lead_time.py:234-240` | legacy criterion; column is **not** NaN — see N-12 |

### 5A.3 Counts, per dataset (source: `results/tables/benchmark_*_long.csv`)

| Dataset | rows | NaN FAR | R1 filler | R2 real | **NaN & valid** | total valid | ungated share of valid |
|---|---:|---:|---:|---:|---:|---:|---:|
| IMS | 300 | 50 (16.7%) | 36 | 14 | **10** | 99 | 10.1% |
| XJTU-SY | 900 | 472 (52.4%) | 228 | 244 | **189** | 304 | **62.2%** |
| FEMTO | 600 | 45 (7.5%) | 45 | 0 | **0** | 191 | 0% |
| Ferrara | 600 | 142 (23.7%) | 42 | 100 | **96** | 350 | 27.4% |
| ONGC | 100 | 0 | 0 | 0 | **0** | 12 | 0% |
| **Total** | | | | | **295** | 956 | |

**All 295 are route R2** — none is a filler row, none is a no-onset row. On every one, `t_onset` is present and `lead_time > 0`.

**Concentration matters more than the totals.** Two XJTU bearings have NaN `FAR_pre` on **100% of their 100 rows** — `Bearing2_2` (50 valid) and `Bearing2_5` (67 valid). For those two bearings the gate never operated at all. Ferrara's 96 are all in one run, `E3`.

### 5A.4 Do the published counts stand? Verified, then recounted under strict Eq. 5

Both figures reproduce **to the digit**. The `450` denominator is all rows for the five detectors *including* the duplicated `factor=1` cells; that convention reproduces 209 exactly, so the published pair is internally consistent. The "five" are named at `tex:396`: 3σ, EWMA, Hotelling T², Isolation Forest, RMS-trend (CUSUM and Deep SVDD excluded).

| Published | Location | Reproduced | Strict Eq. 5 (NaN fails) |
|---|---|---|---|
| **20/50** | Table 12 total, `tex:589` | ✅ 20/50 | **7/50** |
| **209/450** | `tex:396` | ✅ 209/450 | **73/450** |
| **191/600** | **§6.4, `tex:426`** — "Across all ten evaluated detectors (every one runs on the full n = 6), 191/600 evaluations yield a valid alarm" | ✅ 191/600 | **191/600 — unchanged** |

> **Correction (session 2).** An earlier version of this record claimed 191/600 was not a manuscript number. **It is** — `scada_ijphm.tex:426`, §6.4. The error was mine and *not* a LaTeX-escaping problem: the grep matched line 426 correctly, but the output was piped through `cut -c1-240`, the match sits far past character 240 in that very long single-line paragraph, and the visible prefix was misread as a match on "valid alarm". **The substantive conclusion is unchanged: 191/600 does not move under either convention and needs no revision.** This is the failure mode rule 8 above exists to prevent.

Whole-file, all detectors:

| Dataset | published | strict | Δ |
|---|---:|---:|---:|
| IMS | 99 | 89 | −10 |
| XJTU-SY | 304 | 115 | **−189** |
| FEMTO | 191 | 191 | 0 |
| Ferrara | 350 | 254 | −96 |
| ONGC | 12 | 12 | 0 |

**Table 12 per-bearing deltas** — four of ten rows change:

| Bearing | V/5 published | V/5 strict | Mean pub | Best pub |
|---|---:|---:|---:|---:|
| Bearing1_1 | 0 | 0 | — | 0.00 |
| Bearing1_2 | 1 | 1 | 0.67 | 0.67 |
| **Bearing1_3** | **4** | **0** | 1.03 | 1.03 |
| Bearing1_4 | 2 | 2 | 0.68 | 0.68 |
| **Bearing1_5** | **3** | **0** | 0.35 | 0.35 |
| Bearing2_1 | 3 | 3 | 0.67 | 0.67 |
| **Bearing2_2** | **2** | **0** | 1.00 | 1.08 |
| Bearing2_3 | 1 | 1 | 3.45 | 3.45 |
| Bearing2_4 | 0 | 0 | — | 0.00 |
| **Bearing2_5** | **4** | **0** | 2.30 | 2.30 |

**Verdict:** the counts are correctly computed *under the code as written*, but they are **not the counts Eq. 5 describes**. This is a definitional decision, not an arithmetic error → D-7.

### 5A.5 What does NOT move

`lead_time_hours` is computed independently of `valid_alarm`, so **the headline aggregate-vs-decimate contrast is untouched**. Tables 7-11 (median Δ, n₊/n₋, sign tests, Holm) are on raw ungated lead exactly as §6.2 states. **Nothing in the sign-test family changes.** What moves is every *valid-alarm fraction*.

### 5A.6 Gate-dependent manuscript locations

Audited and confirmed to move: `tex:589` (Table 12, 20/50) and `tex:396` (209/450).

**Candidates, NOT yet audited** — they report valid-alarm fraction so they are gate-dependent by construction, but they are produced from the *ablation* result files, not `benchmark_*_long.csv`, so their sensitivity is unmeasured: `tex:370` (3σ valid-alarm fraction, persistence sweep — currently 1.00 across all four), `:738`, `:758`, `:775`, `:798` (IMS feature-group and spectral ablation validity tables). **Do not assume these move; measure them.**

### 5A.7 Coupling to item 1.6 (G1)

244 XJTU rows and 100 Ferrara rows have onset placed at or before the first test sample. That is an **onset-estimator** result and it bears directly on register item 1.6: the estimator's late-onset bias `≈ kσ_b/m + PΔt` predicts exactly this on short, fast-degrading bearings. Not pursued — Phase 2.

---

## 5B. Phase 0.5(B) findings — **CORRECTED session 3. Read 5B.0 first.**

### 5B.0 ⚠️ THE SESSION-2 NUMBERS IN THIS SECTION ARE SUPERSEDED

**Every number in §5B.2, §5B.3 and §5B.4 below is superseded and may not enter the manuscript.** They were computed under a convention the paper does not use:

| | session 2 (wrong) | the paper (§4.8) |
|---|---|---|
| collapsing the five within-run factors | **median** | **mean** — `tex:252`, and Table 10's caption `tex:491`: "collapsing the five within-run sampling factors to one **mean** difference per run" |
| the test | **pooled 15-pair Wilcoxon** per detector | **run-level exact two-sided sign test**, n=3, then **Holm** across the N=40 family |

§4.8 does not merely prefer the run-level test — it **explicitly disavows** the pooled one: pooling the factors as 15 pairs "inflates the effective sample size fivefold and yields overconfident p-values (as an earlier version of this work did)". Reporting a pooled p-value would reintroduce, in the revision, the exact error the paper says it fixed.

The mismatch was visible in the session-2 record and was not acted on: its "legacy (published)" 3σ per-run values were 17.500 / 5.833 / 20.500 with median 18.4, whereas published Table 10 gives **+27.1 / +18.4 / +15.6**, median +18.4. The medians coincide by accident; the per-run values never matched.

**Corrected recomputation:** `src/d2_convention_recompute.py` (new, read-only, writes no result file).

**Verification — the legacy column reproduces published Table 10 EXACTLY.** All ten detectors, all three per-run differences, all medians, all sign-test p-values, to the printed precision:

| Detector | recomputed run diffs (h) | published Table 10 | med | p |
|---|---|---|---:|---:|
| 3σ | +27.1, +18.4, +15.6 | +27.1, +18.4, +15.6 | +18.4 | 0.25 |
| Iso. Forest | +19.9, +12.2, +1.8 | +19.9, +12.2, +1.8 | +12.2 | 0.25 |
| EWMA | +22.6, +5.0, +5.8 | +22.6, +5.0, +5.8 | +5.8 | 0.25 |
| CUSUM | +22.6, +5.0, +5.4 | +22.6, +5.0, +5.4 | +5.4 | 0.25 |
| Hotelling T² | +3.3, +12.3, +4.6 | +3.3, +12.3, +4.6 | +4.6 | 0.25 |
| Deep SVDD | +15.2, 0.0, +1.8 | +15.2, 0.0, +1.8 | +1.8 | 0.50 |
| RMS-trend | −19.4, 0.0, +2.8 | −19.4, 0.0, +2.8 | 0.0 | 1.00 |
| LSTM-AE | −1.4, −0.4, −1.7 | −1.4, −0.4, −1.7 | −1.4 | 0.25 |
| TCN-AE | −1.4, −0.4, −0.2 | −1.4, −0.4, −0.2 | −0.4 | 0.25 |
| Transformer-AD | −1.4, −0.4, −2.5 | −1.4, −0.4, −2.5 | −1.4 | 0.25 |

Independently corroborated: `results/tables/ims_runlevel_test.csv` stores `run_diffs = "+27.1, +18.4, +15.6"`, `median_diff = 18.433`, `sign_test_p = 0.25` — Table 10's actual source file, confirming the mean convention.

The **N=40 Holm family also reproduces**: smallest raw p = 0.031 (Isolation Forest on FEMTO), Holm-adjusted 1.000, **0 of 40 rejected** — identical to the published §5.10 text and Table 11.

**No separate defect. The published pipeline is sound; the session-2 comparison script was not.**

### 5B.0.1 The corrected legacy-vs-invariant comparison

Source: `results/tables/benchmark_IMS_long.csv` and `benchmark_IMS_long_invariant.csv`, via `src/d2_convention_recompute.py`.

| Detector | legacy run diffs (h) | med | p | invariant run diffs (h) | med | p | Δmed |
|---|---|---:|---:|---|---:|---:|---:|
| 3σ | +27.1, +18.4, +15.6 | +18.4 | 0.25 | +25.8, +15.1, **−1.0** | +15.1 | **1.00** | −3.3 |
| Iso. Forest | +19.9, +12.2, +1.8 | +12.2 | 0.25 | **−0.7**, +16.9, +3.4 | +3.4 | **1.00** | −8.8 |
| EWMA | +22.6, +5.0, +5.8 | +5.8 | 0.25 | **−3.9**, +4.3, +2.1 | +2.1 | **1.00** | −3.7 |
| CUSUM | +22.6, +5.0, +5.4 | +5.4 | 0.25 | +4.2, +4.7, +4.3 | +4.3 | 0.25 | −1.2 |
| Hotelling T² | +3.3, +12.3, +4.6 | +4.6 | 0.25 | +1.0, +1.2, **+81.7** | +1.2 | 0.25 | −3.4 |
| Deep SVDD | +15.2, 0.0, +1.8 | +1.8 | 0.50 | +8.9, 0.0, 0.0 | 0.0 | 1.00 | −1.8 |
| RMS-trend | −19.4, 0.0, +2.8 | 0.0 | 1.00 | −0.2, 0.0, +2.4 | 0.0 | 1.00 | 0.0 |
| LSTM-AE | −1.4, −0.4, −1.7 | −1.4 | 0.25 | −1.4, −0.4, **+56.1** | −0.4 | 1.00 | +1.0 |
| TCN-AE | −1.4, −0.4, −0.2 | −0.4 | 0.25 | −1.4, −0.4, **+9.0** | −0.4 | 1.00 | 0.0 |
| Transformer-AD | −1.4, −0.4, −2.5 | −1.4 | 0.25 | −1.4, −0.4, **+68.8** | −0.4 | 1.00 | +1.0 |

Sign tallies over the three runs (n₊/n₋/n₀):

| Detector | legacy | invariant |
|---|---|---|
| 3σ | **3+/0−/0** | **2+/1−/0** |
| Iso. Forest | **3+/0−/0** | **2+/1−/0** |
| EWMA | **3+/0−/0** | **2+/1−/0** |
| CUSUM | 3+/0−/0 | 3+/0−/0 |
| Hotelling T² | 3+/0−/0 | 3+/0−/0 |
| Deep SVDD | 2+/0−/1 | 1+/0−/2 |
| RMS-trend | 1+/1−/1 | 1+/1−/1 |
| LSTM-AE | 0+/3−/0 | 1+/2−/0 |
| TCN-AE | 0+/3−/0 | 1+/2−/0 |
| Transformer-AD | 0+/3−/0 | 1+/2−/0 |

Holm over N=40 with the invariant IMS rows substituted in: smallest raw p still 0.031 (FEMTO / Isolation Forest), **0 of 40 rejected**. The Holm conclusion is schema-invariant. Six of the ten IMS raw p-values move (0.25 → 1.00).

### 5B.0.2 Reading — this REVERSES the session-2 conclusion

1. **Sign-consistency does NOT survive.** Session 2 reported "no sign reversal anywhere". That was an artifact of the median collapse, which hides a run whose *mean* difference is negative. Under the paper's own convention, **three of the six magnitude-monitoring detectors flip a run negative** — 3σ (−1.0 h on 3rd_test), Isolation Forest (−0.7 h on 1st_test), EWMA (−3.9 h on 1st_test).
2. **The manuscript sentence that breaks is `tex:480`:** *"in no run does aggregation shorten their lead time"*, and with it the abstract's *"a consistent positive trend appears for variance-sensitive charts"*. Under the invariant schema these are **false as written** for 3σ, EWMA and Isolation Forest.
3. **The abstract's headline IMS magnitude moves**: 3σ median **+18.4 h → +15.1 h**.
4. **Deep sequence models are wildly unstable** under the schema change on 3rd_test: LSTM-AE −1.7 → **+56.1 h**, Transformer-AD −2.5 → **+68.8 h**, Hotelling T² +4.6 → **+81.7 h**. n=3. Nothing should be leaned on here.
5. **The Holm conclusion is untouched** — 0 of 40 either way. The paper's central *statistical* claim (no significant effect after correction) is schema-robust. What is not robust is the *directional trend* reported alongside it.
6. **Validity is unchanged** (99/300 both), so the N-7 story stays independent of D-2.

### 5B.0.3 D-2 is not only a robustness question — defect N-14

Recorded per author instruction, session 3. §4.2 of the manuscript (`Channel-Invariant Feature Schema`, `tex:163`) argues at length that the 445-dim scheme is ill-posed at p ≫ n and presents the **49-dim invariant space as the paper's methodology**. The IMS controlled sweep ran at **445 dims** (78 test windows at f=1 on `2nd_test`; p ≫ n by a factor of ~5.7).

Therefore **§4.2 does not describe what was done on the headline dataset.** This is the same class of defect as §4.7 — a methods section describing a procedure other than the one executed — which Reviewer D has already flagged three times. It is a **correctness/reporting** issue that exists independently of whether the invariant numbers are better or worse, and it does not go away by labelling the invariant rerun an "appendix robustness check": that framing leaves §4.2 describing a schema the headline result did not use. Logged as **N-14, severity High**.

---

### 5B.1–5B.5 below: SESSION-2 RECORD, SUPERSEDED — retained only as a record of the error. Do not cite.

**Question (D-2 / N-2):** the published IMS results ran the controlled path under the **445-dim legacy** schema; the other four datasets ran the **49-dim invariant** schema the paper argues for. Does the IMS trend survive the schema the paper endorses?

**~~Answer: the direction survives on every detector; the magnitude does not.~~** — superseded by §5B.0.2.

### 5B.1 What was run

- `src/ims_schema_check.py` (new) → **`results/tables/benchmark_IMS_long_invariant.csv`** (300 rows).
- `load_pipeline_controlled` gained `feature_mode` (default `"legacy"`); `run_benchmark` threads it. Invariant branch uses `extract_invariant_features` + config top-k (50, stratified), mirroring `load_pipeline`.
- **Nothing swapped in.** `run_benchmark(save=False)`; the script refuses to overwrite its own output; published files untouched.
- **Geometry identical** to published — test windows 172/86/35/18/9 · 78/40/16/8/4 · 506/253/102/51/26; `window_rows`=10; `persistence`=3; `window_floored`=False. Total valid alarms **99 under both schemas**.
- **Reproducibility verified:** re-running `2nd_test` on the *default* (legacy) path matches the published rows to CSV round-trip — max |diff| 7.1e-15 h (≈26 ns on ~50 h values), `valid_alarm` and all window counts exact.

### 5B.2 ~~Per-run aggregate − decimate (h), factors collapsed by median~~ — SUPERSEDED (wrong collapse; use §5B.0.1)

| Detector | 1st_test leg → inv | 2nd_test leg → inv | 3rd_test leg → inv |
|---|---|---|---|
| 3σ | 17.500 → **11.633** | 5.833 → 9.167 | 20.500 → **0.833** |
| EWMA | 0.833 → 0.833 | 5.833 → 2.500 | 2.500 → 0.000 |
| CUSUM | 0.833 → 0.833 | 5.833 → 4.167 | 0.833 → 0.833 |
| Hotelling T² | 0.000 → 0.833 | 9.167 → **0.833** | 0.833 → 0.833 |
| Iso. Forest | 0.833 → 0.833 | 0.833 → 2.500 | −0.833 → 0.000 |
| Deep SVDD | 0.000 → 0.000 | 0.000 → 0.000 | 0.000 → 0.000 |
| RMS-trend | 0.000 → 0.000 | 0.000 → 0.000 | 0.000 → 0.000 |
| LSTM-AE | −0.833 → −0.833 | −0.417 → −0.417 | −1.667 → **+27.583** |
| TCN-AE | −0.833 → −0.833 | −0.417 → −0.417 | −1.667 → −3.750 |
| Transformer-AD | −0.833 → −0.833 | −0.417 → −0.417 | −1.667 → **+11.667** |

### 5B.3 ~~Pooled paired test (Wilcoxon, uncorrected)~~ — SUPERSEDED (§4.8 disavows the pooled test; use §5B.0.1)

| Detector | n | legacy median / p | invariant median / p |
|---|---:|---|---|
| 3σ | 15 | 17.5000 / **0.0029** | 5.8333 / **0.0229** |
| CUSUM | 15 | 0.8333 / **0.0076** | 0.8333 / **0.0076** |
| EWMA | 15 | 2.5000 / **0.0060** | 0.8333 / 0.2719 |
| Hotelling T² | 15 | 0.8333 / 0.0843 | 0.8333 / **0.0040** |
| Iso. Forest | 15 | 0.0000 / 0.3668 | 0.8333 / 0.1821 |
| Deep SVDD | 15 | 0.0000 / 0.1797 | 0.0000 / 0.3173 |
| RMS-trend | 15 | 0.0000 / 0.2850 | 0.0000 / 0.2850 |
| LSTM-AE | 9 | −0.8333 / 0.2812 | 0.0000 / 1.0000 |
| TCN-AE | 9 | −0.8333 / 0.4062 | −0.8333 / 0.4375 |
| Transformer-AD | 9 | −0.8333 / 0.1250 | 0.0000 / 0.4375 |

*(p uncorrected; Holm across the N=40 family not applied here.)*

### 5B.4 ~~Reading~~ — SUPERSEDED, and its conclusion (1) is now known to be WRONG. Use §5B.0.2.

1. **No sign reversal anywhere.** Every SPC chart stays positive; RMS-trend and Deep SVDD stay at exactly zero on all three runs under both schemas. The qualitative IMS claim — aggregation ≥ decimation — is schema-robust.
2. **The two largest published IMS effects shrink by roughly a factor of three.** 3σ 17.5 → 5.8 h; EWMA 2.5 → 0.8 h. If IMS were re-baselined, the headline IMS magnitudes in the paper move materially.
3. **Significance moves in both directions**, so this is not a uniform weakening: EWMA loses it (0.0060 → 0.2719), Hotelling T² gains it (0.0843 → 0.0040), 3σ survives weaker.
4. **The deep sequence models are unstable under the schema change** and should not be leaned on: `3rd_test` LSTM-AE swings −1.667 → +27.583 h and Transformer-AD −1.667 → +11.667 h. n = 9 pairs.
5. **Validity is unchanged in total** (99/300 both), so the N-7 valid-alarm story is independent of this schema question.

### 5B.5 What this does NOT settle

D-2 is a **judgement call and remains open.** ~~The measurement says the direction is safe and the magnitude is not.~~ (Direction is **not** safe — §5B.0.2.) Two defensible routes: (a) keep the published legacy baseline and add the invariant rerun as an appendix robustness check; (b) re-baseline IMS onto the invariant schema. **Do not choose without the author.** Cascade quantified in §5C.

---

## 5C. The D-2 cascade — measured, session 3

**Question:** if IMS is re-baselined onto the invariant schema, what actually moves?

**Source:** `src/d2_cascade_audit.py` (new, read-only, writes nothing) + `src/d2_convention_recompute.py`. Derived from the existing `benchmark_IMS_long_invariant.csv`; no pipeline was rerun.

### 5C.1 The structural finding that bounds the cascade

**The 445-dim legacy schema is reachable through exactly one function.** `load_pipeline_controlled` (`src/sampling.py:365`) is the only legacy-schema entry point, and it is called from only two places: `src/benchmark.py:164` (the IMS controlled sweep) and `src/sampling.py:547`.

Every other IMS analysis in the repo goes through `src.load_pipeline`, which reads `FEATURES["mode"]` from `src/config.py` — set to `"invariant"`. Verified call sites: `ablation.py:98-100`, `calibration.py:46`, `tradeoff.py:48`, `onset_sensitivity.py:75`, `robustness.py:204`, `feature_coarsening_ablation.py:77-80`, `training_sweep.py:76`.

**Consequence: most of the IMS material in the paper is already on the invariant schema and cannot move under D-2.** The cascade is confined to the controlled sweep and its derivatives.

### 5C.2 Onset is schema-independent — verified

`t_onset`, `t_fail` and `max_lead_hours` are **identical on 300/300 paired rows** between the legacy and invariant files. Onset is computed from the RMS/kurtosis health indicator on the snapshot series, upstream of feature extraction. Tables 3 and 4 and Figure 1 are therefore fixed by construction, not by luck.

### 5C.3 The cascade table

| Artifact | Changes? | Magnitude | Rerun needed? |
|---|---|---|---|
| **Abstract** — "3σ median +18.4 h" | **YES** | → **+15.1 h** | no |
| **Abstract** — "a consistent positive trend appears for variance-sensitive charts" | **YES** | becomes **false as written**: 3σ, EWMA, Iso. Forest each flip one run negative | no |
| **Abstract** — "does not survive Holm … smallest adjusted p = 1.00" | no | 0/40 rejected under both schemas | no |
| **§6, `tex:480`** — "in no run does aggregation shorten their lead time" | **YES** | **false as written** — 3 of 6 chart detectors have a negative run | no |
| **§6, `tex:480`** — the six per-detector run-diff triples quoted in prose | **YES** | all six change; see §5B.0.1 | no |
| **§5.1, `tex:478`** — "3σ falls from 58.0 h at full rate to 7.1 h at 10× decimation … aggregation holds it near 59 h" | **YES** | invariant: **64.6 h → 24.8 h**, aggregation holds near **64.6 h**. The decimation collapse is ~3.5× weaker | no |
| **Table 2** (`tab:imslead`) IMS mean raw lead + 95% CI | **YES, large** | Hotelling T² **67.5 → 174.8** (+107.3); RMS-trend **34.5 → 3.2** (−31.3); Iso. Forest 69.8 → 87.2; LSTM-AE 214.9 → 197.6; TCN 201.5 → 183.7; Transformer 199.6 → 183.4; CUSUM 77.2 → 64.8; 3σ 58.0 → 64.6; Deep SVDD 18.4 → 14.8; EWMA 78.3 → 78.6. **Rank order changes** | no — regenerated with the existing `bootstrap_ci_across_runs` (verified: it reproduces the published legacy column exactly) |
| **Table 3** (`tab:onsetsens`) onset sensitivity | **NO** | onset identical 300/300 | no |
| **Table 4** (`tab:decoupled`) decoupled onset | **NO** | same reason | no |
| **Table 5** (`tab:persistence`) persistence = 3 column | **YES** | 3σ +18.4 → **+15.1**; EWMA +5.8 → **+2.1**; Iso. Forest +12.2 → **+3.4** | no for p=3 |
| **Table 5** persistence ∈ {1, 5, 10} columns | **unmeasured** | — | **YES** — and see N-15: `persistence_sensitivity_IMS.csv` has **no generating script anywhere in the repo** |
| **Table 6** (`tab:missing`) historian-gap robustness | **NO** | `robustness.py:204` → `load_pipeline` → already invariant | no |
| **Table 10** (`tab:imssweep`) | **YES, every row** | full table in §5B.0.1 | no |
| **Table 11** (`tab:holm`) IMS rows | **YES** | 6 of 10 raw p move 0.25 → 1.00; **Holm verdict unchanged, 0/40** | no |
| **Table 13** (`tab:conformal`) conformal FAR | **NO** | `calibration.py:46` → `load_pipeline` → already invariant | no |
| **Table 14** (`tab:farbudget`) FAR-budget sensitivity | **NO** | `tradeoff.py:48` → `load_pipeline` → already invariant | no |
| **Table 16** (`tab:tradeoff`) lead-vs-FAR trade-off | **NO** | same source | no |
| **Table 17** (`tab:ablation`) feature-group ablation | **NO** | `ablation.py:98` → `load_pipeline` | no |
| **Table 18** (`tab:coarsen_ablation`) | **NO** | `feature_coarsening_ablation.py:77` → `load_pipeline` | no |
| **Table 19** (`tab:ablation_general`) | **NO** | `ablation.py` | no |
| **Table 20** (`tab:spectral`) spectral ablation | **NO** | `ablation.py` (spectral variant) | no |
| **Table 22** (`tab:phrank`) PH vs gated ranking | **NO** | built from `tradeoff_IMS.csv` → invariant | no |
| **Table 25** (`tab:compute`) per-detector compute cost | **YES** | timings were measured at **445 dims**; the invariant run is 49 dims. Direction: faster. Magnitude unmeasured | **YES** — one timing pass on `3rd_test` |
| **Table 27** (`tab:noise`) noise injection | **NO** | `robustness.py` → `load_pipeline` | no |
| **Table 28** (`tab:denoise`) denoiser comparison | **NO** | `robustness.py` → `load_pipeline` | no |
| **Figure 1** (`fig:health`) health trajectory + onset | **NO** | onset identical; the plotted indicator is pre-feature | no |
| **Figure 2** (`fig:crossdataset`) cross-dataset median diffs | **YES** — IMS column only | same values as Table 10's Med. column | no |
| **Figure 3** (`fig:sweep`) lead vs logging interval | **YES** | full curve regenerated in the audit output; the aggregate/decimate gap narrows markedly at f=10 | no |
| **Figure 4** (`fig:conf_ims`) conformal calibration | **NO** | plots Table 13 | no |
| **Figure 7** (`fig:tradeoff_ims`) trade-off curve | **NO** | plots Table 16's source | no |
| **Figure 9** (`fig:farbudget_fig`) FAR-budget curve | **NO** | plots Table 14 | no |
| Result files: `benchmark_IMS_aggregate.csv`, `benchmark_IMS_leadtime_ci.csv`, `benchmark_IMS_paired_test.csv`, `ims_runlevel_test.csv`, `sampling_sweep_*.csv`, IMS rows of `paired_tests_holm.csv` | **YES** | all derived from the controlled sweep | no — regenerable from the existing invariant CSV |

**Totals: 11 artifacts move, 17 do not, 2 need a rerun** (Table 5's other three persistence columns; Table 25's timings).

### 5C.4 Rerun cost

Only two reruns would be required for a full re-baseline, and neither is on the critical path for the D-2 decision:

- **Table 5, persistence ∈ {1, 5, 10}** — three additional controlled sweeps restricted to the six non-sequence detectors. The one full invariant controlled sweep already run (session 2, all ten detectors including three deep AEs, 300 rows) completed inside a single working session; these three are cheaper per sweep because the deep models are excluded, but they are blocked on N-15 first — there is no script to rerun.
- **Table 25 compute timings** — a single-pass timing run on `3rd_test` (631 train / 506 test windows). Cheap; one pass, no sweep.

Everything else in the "changes = YES" column was regenerated from the existing `benchmark_IMS_long_invariant.csv` without touching the pipeline.

### 5C.5 What the cascade means for the decision

The cascade is **narrower than §5B.5 assumed** — it does not touch the ablations, the conformal analysis, the trade-off family, or the onset tables, and it does not touch Tables 7-9 (XJTU / FEMTO / Ferrara), which were never on the legacy path. But it is **sharper where it lands**: Table 2's ordering, Table 10 in full, the §6 sign-consistency sentence, and two abstract claims. Option (a) — appendix robustness check — leaves N-14 unresolved: §4.2 would still describe a schema the headline dataset did not use.

---

## 5D. N-15 RESOLVED — Table 5 regenerated, and §6.2's conclusion does NOT survive

**The defect was the absence itself.** `results/tables/persistence_sensitivity_IMS.csv` had no generating script anywhere in the repo, so its numbers could be neither traced nor rerun. **Generator now written: `src/persistence_sweep_ims.py`.** It sweeps `THRESHOLD["alarm_persistence"]` over {1, 3, 5, 10} inside a `try/finally`, the same pattern `src/training_sweep.py` uses for `SPLIT`, and runs the six non-sequence detectors that the published file contains.

Output: **`results/tables/persistence_sensitivity_IMS_invariant.csv`** (24 rows). The published file is untouched.

### 5D.1 Median aggregate − decimate (h), invariant schema, §4.8 mean collapse

| Detector | p=1 | p=3 | p=5 | p=10 | published (p=1/3/5/10) |
|---|---:|---:|---:|---:|---|
| 3σ | +5.83 | **+15.10** | +7.77 | +3.83 | +4.2 / +18.4 / +17.4 / +11.4 |
| EWMA | +2.91 | +2.10 | +2.91 | +2.33 | +5.2 / +5.8 / +4.8 / +3.0 |
| Iso. Forest | +0.33 | +3.43 | **−0.83** | +4.17 | +10.4 / +12.2 / −0.8 / −0.2 |
| CUSUM | +4.15 | +4.27 | +4.15 | +2.67 | *(not in Table 5)* |
| Hotelling T² | **−7.11** | +1.17 | +1.00 | +9.13 | *(not in Table 5)* |
| RMS-trend | **−11.17** | 0.00 | 0.00 | 0.00 | *(not in Table 5)* |

Cross-check: the p=3 column reproduces §5B.0.1's invariant medians exactly (3σ 15.10, EWMA 2.10, IsoF 3.43, CUSUM 4.27, Hotelling 1.17) — two independently written scripts agree.

### 5D.2 The 3σ valid-alarm fraction — the N-15 question, answered

| Persistence | f=1 aggregate | all factors, aggregate | **published** |
|---|---:|---:|---:|
| 1 | **0.67** | 0.67 | 1.00 |
| 3 | **0.67** | 0.67 | 1.00 |
| 5 | **0.67** | **0.53** | 1.00 |
| 10 | **0.67** | **0.33** | 1.00 |

**The published 1.00 is not reproduced at any persistence.** `1st_test` carries pre-onset FAR 41.8% (invariant) / 29.1% (legacy), far above τ=10%, so its alarm is invalid under Eq. 5 — 2 of 3 runs, i.e. 0.67, under every denominator tried and under **both schemas**. This is **not** a D-2 consequence.

### 5D.2b Legacy-schema control run — this isolates the defect precisely

`persistence_sensitivity_IMS_legacy.csv` (24 rows) reruns the same sweep on the **445-dim legacy schema the published table was produced on**:

| Row | published Table 5 (p=1/3/5/10) | legacy rerun | match |
|---|---|---|---|
| 3σ median Δ | +4.2 / +18.4 / +17.4 / +11.4 | **4.17 / 18.43 / 17.43 / 11.43** | ✅ **exact** |
| EWMA median Δ | +5.2 / +5.8 / +4.8 / +3.0 | **5.17 / 5.77 / 4.83 / 3.00** | ✅ **exact** |
| Iso. Forest median Δ | +10.4 / +12.2 / −0.8 / −0.2 | **10.43 / 12.20 / −0.83 / −0.17** | ✅ **exact** |
| **3σ valid-alarm frac.** | **1.00 / 1.00 / 1.00 / 1.00** | **0.67 / 0.67 / 0.67 / 0.67** | ❌ **does not reproduce** |

**Three of four rows reproduce to the digit; the fourth does not.** Same script, same schema, same collapse convention. That eliminates every alternative explanation — not the schema, not the §4.8 convention, not an error in the new generator, which demonstrably reconstructs the rest of the table. **The published `valid_frac_f1_agg` column is wrong, and was wrong in the originally released file.**

It also **validates `src/persistence_sweep_ims.py` as the authentic missing generator**: it reproduces the published table exactly except in the one cell already inconsistent with the released benchmark CSV.

Legacy 3σ validity across all factors: **0.67 / 0.67 / 0.47 / 0.33** for p = 1/3/5/10 — the same degradation seen on the invariant schema (0.67 / 0.67 / 0.53 / 0.33).

### 5D.3 Does §6.2's conclusion still hold? **No — but the causes must be separated.**

⚠️ **Correction to the first version of this section, which ran two different things together.** The legacy control run (§5D.2b) shows that only the first failure below is a *published defect*; the others are *consequences of D-2* and were correct as published.

§6.2 (`tex:357`) makes three claims from this table. Measured against the regenerated data:

1. *"the 3σ valid-alarm fraction is 1.00 at every persistence"* — **false**. It is 0.67, and was 0.67 in the originally released data too.
2. *"so the deployable-detector recommendation does not depend on this parameter"* — **false as stated once the sweep is not restricted to full resolution.** At f=1 the fraction is flat at 0.67, so the recommendation is stable *there*; but across the coarsening factors it **halves**, 0.67 → 0.67 → 0.53 → **0.33** as persistence goes 1 → 10. A longer persistence filter costs 3σ half its valid alarms at SCADA rates. The parameter matters; the published table hid this by reporting only the f=1 column.
3. *"the 3σ and EWMA charts show a sign-consistent positive run-level median at all four settings (n₊/n₋ = 3/0)"* — **CORRECT AS PUBLISHED; broken by D-2.** The legacy rerun confirms 3+/0− for both detectors at all four persistences, exactly as claimed. Under the **invariant** schema 3σ is 3+/0− at p=1, 5, 10 but **2+/1− at p=3**, and EWMA is **2+/1−** at p=1, 3, 5, reaching 3+/0− only at p=10. This is a **consequence of the re-baseline, not an authoring error** — the response letter should say so plainly.
4. *"only the spike-robust Isolation Forest drifts to a near-zero negative median at the longest persistence"* — **also correct as published** (legacy: Iso. Forest is the only negative among the three tabulated detectors, −0.83 at p=5 and −0.17 at p=10), **broken by D-2**: under the invariant schema Iso. Forest is negative at p=5 (−0.83) but **positive at p=10 (+4.17)**, while Hotelling T² (−7.11) and RMS-trend (−11.17) turn strongly negative at p=1. Those two are not among Table 5's rows, so if the table keeps its present three-row shape this sentence can be repaired rather than deleted.

**Recommended replacement claim, supportable from the regenerated file:** the aggregate-vs-decimate direction is positive at every persistence for 3σ, EWMA and CUSUM in *median*, but is not sign-consistent across runs at any setting except CUSUM; and the 3σ valid-alarm fraction is 0.67 at full resolution, falling to 0.33 across the coarsening sweep at persistence 10. **Do not restate the "does not depend on this parameter" conclusion.**

---

## 5F. D-2 execution record — code change and regenerated artifacts

### 5F.1 The code change (brief rule 4 sign-off, scoped to the IMS controlled-sweep path)

| File | Change |
|---|---|
| `src/sampling.py:371` | `load_pipeline_controlled(..., feature_mode=)` default **`"legacy"` → `"config"`** — `FEATURES["mode"]` now governs. Docstring rewritten to state that legacy is still reachable and why. |
| `src/benchmark.py:103` | `run_benchmark(..., feature_mode=)` default **`"legacy"` → `"config"`**; comment at `:161` updated. |
| `src/ims_schema_check.py` | median-collapse `run_level_diffs` and the pooled Wilcoxon block marked **DO NOT USE FOR REPORTED NUMBERS** (session-3 correction 1). Behaviour unchanged. |

**Nothing else changed.** No detector, onset, or metric implementation was touched. `control=False` never reads `feature_mode`, and `control` is forced `False` for non-IMS datasets (`benchmark.py:117`), so **no other dataset is affected**.

**Legacy path kept reachable and tested** — new `tests/test_feature_mode.py`, 7 tests, all passing:
- defaults are `"config"` on both entry points;
- `feature_mode="legacy"` still yields **445 dims** with p > n (the N-14 condition, pinned as a fact);
- `"config"` resolves to invariant with p ≤ 50 and p < n;
- explicit `"invariant"` ≡ the default;
- **downsampling geometry is schema-independent** (test-window counts, window size, effective interval identical) — this is what makes the old and new columns comparable;
- unknown mode raises.

Full suite after the change: **99 passed, 1 skipped, 1 failed** — the failure is the pre-existing benign **N-9** (`test_metropt_loads_with_expected_parameters`, `assert 'real' == 'fixture'`, MetroPT, touches no paper number). **No new failures.**

### 5F.2 Regenerated artifacts

All produced by the repo's **own** generator functions fed the invariant frame — `aggregate_long`, `bootstrap_ci_across_runs`, `paired_test_aggregate_vs_decimate` (`src/benchmark.py`), `ims_runlevel_table`, `family_holm` (`src/stats_rigor.py`). No statistic was reimplemented. Runner: `src/d2_regenerate_artifacts.py`.

| New file | Backs | Rows |
|---|---|---|
| `benchmark_IMS_long_invariant.csv` | the sweep itself | 300 |
| `benchmark_IMS_leadtime_ci_invariant.csv` | **Table 2** | 108 |
| `ims_runlevel_test_invariant.csv` | **Table 10** | 10 |
| `paired_tests_holm_invariant.csv` | **Table 11** | 40 |
| `benchmark_IMS_aggregate_invariant.csv` | **Figure 3**, sweep curve | 120 |
| `persistence_sensitivity_IMS_invariant.csv` | **Table 5** (N-15 fix) | 24 |
| `compute_cost_IMS_invariant.csv` + `compute_cost_IMS_legacy.csv` | **Table 25** — clean paired run, idle machine, 5 repeats. **Report the ratio, not the absolutes** (§5E.7) | 9 each |
| `benchmark_IMS_paired_test_invariant.csv` | *diagnostic only* — the pooled test §4.8 disavows. **Never report from it.** | 10 |

**Cross-validation:** `stats_rigor.ims_runlevel_table` on the invariant frame reproduces, to the digit, the medians and p-values that `src/d2_convention_recompute.py` derived independently — two separately written implementations of §4.8 agreeing.

> **Published files were NOT overwritten.** New artifacts carry an `_invariant` suffix and the originals remain. Reasons: the response letter needs both columns side by side (§5E is built from exactly that pairing), and `results/` is gitignored (**N-3**), so an overwrite would be unrecoverable. Promoting the new files to the published names is a rename the author can authorise once §5E has been checked.

---

## 5E. CLAIM-DELTA INVENTORY — the spine of the Response to Review

Every manuscript value that moves under D-2. **Old** = as published; **new** = invariant re-baseline. Line numbers are `paper/files/scada_ijphm.tex`. Sources: `benchmark_IMS_leadtime_ci_invariant.csv`, `ims_runlevel_test_invariant.csv`, `paired_tests_holm_invariant.csv`, `persistence_sensitivity_IMS_invariant.csv`, `benchmark_IMS_long_invariant.csv`, `compute_cost_IMS_invariant.csv`.

### 5E.1 Prose claims

| # | Loc | Claim | Old | New |
|---|---|---|---|---|
| P1 | `:63` abstract | 3σ IMS median | **+18.4 h** | **+15.1 h** |
| P2 | `:63` abstract | "a consistent positive trend appears for variance-sensitive charts" | asserted | **must be withdrawn** — 3σ 2+/1−, EWMA 2+/1−, IsoF 2+/1− |
| P3 | `:63` abstract | "does not survive Holm … smallest adjusted p=1.00" | p=1.00 | **unchanged** |
| P4 | `:267` §5 roadmap (ii) | "the same sign in all three runs for every magnitude detector" | asserted | **false** — three detectors flip a run |
| P5 | `:267` §5 roadmap (ii) | 3σ / IF / EWMA medians | **+18.4 / +12.2 / +5.8 h** | **+15.1 / +3.4 / +2.1 h** |
| P6 | `:268` §5 roadmap (iii) | smallest adjusted p | 1.00 | **unchanged** |
| P19 | `:275` §5.1 | "the three deep reconstruction models top the table and **EWMA and Isolation Forest lead the classical detectors**" | asserted | **false** — under the re-baseline **Hotelling T² (174.8 h) leads the classical detectors**, ahead of Iso. Forest (87.2) and EWMA (78.6). The deep models still top the table, and the clause's *purpose* survives: this is still the ordering the FAR budget overturns |
| P7 | `:275` §5.1 | deep models' raw leads | **199–215 h** | **183–198 h** |
| P8 | `:275` §5.1 | deep models' pre-onset FAR | "48% on test 3 to 100% on test 1" | **"61% on test 3 to 100% on tests 1–2"** |
| P9 | `:275` §5.1 | deep models' valid-alarm fraction | 0/3 | **unchanged (0/3)** |
| P10 | `:357` §6.2 | "3σ valid-alarm fraction is 1.00 at every persistence" | 1.00 | **0.67** — and was 0.67 in the released data too (**N-15**) |
| P11 | `:357` §6.2 | "the deployable-detector recommendation does not depend on this parameter" | asserted | **withdraw** — validity falls 0.67→0.33 across factors as persistence 1→10 |
| P12 | `:357` §6.2 | "3σ and EWMA … sign-consistent positive … at all four settings (n₊/n₋=3/0)" | **verified correct as published** (legacy rerun: 3+/0− ×4 for both) | **breaks under D-2** — 3σ 2+/1− at p=3; EWMA 2+/1− at p=1,3,5. A re-baseline consequence, **not** an authoring error |
| P13 | `:357` §6.2 | "only … Isolation Forest drifts to a near-zero negative median at the longest persistence" | **verified correct as published** (legacy: IsoF the only negative, −0.83 / −0.17) | **breaks under D-2** — IsoF negative at p=5 but **+4.17 at p=10**; Hotelling (−7.11) and RMS-trend (−11.17) negative at p=1, though neither is a Table 5 row |
| P14 | `:478` §5.x | 3σ full-rate → 10× decimation | **58.0 → 7.1 h** | **64.6 → 24.8 h** |
| P15 | `:478` §5.x | "aggregation holds it near 59 h" | 59 h | **near 64.6 h** |
| P16 | `:480` §5.x | "in no run does aggregation shorten their lead time" | asserted | **false** — must be withdrawn |
| P17 | `:480` §5.x | six per-detector run-diff triples | see Table 10 old | see Table 10 new |
| P18 | `:513` §5.10 | "smallest raw p is 0.031 (IsoForest on FEMTO) … 0 of 40" | 0.031 / 0 of 40 | **unchanged** |

### 5E.2 Table 2 (`tab:imslead`, `:286–297`) — mean raw lead, 95% bootstrap CI

| Detector | Line | Old | Old CI | New | New CI | Δ |
|---|---|---:|---|---:|---|---:|
| LSTM-AE | `:286` | 214.9 | [65.5, 383.5] | **197.6** | [65.5, 331.7] | −17.3 |
| TCN-AE | `:287` | 201.5 | [65.5, 343.5] | **183.7** | [65.5, 330.9] | −17.9 |
| Transformer-AD | `:288` | 199.6 | [65.5, 337.7] | **183.4** | [65.5, 330.9] | −16.2 |
| EWMA | `:289` | 78.3 | [27.2, 152.2] | **78.6** | [28.0, 152.2] | +0.3 |
| CUSUM | `:290` | 77.2 | [26.3, 151.4] | **64.8** | [26.3, 114.9] | −12.4 |
| Isolation Forest | `:291` | 69.8 | [28.0, 123.3] | **87.2** | [49.7, 152.2] | +17.4 |
| Hotelling T² | `:292` | 67.5 | [27.2, 113.3] | **174.8** | [56.3, 315.9] | **+107.3** |
| 3σ | `:295` | 58.0 | [22.2, 93.7] | **64.6** | [28.8, 108.7] | +6.7 |
| RMS-trend | `:296` | 34.5 | [0.0, 93.7] | **3.2** | [0.0, 9.7] | **−31.2** |
| Deep SVDD | `:297` | 18.4 | [0.0, 45.5] | **14.8** | [0.0, 34.0] | −3.5 |

**Row order changes.** Old: LSTM, TCN, Transformer, EWMA, CUSUM, IsoF, Hotelling, 3σ, RMS-trend, SVDD. New: LSTM, TCN, Transformer, **Hotelling**, **IsoF**, EWMA, **CUSUM**, 3σ, SVDD, **RMS-trend**. Hotelling T² rises from 7th to 4th; RMS-trend falls to last. The two-block split (`:284` / `:294`) is driven by Table 16, which is on the invariant path already and **does not move** — so 3σ, RMS-trend and Deep SVDD remain the deployable block. §5 roadmap item (i)'s "RMS-trend correctly weakest" (`:266`) **still holds** and strengthens.

### 5E.3 Table 5 (`tab:persistence`, `:367–370`)

| Row | Line | Old (p=1/3/5/10) | New (p=1/3/5/10) |
|---|---|---|---|
| 3σ median Δ | `:367` | +4.2 / +18.4 / +17.4 / +11.4 | **+5.8 / +15.1 / +7.8 / +3.8** |
| EWMA median Δ | `:368` | +5.2 / +5.8 / +4.8 / +3.0 | **+2.9 / +2.1 / +2.9 / +2.3** |
| Iso. Forest median Δ | `:369` | +10.4 / +12.2 / −0.8 / −0.2 | **+0.3 / +3.4 / −0.8 / +4.2** |
| 3σ valid-alarm frac. | `:370` | 1.00 / 1.00 / 1.00 / 1.00 | **0.67 / 0.67 / 0.67 / 0.67** (f=1); **0.67 / 0.67 / 0.53 / 0.33** across all factors |

### 5E.4 Table 10 (`tab:imssweep`, `:497–506`)

| Detector | Line | Old run diffs | Old med / p | New run diffs | New med / p |
|---|---|---|---|---|---|
| 3σ | `:497` | +27.1, +18.4, +15.6 | +18.4 / 0.25 | **+25.8, +15.1, −1.0** | **+15.1 / 1.00** |
| Iso. Forest | `:498` | +19.9, +12.2, +1.8 | +12.2 / 0.25 | **−0.7, +16.9, +3.4** | **+3.4 / 1.00** |
| EWMA | `:499` | +22.6, +5.0, +5.8 | +5.8 / 0.25 | **−3.9, +4.3, +2.1** | **+2.1 / 1.00** |
| CUSUM | `:500` | +22.6, +5.0, +5.4 | +5.4 / 0.25 | **+4.2, +4.7, +4.3** | **+4.3 / 0.25** |
| Hotelling T² | `:501` | +3.3, +12.3, +4.6 | +4.6 / 0.25 | **+1.0, +1.2, +81.7** | **+1.2 / 0.25** |
| Deep SVDD | `:502` | +15.2, 0.0, +1.8 | +1.8 / 0.50 | **+8.9, 0.0, 0.0** | **0.0 / 1.00** |
| RMS-trend | `:503` | −19.4, 0.0, +2.8 | 0.0 / 1.00 | **−0.2, 0.0, +2.4** | **0.0 / 1.00** |
| LSTM-AE | `:504` | −1.4, −0.4, −1.7 | −1.4 / 0.25 | **−1.4, −0.4, +56.1** | **−0.4 / 1.00** |
| TCN-AE | `:505` | −1.4, −0.4, −0.2 | −0.4 / 0.25 | **−1.4, −0.4, +9.0** | **−0.4 / 1.00** |
| Transformer-AD | `:506` | −1.4, −0.4, −2.5 | −1.4 / 0.25 | **−1.4, −0.4, +68.8** | **−0.4 / 1.00** |

**The S-c. (sign-consistent) column changes on SEVEN of ten rows.** Verified against `all_same_sign` in `ims_runlevel_test_invariant.csv`:

- **was plain "yes", becomes "no":** 3σ, Iso. Forest, EWMA (each now 2+/1−);
- **was "yes (−)", becomes "no":** LSTM-AE, TCN-AE, Transformer-AD (each now 1+/2−, because `3rd_test` flips hard positive);
- **was "2+,tie", becomes "1+, 2 ties":** Deep SVDD;
- **unchanged:** CUSUM and Hotelling T² (both stay 3+/0− "yes"), and RMS-trend (stays "no").

The caption's "the exact two-sided sign test floors at p=0.25 at n=3" stays correct.

### 5E.5 Table 11 (`tab:holm`, `:523–532`) — IMS rows only

| Detector | Line | Old raw p | New raw p | Holm p | Reject |
|---|---|---:|---:|---:|---|
| 3σ | `:523` | 0.250 | **1.000** | 1.000 | no |
| EWMA | `:524` | 0.250 | **1.000** | 1.000 | no |
| CUSUM | `:525` | 0.250 | 0.250 | 1.000 | no |
| Hotelling T² | `:526` | 0.250 | 0.250 | 1.000 | no |
| Iso. Forest | `:527` | 0.250 | **1.000** | 1.000 | no |
| Deep SVDD | `:528` | 0.500 | **1.000** | 1.000 | no |
| LSTM-AE | `:529` | 0.250 | **1.000** | 1.000 | no |
| TCN-AE | `:530` | 0.250 | **1.000** | 1.000 | no |
| Transformer-AD | `:531` | 0.250 | **1.000** | 1.000 | no |
| RMS-trend | `:532` | 1.000 | 1.000 | 1.000 | no |

**Seven of ten raw p-values move; every Holm-adjusted p and every reject decision is unchanged. 0 of 40 survive under both schemas.**

### 5E.6 Figures

| Figure | Loc | Change |
|---|---|---|
| **F2** `fig:crossdataset` | `:418–421` | IMS column only; new medians = Table 10's new Med. column (§5E.4). Other three datasets unchanged. |
| **F3** `fig:sweep` | `:482–486` | Full IMS curve. 3σ aggregate 58.0/60.7/57.7/59.1/56.3 → **64.6/67.8/66.8/64.6/61.9**; 3σ decimate 58.0/54.9/42.0/7.1/27.9 → **64.6/60.5/58.2/24.8/51.1**. IsoF aggregate 69.8/66.7/56.3/49.5/22.6 → **87.2/75.2/56.4/63.4/40.6**; IsoF decimate 69.8/67.0/13.7/9.3/48.5 → **87.2/76.6/48.5/44.3/33.5**. **The aggregate–decimate gap narrows sharply**; the caption's "where the variance-sensitive detectors collapse at coarse rates" overstates the new curve. |
| **F1** `fig:health` | `:303–306` | **no change** — onset identical 300/300 |
| **F4/F7/F9** | `:617,:651,:665` | **no change** — invariant-path sources |

### 5E.7 Table 25 (`tab:compute`, `:1013–1021`) — ✅ CLEAN PAIRED MEASUREMENT

Generator written (`src/compute_cost_ims.py` — Table 25 had no generator either, the same gap as N-15). **Paired run on an idle machine, legacy then invariant back to back, 5 repeats each per the caption.** Geometry identical on both passes and matching the caption exactly — **631 train / 506 test windows**; only the feature width differs, **445 → 49**.

| Detector | train legacy → invariant (s) | ×faster | inference legacy → invariant (µs/win) | ×faster |
|---|---|---:|---|---:|
| 3σ | 0.0021 → 0.00022 | **9.4** | 3.03 → **0.22** | **13.8** |
| EWMA | 0.0021 → 0.00022 | 9.6 | 3.72 → **0.98** | 3.8 |
| CUSUM | 0.0023 → 0.00022 | 10.4 | 5.25 → **2.11** | 2.5 |
| Hotelling T² | 0.261 → 0.020 | **13.1** | 4.35 → **1.49** | 2.9 |
| Iso. Forest | 0.801 → 0.731 | 1.10 | 142.4 → **119.7** | 1.19 |
| Deep SVDD | 2.80 → 2.27 | 1.24 | 5.05 → **2.33** | 2.17 |
| LSTM-AE | 102.0 → 49.5 | 2.06 | 1313 → **513** | 2.56 |
| TCN-AE | 72.5 → 46.2 | 1.57 | 911 → **379** | 2.40 |
| Transformer-AD | 51.2 → 41.6 | 1.23 | 685 → **300** | 2.28 |

**The invariant schema is faster on every detector, on both axes.** The gain is largest where cost scales directly with dimensionality — the SPC charts (2.5–13.8× on inference) and Hotelling T² (13.1× on training, since it inverts a p×p covariance). It is smallest for Isolation Forest (1.1–1.2×), whose cost is dominated by sample count rather than feature count.

> ⚠️ **Use the RATIO, not these absolute values, when revising Table 25.** The legacy pass on this machine runs **4–13× slower than the published column** (Iso. Forest train 0.80 s here vs 0.20 s published; LSTM-AE 102 s vs 7.8 s). That gap is hardware and threading, not schema — it appears on the *same* legacy configuration the published numbers came from. Three defensible options: (a) re-time the whole table on the original hardware under the invariant schema; (b) keep the published table and state the schema it was measured under; (c) publish this machine's invariant column and rewrite the caption's hardware description. **Never mix a published legacy row with a new invariant row.**

**Table 25's actual claim strengthens.** The caption argues "even the slowest model's inference is ≪ the 10 s SCADA polling interval". The slowest invariant inference here is LSTM-AE at **513 µs/window ≈ 0.5 ms** — about 20,000× inside the budget, with 2.6× more margin than the legacy schema gave.

<details><summary>Superseded first attempt — contaminated, deleted</summary>

An initial invariant-only pass ran while the legacy persistence sweep held the same core, giving values 10–20× inflated by contention. That file was **deleted**, never published, and the measurement redone paired on an idle machine. Noted so the discarded numbers are not mistaken for a result.

</details>

### 5E.8 Unchanged — state explicitly in the response letter

Tables 3, 4, 6, 13, 14, 16, 17, 18, 19, 20, 22, 27, 28; Figures 1, 4, 5, 6, 7, 8, 9, 10, 11; Tables 7, 8, 9 (XJTU / FEMTO / Ferrara — never on the legacy path); the Holm verdict; the non-destruction headline.

---

## 5G. Reviewer D run-dependent items — session 4

Four items run this session: **D2** (deep models in the Table 16 sweep), **D3** (one-class SVM),
**D15** (equivalence evidence), **D17** (original test-3 label). No manuscript edit was made.
Every run wrote a **new** result file; no published file was read-modified-written.

### 5G.1 D15 — equivalence evidence ✅ COMPLETE

**Margin δ = 1 h**, pre-specified on operational grounds (a planner cannot act on sub-hour
differences in warning time), fixed before any result was read. Generator:
`src/d15_equivalence.py`. Metric: `lead_time_hours`, run-level differences via
`stats_rigor.run_level_diffs` (**mean** collapse over factors and seeds, §4.8).

**Primary — two-sided 95% bootstrap CI**, runs resampled, B = 2000, seed 42, percentile
interval, reusing the construction in `benchmark.bootstrap_ci_across_runs`.
Source: `results/tables/d15_equivalence_bootstrap.csv`.

| Dataset arm | Equivalent | Inconclusive | Aggregate superior beyond δ | Untestable |
|---|---:|---:|---:|---:|
| IMS (published, legacy 445-dim) | 0 | 5 | 5 | 0 |
| IMS (invariant re-baseline, D-2) | 0 | 8 | 2 | 0 |
| XJTU-SY | 10 | 0 | 0 | 0 |
| FEMTO | 10 | 0 | 0 | 0 |
| Ferrara | 10 | 0 | 0 | 0 |
| ONGC (n=1) | 0 | 0 | 0 | 10 |
| **Total** | **30** | **13** | **7** | **10** |

> **No cell anywhere is "aggregate inferior beyond margin."** The seven non-equivalent cells
> are all cells where aggregation **beats** decimation by more than 1 h. That refutes *symmetric*
> equivalence while supporting the paper's direction — the distinction must be stated, not blurred.

**Secondary — TOST by two one-sided exact sign tests.** Floor `0.5^(n₊+n₋)` per detector;
feasible only where n₊+n₋ ≥ 5. Source: `results/tables/d15_equivalence_tost.csv`.

| Dataset arm | TOST feasible | Of which equivalent | Infeasible (floor > α) |
|---|---:|---:|---:|
| IMS (legacy) | 0 | — | 10 (n_eff 2–3, floor 0.125–0.25) |
| IMS (invariant) | 0 | — | 10 (n_eff 1–3, floor 0.125–0.50) |
| XJTU-SY | 2 | 2 | 8 (n_eff 0–4) |
| FEMTO | 10 | 10 | 0 |
| Ferrara | 10 | 5 | 0 |
| ONGC | 0 | — | 10 (n_eff 1, floor 0.50) |
| **Total** | **22** | **17** | **38** |

**Cross-validation.** The XJTU n₊/n₋ counts computed here reproduce the register's worked
example exactly (3σ 3/1, EWMA 2/2, CUSUM 1/2, Hotelling 2/0, Iso. Forest 2/7, Deep SVDD 3/2,
RMS-trend 2/2) — an independent confirmation of the §4.8 collapse convention.

**Reading.** Equivalence at ±1 h is **established on all three multi-bearing campaigns**
(XJTU-SY, FEMTO, Ferrara: 30/30 cells) and **not established on IMS under either schema** —
there the intervals are wide and, where they exclude the margin, they do so on the
*aggregation-is-better* side. Register item 2.1's drafted abstract clause survives for the
three multi-bearing campaigns; it must **not** be extended to IMS.

### 5G.2 D2 — deep models in the Table 16 sweep ✅ COMPLETE — ⚠️ **§6.1 IS WRONG**

Generator: `src/d2_deep_tradeoff.py`, which calls `src.tradeoff.tradeoff_for_run`
**unmodified**. No code change was needed: `EXPERIMENT["methods_to_run"]` already contains
`lstm_ae`, `tcn`, `transformer_ad`, so Table 16's omission was a run-time choice, not a code
limitation. `tradeoff.py` uses `load_pipeline` (not `load_pipeline_controlled`), so these rows
were never on the 445-dim legacy path and are directly comparable to published Table 16.

**Published Table 16 was verified to reproduce to the digit first** (3σ 77.0/18.1, 60.7/11.7,
56.3/8.9 — matches `tex:717`), so the new rows sit on a confirmed baseline.

Source: `results/tables/tradeoff_IMS_deepmodels.csv`. † = mean FAR_pre > τ = 10%.

| Detector | 95th Ld | 95th FAR | 99th Ld | 99th FAR | 99.5th Ld | 99.5th FAR |
|---|---:|---:|---:|---:|---:|---:|
| LSTM-AE | 199.61 | 87.81† | 193.99 | 82.16† | 93.58 | 62.00† |
| TCN-AE | 185.36 | 82.63† | 183.14 | 79.93† | 180.36 | 74.43† |
| Transformer-AD | 183.97 | 81.05† | 181.75 | 79.18† | 178.69 | 71.99† |

**All nine mean cells are daggered — but that is NOT what the claim says.** The sentence is at
**`paper/files/scada_ijphm.tex:275`**, inside `\subsection{Lead Time and Confidence Intervals on
IMS}` (header at `:274`). **The reviewer's "§6.1" is correct** — `\section{Results}` at `:261` is
§6, so that subsection is §6.1. *(An earlier note here claimed the numbering did not resolve;
that was wrong and is retracted — section numbering was counted properly afterwards:
§6.7 = `:512` Multiple-Comparison Correction, §6.9 = `:638` Trade-off, §6.12 = `:829` Saxena PH.)*
It reads: their pre-onset FAR "ranges from 48% on test 3 to 100% on test 1, far above the
$\tau=10\%$ budget **regardless of threshold**." The per-run data
(`tradeoff_IMS_deepmodels_long.csv`) refute the final clause:

| Run | Detector | Percentile | Lead (h) | FAR_pre | `valid_alarm` |
|---|---|---:|---:|---:|---|
| `3rd_test` | **LSTM-AE** | **99.5** | **59.67** | **4.19%** | **True** |
| `3rd_test` | LSTM-AE | 99.0 | 320.85 | 46.48% | False |
| `3rd_test` | TCN-AE | 99.5 | 320.85 | 42.07% | False |
| `3rd_test` | Transformer-AD | 99.5 | 318.35 | 36.56% | False |

**LSTM-AE has a valid operating point at the 99.5th percentile on IMS test 3.** Tightening the
threshold from the 99th to the 99.5th collapses its FAR from 46.5% to 4.19% and its lead from
320.85 h to 59.67 h — the detector does not "flood regardless of threshold"; it trades lead for
FAR like every other detector, and at a strict enough threshold it lands inside the budget.

**Consequences.**
- "regardless of threshold" must be **corrected, not merely supported** — this is a fifth
  internal contradiction of the species Reviewer D is hunting. Logged as **N-16**.
- **Orthogonal to, and additional to, §5E.1's P8.** P8 already moves the *same sentence*'s
  "48% on test 3" to 61% under the D-2 re-baseline. N-16 is a different defect in that
  sentence: the universal quantifier over thresholds. **Both** must be fixed, and the sweep
  that shows N-16 runs on the standard `load_pipeline` path, so it is unaffected by D-2 —
  the two corrections are independent.
- The abstract's and §5's deep-model framing ("no valid operating point", valid fraction 0/3)
  is true **at the paper's operating threshold (97.5th)** but false as a universal over thresholds.
- The honest replacement is bounded: *at the 95th and 99th percentiles no deep model attains a
  valid operating point on any IMS run; at the 99.5th, LSTM-AE attains one on test 3 only
  (1 of 3 runs, 59.7 h at 4.2% FAR), while TCN-AE and Transformer-AD attain none at any
  percentile tested.*
**Seed-robustness check — the earlier caveat is now DISCHARGED.** Generator
`src/d2_seed_check.py` → `results/tables/d2_seed_check_lstmae.csv`. The one cell carrying N-16
was re-run at **10 seeds** (42, 1–9). **This is a check only; the paper's fixed-seed protocol is
unchanged and seed 42 remains the reported configuration.**

| Quantity | Result across 10 seeds |
|---|---|
| Valid operating point | **10 / 10 seeds (100%)** |
| Pre-onset FAR | **4.19% at every seed** (min = median = max), vs τ = 10% |
| Lead | **59.67 h at every seed** |

**The identical values are not an artifact of an ignored seed — verified.** `LSTMAEDetector.fit`
calls `torch.manual_seed(self.random_state)` and `np.random.seed(...)` (`src/models.py`), and
`make_detectors` injects the seed. Training demonstrably differed: **final loss ranged
0.002736–0.003964** and the **alarm threshold ranged 0.006223–0.008351** (a ~35% spread). Ten
materially different models all land on the same operating point, because at the 99.5th percentile
the threshold falls in a flat region of the score series and the first-crossing window does not move.

So N-16 is **robust, not a seed artifact**, and the FAR sits ~5.8 points inside the budget rather
than marginally under it. The correction to `tex:275` can be stated without a seed caveat.

### 5G.3 D3 — one-class SVM ✅ COMPLETE — **it exists, it runs, D-5's premise is wrong**

**Answer to the reviewer's question: YES.** The released code produces OC-SVM results.

| Evidence | Location |
|---|---|
| Detector implemented | `src/models.py:378` `OneClassSVMDetector` (RBF, `nu`, `gamma`) |
| Dispatched by the factory | `src/models.py:623-624` |
| Hyperparameters configured | `src/config.py:166-170` (`kernel="rbf"`, `nu=0.05`, `gamma="scale"`) |
| Registered as deterministic | `src/benchmark.py:50` `_DETERMINISTIC` |
| Exported | `src/__init__.py:50` |
| **Why no results existed** | absent from `EXPERIMENT["methods_to_run"]` (`config.py:258-269`) — a run-list omission, nothing more |

So §4.5's clause is **runnable, not fabricated**. **Decision D-5 must be revisited**: the register's
"simplest safe path: delete" and the brief's escalation "OC-SVM turns out not to exist" both assumed
the opposite. The numbers now exist, so reporting is available.

Generator `src/d3_ocsvm.py`, seed 42, IMS on the controlled path, the other four on the standard
path — matching how each published sweep was produced.

**Tables 2 / 7 / 8 / 9 — mean raw lead, 95% bootstrap CI, f=1 aggregate**
(`d3_ocsvm_leadtime_ci.csv`, via `benchmark.bootstrap_ci_across_runs`, runs resampled, B=2000, seed 42)

| Dataset | n | Mean lead (h) | 95% CI |
|---|---:|---:|---|
| IMS (Table 2) | 3 | 180.25 | [65.50, 316.68] |
| XJTU-SY (Table 7) | 10 | 1.44 | [0.82, 2.10] |
| FEMTO (Table 8) | 6 | 0.95 | [0.69, 1.30] |
| Ferrara (Table 9) | 6 | 0.98 | [0.52, 1.50] |
| ONGC (n=1, not inferential) | 1 | 35.34 | — |

**Validity — reported under decision D-7's three-outcome convention, which matters here.**
The raw `valid_alarm` column says IMS 1/3, XJTU 4/10, FEMTO 0/6, Ferrara 2/6, ONGC 0/1 — **but every
one of XJTU's four, and one of Ferrara's two, has `far_preonset_pct = NaN`**, i.e. they are
**unscoreable** (defect **N-7**: the FAR gate is skipped when `FAR_pre` is undefined, leaving
`valid_alarm = lead > 0`). Counting them as valid would repeat exactly the defect D-7 was decided to fix.

| Dataset | Valid (gated, genuine) | Invalid | Unscoreable (`FAR_pre` NaN) |
|---|---:|---:|---:|
| IMS | **1** (`3rd_test`, FAR 6.61%) | 2 | 0 |
| XJTU-SY | **0** | 6 | 4 (`Bearing1_3`, `1_5`, `2_2`, `2_5`) |
| FEMTO | **0** | 6 | 0 |
| Ferrara | **1** (`E1`, FAR 9.69%) | 4 | 1 (`E3`) |
| ONGC | **0** | 1 | 0 |
| **Total** | **2 of 26 runs** | 19 | 5 |

**Table 11 — Holm family recomputed at N = 44** (`d3_ocsvm_holm_N44_invariant.csv`, `_legacy.csv`)

*Verification first:* rebuilding the existing 40 cells from the published long files through
`ims_runlevel_table` + `family_holm` reproduces `paired_tests_holm.csv` to floating point
(max |Δ| on `median_diff` 8.3e-17; `n_pos`, `n_neg`, `sign_test_p`, `holm_p` exact; `holm_reject`
identical; 0/40 both). The N=44 family therefore rests on a confirmed rebuild.

| Dataset | Run diffs (h) | Median | n₊/n₋ | Sign-test p | Holm p | Reject |
|---|---|---:|---|---:|---:|---|
| IMS | −2.4, −5.5, +1.5 | −2.43 | 1/2 | 1.0000 | 1.0000 | No |
| XJTU-SY | +0.0 ×5, +0.1, +0.0 ×4 | +0.00 | 1/0 | 1.0000 | 1.0000 | No |
| FEMTO | +0.1, +0.0, +0.1, −0.0, +0.1, −0.4 | +0.04 | 4/2 | 0.6875 | 1.0000 | No |
| Ferrara | −0.2, +0.0, +0.0, +0.0, +0.1, +0.0 | +0.02 | 5/1 | 0.2188 | 1.0000 | No |

**Family verdict: 0 of 44 rejections** — identical under both IMS schemas, and unchanged from 0/40.
**Adding OC-SVM does not disturb the non-destruction headline**; it only widens the family. State that
explicitly in the response letter: the reviewer's requested addition strengthens the null result rather
than threatening it.

**Table 16 — IMS trade-off** (`d3_ocsvm_tradeoff.csv`). † = mean FAR_pre > τ = 10%.

| Percentile | Ld (h) | FAR_pre | per-run FAR range | valid_frac |
|---:|---:|---:|---|---:|
| 95th | 180.25 | 63.21† | 6.6 – 100.0 | 0.33 |
| 99th | 92.47 | 56.68† | 4.0 – 100.0 | 0.33 |
| 99.5th | 92.47 | 55.45† | 0.9 – 100.0 | 0.33 |

**Tables 14 and 22** (`d3_ocsvm_farbudget_phrank.csv`): PH = **180.2 h**;
L(τ=0.05) = L(τ=0.10) = L(τ=0.20) = **0.0** — no valid operating point at any budget on the
mean-across-runs convention the published tables use. In Table 22's ranking OC-SVM would sit
**first on PH** (180.2 h, ahead of Hotelling's 176.9) and **last on L** — the sharpest instance
of the very inversion Table 22 exists to demonstrate. That is a genuine argument *for* reporting it.

> ⚠️ Same per-run nuance as D2: OC-SVM's `valid_frac` is 0.33 at all three percentiles because
> `3rd_test` sits inside budget, while the *mean* FAR is daggered. Tables 14/22 use the mean, so
> the 0.0 entries are correct under the published convention — but the per-run fact must not be
> hidden if the deep-model sentence is being corrected for exactly this reason (N-16).

### 5G.4 D17 — IMS under the ORIGINAL 2004-04-08 test-3 label ✅ COMPLETE

Generator `src/d17_original_label.py`. `config.py` was **not** edited: the label is patched in
memory by a context manager that restores it. Exact here because `load_pipeline_controlled`
loads the cached `*_features.parquet` when present, so `failure_times` never reaches feature
extraction — it changes only the returned `failure_time` and the onset. Features, splits and
windowing are identical between arms, so the contrast isolates the label.
Verified in the log: `failure label for 3rd_test: 2004-04-18 02:42:00 -> 2004-04-08 09:16:00`,
with tests 1 and 2 keeping their own labels.
Corrected arm read from `benchmark_IMS_long_invariant.csv` (D-2), so both arms sit on the 49-dim schema.
Collapse: **mean** over factors and seeds, §4.8. Source: `results/tables/d17_label_comparison.csv`.

**Side by side** — run diffs are (`1st_test`, `2nd_test`, `3rd_test`); floor = attainable two-sided
exact sign-test p at that n_eff.

| Detector | Corrected: diffs | Med | n₊/n₋/0 | p | Original: diffs | Med | n₊/n₋/0 | n_eff | p | floor |
|---|---|---:|---|---:|---|---:|---|---:|---:|---:|
| 3σ | +25.81, +15.10, −1.00 | +15.10 | 2/1/0 | 1.00 | +25.81, +15.10, **0.00** | +15.10 | 2/0/1 | **2** | 0.50 | 0.50 |
| CUSUM | +4.15, +4.67, +4.27 | +4.27 | 3/0/0 | 0.25 | +4.15, +4.67, **0.00** | +4.15 | 2/0/1 | **2** | 0.50 | 0.50 |
| EWMA | −3.89, +4.33, +2.10 | +2.10 | 2/1/0 | 1.00 | −3.89, +4.33, **0.00** | +0.00 | 1/1/1 | **2** | 1.00 | 0.50 |
| Hotelling T² | +1.00, +1.17, +81.74 | +1.17 | 3/0/0 | 0.25 | +1.00, +1.17, +35.30 | +1.17 | 3/0/0 | **3** | 0.25 | 0.25 |
| Iso. Forest | −0.67, +16.87, +3.43 | +3.43 | 2/1/0 | 1.00 | −0.67, +16.87, **0.00** | +0.00 | 1/1/1 | **2** | 1.00 | 0.50 |
| Deep SVDD | +8.93, 0.00, 0.00 | 0.00 | 1/0/2 | 1.00 | +8.93, 0.00, **0.00** | 0.00 | 1/0/2 | **1** | 1.00 | 1.00 |
| RMS-trend | −0.17, 0.00, +2.37 | 0.00 | 1/1/1 | 1.00 | −0.17, 0.00, **0.00** | 0.00 | 0/1/2 | **1** | 1.00 | 1.00 |
| LSTM-AE | −1.39, −0.42, +56.12 | −0.42 | 1/2/0 | 1.00 | −1.39, −0.42, +41.33 | −0.42 | 1/2/0 | **3** | 1.00 | 0.25 |
| TCN-AE | −1.39, −0.42, +9.00 | −0.42 | 1/2/0 | 1.00 | −1.39, −0.42, +9.00 | −0.42 | 1/2/0 | **3** | 1.00 | 0.25 |
| Transformer-AD | −1.39, −0.42, +68.79 | −0.42 | 1/2/0 | 1.00 | −1.39, −0.42, +48.15 | −0.42 | 1/2/0 | **3** | 1.00 | 0.25 |

**⚠️ The register's anticipated result is WRONG and must be rewritten.** Register 1.4 pre-wrote:
*"Under the old label, test 3 is a guaranteed miss for every detector (L = 0) … and IMS effectively
falls to n = 2."* Measured, test 3 is a guaranteed miss for **6 of 10 detectors, not all ten**:

| Detector | test-3 agg (h) | test-3 dec (h) | diff | guaranteed miss? |
|---|---:|---:|---:|---|
| 3σ, CUSUM, EWMA, Iso. Forest, Deep SVDD, RMS-trend | 0.00 | 0.00 | 0.00 | **yes** — drops out |
| Hotelling T² | 51.78 | 16.48 | +35.30 | no |
| LSTM-AE | 107.94 | 66.60 | +41.33 | no |
| TCN-AE | 123.96 | 114.96 | +9.00 | no |
| Transformer-AD | 92.48 | 44.33 | +48.15 | no |

Those four alarm early enough to still precede the *earlier* failure time, so they keep a
positive lead in both modes and their runs survive the zero-difference exclusion.

**Effective n and the floor — the item's actual question, answered per detector.**

| n_eff under original label | Detectors | Two-sided floor |
|---:|---|---:|
| 3 | Hotelling T², LSTM-AE, TCN-AE, Transformer-AD | 0.25 |
| 2 | 3σ, CUSUM, EWMA, Iso. Forest | **0.50** |
| 1 | Deep SVDD, RMS-trend | **1.00** |

So the honest statement is **not** "IMS falls to n = 2" but: *under the original label test 3 becomes
a guaranteed miss for six of ten detectors and drops out of the sign-test count under §4.8's
zero-difference exclusion. For those six the effective n falls from 3 to 2 (four detectors) or to 1
(two detectors), where the exact two-sided sign test floors at p = 0.50 and p = 1.00 respectively and
can never reach α at any margin. The four remaining detectors keep n = 3 and a floor of 0.25 — which
is itself already above α, so **no IMS detector can reach significance under either label**.*

**What does NOT change.** The direction is stable: **no median flips sign** between labels; 3σ holds
at **+15.10 h** and Hotelling at **+1.17 h**. The best attainable p is **0.25 under both labels**
(Hotelling), so the Holm verdict and the non-destruction headline are untouched by the relabel.
The contrast is computed *within* each run, so the label cannot inflate it.

**An honest point that cuts the author's way — state it, do not hide it.** Under the *original*
label 3σ's test-3 difference becomes exactly 0.00 and drops out, leaving **2 positive, 0 negative**.
So `tex:480`'s withdrawn claim *"in no run does aggregation shorten their lead time"* would be
**true under the original label** and is false only under the corrected one (where test 3 gives
−1.00 h). The author chose the label that makes the paper's own claim harder to support. That is
worth saying plainly in Appendix C — it pre-empts the suspicion that the relabel was
result-motivated, which is precisely what Reviewer D is probing.

## 5H. N = 40 → N = 44 change inventory (decision D-5: REPORT OC-SVM)

**Method, per brief rule 10.** The PDF (`paper/files/scada_ijphm.pdf`, built 2026-07-08 00:50,
one minute after the `.tex` was last saved — they correspond) was text-extracted and cross-checked
against the source. **Do not repeat this with a bare `.tex` grep.**

*Extractor calibration against the brief's reference counts* — `pdftotext` **failed** (`does not
cost` 1 vs 2: its reading order interleaves a citation through the sentence). **PyMuPDF (`fitz`)
passed** and is the tool to use. Hyphenation must be handled as `-\n → -`, **not** `-\n → ""`,
or genuine compounds are destroyed (`non-\ndestruction` → `nondestruction`).

| Target | Brief | Measured (fitz) | Note |
|---|---:|---:|---|
| never better | 3 | 3 | ✅ |
| never costs | 2 | 2 | ✅ |
| does not cost | 2 | 2 | ✅ |
| honest/honestly | 18 | 17 + 1 `hon-\nest` = **18** | ✅ after hyphen fix |
| non-destruction | 20 | **21** distinct contexts, no duplicates | ⚠️ **one MORE than the brief** — the brief's 20 appears to undercount by one; re-verify before any occurrence sweep that relies on it |
| em-dashes | 180 | 180 | ✅ |

*Reconciliation of the family-size sweep.* A context-window sweep of the PDF first returned **12**
occurrences against the source's 16 — adjacent hits were being swallowed by window overlap and
de-duplication. Exact-string counting reconciles them **exactly at 16 = 16**:

| Form | PDF | tex |
|---|---:|---:|
| `N = 40` / `$N=40$` | 9 | 9 |
| `10 × 4 = 40` | 1 | 1 |
| `0 of 40` | 2 | 2 |
| `forty` | 3 | 3 |
| `(1−0.05)^40` | 1 | 1 |
| **Total** | **16** | **16** |

**Derived values at N = 44** (from `results/tables/d3_ocsvm_holm_N44_invariant.csv`):
uncorrected FWER `1−(1−0.05)^44` = **0.8953** (was 0.8715 at N=40); **0 of 44 rejected**;
smallest raw p still **0.0312** (Isolation Forest on FEMTO), Holm-adjusted still **1.00**.

### The 16 atomic edits

| # | tex line | Location | Current | Required |
|---:|---:|---|---|---|
| 1 | 63 | **Abstract** | `$N=40$ family` | `$N=44$ family` |
| 2 | 95 | Introduction, Contribution 4 | `$N=40$ family` | `$N=44$ family` |
| 3 | 268 | Results, item (iii) | `$N=40$ detector $\times$ dataset family` | `$N=44$ …` |
| 4 | 513 | §Multiple-Comparison Correction | `$10 \times 4 = 40$ detector $\times$ dataset tests` | `$11 \times 4 = 44$ …` |
| 5 | 513 | ″ | `$1 - (1-0.05)^{40} \approx 0.87$` | `$1 - (1-0.05)^{44} \approx 0.90$` |
| 6 | 513 | ″ | `the forty run-level sign-test $p$-values` | `the forty-four …` |
| 7 | 513 | ″ | `No hypothesis survives (0 of 40)` | `(0 of 44)` |
| 8 | 513 | ″ | `across the $N=40$ family its adjusted $p$ is 1.00` | `$N=44$` — **adjusted p stays 1.00**, verified |
| 9a | 513 | ″ | `so the $N=40$ count` | `$N=44$ count` |
| 9b | 513 | ″ | `is not read as forty equally-powered tests` | `forty-four equally-powered tests` |
| 10 | 517 | **Table 11 caption** | `across the $N=40$ detector $\times$ dataset family` | `$N=44$ …` |
| 11 | 517 | ″ | `(0 of 40 survive)` | `(0 of 44 survive)` |
| 12 | 517 | ″ | `The $N=40$ family is the full evaluated set of ten detectors (nine headline plus the additionally-evaluated Deep SVDD)` | `The $N=44$ family … **eleven detectors** (nine headline plus the additionally-evaluated Deep SVDD **and one-class SVM**)` |
| 13 | 930 | §Summary of Key Outcomes, item (4) | `$N=40$ detector $\times$ dataset family` | `$N=44$ …` |
| 14 | 945 | §Limitations and Threats to Validity | `the forty-test family` | `the forty-four-test family` |
| 15 | 949 | **Conclusion** | `$N=40$ family` | `$N=44$ family` |

> tex:945 sits in `\section{Limitations and Threats to Validity}`, **not** in §7.4 — so Phase 6's
> deletion of §7.4 does **not** remove it. Confirmed by resolving the enclosing header.

### Phrases that must change with them (not "40", but wrong once OC-SVM is in)

| tex line | Location | Current | Required |
|---:|---|---|---|
| 235 | §Detectors | `We also evaluate Deep SVDD … and one-class SVM` | **now TRUE as written** — this is the sentence D-5 makes honest. Add the pointer to the new rows. |
| 279 | Table 2 caption | `all ten evaluated detectors (the nine headline detectors plus Deep SVDD)` | `all **eleven** … (nine headline plus Deep SVDD **and one-class SVM**)` |
| 426 | §FEMTO | `Across all ten evaluated detectors …, **191/600** evaluations yield a valid alarm` | `all **eleven** …, **193/660**` — published 191/600 verified to reproduce; OC-SVM adds 2 valid of 60 |
| 430 | Table 8 caption | `All ten evaluated detectors (nine headline plus Deep SVDD) run on the full $n=6$` | `All **eleven** … (… plus Deep SVDD and one-class SVM)` |
| 480 | §Aggregate vs Decimate on IMS | `the run-level test over all ten evaluated detectors` | `all **eleven** …` |
| 970 | Conclusion | `not compute-bound for any of the ten evaluated detectors` | `… **eleven** …` — ⚠️ **needs a Table 25 timing row for OC-SVM before this can be claimed**; not yet measured |
| 224 / 85 / 63 | §Detectors, Intro, Abstract | `nine detectors` (headline set) | **unchanged** — OC-SVM joins the *additionally evaluated* tier, not the headline nine (D-5) |

**Open sub-item flagged, not silently assumed:** tex:970's compute claim would extend to OC-SVM,
but no OC-SVM timing exists in `compute_cost_IMS_*.csv`. Either measure it or scope the sentence
to the ten timed detectors. Recorded so it is not missed.

## 5I. CONSOLIDATED CLAIM-DELTA INVENTORY — D-2 + D2 + D3 + D15 + D17

**The spine of both the revision and the Response to Review.** Supersedes nothing in §5E; it
*merges* §5E (D-2) with the session-4 items. Driver codes: **[D-2]** invariant re-baseline ·
**[D2]** deep models in the threshold sweep (N-16) · **[D3]** one-class SVM (N=44) ·
**[D15]** equivalence at δ=1 h · **[D17]** original test-3 label.

### 5I.1 ⚠️ COLLISION SENTENCES — where two or more items hit one sentence

These must be rewritten **once, combining all drivers**. Editing them per-item will corrupt them.

---

**`tex:275`** — §Lead Time and Confidence Intervals on IMS. **Four drivers: [D-2]×3 + [D2].**

| Driver | Element | Old | New |
|---|---|---|---|
| [D-2] P19 | which classical detector leads | "EWMA and Isolation Forest lead the classical detectors" | **Hotelling T² leads** (174.8 h), ahead of Iso. Forest (87.2) and EWMA (78.6) |
| [D-2] P7 | deep raw leads | 199–215 h | **183–198 h** |
| [D-2] P8 | deep pre-onset FAR range | "48% on test 3 to 100% on test 1" | **61% on test 3 to 100% on tests 1–2** |
| [D-2] P9 | deep valid-alarm fraction | 0/3 | **unchanged (0/3)** |
| **[D2] N-16** | **"regardless of threshold"** | asserted universal | **FALSE — must be bounded** |

**Combined requirement.** One sentence cannot carry both the corrected FAR range *and* the
threshold bound, because they describe different experiments (the operating threshold vs. the
sweep). Split into two: (a) at the paper's 97.5th-percentile operating point the deep models
score L=0 on all three runs with pre-onset FAR 61–100%; (b) **across the swept thresholds
(Table 16) no deep model attains a valid operating point at the 95th or 99th percentile, and at
the 99.5th LSTM-AE attains one on test 3 alone (59.7 h at 4.19% FAR; 10/10 seeds)** — TCN-AE and
Transformer-AD attain none at any percentile. Delete "regardless of threshold" outright.
Sources: `benchmark_IMS_long_invariant.csv`, `tradeoff_IMS_deepmodels_long.csv`, `d2_seed_check_lstmae.csv`.

---

**`tex:63`** — **Abstract**. **Three drivers: [D-2]×2 + [D3] + [D15].**

| Driver | Element | Old | New |
|---|---|---|---|
| [D-2] P1 | 3σ IMS median | +18.4 h | **+15.1 h** |
| [D-2] P2 | "a consistent positive trend … variance-sensitive charts" | asserted | **withdraw** — 3σ, EWMA, IsoF each 2+/1− |
| [D-2] P3 | smallest adjusted p | 1.00 | unchanged |
| **[D3]** | `$N=40$ family` | 40 | **44** |
| **[D15]** | `does not cost bearing-fault warning time` | null-acceptance | **bounded equivalence** (below) |

**Combined requirement.** The abstract currently asserts a *universal* non-destruction from a
*non-rejection*. Replace with the measured bound: *equivalence at a pre-specified ±1 h
operational margin is established on all three multi-bearing campaigns (XJTU-SY, FEMTO, Ferrara;
30/30 dataset×detector cells) and is **not** established on IMS, where the intervals are wide and,
where they exclude the margin, do so on the aggregation-is-better side.* Do **not** paste register
item 2.1's drafted clause — it presumes equivalence holds everywhere.

---

**`tex:930`** — §Summary of Key Outcomes. **[D15] + [D3] + [D-2].**
(1) "SCADA bin-averaging **never costs** lead time relative to decimation" → bounded equivalence
statement, scoped to the three multi-bearing campaigns; (2) IMS magnitudes per §5E.1;
(4) `$N=40$` → **`$N=44$`**.

**`tex:949`** — **Conclusion**. **[D15] + [D3].**
"decimation is **never better**" → bounded; `$N=40$` → **`$N=44$`**.

**`tex:480`** — §Aggregate vs Decimate on IMS. **[D-2] P16/P17 + [D3] + [D17].**
"in no run does aggregation shorten their lead time" is **false** under the corrected label and
must be withdrawn ([D-2]); "all ten evaluated detectors" → **eleven** ([D3]); and **[D17]** supplies
the honest footnote — *under the original label 3σ's test-3 difference is exactly 0.00 and drops
out, so the withdrawn claim would have been true there; the corrected label is the harder one.*

**`tex:513` / `tex:517`** — §Multiple-Comparison Correction + Table 11 caption. **[D3] only**,
10 atomic edits, itemised in **§5H**. [D-2] P18 confirms the smallest raw p (0.031) and the
0-rejection verdict are unchanged.

### 5I.2 Tables

| Table | tex | Driver | Change |
|---|---:|---|---|
| **2** `tab:imslead` | 280 / rows 286–297 | [D-2] + [D3] | All ten values + row order per §5E.2, **plus a new OC-SVM row 180.25 [65.50, 316.68]**, which inserts at **rank 4** (below Transformer-AD 183.4, above Hotelling T² 174.8). Caption `:279` "all ten evaluated detectors (nine headline plus Deep SVDD)" → **eleven … plus Deep SVDD and one-class SVM** |
| **7** `tab:xjtu` | 401 | [D3] | new OC-SVM row: **1.44 h [0.82, 2.10]**, n=10 |
| **8** `tab:femto` | 431 | [D3] | new OC-SVM row: **0.95 h [0.69, 1.30]**, n=6; caption `:430` ten → **eleven** |
| **9** `tab:ferrara` | 457 | [D3] | new OC-SVM row: **0.98 h [0.52, 1.50]**, n=6 |
| **10** `tab:imssweep` | 492 / rows 497–506 | [D-2] | all ten rows + **sign-consistency column changes on 7 of 10** (§5E.4) |
| **11** `tab:holm` | 518 / rows 523–532 | [D-2] + [D3] | 7 of 10 IMS raw p move (§5E.5); **4 new OC-SVM rows** — IMS 1.0000, XJTU-SY 1.0000, FEMTO 0.6875, Ferrara 0.2188, all Holm p 1.0000, none rejected; caption per §5H |
| **5** `tab:persistence` | 367–370 | [D-2] | §5E.3, incl. N-15's 1.00 → **0.67** |
| **14** `tab:farbudget` | 675 | [D3] + [D2] | new OC-SVM row **0.0 / 0.0 / 0.0**; if the deep rows are added for consistency, all three are **0.0 / 0.0 / 0.0** |
| **16** `tab:tradeoff` | 711 | [D2] + [D3] | **4 new rows** — LSTM-AE 199.61/87.81† · 193.99/82.16† · 93.58/62.00† ; TCN-AE 185.36/82.63† · 183.14/79.93† · 180.36/74.43† ; Transformer-AD 183.97/81.05† · 181.75/79.18† · 178.69/71.99† ; OC-SVM 180.25/63.21† · 92.47/56.68† · 92.47/55.45† |
| **22** `tab:phrank` | 864 | [D3] + [D2] | new OC-SVM row **PH 180.2 / L 0.0 / not valid**; see the ⚠️ below |
| **25** `tab:compute` | 1013–1021 | [D-2] + [D3] | §5E.7 ratio; **OC-SVM timing NOT measured** — blocks `tex:970` |

> ### ⚠️ The D-5 rationale needs one correction before it goes in the response letter
>
> The recorded rationale is that OC-SVM "ranks **first** on PH". That is true **only against
> Table 22's current seven-row set** (OC-SVM 180.2 > Hotelling 176.9). But **[D2] adds LSTM-AE,
> TCN-AE and Transformer-AD to Table 16**, and if Table 22 gains the same rows for consistency the
> PH ranking becomes: **LSTM-AE 199.6, TCN-AE 185.4, Transformer-AD 184.0, OC-SVM 180.2**,
> Hotelling 176.9, … So OC-SVM would rank **4th, not 1st**.
>
> **The inversion argument survives either way and is in fact stronger** — the top four on PH all
> score **L = 0.0**, so four detectors, not one, invert. But the response letter must say
> *"OC-SVM ranks first among the non-deep detectors on PH and last on L"*, or add the deep rows
> and describe a four-way inversion. **Do not write "first on PH" unqualified.**
> Author decision needed: do Tables 14 and 22 gain the deep rows alongside Table 16?

### 5I.3 Figures

| Figure | tex | Driver | Change |
|---|---:|---|---|
| **F2** `fig:crossdataset` | 418–421 | [D-2] | IMS column → Table 10's new medians |
| **F3** `fig:sweep` | 482–486 | [D-2] | full IMS curve, §5E.6 |
| **F6** `fig:tradeoff_ims` | 653 | [D2] + [D3] | regenerate — **4 new curves**; currently plots 7 detectors |
| F1, F4, F7, F9 | 303, 617, 651, 665 | — | no change |

### 5I.4 New content required

| Item | Driver | Content |
|---|---|---|
| **Appendix C** | [D17] | Side-by-side original-vs-corrected label table, all ten detectors (§5G.4). Must state: test 3 is a guaranteed miss for **6 of 10** detectors, not all ten; n_eff falls to 2 (four detectors) or 1 (two) and stays 3 for four; **no median flips sign**; best p = 0.25 under both labels; and the relabel made the paper's claim *harder*, not easier |
| **§ equivalence paragraph** | [D15] | δ=1 h pre-specified on operational grounds *before* results; bootstrap CI as primary; TOST only where n₊+n₋ ≥ 5 with the attainable floor shown beside every cell; **22/60 feasible, 17 equivalent**; infeasible cells reported as untestable, never as null findings |
| **§4.5 pointer** | [D3] | `tex:235`'s "and one-class SVM" becomes **true**; add the table pointers, matching the Deep SVDD sentence pattern |
| **§ deep-model bound** | [D2] | the bounded replacement for "regardless of threshold" (§5I.1, `tex:275`) |

### 5I.5 Unchanged — state explicitly in the response letter

The **0-rejection Holm verdict** (0/40 → **0/44**), the **non-destruction headline direction**,
the smallest raw p (**0.031**, Iso. Forest on FEMTO, Holm-adjusted **1.00** at both family sizes),
IMS onset (identical 300/300), Tables 3, 4, 6, 13, 17–20, 27, 28, and Figures 1, 4, 5, 7, 8, 9, 11.

## 5J. D-9 — Tables 14 and 22 rebuilt with all eleven detectors ✅ COMPLETE

Generator `src/d9_tables_14_22.py` → `results/tables/d9_tables_14_22_eleven.csv`.
Convention verified against the published tables before use: candidates are the three swept
percentiles {95, 99, 99.5}, and the budget test is on the **mean** pre-onset FAR across runs.
(Checks: published 3σ PH = 77.0 is the max over those three, not the 90th's 163.8; published
Deep SVDD L(0.05) = 14.8 is the 95th, not the 90th's 34.7.)

### Table 14 (`tab:farbudget`, tex:675) — best valid lead (h) per budget

| Detector | τ=0.05 | τ=0.10 | τ=0.20 | min mean FAR |
|---|---:|---:|---:|---:|
| LSTM-AE **(new)** | 0.0 | 0.0 | 0.0 | 62.00% |
| TCN-AE **(new)** | 0.0 | 0.0 | 0.0 | 74.43% |
| Transformer-AD **(new)** | 0.0 | 0.0 | 0.0 | 71.99% |
| One-Class SVM **(new)** | 0.0 | 0.0 | 0.0 | 55.45% |
| Hotelling T² | 0.0 | 0.0 | 73.9 | 18.99% |
| Iso. Forest | 0.0 | 0.0 | 53.4 | 19.80% |
| EWMA | 0.0 | 0.0 | 0.0 | 21.01% |
| 3σ | 0.0 | **56.3** | 77.0 | 8.89% |
| CUSUM | 0.0 | 0.0 | 65.0 | 18.99% |
| RMS-trend | 34.7 | 34.7 | 34.7 | 0.00% |
| Deep SVDD | 14.8 | 14.8 | 14.8 | 0.00% |

**All seven published rows are unchanged** — the four new rows are additions only.

### Table 22 (`tab:phrank`, tex:864) — PH vs gated L

| Method | PH | Rk | L | L Rk | Valid? |
|---|---:|---:|---:|---:|---|
| LSTM-AE **(new)** | 199.6 | 1 | 0.0 | 4 | no |
| TCN-AE **(new)** | 185.4 | 2 | 0.0 | 4 | no |
| Transformer-AD **(new)** | 184.0 | 3 | 0.0 | 4 | no |
| One-Class SVM **(new)** | 180.2 | 4 | 0.0 | 4 | no |
| Hotelling T² | 176.9 | 5 | 0.0 | 4 | no |
| Iso. Forest | 174.7 | 6 | 0.0 | 4 | no |
| EWMA | 89.1 | 7 | 0.0 | 4 | no |
| **3σ** | 77.0 | **8** | **56.3** | **1** | **yes** |
| CUSUM | 65.0 | 9 | 0.0 | 4 | no |
| RMS-trend | 34.7 | 10 | 34.7 | 2 | yes* |
| Deep SVDD | 14.8 | 11 | 14.8 | 3 | yes |

> ### ✅ SETTLED: the inversion is SEVEN-way — use these figures everywhere
>
> **The top SEVEN detectors by prognostic horizon all score L = 0**, and the deployable chart
> **3σ ranks EIGHTH of eleven on PH while ranking FIRST on L.** For contrast, the *published*
> seven-row Table 22 is only a **three-way** inversion with 3σ 4th, so D-9 roughly doubles the
> demonstration's reach.
> **"Top four / ranks fifth" is superseded and must not appear** in §6.12, Table 22's caption,
> the D-5 or D-9 rationale, or the Response to Review. Corrected at both §4 rationale sites.

### The LSTM-AE question — answered: **NO**

**LSTM-AE attains no valid operating point in Table 14 at any τ**, including τ=0.20.
Its minimum *mean* pre-onset FAR over the three percentiles is **62.00%** (at the 99.5th).

**This does not contradict N-16, and the distinction must be kept straight in the manuscript:**

| | Quantity | Value | Consequence |
|---|---|---|---|
| Table 14 / 22 | **mean** FAR across the 3 runs at 99.5th | **62.00%** | L = 0.0 at every τ — the row is all zeros |
| N-16 / §6.1 | **per-run** FAR, `3rd_test` at 99.5th | **4.19%** | a valid operating point **exists**, so "regardless of threshold" is false |

Both are true. Table 14's zeros describe the mean across runs; §6.1's claim quantifies over
*thresholds*, and one run inside budget at one threshold defeats it. **Do not cite Table 14's
0.0 row as evidence that the deep models have no valid operating point regardless of threshold** —
that would rebuild the same defect N-16 identifies, in a new location.

### §6.9's 3σ recommendation — **HOLDS, unchanged**

Detectors with a valid operating point at τ=0.10, best lead first: **3σ 56.3 h**, RMS-trend 34.7 h,
Deep SVDD 14.8 h. **3σ remains the best valid chart at τ=0.10**, so §6.9 (`tex:638–728`) and
Table 14's caption (`tex:674`, "the 3σ recommendation holds at τ=0.10 and 0.20 but not at a strict
τ=0.05") need **no correction**. None of the four added detectors reaches a valid point at any τ,
so they cannot displace it. State this explicitly in the response letter: the reviewer-requested
additions were checked against the recommendation and left it standing.

## 5K. Table 25 completion + deep-model parameter counts ✅ COMPLETE

Generator `src/d3_compute_cost_extra.py`, which **imports `time_detector` from
`src/compute_cost_ims.py`** rather than reimplementing it, so the protocol is identical by
construction: largest IMS run (`3rd_test`), 631 train / 506 test windows, single CPU core
(`OMP/MKL/OPENBLAS_NUM_THREADS=1`, `torch.set_num_threads(1)`), median of five repeats.

### 5K.1 ⚠️ A pre-existing gap, found while doing this — defect N-17

The three deep models were **already timed** (`compute_cost_IMS_invariant.csv`, 9 rows).
What was missing was **two** detectors, not one:

- **`one_class_svm`** — expected, added by D-5;
- **`rms_trend`** — **missing before OC-SVM ever came up.** Table 25 (`tex:1013–1021`) has
  **nine** rows, yet `tex:970` claims monitoring "is therefore not compute-bound for any of the
  **ten** evaluated detectors". **The sentence already overreached its own table by one detector
  in the submitted manuscript.** Logged as **N-17 (Medium)**.

Both are now measured, so Table 25 can carry all **eleven** evaluated detectors and `tex:970`
becomes true as "eleven".

### 5K.2 New Table 25 rows (`results/tables/compute_cost_IMS_extra_invariant.csv`)

| Detector | Train | Inference (µs/win) |
|---|---:|---:|
| One-Class SVM (ν=0.05) | 10.8 ms | **25.83** |
| RMS-Trend (kσ) | <1 ms (0.33 ms) | **0.29** |

Context on the same machine and schema (`compute_cost_IMS_invariant.csv`): 3σ 0.22 µs/win,
Isolation Forest 119.7, LSTM-AE 513.4. **OC-SVM at 25.8 µs/win is cheaper than Isolation Forest
and ~20× cheaper than the deep models**, so it does not disturb `tex:970`'s conclusion — the
sentence holds once restated to eleven.

> ⚠️ **Report ratios, not absolutes** (§5E.7). This machine is not the machine that produced the
> published Table 25 (published LSTM-AE 7.8 s train vs 49.45 s measured here). The two new rows
> are measured on the **same machine as the existing nine**, so same-machine ratios are valid;
> the published absolute column must be regenerated wholesale or reported as ratios.

### 5K.3 Deep-model architecture table — register item 3.3 (G5)

Parameter counts measured at the **49-dim invariant schema, seq_len 30**
(`results/tables/deep_model_params.csv`); hyperparameters transcribed verbatim from
`src/config.py` `MODELS` as register 3.3 requires.

| Model | Config (`config.py` `MODELS`) | Total params | Trainable |
|---|---|---:|---:|
| **LSTM-AE** | `seq_len 30, latent_dim 16, hidden_dim 64, epochs 50, batch 32, lr 1e-3, dropout 0.1` | **54,657** | 54,657 |
| **TCN-AE** | `seq_len 30, channels 32, kernel_size 3, levels 4, epochs 40, batch 32, lr 1e-3, dropout 0.1` | **29,681** | 29,681 |
| **Transformer-AD** | `seq_len 30, d_model 32, nhead 2, num_layers 2, dim_feedforward 64, epochs 40, batch 32, lr 1e-3, dropout 0.1` | **20,305** | 20,305 |

For completeness, the two non-sequence additions: **Deep SVDD** `hidden_dim 32, latent_dim 8,
epochs 40`; **One-Class SVM** `kernel rbf, nu 0.05, gamma scale`.

**The data-starvation caveat is now quantifiable, which strengthens §4.5.** LSTM-AE fits
**54,657 parameters** to **631 training windows** — roughly **87 parameters per training
window**. That is the concrete form of the manuscript's existing "with on the order of 100 normal
training windows they are data-starved" remark (`tex:235`), and it is worth stating numerically.

---

## 5L. FIRST MANUSCRIPT EDITS APPLIED — session 4

**Branch `ijphm-r1`. Two sites written to `paper/files/scada_ijphm.tex`; nothing else touched.**
Diff reviewed and approved by the author before writing.

> ⚠️ **`paper/` is gitignored (N-3), so git cannot restore these lines.** A backup of the
> post-edit file and an exact reverse patch are at
> `<scratchpad>/scada_ijphm_AFTER_session4_edit.tex` and `<scratchpad>/reverse_patch_session4.json`.
> **Scratchpad is session-scoped — copy both somewhere durable before this session ends.**

### 5L.1 `tex:63` — abstract, rewritten

Length **257 → 285 words (+28, +11%)**. The overrun is a direct consequence of the author's own
revisions 1 and 3 (self-evident detector count; restore both halves of the IMS cell split);
the three accepted cuts had already brought a longer draft down to +12.

| Element | New value | Source |
|---|---|---|
| detector count | **"Eleven detectors"**, enumerated so 11 × 4 = 44 is self-evident | D-5/D-9; headline-nine distinction stays in §4.5 |
| 3σ IMS median | **+15.1 h** (was +18.4) | `results/tables/ims_runlevel_test_invariant.csv` |
| consistency | **"but the direction is not consistent across the three runs"** (was "a consistent positive trend appears") | same |
| family size | **N = 44**, smallest adjusted p = 1.00 | `results/tables/d3_ocsvm_holm_N44_invariant.csv` |
| equivalence | **30/30 cells** equivalent at ±1 h on the three multi-bearing campaigns | `results/tables/d15_equivalence_bootstrap.csv` |
| IMS split | **8 of 10 undecided, other 2 favour aggregation beyond margin** | same |
| decimation exception | **Isolation Forest on FEMTO −0.26 h, 95% CI [−0.54, −0.06]**, inside the margin | same |

Also removed: "The metric correctly refuses to manufacture a positive effect" (self-descriptive,
serves item 2.4) and "the aggregate-vs-decimate difference is null (median |diff| ≤ 8 min)"
(the null-acceptance phrasing D18/F5 objected to, now superseded by the equivalence sentence).

### 5L.2 `tex:275` — split into two sentences, plus the P19 clause

**Sentence 1** now scopes to the operating point: raw leads **183–198 h**, valid-alarm fraction
**"at that threshold is 0/3"**, pre-onset FAR **61% on test 3 to 100% on tests 1–2**.
**Sentence 2** carries the N-16 correction: "Sweeping the alarm threshold **changes this only
once**" — TCN-AE and Transformer-AD attain no valid point at any level; **LSTM-AE attains one at
the 99.5th percentile on test 3 alone, 59.7 h at 4.19% FAR, unchanged across ten seeds**,
fraction 1/3. **"regardless of threshold" is now absent from the whole file** (verified).
**P19 clause:** "EWMA and Isolation Forest lead the classical detectors" →
**"Hotelling $T^2$ leads the classical detectors"** (174.8 vs Iso. Forest 87.2, EWMA 78.6,
`benchmark_IMS_leadtime_ci_invariant.csv`).

### 5L.3 ⚠️ NEW DEFECT N-18 — found by the revision-7 sweep, NOT yet edited

The sweep for downstream EWMA-as-leader claims found **four sites**. One is fixed (tex:275).
The other three are at **`tex:640` (§6.9) and `tex:654` (Figure 6 caption)** and are **left
untouched pending the author's decision**. Two of the three are wrong **independently of D-2**:

| Site | Text | Status |
|---|---|---|
| `tex:640` | "a ranking that the raw-lead column of Table~
ef{tab:imslead}, **where EWMA leads**, would by itself obscure" | **False under D-2.** In Table 2, EWMA is 6th (78.6 h); Hotelling T² leads the classicals (174.8), LSTM-AE leads overall (197.6) |
| `tex:640` | "**EWMA attains the highest raw lead in Table~
ef{tab:tradeoff}**" | ⚠️ **FALSE IN THE SUBMITTED MANUSCRIPT.** Published Table 16 gives Hotelling T² **176.9** and Iso. Forest **174.7** against EWMA **89.1**. The sentence contradicts the table it cites, on the same page — **nothing to do with D-2** |
| `tex:640` + `tex:654` | "**EWMA and Isolation Forest dominate** the upper-left of the curve" (prose + figure caption) | ⚠️ **Misleading as published.** Over the full swept curve Hotelling T² **strictly dominates** EWMA on both axes (max lead 187.8 vs 174.8; min FAR 19.0 vs 20.8). Iso. Forest is defensible; EWMA is not |

**This is a sixth internal contradiction of the species Reviewer D is hunting**, and — like N-17 —
**it was found unprompted and predates the re-baseline.** Sources: `results/tables/tradeoff_IMS.csv`,
`results/tables/benchmark_IMS_leadtime_ci_invariant.csv`. Disclose in the Response to Review.

---

## 5M. Second edit pass — item 2.1 + N-18 (partial) — session 4

**Seven edits written to `paper/files/scada_ijphm.tex` on `ijphm-r1`, diffs approved beforehand.**
The manuscript source is now **tracked** (commits `fc66f98` baseline, `e23125a` first pass), so
these have a real undo for the first time.

### 5M.1 Item 2.1 — the bounded form, five prose sites

| tex | Section | Was | Now |
|---:|---|---|---|
| 87 | Intro summary | "non-destruction---decimation is **never better**, and averaging is at worst neutral" | bounded form + exception |
| 95 | Contribution 4 | "while decimation is **never better**" | bounded form + exception |
| 922 | Discussion | "coarse aggregation **never costs** warning time" | bounded form + exception |
| 930 | Summary (1) | "SCADA bin-averaging **never costs** lead time" | bounded form + exception |
| 949 | Conclusion | "while decimation is **never better**" | bounded form + exception |

Common wording, matching the abstract: *"no dataset × detector cell shows decimation superior
beyond a ±1 h operational margin, and the one place decimation leads, Isolation Forest on FEMTO
(−0.26 h, 95% CI [−0.54, −0.06]), lies inside it."*
Source: `results/tables/d15_equivalence_bootstrap.csv`.

**Rule 10 verification — done properly, on a REBUILT PDF.** The shipped PDF was stale (2026-07-08),
so it was recompiled with `tools/tectonic.exe` and swept with PyMuPDF:
**"never better" → 0, "never costs" → 0.** A source grep alone would not have satisfied rule 10.

Two count reconciliations, both benign: *"operational margin"* reads 4 in hyphen-keeping form and
**6** in hyphen-dropping form (two instances render as `oper-ational`) — 6 is correct and matches
the six sites. *"Isolation Forest on FEMTO"* reads **7** = the six added plus **one pre-existing**
in §6.7's Holm sentence ("smallest raw p-value is 0.031 (Isolation Forest on FEMTO)"), not a duplicate.

Two incidental effects, both recorded rather than hidden:
- **"honest" 18 → 17.** `tex:922`'s "The **honest** synthesis" became "The synthesis" — one of item 2.4's 18 self-descriptive statements, retired early.
- **"non-destruction" 21 → 20.** The abstract's instance was replaced by "bounded equivalence" in §5L.1.
- ⚠️ **em-dashes 180 → 184.** The new clauses added four. **This runs against Phase 7's reduction target** (~100 live). Phase 7 must revisit these five sentences; the repeated 20-word exception clause is also five-fold duplication that a clarity reviewer may flag.

### 5M.2 N-18 — two of three sites fixed, one pair HELD

| tex | Fix | Status |
|---:|---|---|
| 640 | "EWMA attains the highest raw lead in Table 16" → **"Hotelling $T^2$ attains the highest raw lead of any control chart"** | ✅ written |
| 640 | "the raw-lead column of Table 2, **where EWMA leads**" → **"where the deep reconstruction models lead"** | ✅ written |
| 640 + 654 | "**EWMA and Isolation Forest dominate** the upper-left" (prose + Figure 6 caption) | ⬜ **HELD** — author asked to see the caption text first |

**Two traps avoided in the first fix, both of which would have created new defects:**
1. The follow-on clause reads "**the two memory-based control charts** share this liability."
   Hotelling T² is **not** memory-based, so simply swapping the name would have broken it. The
   sentence was reworked so **EWMA and CUSUM** keep the memory-based pairing while Hotelling
   becomes the highest-raw-lead example. Their combined FAR range was recomputed: **19.0–22.1%**
   (was "19.0–19.4%", CUSUM only).
2. "highest raw lead **in Table 16**" would become **false again** once D-9 adds LSTM-AE (199.6 >
   Hotelling 176.9). Scoped to **"of any control chart"**, which holds both before and after D-9.

Dominance evidence for the held pair (`results/tables/tradeoff_IMS.csv`, full 7-percentile curve):
**Hotelling T² strictly dominates EWMA on both axes** — max lead 187.8 vs 174.8, min FAR 19.0 vs
20.8. Isolation Forest also dominates EWMA (185.3 / 16.8). Hotelling and Iso. Forest do **not**
dominate each other (Hotelling higher lead, Iso. Forest lower FAR), so naming both is right.
*Caveat to keep in view:* the dominance is on the **achievable frontier** (max lead, min FAR).
On **mean** FAR across the curve EWMA is lower (21.9 vs Hotelling 26.4) — so the claim must stay
about the curve's upper-left corner, which is what "dominate the upper-left" means.

### 5M.3 ~~THE MANUSCRIPT IS CURRENTLY INTERNALLY INCONSISTENT ON FAMILY SIZE~~ — ✅ RESOLVED in §5N.3

**The abstract now says $N=44$; eight other sites still say $N=40$.** This was introduced by
§5L.1's abstract rewrite and is **not yet resolved**. Two of the sites edited in this pass
(`tex:95`, `tex:949`) contain `$N=40$` and were deliberately **left alone**, because doing two of
eight would have left the same inconsistency in a less obvious form. **The §5H sweep (16 atomic
edits) must be run as one pass, and should be the next thing done.** Until then the manuscript
must not be compiled for circulation.

---

## 5N. Third and fourth edit passes — session 4

Commits `0a5a85b` (Figure 6 + repetition) and `18abc94` (N=44 sweep), kept separate so the
diffs stay reviewable. **§5M.3's family-size inconsistency is now RESOLVED.**

### 5N.1 Figure 6 — frontier wording (N-18 site 3, approved)

`tex:640` prose and `tex:654` caption now read **"the achievable frontier---highest lead at the
lowest FAR each detector attains"** rather than an unqualified "dominate the upper-left".
This was the author's amendment and it closes a real trap: a reviewer computing **mean** FAR
across the curve gets **EWMA 21.9% vs Hotelling 26.4%** and would read the claim as another
contradiction. Naming the frontier makes the axis of comparison explicit.
Evidence: over the full swept curve Hotelling T² dominates EWMA on both axes
(max lead **187.8 vs 174.8 h**, min FAR **19.0 vs 20.8%**); Isolation Forest also dominates EWMA;
Hotelling and Iso. Forest do not dominate each other. Source `results/tables/tradeoff_IMS.csv`.
**N-18 is now fully closed.**

### 5N.2 Repetition fixed now, not deferred to Phase 7

The exception clause was stated verbatim at six sites. Now **in full exactly twice** — the
**abstract** (must stand alone) and **§6.4** (`tex:426`, where the FEMTO result is first
reported) — and by **cross-reference at the other five** (`tex:87`, `95`, `922`, `930`, `949`).
`\label{sec:femto}` was added to `tex:425` to support the references; it is appended to the
subsection line rather than placed on its own line, to avoid renumbering mid-pass.

> The author's instruction said "the other three sites"; there were **five**. The principle
> (full form exactly twice) was applied as stated; only the arithmetic differed.

**Verified on a freshly compiled PDF:** full CI form appears **exactly twice**; the ±1 h margin
is still named at **all seven** sites; the exception is still named at every site; five
cross-references resolve; **zero undefined references**.

**Em-dash count: 184 → 182** against the 180 baseline. The restructuring removed two of the four
the previous pass had added. Phase 7 still has to reduce ~167 live prose dashes toward ~100.

### 5N.3 N = 40 → N = 44 executed as ONE pass

20 edit operations. Source and rendered PDF both verified.

| Change | Count | Sites |
|---|---:|---|
| `$N=40$` → `$N=44$` | 8 | `tex:95, 268, 513`×2, `517`×2, `930, 949` (abstract already done) |
| `10 × 4 = 40` → `11 × 4 = 44` | 1 | `tex:513` |
| FWER `(1−0.05)^40 ≈ 0.87` → `(1−0.05)^44 ≈ 0.8953` | 1 | `tex:513` |
| "forty" → "forty-four" | 3 | `tex:513`×2, `945` |
| "0 of 40" → "0 of 44" | 2 | `tex:513, 517` |
| "ten evaluated detectors" → "eleven" | 5 | `tex:279, 426, 430, 480, 970` |
| "ten detectors" → "eleven detectors" + names OC-SVM | 1 | `tex:517` (Table 11 caption) |
| `191/600` → `193/660` | 1 | `tex:426` |

**PDF sweep (tectonic + PyMuPDF, BOTH hyphen-join forms) — all zero:** `N = 40`, `N=40`,
`4 = 40`, `0 of 40`, `(1−0.05)^40`, bare `forty`, `ten evaluated detectors`, `ten detectors`,
`191/600`. **All replacements present at expected counts. Zero undefined references.**

Three apparent failures in the first sweep were **search-key artifacts, not defects** — worth
recording because they will recur:
1. **bare "forty" ×1** — the hyphen-**dropping** form turns `forty-
four` into `fortyfour`,
   which matches `forty`. The keep-form reads it correctly. Always check both forms.
2. **`(1-0.05)44` → 0** — renders as `1 -(1 -0.05)44` with spaces after the minus signs;
   the search key must not assume spacing. U+2212 must also be normalised to ASCII `-`.
3. **`eleven detectors` ×2 rather than 1** — the abstract already said "Eleven detectors" from
   the first pass. The expectation was wrong, not the text.

**Holm verdict unchanged: 0 rejections; smallest raw p still 0.031 (Iso. Forest on FEMTO),
Holm-adjusted 1.00 at both family sizes.** FEMTO `193/660` = published 191/600 (verified to
reproduce) plus OC-SVM's 60 evaluations of which 2 are valid
(`results/tables/d3_ocsvm_benchmark_long.csv`).

> ✅ **FWER precision — RESOLVED session 5.** Flagged because `≈ 0.8953` mixes an approximation
> sign with four decimals against two-decimal neighbouring text. **Author ruled `≈ 0.90`;
> applied at `tex:513`.** Verified on a rebuilt PDF (rule 10): `0.8953` now absent (×0),
> `0.90, which is exactly why` present (×1). The full-precision value is retained in §5G above
> as the derived quantity; `≈ 0.90` is the printed form.

---

## 5N. Session 5 — DEC-7 deferral, RD-17 appendix, N-19

### 5N.1 The nine-site restatement is DEFERRED (author decision, session 5)

Items 2.7 and 2.8 were cut to a minimum: one sentence after Eq. 5, no restatement of any
number. **The measurement below is complete and verified — preserved so that a future
revision can act on it without re-running anything.** Classifier: a cell is *unscoreable*
when `far_preonset_pct` is NaN while `lead_time_hours` is not (empty pre-onset region), or
when `t_onset` is NaN (the D-8 `Bearing1_2` no-onset fallback, which writes a *legacy* FAR
into the onset-relative column and therefore looks scoreable — NaN alone misses it).

**Cross-check:** the strict-convention figures reproduce §5A exactly — **73/450** and
**7/50** — which validates the classifier before any new number is trusted.

**Nine manuscript sites change.** Published → strict Eq. 5 → three-outcome:

| # | Site | Published | Strict | Three-outcome |
|---|---|---|---|---|
| 1 | `tex:396` §6.3 XJTU headline | 209/450 | 73/450 | **48/230** |
| 2 | `tex:568` §6.6 prose restating it | 209/450 | 73/450 | **48/230** |
| 3 | `tex:568` `Bearing2_2` mean-vs-oracle example (1.00 h / 1.08 h) | — | — | **bearing unscoreable; example must move** |
| 4 | `tex:578-587` Table 12 `V/5`, `Mean`, `Best` | 10 rows | — | **5 rows unscoreable** |
| 5 | `tex:589` Table 12 total | 20/50 | 7/50 | **6/25** |
| 6 | `tex:590` Table 12 "no valid detector" | 2/10 | — | **2/5 scoreable** |
| 7 | `tex:734` §6.10 prose "0.89 / 0.67" at f=20 | 0.89 / 0.67 | — | **0.83 / 0.50** |
| 8 | `tex:764-765` Table 18 f=20, rms_only and time_only | 0.67 / 0.89 | — | **0.50 / 0.83** |
| 9 | `tex:904` Table 23 T=0.20 row + `tex:887-890` prose | 0.83/0.83/0.83/0.00/0.83 | — | **0.80/0.80/0.80/0.00/0.80** |

Table 12's five fully-unscoreable bearings: `Bearing1_2`, `1_3`, `1_5`, `2_2`, `2_5`. The five
that survive keep their counts over a denominator of 5 — `1_1` 0/5, `1_4` 2/5, `2_1` 3/5,
`2_3` 1/5, `2_4` 0/5. Table 23 moves only at `T=0.20`, where `Bearing2_2` becomes unscoreable
for all ten detectors; deep models move too (LSTM-AE and Transformer-AD 0.50→0.40, TCN 0.33→0.20).

**§5A.6's candidate list was wrong in both directions — corrected here.** Of its five
unmeasured candidates, **four do NOT move**: `tex:370` (Table 5, 3σ 1.00×4 — IMS's 14
unscoreable rows are all `2nd_test` at f=10/20 aggregate, and that row is f=1 aggregate),
`tex:739` (Table 17), `tex:776` (Table 19) and `tex:799` (Table 20) — the last three have zero
unscoreable rows in their source files. Only `tex:759` (Table 18) moves. **And one site nobody
listed does move: Table 23 (`tab:mintrain`).** It was missed because the FEMTO *benchmark* has
zero unscoreable rows; the training sweep moves the split boundary, which is what pushes
`Bearing2_2`'s onset to the start of the scored region at `T=0.20`.

**Also confirmed unchanged** (matters for item 2.9): `tradeoff_IMS_long.csv` has zero
unscoreable rows, so Tables 14, 16, 22 and the §6.1 daggers at `tex:275`/`:279`/`:285` are
untouched by D-7. `tex:426` FEMTO 193/660 likewise unchanged, confirming §5A.

**Ferrara correction.** All 100 Ferrara unscoreable rows are in a **single** bearing, `E3`
(1 of 6, at 100% of its rows). On XJTU it is genuinely frequent — 7 of 10 bearings affected,
5 of 10 fully unscoreable at full resolution. Any future §8 sentence must not say "Ferrara
bearings" plural. **The §8 limitation sentence was drafted but NOT applied**, parked with this batch.

### 5N.2 RD-17 written into Appendix C ✅ DONE session 5

Appendix C (`tex:1051`) now carries the D17 result from §5G.4. It leads with the finding that
under the original label 3σ's test-3 difference is exactly `0.00` h, drops out under §4.8's
zero-difference rule, and leaves **2 positive / 0 negative** — so the withdrawn claim *"in no
run does aggregation shorten their lead time"* **would have been TRUE under the original
label**. The relabelling made the paper's own claim harder to support, not easier. Then the
side-by-side ten-detector table (new `tab:d17label`, `table*`), the 6-of-10 guaranteed-miss
correction, and the detector-dependent effective n (3 / 2 / 1 with floors 0.25 / 0.50 / 1.00),
closing on: no IMS detector reaches significance under either label, best attainable p = 0.25
in both arms, and no median flips sign. Verified on a rebuilt PDF (rule 10): "guaranteed miss
for six of the ten" ×1, "harder to support" ×1, `+25.81` ×2 (both arms of the 3σ row).

### 5N.3 N-19 — gap injection re-run with `far_preonset_pct` ✅ DONE session 5

**New generator `src/d19_gap_injection.py`.** `gap_injection.csv` had **no generating script
anywhere in the tree** — the same orphaned-artifact defect as N-15 — so the re-run required
reconstructing it. Writes `results/tables/gap_injection_far.csv` (234 rows, matching the
released row count); does not overwrite the released file.

**Reconciled:** at `factor=1, mode=none` the **gap=0 arm reproduces the released file exactly**
on both IMS and XJTU-SY, which confirms the reconstructed configuration.

**⚠️ The gap>0 arms do NOT reproduce, and cannot.** The original RNG draw is unrecoverable, so
the injected-gap realizations differ. Example — IMS Isolation Forest mean valid lead:
released `54.67 / 53.42 / 37.17`, re-run `54.67 / 54.67 / 53.42`. **This is a reproducibility
defect in the released artifact, not an arithmetic error in either arm.** Table 6's body was
therefore left on the released numbers and NOT rewritten from the re-run.

**Table 6's caption claim was false and is now corrected.** "Valid-alarm fractions (not shown)
are unchanged across gap levels" does not hold on XJTU-SY. Measured, released file: IMS 2/3 for
each of the three detectors at every gap level (unchanged ✅); XJTU-SY 3σ **5/10 → 6/10 → 5/10**
(moves), EWMA 7/10 and Iso. Forest 4/10 (hold). The re-run independently confirms the
qualitative finding — fractions move on XJTU, stable on IMS — with a different draw (3σ
5/10 → 5/10 → 6/10; EWMA 7/10 → 8/10 → 7/10). The corrected caption states the released
figures and adds that one random draw is used per level, so a one-bearing move is draw noise
rather than a gap effect. Verified on a rebuilt PDF (rule 10): "5/10, 6/10, 5/10" ×1.

**Also observed, NOT pursued** (D-7 is parked): 36 of the 117 Table-6-relevant rows carry a NaN
`far_preonset_pct`, all on XJTU-SY. Recorded only; no action taken.

---

## 5O. Session 6 — RF-2 (register 1.1) and RG-3 (register 1.5), one pass

Script: `src/rf2_rg3_gated_contrast.py` (committed `960f711`). **New result files only; no
published file touched; no manuscript edit.** Both arms use the **invariant IMS schema (D-2)**.

### 5O.0 Conventions, stated once

- **Validity: D-7 minimum.** A row is **unscoreable** when `t_onset` is undefined (no onset) or
  `far_preonset_pct` is undefined (empty pre-onset region). Unscoreable rows are **excluded from
  the denominator and never counted valid**. `valid = scoreable ∧ lead > 0 ∧ FAR_pre ≤ 10%`.
  Gated `L = lead` if valid, `0` if scoreable but invalid, **excluded (NaN)** if unscoreable.
  The published `valid_alarm` column is **not** used, because of the N-7 carve-out and the N-12
  legacy substitution. A **strict** arm (unscoreable → invalid, L = 0) is emitted alongside.
- **Contrast:** `stats_rigor.run_level_diffs` (mean collapse, §4.8) plus the exact two-sided sign
  test. Ties (exact zeros) are dropped from the test and **reported**. Holm is applied over
  **N = 44** (11 detectors × IMS/XJTU-SY/FEMTO/Ferrara). ONGC (n = 1) is reported, outside the family.
- **One gating-induced asymmetry:** IMS `2nd_test` aggregate f=10 and f=20 have an **empty
  pre-onset region**. Decimate does not (onset at 61.9% of span sits just past the 60% test start). For 8
  detectors, that run's gated aggregate mean therefore covers f ∈ {1,2,5} and decimate covers all five.
  Every other exclusion is symmetric across modes. Unscoreable rows: Ferrara `E3` (all),
  XJTU `Bearing1_2` (no onset), `2_2`, `2_5` (all), `1_3` (f 1,2,5), `1_5` (f 1,5), `1_1`/`1_4` (f 20).

### 5O.1 Cross-check first: raw lead reproduces Tables 7–11 ✅

`rf2_crosscheck_raw_vs_published.csv`. The published values were **parsed from the `.tex`**, not
retyped. **238/238 printed values reproduce at printed precision** (Tables 7 28/28, 8 40/40,
9 40/40, 10 50/50, 11 80/80, incl. all 40 Holm p at N=44). This holds only on the **legacy** IMS
file, because **Tables 10 and 11 still carry the legacy IMS numbers** (e.g. 3σ +18.4, raw p 0.250),
although D-2 was decided and the abstract already says +15.1. On the invariant file, 26/70 IMS values
match (expected, §5C), and the invariant medians reproduce **R-13** exactly
(3σ +15.10 · CUSUM +4.27 · EWMA +2.10 · Hotelling +1.17 · Iso. Forest +3.43).
⚠️ **Table 11 prints 40 rows under an N=44 caption. The four OC-SVM rows are missing.**
⚠️ **Tables 10/11 IMS rows still need the D-2 swap. Not yet done.**

### 5O.2 RF-2 result — gated contrast (`rf2_gated_contrast.csv`)

**Holm N=44: 0/44 rejected under raw, gated-D7 and gated-strict. Smallest adjusted p = 1.00 in
all three.** No gated raw p < 0.05 anywhere (raw had one, FEMTO Iso. Forest 0.031).

**Power loss, made visible (family datasets):**

| Dataset | raw ties | raw n₊+n₋ | gated ties | gated n₊+n₋ | runs excluded (unscoreable) |
|---|---:|---:|---:|---:|---:|
| IMS | 3 | 30 | **20** | **13** | 0 |
| XJTU-SY | 56 | 33 | 48 | **14** | **27** |
| FEMTO | 0 | 66 | **29** | **37** | 0 |
| Ferrara | 0 | 66 | 11 | **44** | **11** |
| **Total (44 cells)** | **59** | **195** | **108** | **108** | **38** |

Gating removes **45%** of the non-zero run pairs (195 → 108). Under strict Eq. 5 the excluded runs
become ties instead (XJTU ties 75, Ferrara 22). n₊+n₋ is unchanged, so the tests are identical.

**Per-cell headline shifts (D-7):**
- **IMS 3σ: raw +15.10 (2+/1−) → gated 0.00 (1+/1−/1 tie), p 1.00.** The paper's largest IMS
  effect **vanishes under its own gated metric**. CUSUM +4.27 → +4.27 (2+/0/1 tie, p 0.50);
  EWMA +2.10 → +2.10 (2+/0/1); Hotelling +1.17 → **+3.50** (2+/0/1); Iso. Forest +3.43 → +3.43
  (2+/0/1). The deep models and OC-SVM go to 0.00 (all ties, or 0+/1−).
- **Ferrara: gated direction turns negative.** EWMA −0.114 h and Hotelling −0.064 h are **0+/5−,
  p 0.0625** (raw 3/3 and 5/1). 3σ, CUSUM, Iso. Forest and Deep SVDD are 1+/4−. The magnitudes are
  sub-0.12 h, far inside the ±1 h margin, and nothing survives Holm.
- **FEMTO:** 3σ flips from raw 1+/5− (−0.099) to gated **3+/1−** (+0.005). Iso. Forest's raw 0/6
  (p 0.031) becomes gated 2/2/2 ties (p 1.00).
- **XJTU-SY:** gated medians are all 0.00 except LSTM-AE −0.125 (n=2). At most 4 non-zero pairs per cell.
- **ONGC (n=1, descriptive):** Hotelling raw **+2.41 h → gated −4.67 h**, a sign flip.

### 5O.3 RF-2 companion — valid-alarm fraction, aggregate vs decimate (`rf2_valid_fraction_agg_vs_dec.csv`)

`valid / scoreable` (D-7). Pooled over run × factor rows, detector-N/A rows omitted (numbers read back from the file):

| Dataset | aggregate valid | decimate valid | validity flips (both scoreable) | valid only under agg / only under dec |
|---|---|---|---:|---|
| IMS | 47/131 | 47/147 | 7 | 7 / 0 |
| XJTU-SY | 34/202 | 44/202 | 12 | 1 / 11 |
| FEMTO | 94/300 | 99/315 | 38 | 18 / 20 |
| Ferrara | 103/245 | 155/263 | 63 | 9 / 54 |
| ONGC | 6/55 | 6/55 | 2 | 1 / 1 |

**Ferrara is the striking case: decimation keeps validity far better**, e.g. CUSUM and EWMA 13/25 (agg)
vs **24/25** (dec), 3σ 15/25 vs 22/25, Hotelling 8/25 vs 16/25. Aggregation raises pre-onset FAR
above τ on Ferrara. **None of the 122 flips (all five datasets; 120 in the family) occurs with identical raw lead.** Validity never flipped
with the raw lead held fixed, so the register's "gating can flip validity even where raw lead is
unchanged" **did not occur** in these data.

### 5O.4 RG-3 result — onset from `pca1` and `kurt_only` (end-to-end rerun, 14 arms)

**Method.** The repo's own `run_benchmark` was re-run once per indicator, with every detector
re-fitted (10 default detectors, then OC-SVM alone, mirroring the published calls). The indicator
was switched **in memory** only. `kurt_only` = baseline-z of the mean `kurt_ch*` trend (the
kurtosis half of `rms_kurt`). **Table 4 had no generator anywhere in the repo** (same class as
N-15/N-19); this reconstruction **reproduces Table 4 exactly** on IMS for all three indicators
(`rg3_onsets.csv`). **ONGC has no kurtosis channel, so `kurt_only` is undefined there** (arm
skipped, stated); its `rms_kurt` is already RMS-only. Under **D-7**, a run with no onset is
unscoreable. It is **not** scored with the N-12 legacy fallback.

**Onset coverage.** `kurt_only` finds **no onset on 11 runs** (XJTU `1_1 1_2 1_5 2_2 2_4 2_5`,
FEMTO `1_2`, Ferrara `E2 E3 E4 E6`); `pca1` misses **4** (XJTU `1_1 1_2 2_2`, FEMTO `1_2`);
`rms_kurt` misses 1 (XJTU `1_2`).

**Confirmed rebuild first ✅** (`rg3_reproduction_check.csv`): the `rms_kurt` arm reproduces the
published long files (invariant IMS + OC-SVM rows) on **2,750/2,750 rows**, with **max |Δ| = 0.0**
on raw lead **and** pre-onset FAR, 0 onset mismatches, no NaN mismatch, deep models included.
The pipeline is deterministic, so any cross-indicator deviation would be a real effect.

**Raw-lead invariance — VERIFIED, not assumed ✅** (`rg3_raw_invariance.csv`): across
**99 dataset × detector × alt-indicator cells**, **max |Δ raw lead| = 0.000 h at row level and
0.000 h at run-difference level; 0 NaN mismatches.** Raw lead is exactly invariant to the
onset definition.

**Gated contrast (D-7) — NOT stable on IMS; bounded elsewhere** (`rg3_contrast_by_indicator.csv`).
Median Δ (h), with n₊/n₋/ties:

| IMS detector | rms_kurt | pca1 | kurt_only |
|---|---|---|---|
| CUSUM | **+4.27** (2/0/1) | 0.00 (1/0/2) | 0.00 (1/0/2) |
| EWMA | **+2.10** (2/0/1) | 0.00 (1/0/2) | 0.00 (1/0/2) |
| Hotelling T² | **+3.50** (2/0/1) | 0.00 (1/0/2) | 0.00 (0/0/3) |
| Iso. Forest | **+3.43** (2/0/1) | **+3.43** (2/0/1) | 0.00 (1/0/2) |
| 3σ | 0.00 (1/1/1) | 0.00 (0/1/2) | 0.00 (1/0/2) |
| deep ×3, Deep SVDD, OC-SVM, RMS-trend | 0.00 | 0.00 | 0.00 |

**Max |median shift| vs rms_kurt (gated D-7), in hours:** IMS **4.27** (both indicators);
FEMTO 0.024 (pca1) / 0.030 (kurt_only); XJTU-SY 0.125 / 0.007; Ferrara 0.073 / **0.603**
(kurt_only rests on **n = 2** runs); ONGC (n=1) Hotelling **−4.67 → +2.31** (6.98 h) under pca1.

**Power (family, gated D-7) — ties / n₊+n₋ / runs excluded as unscoreable:**
rms_kurt 108 / 108 / 38 · pca1 122 / 97 / 35 · kurt_only 59 / 70 / **125** (`kurt_only`
drops most runs as unscoreable).

**Holm N=44: 0/44 under every indicator × {raw, gated-D7, gated-strict}; min adjusted p = 1.00
everywhere.** Smallest unadjusted gated p: 0.0625 (rms_kurt, pca1), 0.25 (kurt_only).

**Bounded claim this supports:** the raw-lead non-destruction result is exactly onset-invariant.
The gated contrast is **not**. On IMS every positive gated median collapses to 0 under a
decoupled onset, except Iso. Forest under pca1, so the gated IMS "aggregation helps" pattern is
**onset-dependent and must not be claimed**. On XJTU-SY, FEMTO and Ferrara, gated medians move by
≤ 0.13 h (≤ 0.60 h for Ferrara kurt_only at n = 2), inside the ±1 h margin, with no rejection
under any indicator.

**Artifacts (all new, `results/tables/`):** `rf2_crosscheck_raw_vs_published.csv`,
`rf2_gated_contrast.csv`, `rf2_valid_fraction_agg_vs_dec.csv`, `rg3_onsets.csv`,
`rg3_rerun_long_{IMS,XJTU-SY,FEMTO,Ferrara}_{rms_kurt,pca1,kurt_only}.csv`,
`rg3_rerun_long_ONGC_{rms_kurt,pca1}.csv`, `rg3_reproduction_check.csv`, `rg3_raw_invariance.csv`,
`rg3_contrast_by_indicator.csv`, `rg3_valid_fraction_{rms_kurt,pca1,kurt_only}.csv`.

### 5O.5 Results-preservation audit (session 6)

- **N-3 was still true:** `.gitignore:23` ignored `results/tables/`; **0 result files tracked**
  (93 on disk before this session). **Fixed** with a negation (`results/tables/*`,
  `!results/tables/*.csv`, `!results/tables/*.log`). Every result file is now committed.
  `results/figures/` stays ignored (the paper's figures are tracked in `paper/files/`).
- **Ledger R-1…R-17: no broken path.** R-1 is code inspection (no file); R-5, R-6, R-9, R-11 and
  R-12 had no path (open). Two entries use abbreviations that resolve:
  R-7 `_tradeoff{,_long}.csv` → `d3_ocsvm_tradeoff.csv`, `d3_ocsvm_tradeoff_long.csv`;
  R-15 `..._invariant.csv` → `benchmark_IMS_long_invariant.csv`. All exist.
- **Revision scripts were ALL untracked.** `src/d*.py` written this revision (11):
  `d2_cascade_audit`, `d2_convention_recompute`, `d2_deep_tradeoff`, `d2_regenerate_artifacts`,
  `d2_seed_check`, `d3_compute_cost_extra`, `d3_ocsvm`, `d9_tables_14_22`, `d15_equivalence`,
  `d17_original_label`, `d19_gap_injection`. Also untracked: `compute_cost_ims`,
  `ims_schema_check`, `persistence_sweep_ims`, `rf2_rg3_gated_contrast`. **All committed `960f711`.**
- **The D-2 code change itself was uncommitted** (`src/benchmark.py`, `src/sampling.py`), together
  with `tests/test_feature_mode.py`. Tests: 7 passed. **Committed `d873e58`.**

### 5O.6 Paired valid-alarm comparison — the §5O.3 unpaired table is SUPERSEDED

**Do not report §5O.3's unpaired fractions.** Their denominators differ between modes for two
reasons: (i) gating-induced unscoreability in one mode only (IMS `2nd_test` aggregate f=10,20);
(ii) **detector-N/A cells present in one mode only** (deep models give a lead at more factors under
decimate on Ferrara/FEMTO). Reason (ii) was not the author's hypothesised mechanism. On Ferrara it
is the **only** reason, because Ferrara's unscoreability (`E3`) is symmetric.

Recomputed **paired**: only (run, factor, detector) cells that have a lead and are scoreable in
**both** modes (`rf2_valid_fraction_paired.csv`, `paired_validity()`). The pooled McNemar p is
**descriptive only**, because cells within a run are pseudoreplicates. The run-level sign test is
the §4.8 unit.

| Dataset | cells | paired | excluded (agg-only / dec-only / neither) | valid agg | valid dec | discordant agg-only / dec-only | pooled McNemar p | runs +/−/tie | run sign p |
|---|---:|---:|---|---|---|---|---:|---|---:|
| IMS | 165 | 131 | 34 (0 / 16 / 18) | 47 (35.9%) | 40 (30.5%) | 7 / 0 | 0.016 | 3/0/0 | 0.25 |
| XJTU-SY | 495 | 202 | 293 (0 / 0 / 293) | 34 (16.8%) | 44 (21.8%) | 1 / 11 | 0.0063 | 0/3/4 | 0.25 |
| FEMTO | 330 | 300 | 30 (0 / 15 / 15) | 94 (31.3%) | 96 (32.0%) | 18 / 20 | 0.87 | 2/3/1 | 1.00 |
| **Ferrara** | 330 | **245** | 85 (0 / 18 / 67) | **103 (42.0%)** | **148 (60.4%)** | **9 / 54** | 6.1e-9 | **0/5/0** | **0.0625** (floor at n=5) |
| ONGC | 55 | 55 | 0 | 6 | 6 | 1 / 1 | 1.00 | 0/0/1 | 1.00 |

("neither" = N/A in both modes or unscoreable in both; XJTU's 293 are mostly deep-model N/A plus
the unscoreable bearings.) **The IMS unpaired "47/131 vs 47/147" hid a direction:** paired, aggregate
is valid more often (7 vs 0 discordant).

**Ferrara: the gap SURVIVES pairing** (unpaired 42.0% vs 58.9%, i.e. 103/245 vs 155/263; paired
42.0% vs 60.4%), with all 5 scoreable runs in the same direction. Per detector it is carried by the
charts: CUSUM and EWMA 13/25 vs 24/25, Hotelling 8/25 vs 16/25, 3σ 15/25 vs 22/25.

**⚠️ BUT IT IS NOT YET A REAL FINDING — see N-20.** By factor, Ferrara aggregate validity is
0.60 / **0.00** / 0.41 / 0.55 / 0.50 against decimate 0.60 / 0.62 / 0.56 / 0.65 / 0.51. The collapse
at f=2 is where the two modes are compared at **different logging intervals** (aggregate 1.00 min,
decimate 0.17 min; 82 vs 492 test windows on E1). Pairing fixes the denominator, not this. **Verdict:
neither "real" nor "artifact" can be recorded until N-20 is fixed and Ferrara is re-run. Keep it
out of the paper.**

### 5O.7 Generator coverage — Table 4 was the FOURTH orphaned artifact (N-21)

Table 4 (`tab:decoupled`, `kurt_only` / `pca1` onset positions) had **no generating script and no
result file anywhere in the repo**, and `kurt_only` is not even a health-indicator kind in
`src/onset.py`. It has now been **reconstructed** (`src/rf2_rg3_gated_contrast.py` `onsets`, output
`rg3_onsets.csv`: `kurt_only` = baseline-z of the mean `kurt_ch*` trend) and **reproduces Table 4
exactly** on all 3 runs × 3 indicators, on both onset % and max lead.

**Orphan count, corrected:** the author's note called Table 4 the *third* orphan, after N-15 and
`gap_injection`. **§5E.7 already records a third: Table 25's compute timings had no generator**
(now `src/compute_cost_ims.py`). Table 4 is therefore the **fourth**:

| # | Artifact | Found | Generator now |
|---|---|---|---|
| 1 | Table 5 `persistence_sensitivity_IMS.csv` (N-15) | session 3 | `src/persistence_sweep_ims.py` |
| 2 | Table 25 compute timings (§5E.7) | session 3 | `src/compute_cost_ims.py` |
| 3 | Table 6 `gap_injection.csv` (N-19) | session 5 | `src/d19_gap_injection.py` (gap=0 arm only reproduces) |
| 4 | **Table 4 decoupled onset (N-21)** | session 6 | `src/rf2_rg3_gated_contrast.py onsets` — **reproduces exactly** |

🗣️ **Response to Review — DEFECT DISCLOSURE LIST (author instruction, session 6):** **N-15** (Table 5 validity 1.00 not reproducible), **N-17** (compute-cost sentence overreached its table), **N-18** (EWMA-leads claims contradicting Table 16), **N-20** (aggregate and decimate compared at different logging intervals on FEMTO/Ferrara/ONGC; fixed; verdict and 30/30 equivalence unchanged, IF-on-FEMTO exception and FEMTO sign-consistency claim withdrawn), **N-21** (Table 4 orphaned, reconstructed), **N-22** (the FEMTO training-fraction sweep did not vary the training fraction: load_pipeline took it from the dataset bundle and never read the swept SPLIT value, so all five T produced one identical training split; fixed, re-run, and the no-crossover conclusion survives). Every one was found unprompted.

🗣️ **Response to Review, disclosure paragraph:** list all four as evidence that generator coverage was
audited artifact by artifact. Three now reproduce exactly. `gap_injection`'s gap>0 arms do not
(its RNG draw was lost), and that must be stated.

### 5O.8 Scope of the two live inconsistencies — every site still carrying legacy IMS values

**(a) Missing detector rows.** OC-SVM appears in **no table body**. It is only in prose (`tex:110`,
`tex:235`) and in Table 11's caption. Data rows per table (caption claim in brackets):

| Table | rows | claimed | missing |
|---|---:|---|---|
| 2 `tab:imslead` | 10 | "all eleven" | OC-SVM |
| 7 `tab:xjtu` | 7 | "seven non-sequence" | OC-SVM (non-sequence) — D-5 |
| 8 `tab:femto`, 9 `tab:ferrara` | 10 each | "all eleven" (8) | OC-SVM — D-5 |
| 10 `tab:imssweep` | 10 | "all eleven" (`tex:480`) | OC-SVM |
| **11 `tab:holm`** | **40** | **N=44** | **4 OC-SVM rows** |
| 14, 16, 22 | 7 each | — | deep ×3 + OC-SVM — **D-9 decided, never applied** |
| 25 `tab:compute` | 9 | "eleven" (`tex:970`) | OC-SVM, RMS-trend (N-17) |

**(b) Legacy IMS values still in print (D-2 re-baseline incomplete):**

| Site | Legacy content | Invariant source |
|---|---|---|
| `tex:87` Intro "Finding" | "on IMS it shows a consistent positive trend" | direction not consistent (3σ, EWMA, IF each 2+/1−) |
| `tex:95` Contribution 4 | "consistent positive trend for the variance-sensitive control charts" | same |
| `tex:267` §6 summary (ii) | "same sign in all three runs … 3σ +18.4, IF +12.2, EWMA +5.8" | +15.1 / +3.4 / +2.1, not same-sign |
| `tex:286–297` **Table 2 body** | 214.9 … 18.4, legacy CIs, legacy order | `benchmark_IMS_leadtime_ci_invariant.csv` (its prose at `tex:273` is ALREADY invariant, so the section contradicts itself) |
| `tex:357` + `tex:361–371` **Table 5** + caption | legacy medians; "3σ and EWMA 3/0 at all four"; "valid 1.00" (N-15) | `persistence_sensitivity_IMS_invariant.csv` |
| `tex:421` Figure 2 caption + `fig_crossdataset.png` | "IMS shows a consistent positive trend"; bars from `ims_runlevel_test.csv` (legacy) | `ims_runlevel_test_invariant.csv` |
| `tex:478` §5.1 + `fig_sweep.png` | "58.0 h → 7.1 h … near 59 h"; plot from `benchmark_IMS_long.csv` | 64.6 → 24.8, near 64.6; `benchmark_IMS_long_invariant.csv` |
| `tex:480` §6 prose | six legacy triples, "in no run does aggregation shorten", "p=0.25" floor as attained, deep medians −1.4/−0.4/−1.4 | §5B.0.1 / `ims_runlevel_test_invariant.csv` |
| `tex:491–506` **Table 10** | every row | same |
| `tex:523–532` **Table 11** IMS rows | raw p 0.250 ×8 | invariant raw p (6 move to 1.00) |
| `tex:930` Summary (2) | "same sign in all three runs … +18.4, +12.2, +5.8, +5.4, +4.6; floors at p=0.25" | invariant |
| `tex:937` External validity | "sign-consistent but non-significant trend" | not sign-consistent |
| `tex:945` Statistical-conclusion validity | "Cohen's d ≈ 0.7–1.2" → n≈6–17. **No source file exists for this d range** (rule 1), and legacy run-level d does not give it either | remove or source |
| `tex:970` + `tex:1008–1021` **Table 25** | timings measured at 445 dims on other hardware | `compute_cost_IMS_invariant.csv` + `_extra_` — option (c) of §5E.7 |

**Already invariant (no change):** abstract `tex:63`, `tex:273` Table 2 prose, the D-17 appendix
`tex:1051–1082`, `tex:166` (§4.2, now true), Tables 3/4/6/13–22/27/28 (§5C.3). `tex:718–723`
token hits are Table 16 values (invariant path), a coincidental match.

### 5O.9 D-2 re-baseline COMPLETED + Table 11 at 44 rows — manuscript pass applied ✅

**Commits:** `20658e5` (manuscript) · `6bb3f74` (Figures 2 and 3 + `paper/make_figures.py`, which was
gitignored and is now force-tracked). Every site in §5O.8(b) was edited. The diff was reviewed
before writing (rule 6); the full unified diff was generated from the scratchpad proposal.

| Site | Now |
|---|---|
| `tex:87`, `:95` | "positive median shift … not consistent across the runs" |
| `tex:267` | 3σ +15.1, CUSUM +4.3, IF +3.4, EWMA +2.1; only CUSUM and Hotelling positive in all three runs |
| `tex:273` | "…followed by the one-class SVM, and Hotelling $T^2$ leads the **control charts**" (OC-SVM 180.3 now sits above Hotelling 174.8, so "classical detectors" would have been false) |
| Table 2 | invariant means/CIs, re-ordered, **+ OC-SVM† 180.3 [65.5, 316.7]**; caption names the one-class SVM |
| `tex:357` + Table 5 + caption | invariant medians; N-15 fix (full-res valid **0.67** ×4); **new row: pooled valid 0.67/0.67/0.53/0.33**; "does not depend on this parameter" **withdrawn**; "Non-destruction … stable throughout" removed from the caption |
| Figure 2 caption + `fig_crossdataset.png` | invariant IMS bars |
| `tex:478` + `fig_sweep.png` | 64.6 h → 24.8 h at 10×, aggregation near 64.6 h; invariant curve |
| `tex:480` | CUSUM and Hotelling are the only sign-consistent detectors; 3σ/IF/EWMA each have a negative run; deep models + OC-SVM have negative medians, with test 3 strongly positive for the deep models (+56.1/+9.0/+68.8). **"in no run does aggregation shorten" removed** (the D-17 appendix at `tex:1054` already describes it as withdrawn, which is now true). **The "negligible magnitude … smoothing mechanism" explanation for the deep models was removed**, because it is false under D-2 |
| Table 10 | invariant, **+ OC-SVM** |
| **Table 11** | **44 rows** (4 OC-SVM rows added); IMS raw p invariant (**7** rows changed, not 6 as §5C said: Deep SVDD also moves, 0.50 → 1.00); caption "retained exactly as originally computed" → "IMS rows are computed on the 49-dimensional invariant feature schema" |
| `tex:930`, `:937` | invariant medians; "sign-consistent only for CUSUM and Hotelling $T^2$" |
| `tex:945` | **unsourced "Cohen's d ≈ 0.7–1.2 → n ≈ 6–17" removed** (rule 1). The exact sign-test statement is kept: six concordant runs are needed, so IMS is "at least a factor of two short" |
| `tex:970` + Table 25 | **§5E.7 option (c)**: all **eleven** rows from this machine's invariant run (`compute_cost_IMS_invariant.csv` + `_extra_`); caption names "49-dimensional invariant features, one core of an Intel Core i5-13420H". Option (a) was impossible (original hardware unknown); (b) would leave a legacy-schema table. Sentence: "at most ~0.5 ms per window (LSTM-AE), more than four orders of magnitude below" 10 s (10 s / 513 µs ≈ 1.9×10⁴). **N-17 resolved in print** |

**Verification.**
- Tables 7–11, re-parsed from the new `.tex`, match the result files on **251/251** values.
- Rebuilt with `tools/tectonic.exe`: **26 pages**, no errors or undefined references. The pre-edit HEAD was also rebuilt: 26 pages.
- PyMuPDF sweep, base → new: `+18.4` 7→**0**, `consistent positive trend` 5→**0**, `58.0 h` 1→0, `214.9` 1→0, `Cohen` 1→0, legacy valid row 1→0, `54 µs` 1→0; `One-class SVM` 0→**7**; Table 11 dataset cells in the PDF **40→44**. The page render confirms Table 11 fits its float.
- Residual hits reconciled: `27.1` is Table 16's FAR (invariant path); `in no run does aggregation` ×1 is the D-17 appendix's withdrawal sentence.

**Rule 10 reference counts — RE-BASELINED on this build (the §0 checklist values are stale):**
"never better" **0** · "never costs" **0** · "does not cost" **1** · "honest"/"honestly" **17** ·
"non-destruction" **21** (22→21: the Table 5 caption clause) · em-dashes **180** in the PDF (186 in the pre-edit
build) · **176** live `---` in the source (182 before). Negative hits were reconciled, not trusted: the
"ﬁ" ligature hid "five orders", and line breaks rendered "sign- consistent" and "or- ders".

**Left for the author's prose pass (not changed, flagged):**
1. `tex:478` says the upturn is "at the very largest factor". In Figure 3 the deep models spike to
   ~420 h at the **500-min** point, because only **one run** survives there (two at 250 min). The same
   survivorship exists in the legacy data, so this is a pre-existing understatement, not new.
2. `tex:480` no longer offers a mechanism for the deep models, and one may be wanted.
3. Tables 7, 8, 9 (OC-SVM) and 14, 16, 22 (deep ×3 + OC-SVM) still lack their D-5/D-9 rows (§5O.8a),
   and FEMTO/Ferrara values are provisional under **N-20**.
4. Table 12 still carries the pre-D-7 validity counts (§5N.1 deferral), independent of D-2.
5. `paper/build_pdf.sh` (untracked, gitignored) builds the superseded `scada_journal.tex`. It is stale,
   same class as N-8. The IJPHM build command is
   `tools/tectonic.exe --outdir <dir> scada_ijphm.tex`, run from `paper/files/`.

### 5O.10 N-20 FIXED (D-10) — verification and propagation. NO manuscript edit yet

**Code** (`src/__init__.py:207-213`, the only change): aggregate bins at `round(base_min·60·factor)` **seconds**
instead of `max(1, round(base_min·factor))` minutes. Nothing else touched: no detector, onset, metric,
seed or hyperparameter change. Generators: `src/n20_resample_fix.py` (verify, rerun, chunked rerun) and
`src/n20_propagate.py`. RF-2 gets `--arm n20` (outputs `*_n20.csv`).

**Mandatory verification — PASSED; no scope creep.**
- `load_pipeline` fingerprints (X_train, X_test, ts_test, features, interval) are identical before and after
  for every IMS and XJTU-SY run × mode × factor: **117/117** (`n20_pipeline_hash_check.csv`). The pre-fix
  hash was taken with `src/__init__.py` confirmed unmodified.
- Full post-fix benchmark reruns (`n20_reproduction_check.csv`): **XJTU-SY raw file bytes identical** to
  `benchmark_XJTU-SY_long.csv`. **IMS values and bytes identical** on all 24 shared columns of
  `benchmark_IMS_long_invariant.csv`; the published file has one extra `feature_mode` column that
  `ims_schema_check.py` appended.
- FEMTO, Ferrara, ONGC: **every decimate row and every f=1 row is identical** to the published data (lead,
  FAR, window count). Only aggregate f>1 rows change (lead changed in 192/240, 215/240 and 35/40 rows).
  Agg/dec interval mismatches 24/24/4 → **0/0/0**. ONGC f=20 test windows 641 vs 640, an edge-bin effect.
- ONGC ran as 20 atomic per-cell chunks (the harness killed whole-run jobs for low memory). The f=1 chunk
  equals the published f=1 rows exactly, which shows chunking does not change results.

**1. Raw-lead run-level contrast, published → post-fix** (`n20_raw_contrast_old_vs_new.csv`; median h, n₊/n₋/ties, p):

| FEMTO | old | new |
|---|---|---|
| 3σ | −0.099, 1/5/0, 0.219 | −0.139, 1/5/0, 0.219 |
| EWMA | +0.008, 3/3/0, 1.000 | +0.093, 4/2/0, 0.688 |
| CUSUM | +0.001, 3/3/0, 1.000 | +0.101, 4/2/0, 0.688 |
| Hotelling | +0.069, 5/1/0, 0.219 | +0.071, 5/1/0, 0.219 |
| **Iso. Forest** | **−0.137, 0/6/0, 0.031 (sign-consistent)** | **−0.065, 2/4/0, 0.688** |
| Deep SVDD | −0.003, 3/3/0, 1.000 | −0.004, 1/3/2, 0.625 |
| LSTM-AE | −0.049, 2/4/0, 0.688 | −0.040, 0/3/3, 0.250 (sign-consistent −) |
| TCN-AE | +0.001, 3/3/0, 1.000 | 0.000, 1/2/3, 1.000 |
| Transformer-AD | +0.041, 5/1/0, 0.219 | −0.053, 0/4/2, 0.125 (sign-consistent −) |
| RMS-trend | −0.025, 2/4/0, 0.688 | −0.017, 1/3/2, 0.625 |
| OC-SVM | +0.036, 4/2/0, 0.688 | +0.024, 4/1/1, 0.375 |

| Ferrara | old | new |
|---|---|---|
| 3σ | −0.021, 3/3/0, 1.000 | −0.015, 2/3/1, 1.000 |
| EWMA | +0.007, 3/3/0, 1.000 | +0.008, 4/2/0, 0.688 |
| CUSUM | +0.011, 4/2/0, 0.688 | +0.008, 5/1/0, 0.219 |
| Hotelling | +0.046, 5/1/0, 0.219 | +0.010, 4/1/1, 0.375 |
| Iso. Forest | −0.075, 2/4/0, 0.688 | +0.005, 3/2/1, 1.000 |
| Deep SVDD | −0.006, 2/4/0, 0.688 | −0.003, 1/4/1, 0.375 |
| LSTM-AE | +0.003, 4/2/0, 0.688 | 0.000, 2/2/2, 1.000 |
| TCN-AE | +0.003, 4/2/0, 0.688 | +0.001, 3/1/2, 0.625 |
| Transformer-AD | +0.003, 4/2/0, 0.688 | +0.001, 3/1/2, 0.625 |
| RMS-trend | −0.003, 3/3/0, 1.000 | +0.009, 4/2/0, 0.688 |
| OC-SVM | +0.020, 5/1/0, 0.219 | +0.011, 4/1/1, 0.375 |

ONGC (n=1, h): Hotelling **+2.406 → +0.110**, RMS-trend **+0.001 → +4.575**, Iso. Forest +0.121 → +0.205,
LSTM-AE −0.263 → −0.157, 3σ +0.011 → −0.012, CUSUM −0.017 → +0.002; the others are within 0.02 h.
The ONGC table convention (median over factors, min): 3σ +0.5 → **0.0**, EWMA −1.1 → **−0.5**, Hotelling
+0.8 → **+0.4**, Iso. Forest +1.2 → +1.2, RMS-trend 0.0 → **+1.2** (`n20_ongc_minutes.csv`).

**2. Holm N=44: 0/44 → 0/44; smallest adjusted p 1.00 → 1.00.** Smallest raw p **0.031 (FEMTO Iso. Forest) →
0.125 (FEMTO Transformer-AD)**. Family ties 59 → 83, n₊+n₋ 195 → 171.

**3. D15 equivalence (δ = 1 h) — SURVIVES.** It was recomputed through `d15_equivalence.analyse()` itself. The
old-arm replay reproduces the published 60 rows (max |Δ| 3.6e-15, verdicts identical). Post-fix,
**XJTU-SY 10/10, FEMTO 10/10, Ferrara 10/10 equivalent: 30/30 holds**; with OC-SVM, **33/33**. IMS
(invariant) is unchanged, 2 superior / 8 inconclusive. No cell shows decimation superior beyond the margin.
TOST feasible 22 → **14**, feasible-and-equivalent 17 → **13**.
⚠️ **The abstract's exception clause does not survive:** Iso. Forest on FEMTO −0.257 [−0.544, −0.057] →
**−0.180 [−0.488, +0.025]**; its CI now includes 0. Cells with the CI entirely below 0, post-fix (11-detector):
XJTU Iso. Forest −0.100 [−0.162, −0.041], **FEMTO 3σ −0.213 [−0.449, −0.041]**, FEMTO LSTM-AE −0.061
[−0.113, −0.013], FEMTO RMS-trend −0.123 [−0.327, −0.004], FEMTO Transformer-AD −0.077 [−0.153, −0.018].
**Pre-fix there were already five such cells** (XJTU IF, FEMTO 3σ, FEMTO IF, FEMTO RMS, Ferrara IF), so "the
one place decimation leads" was inaccurate even before N-20.

**4. RF-2 gated (D-7), post-fix** (`rf2_gated_contrast_n20.csv`): Holm **0/44**, min adj p 1.00, min raw p
0.0625 → **0.125**; ties 108 → **118**, n₊+n₋ 108 → **98**; 38 runs excluded (unchanged). Ferrara's
EWMA and Hotelling 0/5 (p 0.0625) become **1/4 (0.375)** and **1/2/2 (1.00)**. ONGC Hotelling gated −4.67 → **+6.98**.

**Paired valid-alarm comparison, post-fix** (`rf2_valid_fraction_paired_n20.csv`):

| Dataset | pairs (excl.) | valid agg vs dec | discordant agg/dec | pooled McNemar | runs +/−/= | run p |
|---|---|---|---|---:|---|---:|
| FEMTO | 315 (15) | 112 (35.6%) vs 99 (31.4%) | 26 / 13 | 0.053 | 4/1/1 | 0.375 |
| **Ferrara** | **263 (67)** | **144 (54.8%) vs 155 (58.9%)** | **11 / 22** | 0.080 | **2/3/0** | **1.00** |
| ONGC | 55 (0) | 10 vs 6 | 4 / 0 | 0.125 | 1/0/0 | 1.00 |
| IMS, XJTU-SY | unchanged (§5O.6) | | | | | |

**VERDICT: the Ferrara validity gap was the bug.** Paired 42.0% vs 60.4% (9/54 discordant, 0+/5− runs) becomes
54.8% vs 58.9% (11/22, 2+/3− runs, p = 1.00). The residual 4-point gap is not directional at the run level.
The f=2 collapse (aggregate 0.00 valid) was the 12× over-coarsening. **Do not report a Ferrara validity finding.**

**5. Manuscript numbers that move — 81 printed cells** (`n20_manuscript_cells.csv`; the old arm reproduces
all 129 checked cells first):
- **Table 8 `tab:femto`** `tex:438-447`: 29 cells, including 3σ −0.10→−0.14; EWMA 0.01→0.09 (4/2, 0.688);
  CUSUM 0.00→0.10 (4/2, 0.688); **Iso. Forest −0.14→−0.07, 0/6→2/4, 0.031→0.688, Sign-con. yes→no**; Deep SVDD 1/3, 0.625;
  LSTM-AE −0.04, 0/3, 0.250, **Sign-con. no→yes (−)**; TCN 1/2; **Transformer-AD 0.04→−0.05, 5/1→0/4, 0.219→0.125, Sign-con. no→yes (−)**;
  RMS-trend −0.02, 1/3, 0.625. (The Sign-con. column is not in the parser; read from `all_same_sign`.) **Still no OC-SVM row** (D-5).
- **Table 9 `tab:ferrara`** `tex:464-473`: 30 cells (every row; no detector sign-consistent, still true).
- **Table 11 `tab:holm`** FEMTO rows `tex:549-558`, Ferrara rows `tex:560-569`: 18 raw p change; all Holm p stay 1.000.
- **ONGC table** `tex:1152-1156`: 4 cells (above). The caption "about a minute or less" still holds (max 1.2 min).
- **Figure 2** (`fig_crossdataset.png`): the FEMTO/Ferrara/ONGC bars move. Its generator reads
  `femto_runlevel_test.csv` / `ferrara_runlevel_test.csv` / `benchmark_ONGC_paired_test.csv`, which are all pre-fix.
- **Prose:**
  - `tex:63` abstract, and the exception clause at `tex:87`, `:95`, `:929`, `:937`(1), and the conclusion: "the one place decimation leads, Isolation Forest on FEMTO (−0.26 h, 95% CI [−0.54, −0.06])" is **no longer true**. 30/30 and "no cell superior beyond the margin" still hold.
  - `tex:267`, `:937`(3): "Isolation Forest reversing sign on FEMTO". Its median is still negative (−0.07) but it is no longer sign-consistent.
  - `tex:937`(3): "≤ 8 min median" on the multi-bearing sets. **Post-fix the maximum is 0.139 h = 8.3 min (FEMTO 3σ)**; pre-fix it was 0.137 h = 8.2 min, so the claim already overshot by rounding.
  - `tex:428`: "the one detector that is sign-consistent on FEMTO, Isolation Forest, trends negative (6/6 runs, median −0.14…)" is **false**. Post-fix, LSTM-AE (0/3) and Transformer-AD (0/4) are the sign-consistent ones, both negative.
  - Table 8 caption: "the only sign-consistent detector, Isolation Forest, trends negative" is **false** (same reason).
  - `tex:454`: "smallest sign-test p is 0.219 (Hotelling $T^2$)" → 0.219 (**CUSUM**).
  - `tex:516` region (Holm prose), if it cites 0.031 / Iso. Forest on FEMTO → 0.125 / Transformer-AD on FEMTO (verify at edit time; rule 10).
  - `tex:944`/`:937` external validity: "on FEMTO the only sign-consistent detector even trends in the opposite direction" is **true in spirit but names no detector**; re-check at edit time.
- **Not moved:** IMS, XJTU-SY, Tables 2, 5, 7, 10 and Table 11's IMS/XJTU rows, and all non-benchmark artifacts. Every other `load_pipeline` aggregate caller (robustness, gap injection, feature-coarsening ablation) runs on IMS or XJTU-SY, whose pipeline outputs are proven unchanged.

**Also found while scanning (D-2 residue from §5O.9, NOT edited):** `tex:398` "a consistent but non-significant
positive trend on IMS" and **`tex:956` (Conclusion)** "on IMS shows a consistent, sign-concordant positive trend".
The §5O.9 sweep matched only the literal "consistent positive trend", so §5O.9's "0 remaining" was wrong.
This is a rule-10 miss, stated plainly.

### 5O.11 N-20 manuscript pass APPLIED — commit `394cd96` (author GO, session 6)

**Scope delivered:** all 81 cells (Tables 8, 9; Table 11 FEMTO/Ferrara rows; ONGC table), the prose
sites, Figure 2, and the two surviving D-2 sentences (`tex:398`, `tex:956`). Table rows were
**generated** from `n20_raw_contrast_old_vs_new.csv` / `n20_ongc_minutes.csv`, not typed. Re-parsed
Tables 7–11 match their sources **251/251**.

**The IF-on-FEMTO exception (D19 in the response letter; the author calls it RD-16).** Removed from
**all six sites**: abstract `tex:63`, `tex:87`, `tex:95`, `tex:929`, `tex:937`(1), Conclusion `tex:956`.
It is replaced by a **margin-based bound**, not an absence-of-negatives claim: *no cell shows decimation
superior beyond ±1 h; the five cells whose interval lies wholly below zero (IF on XJTU-SY; 3σ, LSTM-AE,
RMS-trend, Transformer-AD on FEMTO) favour decimation by less than that margin.* The abstract adds "the
widest such interval (3σ on FEMTO) reaching only −0.44 h" (`n20_d15_bootstrap_new.csv`, 10-detector
family: 3σ −0.213 [−0.443, −0.042]).

**Concept sweep (rule 10, extended), .tex and PyMuPDF text.** Paraphrase list searched: single/sole/the
one/only exception; one place / only place; decimation leads / wins / is better / outperforms /
superior; never better; never costs; IF on FEMTO / Isolation Forest on FEMTO / Iso. Forest on FEMTO /
IF…FEMTO within a sentence; reversing/reverses sign; sign reversal; opposite sign/direction; trends
negative; only sign-consistent; "one detector that is sign"; 6/6; 0/6; 0.031; 0.26; 0.54; 0.06];
−0.14; consistent…positive; sign-concordant; same sign in all three; in no run does aggregation;
consistently positive. **Result: zero surviving instances of the old claim.** Residual hits are all
intended:
- the six new bounded-form sentences;
- "In one place, the numbers that matter" (an unrelated phrase);
- `tex:944`'s new LSTM-AE/Transformer-AD sentence;
- `tex:952`'s arithmetic 2(½)⁶ = 0.031 / "sign-concordant";
- Table 8's new 3σ −0.14;
- the D-17 appendix sentence recording "in no run" as withdrawn.

In the PDF, "five cells" reads "ﬁve" (a ligature); the concept regex found it.

**Other edits.**
- `tex:428` §6.4: sign-consistent detectors are LSTM-AE and Transformer-AD (0/3, 0/4), the smallest p is
  0.125, and there is a new margin paragraph (3σ −0.21 h [−0.44, −0.04]). The valid count is
  **193/660 → 211/660** (old reproduced from file first). "Opposite sign to its IMS trend" is removed.
- Table 8 caption: two sign-consistent detectors, both negative.
- `tex:454` §6.5: smallest p is 0.219 (**CUSUM**). The E1 negatives (published range "−1.0 to −1.5 h",
  reproduced as −0.93 to −1.52) become **−0.5 to −1.1 h**; "few-minute" is removed.
- `tex:516` Holm prose: min raw p **0.125 (Transformer-AD on FEMTO)**; "every uncorrected p exceeds 0.1"
  (was 0.03); "IMS sign-consistency" → "positive IMS median shift" (D-2 residue).
- `tex:929`: the mechanism sentence "weakest for Isolation Forest" is **false under D-2** (IMS: EWMA +2.1
  < IF +3.4) and is replaced by "largest median shift in 3σ (+15.1 h), not consistent in direction".
- `tex:937`(3): ONGC "≤ 1 min" (false even pre-fix: max 1.2 min) → "at most ~1 min"; "≤ 8 min"
  (pre-fix max already 8.2) → **"≤ 9 min"** (post-fix max 8.3); IF-reversal clause removed.
- `tex:267`: IF-reversal clause → "negative FEMTO medians lie well inside the ±1 h margin".
- `tex:944`: "only sign-consistent detectors, LSTM-AE and Transformer-AD, are negative" ("opposite
  direction" removed; their IMS medians are also negative).
- `tex:398`, `tex:956`: D-2 residue fixed.

**Figure 2.** Inputs regenerated by `src/n20_figure_inputs.py`, which **replays** the three published
generator outputs exactly before writing `*_n20.csv`. **An existing Figure 2 bug was fixed along the
way:** `make_figures.py` divided the ONGC paired median (already in hours) by 60 again under a false
"minutes→hours" comment, so the ONGC bars were drawn 60× too small. Still open (register 4.1): the
legend reads "ONGC (n=1 (case study))".

**Build and sweep.** tectonic, **26 pages** (unchanged), no errors or undefined references. Rule-10
counts on this build: "never better" 0 · "never costs" 0 · "does not cost" 1 · "non-destruction" 21 ·
em-dashes **179** (180 before; one `---` removed with the old §6.4 sentence). "honest" reads 16 under
plain whitespace-joining in *both* builds; §5O.9's 17 was measured with hyphen rejoining. It is
unchanged, and this is a method difference only.

**Not done (flagged):**
- The abstract's "all 30 dataset × detector cells" still counts the 10-detector family, while the paper
  now evaluates eleven. The 11-detector result is **33/33** (`n20_d15_bootstrap_new_11det.csv`). Say
  30 or 33 deliberately.
- OC-SVM rows in Tables 7–9 and D-9 rows in Tables 14/16/22 are still missing (§5O.8a).
- The body has no equivalence table or TOST prose yet (R-2 / R-19 hold the numbers).

### 5O.12 Cuts batch — groups A and B (session 6)

| Step | Commit | Pages | Δ | Floats (T/F) |
|---|---|---:|---:|---|
| baseline (after N-20 pass) | `c60ca3c` | 26 | — | 30 / 11 |
| D-2 residue (heading `tex:479`; §6.12 200–215 h → 183–198 h, 48–100% → 61–100%) | `fb34a96` | 26 | 0 | 30 / 11 |
| **Group A** — delete Tables 21, 23, §7.4, §6 (i)–(v) list, Figure 9 | `7397708` | **25** | **−1** | 28 / 10 |
| **Group B** — merge Tables 7–9, 3–4, 5–6; Figures 4–6+11, 7–8 | `8d7fd10` | **25** | **0** | 24 / 6 |

**Group A checks.**
- A1: Table 21's six numbers verified against `onset_sensitivity.csv` (run spans 827.57 / 163.83 /
  1073.25 h; max leads 12.88 / 62.50 / 44.50 h). Table 21 had **no generator** either, but its numbers
  trace to that file.
- A2: Table 23 removed. §6.13 and the §4.5 table list now point to Figure 10.
- A3 and A4: a uniqueness check on every number in the deleted prose found **none that appears only
  there**. −0.35 / +6.6 h survive in Appendix D.1 prose and Table 28.
- A4: Discussion gains `\label{sec:discussion}`.
- A5: Figure 9 was never `\ref`'d.
- Dangling refs repointed: `tex:93`, `tex:107` (latch-on), `tex:235` (min-train).

**Group B checks.**
- B1 `tab:crossds` is **generated** (XJTU-SY from `rf2_gated_contrast.csv`, FEMTO/Ferrara post-N-20)
  and has **all eleven detectors** including OC-SVM, which **closes the D-5 gap for Tables 7–9**.
  Re-parsed from the `.tex`: **33/33 rows match**.
- B1 caught a layout bug: the first build overflowed into the adjacent column. TeX reported no
  overfull box; only a page render caught it. Fixed with `\footnotesize`, `tabcolsep 3pt`,
  "Transf.-AD" and "yes$^-$".
- XJTU prose: "six of the seven detectors" → "ten of the eleven" (asserted from the file).
- B2/B3: panels tiled by the new `paper/make_panels.py` (tracked with `-f`) from the existing PNGs;
  no replotting. The ONGC conformal plot moves from Appendix D.2 into the main-text 4-panel figure
  (panel d).
- B4: merged onset table generated from `onset_sensitivity.csv` + `rg3_onsets.csv`; identical values
  to the published Tables 3/4.
- B5: two tabulars moved verbatim. The gap prose drops "the weakest carrier of the aggregation trend"
  (D-2-stale).

**Every build:** 0 undefined refs, 0 "??" in the PDF, no unreferenced labels, no hard-coded float
numbers. Overfull hboxes 110 → 115 are reflowed prose lines, not tables. Rule-10 counts after B:
"never better" 0 · "never costs" 0 · "does not cost" 1 · "non-destruction" 18 (21 → 18, lost with §7.4
and the §6 list) · em-dashes 169.

**Why B saved no page:** the two-column `figure*` floats and the 33-row merged table take about the
space the separate floats did. B removed float count and captions, not height; the last page holds
398 words vs 437 after A. **The reserve (Tables 15, 17–20, ablations) is untouched, per instruction.**

**Flagged, not changed:** the missing-data prose ("every detector's valid-alarm fraction is unchanged")
contradicts its own caption (XJTU-SY 3σ moves 5/10 → 6/10 → 5/10; N-19 fixed only the caption).

## 6. Item checklist — all 41 reviewer items

Legend: ⬜ not started · 🔄 in progress · ✅ done · ⛔ blocked · ➖ no action needed

### Part 0 — Blocking
- ✅ **0.1** Coarsening level, per dataset (D9, F4) — answered, §5 above
- ⬜ **0.2** Deep AE threshold sweep: run it rather than soften (D6) → see 1.3
- ✅ **0.3** *(new)* Validity gate under missing `FAR_pre` (N-7) — answered, §5A above; produced D-7, D-8, N-10/11/12

### Part 1 — Analyses requiring a pipeline run
- ✅ **1.1** Aggregate-vs-decimate under the **gated** metric (F2) — **DONE session 6**, §5O.1–5O.3, ledger R-18. Holm 0/44; ties 59→108; D-7 convention, strict alongside
- ⬜ **1.2** Equivalence bound replacing the null-acceptance claim (D18, F5) ⛔ blocked on D-4
- ⬜ **1.3** Deep AE rows for Table 16 (D6)
- ⬜ **1.4** IMS test-3 under the original failure label (D20)
- ✅ **1.5** Aggregate-vs-decimate under disjoint onset — `pca1`, `kurt_only` (G3) — **DONE session 6**, §5O.4, ledger R-5. Raw exactly invariant; gated IMS NOT stable → bound the claim
- ⬜ **1.6** Onset estimator bias/variance, Monte Carlo (G1)
- ⬜ **1.7** One-class SVM — report or delete (D7) ⛔ blocked on D-5
- ⬜ **1.8** *(new)* **D-8 code fix** — no-onset fallback emits NaN + `no_onset` flag instead of legacy substitution (`src/lead_time.py:234-240`; fix the `benchmark.py:130` warning too). Sign-off granted, **scoped to that branch only**. Re-emit affected results to **NEW** files; recount validity under both conventions. Add unit tests for the NaN-gate and no-onset paths — there are currently none (`tests/test_metrics.py` asserts only that `compute_FAR_preonset` returns NaN, never what `valid_alarm` does with it).

### Part 2 — Claim corrections (text)
- ✅ **2.1** **DONE session 4.** Bounded form applied at all five prose sites — `tex:87`, `:95`, `:922`, `:930`, `:949` — each naming the Isolation-Forest-on-FEMTO exception as lying inside the ±1 h margin, matching the abstract's wording. **Rule 10 verified on a REBUILT PDF** (`tools/tectonic.exe`): "never better" **0**, "never costs" **0**. The sixth headline location was the abstract, already rewritten (§5L.1). §5M
- ⬜ **2.2** Scope the non-destruction conclusion by bearing lifetime (D21, F5, G8)
- ⬜ **2.3** Scope the deep-model no-crossover claim (G4, F3). **Add the quantitative form of §4.5's "data-starved" remark** (session 4): **LSTM-AE fits 54,657 parameters to 631 training windows — roughly 87 parameters per training example**; TCN-AE 29,681 and Transformer-AD 20,305 at the same 631 windows. This turns a qualitative caveat into a measured one and **strengthens the G4 and F3 scoping**, since it explains *why* no crossover appears in the tested training-fraction range rather than merely asserting it. Source: `results/tables/deep_model_params.csv`; hyperparameters from `src/config.py` `MODELS`.
- ⬜ **2.4** Remove all 18 self-descriptive statements (D23)
- ⬜ **2.5** *(new)* Rewrite the §1 folklore paragraph to separate waveform averaging from summary aggregation — see §5
- ⬜ **2.6** *(new)* Delete the false IMS "signal level" sentence at `scada_ijphm.tex:128` — see N-1
- ✅ **2.7** **DONE session 5 — MINIMUM VERSION.** One sentence added after Eq. 5 (`tex:219`): where the pre-onset region is empty the onset estimator places $t_o$ at or before the first scored window, `FAR_pre` is undefined, and the alarm is excluded from the validity denominator rather than counted as valid. **The full three-outcome `cases` definition was NOT applied** — author scope reset, session 5. Verified on a rebuilt PDF (rule 10): "excluded from the validity denominator" present ×1.
- 🅿️ **2.8** **DEFERRED session 5 — author decision.** The full nine-site restatement under both conventions is parked. Nothing was restated; Table 12, Table 18 and Table 23 are untouched. **The measurement is complete and preserved in §5N below** — if a reviewer raises the gate convention, the numbers are ready and no re-run is needed.

- ✅ **2.9** **DONE session 5.** Caption of `tab:farbudget` (`tex:674`) now states that the gate is applied to the across-run **mean** pre-onset FAR, names LSTM-AE as the case (62.00% mean at the 99.5th percentile vs 4.19% FAR and 59.67 h valid lead on `3rd_test` alone), and says explicitly that a zero row is **not** evidence of no valid operating point at any threshold, pointing to Table 16 and §6. Verified on a rebuilt PDF (rule 10): "averaged across the three runs" present ×1. Confirmed safe from D-7: `tradeoff_IMS_long.csv` has **zero** unscoreable rows, so Tables 14/16/22 do not move under any gate convention. Original item text follows.
- *(original 2.9 text)* *(new, session 4 — D-9 / N-16)* **Table 14's caption must carry the mean-across-runs warning IN THE MANUSCRIPT**, not only in the progress file. `tab:farbudget` (`tex:674`) reports L(τ) gated on the **mean** pre-onset FAR across runs, so a detector can hold a **valid alarm on an individual run and still show 0.0**. LSTM-AE is exactly that case: mean FAR 62.00% at the 99.5th percentile → all-zero row, while `3rd_test` alone sits at **4.19% FAR with 59.67 h of valid lead**. Without the caption warning, Table 14's zero row can be read as evidence that the deep models have no valid operating point *regardless of threshold* — **rebuilding defect N-16 in a new location**. Add one sentence to the caption stating the gate is on the across-run mean and that per-run validity is reported in Table 16 / §6.1. Sources: `results/tables/d9_tables_14_22_eleven.csv`, `results/tables/tradeoff_IMS_deepmodels_long.csv`.
### Part 3 — New content
- ⬜ **3.1** Related work ×3: false-alarm cost / NAB (D1), classical change detection (F1), time-aware & uncertainty-aware evaluation (G6)
- ⬜ **3.2** Signal-theoretic grounding (G2) — **rewrite per path**, see §5
- ⬜ **3.3** Deep-model architecture table (G5) — **numbers ready, ledger R-8 filled.** **LSTM-AE 54,657** params (`seq_len 30, latent_dim 16, hidden_dim 64, 50 epochs`) · **TCN-AE 29,681** (`seq_len 30, channels 32, kernel 3, levels 4, 40 epochs`) · **Transformer-AD 20,305** (`seq_len 30, d_model 32, nhead 2, layers 2, ff 64, 40 epochs`), all at the 49-dim invariant schema. Also Deep SVDD `hidden 32, latent 8, 40 ep` and OC-SVM `rbf, nu 0.05, gamma scale`. Sources: `results/tables/deep_model_params.csv` + `src/config.py`. §5K.3
- ⬜ **3.4** ONGC derived artifacts in Data Availability (G7, D5) ⛔ blocked on D-3
- ⬜ **3.5** Future work: longer / long-life bearings, other bearing types (D8)
- ⬜ **3.6** *(new)* New §4.7.1 per-dataset coarsening-level table — content ready in §5

### Part 4 — Presentation
- ⬜ **4.1** Regenerate Figures 2 and 10 (D17, D16)
- ⬜ **4.2** Abbreviations: SCADA, SPC, BPFO/BPFI/BSF/FTF, ROC–AUC, CUSUM, LSTM, SVDD, PCA, FFT, ONGC (D13, F7)
- ⬜ **4.3** Cut Table 21 (D14)
- ⬜ **4.4** Cut Table 23 and §7.4; move Tables 15 and 20 to appendix (D15, D22, F8)
- ⬜ **4.5** Cross-reference repair after cuts (⚠️ 29 tables, 11 figures)
- ⬜ **4.6** Sentence complexity — 180 em-dashes → under 60 (D10, F6)
- ⬜ **4.7** Table density, esp. Table 11 (F9)

### Part 5 — No action, but state in the response letter
- ➖ **D12** Typos: none identified
- ➖ **G9** Clarity: no corrections required
- ➖ **D2 / G8** Onset circularity — already in §8; reinforced by 1.5 and 1.6
- ➖ **D4** Not all models on all runs — already handled via explicit N/A cells
- ➖ **F3 / G8** Indirect RUL comparison — §2.2 explains; add one limitation sentence

### Part 6 — Final
- ⬜ **6.1** Response to Review document completed (all 50 items)
- ⬜ **6.2** Pre-submission verification checklist (register Part 6)
- ⬜ **6.3** Repo + Zenodo updated **before** the paper is submitted
- ⬜ **6.4** PHM Society formatting check
- ⬜ **6.5** *(new, session 4)* **Unprompted-disclosure paragraph in the Response to Review.** A short, plainly worded paragraph naming the **three defects found during revision that no reviewer caught**: **N-15** (Table 5's 3σ valid-alarm fraction of 1.00 does not reproduce — released data give 0.67, and the source file had no generating script), **N-17** (`tex:970` claimed "ten evaluated detectors" against a nine-row Table 25 — RMS-trend was never timed), and **N-18** (§6.9 claimed EWMA has the highest raw lead in Table 16, which that table contradicts: Hotelling T² 176.9 vs EWMA 89.1). All three are **independent of the D-2 re-baseline and of any reviewer request**, and all three are now fixed. **Why disclose:** Reviewer D's decision was driven by finding internal contradictions unaided; volunteering the ones we found ourselves shows the same audit was run across the whole manuscript rather than only at the points challenged, and each disclosure comes with a fix rather than an excuse. Keep it to one paragraph, factual, no self-praise (item 2.4 applies to the response letter too). Sources: §5D, §5K.1, §5L.3.

  **D3 answer (one-class SVM) — settled wording, session 5.** Recorded here on author
  instruction; use verbatim in the Response to Review:

  > Adding one-class SVM widens the correction family from N = 40 to N = 44 and raises the
  > uncorrected family-wise error rate from approximately 0.87 to approximately 0.90. No
  > hypothesis is rejected at either family size; the smallest raw p-value remains 0.031
  > (Isolation Forest on FEMTO) with a Holm-adjusted p of 1.00. The reviewer's requested
  > addition therefore widens the evidence base without altering any conclusion.

  Sources: `results/tables/d3_ocsvm_holm_N44_invariant.csv` (N=44 family, adjusted p),
  `results/tables/d3_ocsvm_benchmark_long.csv` (OC-SVM run-level results).
  ⚠️ **Naming:** "D3" is the internal analysis-run label (`src/d3_ocsvm.py`, ledger R-10).
  The reviewer's comment is **D7**. There is no reviewer item D3 — do not cross-label them.
  Applied to `IJPHM-response-letter-draft.md` under D7, session 5.

---

## 7. Defects found during execution — not from the reviewers

These are the same class of defect Reviewer D is hunting. Numbered N-1 onward.

| # | Defect | Severity | Status |
|---|---|---|---|
| **N-1** | `scada_ijphm.tex:128` claims IMS coarsening is "at the signal level" — false; IMS is the only dataset at level (c) | **High** — third internal contradiction, on the dataset carrying the only directional trend | ⬜ → item 2.6 |
| **N-2** | IMS ran on the **445-dim legacy** feature schema (78 test windows, p ≫ n); the other four ran on the 49-dim invariant schema. `config.py:110-113` calls the legacy schema "back-compat and appendix comparison only", and §4.2 of the paper argues at length that it is ill-posed | **High** — the headline dataset used the scheme the paper condemns | ⚠️ D-2, measure first |
| **N-3** | `results/` and `paper/` are gitignored; zero result files tracked; the submission `.tex` is untracked. Data Availability claims "every table and figure is generated directly from the released result files" | **High** — all three reviewers praised reproducibility; if Zenodo lacks the files, that praise inverts | ⛔ D-3 |
| **N-4** | `.zenodo.json` stale — lists four datasets (Ferrara missing) and a different title | Medium | ⬜ |
| **N-5** | `feature_coarsening_ablation.py` docstring (lines 7-11) claims it uses `downsample_features`; lines 77-81 call the snapshot-level path. Manuscript inherits the claim at `:734` | Medium | ⬜ |
| **N-6** | ~~XJTU `Bearing1_2` has no onset → effective n = 9; TOST floor 0.5⁹~~ **SUPERSEDED.** The premise was wrong in a deeper way: the sign test excludes *zero-difference* runs, so the floor is per-detector `0.5^(n₊+n₋)`, not `0.5^(bearing count)`. On XJTU that is n=4 (3σ), n=3 (CUSUM), n=2 (Hotelling) — TOST infeasible for most detectors, not just IMS | Medium → **resolved** | ✅ register 1.2 + brief Phase 2 corrected, session 2 |
| **N-7** | NaN `far_preonset_pct` widespread. **Confirmed: the FAR gate is skipped by design when `FAR_pre` is NaN** (`lead_time.py:232`), leaving `valid_alarm = lead_time > 0`. **295 rows corpus-wide carry a valid alarm that was never gated** (XJTU 189, Ferrara 96, IMS 10). Eq. 5 as published has no such carve-out | **CRITICAL** — published counts reproduce exactly (20/50 ✅, 209/450 ✅) but are not the counts Eq. 5 describes; under strict Eq. 5 they become 7/50 and 73/450 | ✅ **RESOLVED** §5A → decision **D-7**; items 2.7, 2.8 |
| **N-8** | `paper/verify_numbers.py` stale — hardcoded `C:\scada` paths, targets `scada_journal.tex` | Low | ⬜ |
| **N-9** | `test_diagnostic_console.py::test_metropt_loads_with_expected_parameters` fails — real MetroPT CSV present, loader prefers it over the fixture. Touches no paper number | Low / benign | ⬜ |
| **N-10** | `src/lead_time.py:179` docstring — "`valid_alarm` is gated on lead_time > 0". That describes the *no-onset fallback*, not the gate. Inaccurate for the primary path | Medium | ⬜ → item 1.8 |
| **N-11** | `src/benchmark.py:130` warns "no onset detected — onset-relative metrics will be NaN". True for `detection_delay`, `max_lead`, `lead_norm`; **false for the two that matter** — `far_preonset_pct` silently becomes legacy FAR and `valid_alarm` silently becomes the legacy VLT test. The log line conceals the substitution rather than flagging it | Medium | ⬜ → item 1.8 |
| **N-13** | **Console encoding breaks the released scripts on Windows.** Detector names contain `σ` (`3σ Rule (σ=3.0)`, `RMS-Trend (kσ)`, `EWMA (λ=0.2, k=3.0)`, `Hotelling T²`). Printing any results table crashes with `UnicodeEncodeError: 'charmap' codec can't encode 'σ'` under the default cp1252 console. This is the **same encoding fault** that corrupts Figures 2 and 10 (register 4.1) — one root cause, two symptoms. A reviewer running the released code on Windows hits it immediately | Medium — reproducibility; all three reviewers praised reproducibility | ⬜ mitigated in `src/ims_schema_check.py` via `sys.stdout.reconfigure(encoding="utf-8")`; **apply the same guard repo-wide and fold into register 4.1** |
| **N-14** | **§4.2 does not describe what was done on the headline dataset.** §4.2 (`tex:163`, *Channel-Invariant Feature Schema*) argues the 445-dim scheme is ill-posed at p ≫ n and presents the 49-dim invariant space as the paper's methodology. The IMS controlled sweep ran at **445 dims** (78 test windows at f=1 on `2nd_test`; p ≫ n by ~5.7×). Same class of defect as §4.7 — a methods section describing a procedure other than the one executed — which **Reviewer D has flagged three times**. Not cured by calling the invariant rerun an "appendix robustness check": that leaves §4.2 describing a schema the headline result did not use | **High** — methods/execution mismatch on the headline dataset | ⚠️ tied to **D-2**; recorded session 3, §5B.0.3 |
| **N-15** | **Table 5's 3σ valid-alarm fraction does not reproduce.** `tab:persistence` (`tex:365`) and the §5.2 prose (`tex:357`) both state the 3σ valid-alarm fraction is **1.00 at every persistence**. `benchmark_IMS_long.csv` gives **0.67** (2 of 3 runs) — `1st_test` has pre-onset FAR 29.1% > τ=10%, so `valid_alarm=False`. **0.67 under every denominator tried** (f=1 aggregate; aggregate all factors; all rows) and **under both schemas**, so it is not a D-2 effect. `persistence_sensitivity_IMS.csv` stores `valid_frac_f1_agg=1.0` at persistence 3 while its `median_agg_minus_dec_h=18.43` in the same row *does* reproduce from the benchmark file — so one column of that file agrees with the released data and the other does not. The file had **no generating script anywhere in the repo** (Grep over all `*.py`), so the discrepancy could not be traced or rerun. The manuscript draws a conclusion from it: "the deployable-detector recommendation does not depend on this parameter" | **High** — a fourth internal contradiction of exactly the species Reviewer D found twice | ✅ **RESOLVED session 3.** Generator written (`src/persistence_sweep_ims.py`) and run on **both** schemas. The legacy rerun reproduces the published table's **three median rows to the digit** but gives **0.67, not 1.00**, for the valid-alarm row — isolating the defect to that single column and ruling out schema, convention, and generator error. Fix: correct the row to 0.67 and **withdraw** the "does not depend on this parameter" conclusion (validity falls to 0.33 across factors at p=10). §5D |
| **N-16** | **§6.1's "regardless of threshold" is false.** `tex:275` states the three deep reconstruction models' pre-onset FAR is "far above the τ = 10% budget regardless of threshold". The threshold sweep that produced Table 16, run for those three models (D2, §5G.2), shows **LSTM-AE attains a valid operating point at the 99.5th percentile on `3rd_test`: FAR_pre 4.19%, lead 59.67 h, `valid_alarm = True`.** Its FAR falls 46.5% → 4.19% between the 99th and 99.5th percentiles, so the model trades lead for FAR normally rather than flooding unconditionally. TCN-AE and Transformer-AD attain no valid point at any percentile tested | **High** — a fifth internal contradiction, and the reviewer asked for exactly this evidence | ✅ measured session 4, `results/tables/tradeoff_IMS_deepmodels_long.csv`; **seed-robust: 10/10 seeds, FAR 4.19% at every seed** (`d2_seed_check_lstmae.csv`) despite training loss varying 0.0027–0.0040 and threshold 0.0062–0.0084 — **not a seed artifact**; **needs a text correction, not a citation** |
| **N-17** | **`tex:970` overreaches Table 25 by one detector, in the submitted manuscript.** Table 25 (`tex:1013-1021`) lists **nine** detectors; `tex:970` states monitoring is "not compute-bound for any of the **ten** evaluated detectors". **RMS-trend was never timed.** Found while adding the OC-SVM timing (D-5), and independent of it | Medium — a count claim exceeding its own table, the species Reviewer D is hunting | ✅ **RESOLVED session 4** — `rms_trend` and `one_class_svm` both timed (`compute_cost_IMS_extra_invariant.csv`); Table 25 can now carry all **eleven** and `tex:970` becomes true as "eleven". §5K.1. 🗣️ **DISCLOSE EXPLICITLY IN THE RESPONSE TO REVIEW** — this defect was **found and fixed unprompted**, not raised by any reviewer, and it predates OC-SVM entirely. Volunteering it demonstrates the same audit Reviewer D performed was run against the whole manuscript, and costs nothing: the conclusion is unchanged once the count is corrected to eleven. |
| **N-18** | **§6.9 contradicts Table 16 about which detector has the highest raw lead.** `tex:640` states "EWMA attains the highest raw lead in Table~
| **N-19** | **Table 6's caption claim is false, and `gap_injection.csv` is an orphaned artifact.** `tab:missing` (`tex:380`) asserted "Valid-alarm fractions (not shown) are unchanged across gap levels". Measured on the released file: IMS holds at 2/3 for all three detectors, but **XJTU-SY 3σ moves 5/10 → 6/10 → 5/10**. Separately, the file carries **no `far_preonset_pct` column** and **no generating script existed anywhere in the tree** (same class as N-15), so its validity flags could not be re-derived | **Medium** — a false invariance claim in a caption, on an artifact that could not be audited | ✅ **RESOLVED session 5.** New generator `src/d19_gap_injection.py` → `results/tables/gap_injection_far.csv`; gap=0 arm reconciles exactly, caption corrected to the measured values. ⚠️ gap>0 arms are **not** reproducible (original RNG draw lost) — Table 6's body left on the released numbers. §5N.3 |
ef{tab:tradeoff}", but the published Table 16 gives **Hotelling T² 176.9 h** and **Iso. Forest 174.7 h** against **EWMA 89.1 h**. The same paragraph and the Figure 6 caption (`tex:654`) say "EWMA and Isolation Forest dominate the upper-left", yet over the full swept curve **Hotelling T² strictly dominates EWMA on both axes** (lead 187.8 vs 174.8; min FAR 19.0 vs 20.8). A third clause, "the raw-lead column of Table 2, where EWMA leads", is additionally false under D-2. **The first two are wrong in the submitted manuscript, independent of the re-baseline** | **High** — a sixth internal contradiction, and it contradicts a table on the same page | ⬜ **NOT YET EDITED** — reported to the author session 4, awaiting decision. Sources: `results/tables/tradeoff_IMS.csv`, `results/tables/benchmark_IMS_leadtime_ci_invariant.csv`. §5L.3 |
| **N-20** | **Aggregate and decimate are NOT compared at the same logging interval on the standard path.** `src/__init__.py:207`: `target_min = max(1, int(round(base_min * downsample_factor)))` rounds aggregation bins to whole minutes with a 1-min floor, while decimation takes exactly every k-th row. With sub-minute base spacing, "aggregate f=2" is a 12× (Ferrara, 5 s base) or 6× (FEMTO/ONGC, 10 s base) coarsening. Measured on the published files: effective interval differs between modes in **24/30** (run, factor) cells on FEMTO, **24/30** on Ferrara and **4/5** on ONGC; **0** on XJTU-SY (1-min base) and IMS (controlled path). E.g. Ferrara E1 f=2: aggregate 1.00 min / 82 test windows vs decimate 0.17 min / 492. Affects Tables 8 and 9, the ONGC case study, Figure 2, the FEMTO/Ferrara Holm cells, the D15 equivalence cells (R-2) and the Ferrara validity gap (§5O.6) | **High** — the matched-factor premise of the central comparison fails on two of four inferential datasets | 🔧 **FIXED session 6 under D-10** (`src/__init__.py:207-213`: bins at `round(base_min*60*factor)` seconds). **Verified:** (i) `load_pipeline` fingerprints for IMS and XJTU-SY identical before and after, 117/117 cells (`n20_pipeline_hash_check.csv`); (ii) full benchmark reruns reproduce the published files: XJTU-SY **raw file bytes identical**; IMS values and bytes identical on all 24 shared columns (the published invariant file carries one extra `feature_mode` column) (`n20_reproduction_check.csv`); (iii) FEMTO and Ferrara: every decimate row and every f=1 row identical to the published data; only aggregate f>1 rows change; agg/dec interval mismatches 24+24 → **0**. Propagation: §5O.10. Found session 6 |
| **N-21** | **Table 4 (`tab:decoupled`) had no generator** — the fourth orphaned artifact (after N-15, Table 25, N-19); `kurt_only` was not an indicator kind in `src/onset.py` | Medium | ✅ **RESOLVED session 6** — reconstructed, reproduces exactly. §5O.7 |
| **N-12** | **`Bearing1_2` legacy-metric substitution.** With no onset, `lead_time.py:234-240` writes **legacy FAR into `far_preonset_pct`** and **legacy VLT into `valid_alarm`**, under onset-relative column names. Verified on all 100 rows: `far_preonset_pct == far_legacy_pct` 100/100; `valid_alarm == (vlt_legacy > 0)` 100/100. Table 12's entry (V/5 = 1, 0.67 h, EWMA) is arithmetically correct but produced by a criterion the paper never states. Hotelling T² earned 1.083 h raw lead and was killed by the *legacy* 20%-marker rule, not Eq. 5. Worse than N-7's NaN case: a real-looking number occupies the `FAR_pre` column and **is not `FAR_pre`** | **High** — a silent metric substitution on a bearing that appears in a published table | ✅ diagnosed §5A → decision **D-8** (code fix signed off); fix in item 1.8 |

---

## 8. Numbers ledger — every ⟦R-n⟧ and where its value came from

**Nothing enters the manuscript from this table until the "Source file" column is filled with a real path.**

| ID | What | Status | Source file | Value |
|---|---|---|---|---|
| R-1 | Per-dataset coarsening level | ✅ resolved | code inspection, §5 above | IMS = (c); XJTU/FEMTO/Ferrara/ONGC = (b) |
| R-2 | Equivalence bound / CIs (item 1.2 / D15) — ⚠️ **FEMTO/Ferrara/ONGC values superseded by R-19 (N-20)**; the verdict 30/30 survives, the IF-on-FEMTO exception does not | ✅ resolved (session 4) | `results/tables/d15_equivalence_bootstrap.csv` · `results/tables/d15_equivalence_tost.csv` via `src/d15_equivalence.py` | **δ = 1 h**, pre-specified on operational grounds. 60 cells (6 dataset-arms × 10 detectors). **Bootstrap (primary):** 30 equivalent · 13 inconclusive · 7 **aggregate superior beyond margin** (never inferior) · 10 untestable (ONGC n=1). Equivalence is **complete on XJTU-SY (10/10), FEMTO (10/10) and Ferrara (10/10)**; **zero** IMS cells are equivalent under either schema. **TOST feasible in 22/60 cells**; feasible-and-equivalent in 17. Full table §5G.1 |
| R-3 | Deep AE threshold-sweep rows (item 1.3 / D2) | ✅ resolved (session 4) — ⚠️ **CONTRADICTS §6.1** | `results/tables/tradeoff_IMS_deepmodels.csv` · `results/tables/tradeoff_IMS_deepmodels_long.csv` via `src/d2_deep_tradeoff.py` | Mean-across-runs Ld / FAR_pre at 95th·99th·99.5th — **LSTM-AE** 199.61/87.81† · 193.99/82.16† · 93.58/62.00† · **TCN-AE** 185.36/82.63† · 183.14/79.93† · 180.36/74.43† · **Transformer-AD** 183.97/81.05† · 181.75/79.18† · 178.69/71.99†. All nine cells daggered on the mean. **But LSTM-AE at the 99.5th percentile on `3rd_test` scores FAR_pre = 4.19% ≤ τ and lead = 59.67 h, `valid_alarm = True`** → valid_frac 0.33. §6.1's "regardless of threshold" is **false as written**. Detail §5G.2 |
| R-4 | IMS test-3 under original label (item 1.4 / D17) | ✅ resolved (session 4) | `results/tables/d17_label_comparison.csv` · `results/tables/d17_ims_long_originallabel.csv` via `src/d17_original_label.py` | Medians (corrected → original): 3σ **+15.10 → +15.10** · CUSUM **+4.27 → +4.15** · EWMA **+2.10 → +0.00** · Hotelling **+1.17 → +1.17** · Iso. Forest **+3.43 → +0.00** · Deep SVDD **0.00 → 0.00** · RMS-trend **0.00 → 0.00** · LSTM-AE/TCN/Transformer **−0.42 → −0.42**. **No median flips sign.** Best p under either label = **0.25** (Hotelling); no detector reaches α under either. **Test 3 is a guaranteed miss for 6 of 10 detectors, NOT all 10** — n_eff falls to 2 for four detectors and 1 for two, but **stays 3 for Hotelling, LSTM-AE, TCN-AE and Transformer-AD**, which still earn lead in both modes. Detail §5G.4 |
| R-5 | Contrast under disjoint onset (item 1.5 / G3) | ✅ resolved (session 6) | `results/tables/rg3_contrast_by_indicator.csv` · `rg3_raw_invariance.csv` · `rg3_reproduction_check.csv` · `rg3_onsets.csv` via `src/rf2_rg3_gated_contrast.py` | **Raw lead exactly invariant**: max abs dev **0.000 h** over 99 cells (rebuild reproduced 2,750/2,750 rows at Δ = 0). **Gated (D-7) max median shift vs rms_kurt:** IMS **4.27 h** (CUSUM +4.27, EWMA +2.10, Hotelling +3.50 → **0.00** under both; Iso. Forest +3.43 holds under pca1, → 0.00 under kurt_only); FEMTO ≤ 0.030; XJTU-SY ≤ 0.125; Ferrara 0.073 (pca1) / 0.603 (kurt_only, n=2); ONGC n=1 Hotelling −4.67 → +2.31. `kurt_only` undefined on ONGC. **Holm 0/44 under every indicator.** §5O.4 |
| R-6 | Onset bias / variance | ⬜ | | |
| R-19 | N-20 post-fix values (FEMTO/Ferrara/ONGC contrasts, Holm, D15, RF-2, paired validity) | ✅ measured (session 6), **NOT yet in the manuscript** | `results/tables/n20_raw_contrast_old_vs_new.csv` · `n20_manuscript_cells.csv` · `n20_ongc_minutes.csv` · `n20_d15_bootstrap_{old,new,new_11det}.csv` · `n20_d15_tost_*.csv` · `rf2_gated_contrast_n20.csv` · `rf2_valid_fraction_paired_n20.csv` via `src/n20_propagate.py`, `src/n20_resample_fix.py` | Holm 0/44 (min raw p 0.031 → 0.125); D15 **30/30** (33/33 with OC-SVM); IF on FEMTO −0.180 [−0.488, +0.025]; Ferrara paired validity 54.8% vs 58.9%, runs 2+/3−, p 1.00 (**the gap was the bug**); 81 printed cells move. §5O.10 |
| R-18 | Gated aggregate−decimate contrast + validity companion (item 1.1 / F2) | ✅ resolved (session 6) | `results/tables/rf2_gated_contrast.csv` · `rf2_valid_fraction_agg_vs_dec.csv` · `rf2_crosscheck_raw_vs_published.csv` via `src/rf2_rg3_gated_contrast.py` | Raw column reproduces Tables 7–11: **238/238** (IMS legacy file). **Gated (D-7): Holm 0/44, min adj p 1.00**; ties **59 → 108**, n₊+n₋ **195 → 108**, **38** runs excluded as unscoreable. IMS 3σ **+15.10 → 0.00**; CUSUM +4.27, EWMA +2.10, Hotelling +3.50, Iso. Forest +3.43 (each 2+/0−/1 tie, p 0.50). Ferrara EWMA −0.114, Hotelling −0.064 (0+/5−, p 0.0625). Validity agg vs dec (valid/scoreable): IMS 47/131 vs 47/147 · XJTU-SY 34/202 vs 44/202 · FEMTO 94/300 vs 99/315 · Ferrara **103/245 vs 155/263**. 0 of 122 flips with identical raw lead. §5O.2–5O.3 |
| R-7 | One-class SVM (item 1.7 / D3) | ✅ resolved (session 4) — **it EXISTS and RUNS** | `results/tables/d3_ocsvm_benchmark_long.csv` · `_leadtime_ci.csv` · `_holm_N44_invariant.csv` · `_holm_N44_legacy.csv` · `_tradeoff{,_long}.csv` · `_farbudget_phrank.csv` via `src/d3_ocsvm.py` | **Mean raw lead + 95% CI at f=1:** IMS **180.25** [65.50, 316.68] (n=3) · XJTU-SY **1.44** [0.82, 2.10] (n=10) · FEMTO **0.95** [0.69, 1.30] (n=6) · Ferrara **0.98** [0.52, 1.50] (n=6) · ONGC **35.34** (n=1). **Holm N=44: 0/44 rejections** under both IMS schemas (was 0/40) — verdict unchanged. **Table 16:** 180.25/63.21† · 92.47/56.68† · 92.47/55.45†. **Tables 14/22:** PH **180.2**, L = **0.0** at τ = 0.05/0.10/0.20. Detail §5G.3 |
| R-8 | Deep-model architecture params (item 3.3 / G5) | ✅ resolved (session 4) | `results/tables/deep_model_params.csv` via `src/d3_compute_cost_extra.py`; hyperparameters from `src/config.py` `MODELS` | **LSTM-AE 54,657** params (`seq_len 30, latent 16, hidden 64, 50 ep`) · **TCN-AE 29,681** (`seq_len 30, ch 32, k 3, levels 4, 40 ep`) · **Transformer-AD 20,305** (`seq_len 30, d_model 32, nhead 2, layers 2, ff 64, 40 ep`). All at 49-dim invariant schema. LSTM-AE = **87 params per training window** at 631 windows — quantifies §4.5's data-starvation caveat. §5K.3 |
| R-9 | ONGC released artifact paths | ⬜ | | |
| R-10 | Strict-Eq.5 validity figures (unscoreable counted invalid) — item 2.8 | ✅ resolved | `results/tables/benchmark_XJTU-SY_long.csv` | **73/450** (five detectors, all cells); **7/50** (Table 12 full-res aggregate) |
| R-11 | Three-outcome validity counts (valid / invalid / **unscoreable**) per dataset × detector — items 2.7, 2.8 | ⬜ | *(to be emitted by item 1.8 into a NEW result file)* | |
| R-12 | Valid-alarm fractions in the IMS ablation tables (`tex:370`, `:738`, `:758`, `:775`, `:798`) under the new convention | ⬜ | *(ablation result files — NOT yet audited, see §5A.6)* | |
| R-16 | Abstract (`tex:63`) values as WRITTEN — item 2.1/2.2/D15/D3 | ✅ **written to `.tex`** (session 4) | `ims_runlevel_test_invariant.csv` · `d3_ocsvm_holm_N44_invariant.csv` · `d15_equivalence_bootstrap.csv` | 3σ median **+15.1 h** · **N=44**, adj. p **1.00** · **30/30** cells equivalent at ±1 h · IMS **8 of 10** undecided, **2** favour aggregation beyond margin · Iso. Forest on FEMTO **−0.26 h [−0.54, −0.06]** inside margin. §5L.1 |
| R-17 | `tex:275` deep-model sentences as WRITTEN — N-16 correction + P19 | ✅ **written to `.tex`** (session 4) | `benchmark_IMS_leadtime_ci_invariant.csv` · `benchmark_IMS_long_invariant.csv` · `tradeoff_IMS_deepmodels_long.csv` · `d2_seed_check_lstmae.csv` | raw leads **183–198 h** · FAR **61%→100%** at the 97.5th · LSTM-AE **59.7 h at 4.19% FAR**, 99.5th, test 3, **10/10 seeds**, fraction **1/3** · Hotelling **174.8** leads classicals. §5L.2 |
| R-13 | IMS aggregate−decimate contrast under the **invariant** schema (D-2) | ✅ resolved (**corrected session 3**) | `results/tables/benchmark_IMS_long_invariant.csv` via `src/d2_convention_recompute.py` | **Run-level medians (mean collapse, §4.8):** 3σ **+15.1** h (sign-test p 1.00, 2+/1−), Iso. Forest **+3.4** (1.00, 2+/1−), EWMA **+2.1** (1.00, 2+/1−), CUSUM **+4.3** (0.25, 3+/0−), Hotelling T² **+1.2** (0.25, 3+/0−) — full table §5B.0.1. ~~Pooled medians 5.83/0.83/0.83/0.83 with Wilcoxon p~~ **SUPERSEDED — wrong convention, must not enter the manuscript** |
| R-14 | IMS Table 2 (`tab:imslead`) mean raw lead + 95% CI under the invariant schema | ✅ resolved | `benchmark_IMS_long_invariant.csv` via `bootstrap_ci_across_runs`, `src/d2_cascade_audit.py` | 3σ **64.6** [28.8, 108.7] · EWMA **78.6** [28.0, 152.2] · CUSUM **64.8** [26.3, 114.9] · Hotelling T² **174.8** [56.3, 315.9] · Iso. Forest **87.2** [49.7, 152.2] · Deep SVDD **14.8** [0.0, 34.0] · RMS-trend **3.2** [0.0, 9.7] · LSTM-AE **197.6** [65.5, 331.7] · TCN **183.7** [65.5, 330.9] · Transformer **183.4** [65.5, 330.9] |
| R-15 | Table 5 3σ valid-alarm fraction as it actually reproduces (N-15) | ✅ resolved | `results/tables/benchmark_IMS_long.csv` and `..._invariant.csv` | **0.67** (2/3 runs) under every denominator and both schemas — **not** the published 1.00 |

---

## 9. Next action

> **SESSION 6 (2026-09-17).** The `.tex` is unfrozen and owned in-repo (§0). RF-2 and RG-3 are done (§5O).
> Manuscript follow-ups now measurable, **not yet applied** (need author prose / go-ahead):
> 1. §6.6a: gated-contrast table + companion validity table (R-18); state the power loss (ties 59→108).
> 2. §6.2 "invariant to the onset definition by construction": **true for raw lead (verified, 0.000 h)**,
>    **false for gated L on IMS** (R-5). Bound it explicitly.
> 3. ~~Tables 10 and 11 still show legacy IMS values~~ ✅ **D-2 re-baseline completed and Table 11 at 44 rows (§5O.9, `20658e5`).**
> 5. **N-20 — FIXED, propagated (§5O.10) and applied to the manuscript (§5O.11, `394cd96`).** Original note: aggregate and decimate run at different logging intervals on FEMTO/Ferrara/ONGC (`src/__init__.py:207`). Needs rule-4 sign-off, a code fix, and reruns before Tables 8/9, Figure 2, the FEMTO/Ferrara Holm and equivalence cells, or the Ferrara validity gap can be trusted.
> 6. D-5/D-9 rows still missing from Tables 7, 8, 9, 14, 16, 22 (§5O.8a).
> 4. Table 4 now has a generator (`rg3_onsets.csv`); cite it in Data Availability.


> **⚠️ SESSION 4 — READ FIRST. Two published claims are now known to be false, and one
> planned fix is now known to be unnecessary.**
>
> 1. **N-16 (new, High).** `tex:275`'s "regardless of threshold" is **false**. LSTM-AE attains a
>    valid operating point at the 99.5th percentile on `3rd_test` (FAR 4.19%, lead 59.67 h).
>    §6.1 must be **corrected**, not merely evidenced. §5G.2.
> 2. **D-5's premise is wrong.** One-class SVM **exists and runs**. Do not delete the §4.5
>    clause on the assumption it was never evaluated. Full results measured; Holm at
>    **N=44 → 0/44**, headline unaffected. §5G.3.
> 3. **Register 1.4's pre-written anticipation is wrong.** Test 3 under the original label is a
>    guaranteed miss for **6 of 10** detectors, not all ten; effective n is detector-dependent
>    (3 / 2 / 1), not a uniform "n = 2". Rewrite that paragraph before it reaches Appendix C. §5G.4.
> 4. **Equivalence does not hold on IMS.** δ = 1 h equivalence is established on XJTU-SY, FEMTO and
>    Ferrara (30/30 cells) and on **no** IMS cell under either schema. Register item 2.1's drafted
>    abstract clause must be scoped to the three multi-bearing campaigns. §5G.1.
>
> **Author decisions: D-4, D-5 and D-9 all DECIDED (session 4).** See §4.
>
> **Phase 7 em-dash target — REVISED.** The brief's "under 60" was set against the rendered 180.
> Measured baselines: **230** naive `grep -c -- '---'` (**wrong** — includes 54 comment-only), **176**
> live, **167** live prose (excluding 9 inside `table`/`tabular`), **180** rendered in the PDF.
> **Target: approximately 100 LIVE dashes**, counted on **non-comment, non-table-rule occurrences
> only** — i.e. measured against the **167** prose baseline, not against 230 and not against 60.

**Phase 0.5(A) ✅ COMPLETE** (session 2) — findings in §5A, decisions D-7 and D-8, defects N-10/11/12. Do not re-derive.

**Phase 0.5(B) ✅ COMPLETE, CORRECTED session 3** — findings §5B.0 (the session-2 numbers in §5B.2–5B.4 are superseded and must not enter the manuscript). **D-2 remeasured and its cascade quantified (§5C) — still NOT decided; author input required.** D-2 now also carries **N-14 (High)**: it is a methods/execution mismatch, not only a robustness question.

⚠️ **New this session: N-15 (High)** — Table 5's 3σ valid-alarm fraction of 1.00 does not reproduce (released data give 0.67), and its source file has no generating script. **Independent of D-2**; needs its own fix regardless of how D-2 is decided.

**Next action: Phase 1** (brief, "Repo audit against the manuscript's claims") — OC-SVM existence, deep-AE threshold sweep feasibility, and the untraceable-claim sweep.

**Then, in order:**
0. **D-2** — author decision on whether IMS is re-baselined onto the invariant schema or the rerun is reported as an appendix robustness check (§5B.5). Everything touching IMS magnitudes waits on this.
1. **Item 1.8** — implement the D-8 fallback fix (sign-off granted, scoped to `src/lead_time.py:234-240` + the `benchmark.py:130` warning). New result files only; add the missing unit tests.
2. **Item 1.1** — now unblocked by D-7. Emit three-outcome validity *and* the strict-convention counts.
3. **Item 2.7 / 2.8** — amend Eq. 5; restate every gate-dependent number under both conventions.

⚠️ Before 2.8, audit the five unmeasured ablation locations in §5A.6. They are gate-dependent by construction but come from the ablation result files, which were **not** part of the Phase 0.5(A) audit. Do not assume they move.

---

## Page target — CLOSED at 24 pages (2026-09-19)

**Decision (author, 2026-09-19): 24 pages is the landing zone. Stop cutting.** No reviewer set a
page limit, and every specific length complaint Reviewer D named is now addressed. The earlier
18.5-page target (25 − 6.5, allowing 1.5 pages for pending additions) is **withdrawn**; it was not
reachable by the C1–C6 plan, whose own estimates summed to 3.7 pages.

**Reserve cut (held, NOT applied):** Sec. 7.1 "What Changed the Story" is the single reserve.
Apply it only if the incoming prose additions push the paper past an acceptable length at the end.

### Cuts applied this session (each independently revertible)

| Cut | Commit | Result |
|---|---|---|
| Missing-data contradiction fix (not a cut) | `8cf56a8` | 25 pages |
| C1 — four ablation tables to `tab:ablation_general` alone | `ef37a40` | **25 to 24** |
| C1 fixup — acute-accent artifact (backslash-apostrophe renders as an accent) | `5bbdf42` | 24 |
| C2 — delete `tab:taugrid` (pure arithmetic from Eq. costratio) | `68bcb52` | 24 |
| C3 — Sec. 6.2 onset prose 4698 to 2845 chars | `5c6f7f3` | 24 |
| C4 — 18 self-descriptive statements to 0; non-destruction 17 to 6 | `48a02ee` | 24 |
| C5 — em-dash pass, rendered 167 to 95 | `f78ef9c` | 24 |
| C6 — Appendix B walkthrough 1146 to 850 chars | `08f6f65` | 24 |

Only C1 crossed a page boundary. C2–C6 removed ~3,400 characters of column height that is banked
but did not tip a page.

### Measurement corrections established this session

- **Page count:** read `fitz.open(pdf).page_count`. The `.log` is a stale XeLaTeX artifact.
- **Em-dashes:** the Phase 7 revision above is confirmed correct. Rendered baseline was **167**,
  now **95**, against the ~100 target. A naive source `grep` overcounts by **54** comment rules.
- **Table numbering:** author-facing numbers ran **+4** ahead of the compiled PDF (stale
  pre-Group-B numbering). Work from `\label{}` keys, not printed numbers.
- **Backslash-apostrophe is LaTeX's acute accent**, not an apostrophe. It compiles silently and
  renders wrong; guard generated prose against it and verify in extracted PDF text.

---

## Additions pass (2026-09-19) - RG-5, equivalence table, figures, abbreviations

| Item | Status | Commit |
|---|---|---|
| RG-5 deep-model architecture table (Appendix A, `tab:deeparch`) | DONE | `1f42a47` |
| Equivalence table, 33/33 cells (Sec. 6, `tab:equiv`) | DONE | `1f42a47` |
| Figures RD-11..RD-14 (mojibake, in-plot title, doubled paren) | DONE | `97101a2` |
| Abbreviations RD-7 / RD-8 / RF-7 | DONE | `1f42a47` |

**Page count: 25** (was 24 at `08f6f65`). The three new floats and the
abbreviation expansions cost one page. Sec. 7.1 "What Changed the Story"
remains the held reserve cut if the incoming prose pushes this further.

### Compile note (resolved)

A machine Application Control policy blocked `tools/tectonic.exe` and pymupdf's
native DLL for part of this session (exit 126, "An Application Control policy
has blocked this file"). It cleared on its own and the manuscript built
normally. If it recurs: `pypdf` is a working substitute for page counting and
text extraction, and matplotlib is unaffected, but there is no substitute for
the compile itself - do not report a page count from a stale PDF, and note that
tectonic writes no `.log`, so `scada_ijphm.log` is a frozen XeLaTeX artifact.

### Data-source correction

The equivalence table must be built from `n20_d15_bootstrap_new_11det.csv`
(2026-09-17, 11 detectors, 33 equivalent cells), **not**
`d15_equivalence_bootstrap.csv` (2026-09-06, 10 detectors, 30 equivalent
cells). The latter predates N-20 and omits One-Class SVM. R-19 already recorded
this as "30/30 (33/33 with OC-SVM)". The abstract moved 30 -> 33 cells, and the
IMS clause 8 of 10 -> 9 of 11, to match.

Widest CI endpoint across the 33 cells is 0.560 h, so the 1 h margin is cleared
with room to spare.

### Finding: no early stopping exists

RG-5 asked for the early-stopping rule. There is none in the code: no patience,
best-state or no-improvement logic in `src/deep_baselines.py`, `src/models.py`
or `src/baselines_extra.py`. Every deep model runs its full epoch budget
(LSTM-AE 50, the rest 40). The table records "none" rather than inventing a
rule.

Parameter counts were **measured** by instantiating each model factory at
`n_features = 49`, not copied: LSTM-AE 54,657, TCN-AE 29,681, Transformer-AD
20,305 (all three matching the author's figures) and Deep SVDD 1,824.

Secondary finding: LSTM-AE's configured `dropout = 0.1` is inert. PyTorch
applies recurrent dropout only between stacked LSTM layers and the encoder and
decoder are one layer each, so the setting has no effect. Recorded as a table
footnote.

### Figures

Root cause was UTF-8 bytes re-read as cp1252, not fonts. The affected display
labels now use matplotlib mathtext, which removes the encoding dependency.
`figure1.png` and `fig_sweep.png` regenerate byte-identical, confirming no
collateral change. All six figures were rendered and inspected.

Two cosmetic issues found while checking, **not** fixed because they were not
in scope - raise with the author:

1. `fig_sweep` (Fig. 3): the legend sits on top of the Decimate panel's data
   and hides several lines.
2. `fig_crossdataset` (Fig. 2) still carries an in-plot title, as do
   `fig_conformal_panels` and `fig_tradeoff_panels`. The register calls in-plot
   titles contrary to IJPHM house style, and only Fig. 10's was ordered
   removed. Decide whether the rest should go too.

---

## N-22 (HIGH, NEW 2026-09-19) — the FEMTO training-fraction sweep does not vary the training fraction

**Found while verifying item (b) for the RG-4 prose blocks. Blocks 2, 3 and 4 are
NOT inserted pending this.**

`src/training_sweep.py` sweeps `T` over {0.20, 0.30, 0.40, 0.50, 0.60} by mutating
the shared `SPLIT` dict (lines 72-74) and then calling
`load_pipeline(bearing, dataset=dataset)` (line 76). Its docstring states this
works "because load_pipeline reads src.config.SPLIT at call time".

**It does not.** `load_pipeline` in `src/__init__.py` takes the training fraction
from the dataset bundle:

- line 200: `train_fraction = bundle.train_fraction`
- line 250: `temporal_split(feat_df, train_frac=train_fraction, cal_frac=SPLIT["calibration_fraction"])`

`SPLIT["train_fraction"]` is never read in `src/__init__.py`. Only
`calibration_fraction` (line 251) and `normal_period_fraction` (lines 282, 323)
are. The training split therefore stays at `bundle.train_fraction = 0.50` for
every T.

**Runtime proof** (FEMTO Bearing1_1, mutating SPLIT exactly as the sweep does):

| T | len(ts_train) | X_train.shape | len(ts_test) |
|---|---|---|---|
| 0.20 | 279 | (279, 49) | 224 |
| 0.60 | 279 | (279, 49) | 224 |

Identical. Corroborating evidence in the released results:
`results/tables/femto_training_sweep_long.csv` records `n_train_windows`
(= `len(pipe["ts_train"])`) as constant across all five T for every bearing —
279, 163, 90, 86, 79, 51 — when it should grow with T.

**What the experiment actually varied.** `train_end` (line 79) is computed
independently as `df.index[int(n * T)]` and passed to `onset_for_run`, so the
*onset anchor* moves with T while the training data does not. The small
variation visible in Figure 10 is an onset effect, not a training-data effect.

**Blast radius.** Every claim of the form "at any training fraction" or "no
crossover in [0.20, 0.60]":

- Sec. 6 minimum-training-data subsection (the whole subsection)
- Figure 10 (`fig_mintrain`) and its caption, including the "no crossover"
  annotation
- the RG-4 discussion adjacent to `tab:phrank`
- the existing Conclusion sentence about the crossover training fraction
- pending BLOCK 2 (abstract), BLOCK 3 (practical recommendation) and BLOCK 4
  (conclusion edit)

**Not affected:** N-20 is unrelated and provably did not touch this sweep —
`load_pipeline` is called with `downsample_factor=1, downsample_mode="none"`
(the defaults), and the N-20 fix sits inside
`if downsample_mode != "none" and downsample_factor > 1:`, a branch that cannot
execute here. Item (a) verified clean.

**Supporting figures for the RG-4 prose, measured:** trainable-parameter counts
at the 49-dim width are LSTM-AE 54,657, TCN-AE 29,681, Transformer-AD 20,305 —
i.e. **2.0 to 5.5 x 10^4**, not "2-5 x 10^4" as drafted. Deep SVDD is 1,824.
FEMTO normal-training windows at the *default* 0.50 split: 51, 79, 86, 90, 163,
279 (median 88) — "on the order of 10^2" holds, but a T = 0.20 count cannot be
quoted until the sweep is fixed.

**Fix options (author decision):**

1. Make `load_pipeline` honour `SPLIT["train_fraction"]` when the caller has set
   it, then re-run the sweep. Changes Figure 10 and the subsection's numbers.
2. Add an explicit `train_fraction=` argument to `load_pipeline` and have
   `training_sweep.py` pass T. Cleaner, same re-run cost.
3. Withdraw the training-fraction claim and rescope the subsection to what was
   actually measured (onset-anchor sensitivity at a fixed 0.50 training split).

Option 2 is the smallest correct change; option 3 is the only one that needs no
re-run.

---

## N-22 re-run outcome (2026-09-19) - fix verified, no-crossover conclusion SURVIVES

Fix committed `df7d54e` (option 2, rule-4 sign-off): `load_pipeline` gained
`train_fraction: float = None`, falling back to `bundle.train_fraction`;
`src/training_sweep.py` passes T. Two sites only; no detector, onset, metric,
seed or hyperparameter code touched.

### Mandatory regression check - PASSED

Fingerprint over X_train/X_cal/X_test + ts_train/ts_cal/ts_test, omitting
`train_fraction` vs passing the bundle value explicitly:

| case | omitted | explicit | |
|---|---|---|---|
| FEMTO Bearing1_1 | 83e0c4dbbd47dcbf | 83e0c4dbbd47dcbf | identical |
| FEMTO Bearing3_1 | 2edd577e6aa32da2 | 2edd577e6aa32da2 | identical |
| IMS 2nd_test | d669981828ece4c7 | d669981828ece4c7 | identical |

**Independent confirmation from the re-run itself:** every delta in the T = 0.50
column is exactly zero. 0.50 is the bundle default, so the published run (pinned
there for all T) must agree with the corrected run at T = 0.50 and at no other T.
It does. That is the fix behaving exactly as predicted.

### 1. n_train_windows now varies with T

| bearing | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | published (all T) |
|---|---|---|---|---|---|---|
| Bearing1_1 | 111 | 167 | 223 | 279 | 335 | 279 |
| Bearing1_2 | 34 | 51 | 69 | 86 | 103 | 86 |
| Bearing2_1 | 36 | 54 | 72 | 90 | 108 | 90 |
| Bearing2_2 | 31 | 47 | 63 | 79 | 94 | 79 |
| Bearing3_1 | 20 | 30 | 40 | 51 | 61 | 51 |
| Bearing3_2 | 65 | 97 | 130 | 163 | 195 | 163 |

### 2. Valid-alarm fraction - 25 of 50 cells moved

| detector | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 |
|---|---|---|---|---|---|
| three_sigma | 1.000 | 0.833 | 0.667 | 0.667 | 0.667 |
| ewma | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 |
| cusum | 0.500 | 0.500 | 0.500 | 0.667 | 0.500 |
| hotelling_t2 | 0.667 | 0.333 | 0.500 | 0.500 | 0.500 |
| isolation_forest | 0.667 | 0.167 | 0.500 | 0.667 | 0.667 |
| rms_trend | 0.000 | 0.333 | 0.500 | 0.500 | 0.500 |
| deep_svdd | 0.000 | 0.000 | 0.000 | 0.000 | 0.167 |
| lstm_ae | 0.200 | 0.000 | 0.000 | 0.333 | 0.167 |
| tcn | 0.200 | 0.000 | 0.000 | 0.167 | 0.167 |
| transformer_ad | 0.200 | 0.167 | 0.167 | 0.333 | 0.000 |

### 3. Crossover test - NO CROSSOVER

SPC baseline (mean of the four charts) by T: 0.708, 0.583, 0.583, 0.625, 0.583.
Best deep reconstruction value anywhere in the range is 0.333 (LSTM-AE and
Transformer-AD at T = 0.50), against a baseline of 0.625 there. No deep
reconstruction model reaches or exceeds the SPC baseline at any T.

Checked specifically at the highest T on the three longest bearings, as asked:
LSTM-AE, TCN-AE and Transformer-AD are invalid on all three, while 3-sigma and
EWMA are valid on two of three. **RG-4's scoping does not invert.** Deep SVDD
does move off zero for the first time: 0.167 at T = 0.60.

### 4. NEW DEFECT EXPOSED - N-23: silent drop, not N/A

At T = 0.20 Bearing3_1 has 20 windows, below the length-30 sequence requirement.
The three deep sequence models raise "LSTM-AE needs >= 30 windows; run has 20",
and the run is **dropped** rather than recorded as N/A: `n_bearings` is 5 for
those three detectors at T = 0.20 and 6 everywhere else, while `na_count` stays
0 in every cell. Their T = 0.20 fractions are therefore x/5 while every other
cell is x/6 - 0.200 is 1/5, not a 6-bearing value.

This contradicts Sec. 4.5, which states that such a cell is recorded "as an
explicit N/A rather than dropping it silently". The published run never hit this
path because the training split was always the 0.50 default. Needs its own
sign-off; not fixed here.

### Manuscript sites that move (prose NOT edited, per instruction)

| line | what breaks |
|---|---|
| L730 | "At no training fraction did any bearing fail to form a length-30 sequence, so every cell is a genuine evaluation rather than an N/A" - false; Bearing3_1 fails at T = 0.20 |
| L732 | "0.67--0.83 ... with as little as T=0.20 and are stable or only mildly lower thereafter" - 3-sigma now runs 1.00 to 0.667, a clear decline; Isolation Forest dips to 0.167 at T = 0.30 |
| L732 | "LSTM-AE and Transformer-AD 0.33--0.50, TCN-AE 0.17--0.33" - now 0.000--0.333 and 0.000--0.200 |
| L732 | "Deep SVDD produces no valid alarm on any FEMTO bearing at any T" - false; 0.167 at T = 0.60 |
| L734 | "do not overtake them anywhere in the 0.20--0.60 training range" - still TRUE, and now actually tested |
| L739 | caption "SPC charts (blue) sit at the top and are flat from T=0.20" - false; 3-sigma declines monotonically |
| L739 | caption "never reach it---no crossover" - still TRUE |
| Fig. 10 | all curves; in-plot annotation "SPC baseline ~ 0.67" becomes "~ 0.62" |
| Fig. 10 | y-axis "(n = 6 bearings)" is wrong for the three deep models at T = 0.20 (n = 5), pending N-23 |
| L96 | "competitive with SPC charts within the tested training-fraction range [0.20, 0.60]" - survives |
| L235 | "Deep SVDD produced no valid alarm on any FEMTO bearing at any training fraction" - false, same as L732 |
| L777 | conclusion "minimum training-data requirement" sentence - survives, wording per BLOCK 4 |

Figure 10 has been regenerated into `paper/figs/` (gitignored) for inspection but
**not** installed into `paper/files/`, since manuscript edits are on hold.

---

## 5Q. Sessions 7-9 — 2026-09-20 — N-23, colour collisions, §6.13, prose blocks, ONGC release, PUBLISH

**Published:** `main` fast-forwarded to `1e638df` and pushed; tag **`v1.1.0`** pushed.
Verified from a clean clone of the public repo (not the working tree): 143 result CSVs
present, all 11 ONGC paths cited in Data Availability resolve, and
`tests/test_ongc_release.py` passes 5/5 against the clone with `src` resolved from the
clone. No `data/raw`, zero ONGC parquets in the public tree.

### New defects found this batch

| ID | Defect | Severity | Status |
|----|--------|----------|--------|
| **N-24** | `lead_time.evaluate_all_methods` still silently DROPS a `ShortRunError` cell for callers other than `training_sweep` (`record_short_run_na` defaults False). `benchmark.run_benchmark` reconciles its own N/A rows, so the main tables are unaffected, but `tradeoff`/`robustness`/`ablation`/`feature_coarsening_ablation` would gain honest N/A rows on coarsened runs if the default flipped. Deliberately left off to keep published artifacts byte-identical. | Medium | ⬜ |
| **N-25** | Eleven detector colours cannot be made dichromat-safe by hue alone. Under simulated tritanopia EWMA and Conformal-IF converge to dE 0; under protanopia Isolation Forest and TCN-AE reach dE 10.8. Distinguishing all eleven for colour-vision-deficient readers needs a redundant channel (line style or marker), which the plot helpers do not vary. | Medium | ⬜ |
| **N-26** | `paper/make_figures.py` kept a SECOND colour table, five entries keyed by display name, diverging from `config.PLOT`. It painted RMS-Trend `#9C27B0` (LSTM-AE's colour) and left five detectors to matplotlib's default cycle. In the SUBMITTED Figure 3, EWMA and LSTM-AE were the same green and Hotelling T2 and Deep SVDD the same orange. | High | ✅ FIXED |
| **N-27** | Long `\texttt{}` filenames in Data Availability overflowed the column and rendered clipped (`ongc_health_indicator.c`). Found by rendering page 20 to an image. | High | ✅ FIXED |
| **N-28** | `DatetimeIndex.view("int64")` exposes the backing unit (microseconds), not nanoseconds; a hard-coded `/1e9` reported `interval_s = 0.01` for the 10 s ONGC stream. | Medium | ✅ FIXED |

### N-23 resolved
`evaluate_all_methods` caught `ShortRunError` in a bare `except Exception` that logged and
dropped the cell, so `training_sweep`'s `na_count` could only ever be 0 and `n_bearings`
fell to 5. Fixed with `_short_run_na_result()` + opt-in `record_short_run_na`. Sweep
re-emitted: `na_count` = 3 (Bearing3_1 at T=0.20, 20 windows vs seq_len 30), `n_bearings`
= 6 everywhere, every other cell byte-identical. TCN-AE's range corrects 0.000-0.200 ->
0.000-0.167 as the denominator goes 5 -> 6.

### RG-7 / D-5 — ONGC derived artifacts released
`src/export_ongc_derived.py` -> `results/tables/ongc_health_indicator.csv` (42,698 rows)
and `ongc_onset_markers.csv`. The exporter refuses to write if the recomputed onset is not
the published `2023-11-13 03:44:01`, and refuses any frame carrying a channel-level column.
Withheld: raw waveforms, per-channel `rms_ch*`, asset identifiers. The indicator is one
baseline-standardized scalar per timestamp aggregated over four channels, so per-channel
values cannot be recovered and no absolute amplitude is disclosed.

### N-4 resolved
`.zenodo.json` and `CITATION.cff` both retitled to the submission title and corrected to
five datasets with Ferrara included; version 1.1.0, released 2026-09-20.

---

## SHORTENING PLAN — PHASE 0 (measurement only) — 2026-09-23, IN PROGRESS

Governing doc: `IJPHM-SHORTENING-PLAN.md` (overrides the "Page target CLOSED at 24 pages"
note above; manuscript is now **30 pages**). No manuscript, code or result-file edits.

- ✅ Fresh build of `paper/files/scada_ijphm.tex` (HEAD `06b6d8b`, tex last touched `7ee007c`,
  1047 lines, sha256 `8d96954d…57b3`): **30 pages**, tectonic exit 0.
- ⚠️ PyMuPDF blocked again by Application Control (`_extra` DLL). Substitutes: pypdf 6.13.2
  for text; xpdf `pdftotext` 4.00 (no bbox). **No page renderer is available** — Rule 10
  image checks for later phases need PyMuPDF back, or another renderer.
- ✅ Measurement method: an instrumented COPY (`revision-artifacts/phase0/instrument.py`)
  records `\pdfsavepos` at every heading (in the first paragraph, horizontal mode), and at the
  top and bottom of every float box (`\@floatboxreset` / `\AtEndEnvironment`) and caption.
  Validated: all 30 pages' extracted text is identical to the real build.
  Two failed attempts, kept for the record: (1) a marker in vertical mode after a heading
  added a page-break point and moved §6.2 from p.9 to p.8; (2) `\AtBeginEnvironment` markers
  fire outside the float box, measuring the anchor instead of the float.
  Raw positions: `revision-artifacts/phase0/positions.mpos`.
- ✅ Text source: xpdf `pdftotext` on MediaBox-cropped copies of each region (section piece,
  float body, caption). pypdf mis-orders math-mode runs (`+0.030` → `+0` `.030`), so it is used
  only for page count. Scripts (all in `revision-artifacts/phase0/`, rerunnable in Phase 6):
  `measure.py` → `page_map.csv`, `floats.csv`, `sections_text.json`; `inventory.py` +
  `claims_catalog.py` (133 claims, paraphrase regex lists) → `revision-artifacts/inventory_before.csv`,
  `redundancy_report.md`, `table_cell_crosscheck.txt`; `labels_and_merges.py` → `label_map.csv`;
  `rollup.py` → `section_rollup.csv`.
- ✅ **Inventory** `inventory_before.csv`: 625 sentences, 688 claim-locations (133 IDs, all located),
  789 prose/caption numbers, 875 table cells, 58 citations. 435/625 sentences map to a catalogued
  claim; the rest stay as sentence units. Every numeric table cell of 22 tables is present in the
  rendered float text (tab:basestats differs only in formula exponents).
- ✅ **Totals:** prose 16,301 words (excl. references), 543 sentences, mean 30.0 / p90 51 words
  (own splitter; the audit's "38" used an unrecorded method). Captions 2,187 words over 30 floats.
  Floats = 6.77 page-equivalents (tables 4.46, figures 2.23, algorithm 0.08).
- ✅ **Merge pre-checks (printed values):** M1 — all 44 `tab:holm` raw p equal the printed p of
  `tab:crossds` (33) + `tab:imssweep` (11); verify_tables sources them from two different post-N-20
  files (`n20_raw_contrast_old_vs_new.csv` arm new vs `*_runlevel_test_n20.csv`). M2 — PH =
  max `tab:tradeoff` lead and L = `tab:farbudget` τ=0.10 for all 7 rows. verify_tables: 558 OK.
- ⚠️ **Findings for the author (not fixed — Phase 0 is read-only):**
  1. Protected G3 "0.000 h across 99 cells" and Corrections "Hotelling T² collapses in 2 of 5
     draws at 20%" are **not in the current PDF** (only "contains no onset term" and "bimodal
     across draws, 0 to 128.1 h").
  2. `tab:gatedcontrast` is per-dataset (median across detectors), not per detector: M1's
     "gated median Δ with its p" column would be new generated numbers.
  3. `tab:farbudget`/`tab:phrank` carry 7 detectors, `tab:imslead` 11: an 11-row M2 table needs
     deep-model τ/PH cells (derivable from `tab:tradeoff`) and OC-SVM is in no threshold sweep.
  4. `tab:ongc` has 5 of 11 detectors; §7.2 says Deep SVDD never alarms before failure on ONGC
     while D.2 says "every detector achieves a long warning" — a live inconsistency.
  5. XJTU rows of `tab:crossds` (Δ, n₊/n₋, S-c.) are checked by no verify_tables guard.
  6. `tab:imssweep` (left column, +21.5 pt overfull) reaches x≈318 bp, past the right column's
     315 bp: possible overprint on p.14 — needs a render to confirm.
  7. Appendix float pages are near-empty: p.25 ≈15% full (tab:compute only), p.26 ≈42%
     (tab:deeparch only), p.28 ≈36%, p.30 ≈49% — roughly 2 pages of stranded space (Phase 5).
  8. Numbers visible only in raster figures today: fig:sweep curves, fig:conformal (b) XJTU and
     most of (c) FEMTO, fig:tradeoffs (b) XJTU, 6 ONGC detector medians in fig:crossdataset.
- **Phase 0 COMPLETE. Stopped for author approval before Phase 1.** Not committed (awaiting
  instruction; branch is `main`).

## SHORTENING — PHASES 1-7 (branch `ijphm-shorten`, 2026-09-23)

Author GO after Phase 0; decisions recorded in `IJPHM-SHORTENING-PLAN.md` §12.
Phase 0 committed as `7755be3` (30 pages).

**Renderer.** xpdf `pdftoppm` is NOT installed (filesystem search of C: and D:; no
Ghostscript/ImageMagick/mutool either). Substitute, stated openly: Mozilla pdf.js in
headless Chrome driven over the DevTools protocol (`revision-artifacts/tools/render_pages.py`)
-- a full rasteriser. Build + checks: `revision-artifacts/tools/build.py`.

**Stale memory corrected.** The "3 residual overfull tabulars" note is stale: the Phase 0
build log and every build since show 0 overfull boxes. Phase 0 finding 6 (possible p.14
overprint) rested on it; the rendered page shows no collision.

### Phase 1 — table consolidation ✅ 29 pages
Generator `paper/make_shortened_tables.py` -> `paper/files/gen/*.tex` (\input). Merges:
M1 crossds+equiv+holm -> `tab:crossds`; imssweep+ongc(11 detectors) -> `tab:imsongc`;
gated contrast compacted side by side; M2 imslead+farbudget+phrank -> `tab:imsdet`
(eleven rows, PH order; 3σ PH's 8th; top seven L=0); OC-SVM row added to `tab:tradeoff`;
M3 noise+denoise -> `tab:mechanism`; M4 hyperparams+compute; M5 tab:conformal values into
the fig:conformal caption. Height (page-equivalents): M1 1.175->0.575, M2 0.533->0.244,
gated 0.175->0.128, M4 0.358->0.313, M3 0.242->0.208, M5 -0.065. No merge reverted.
Merge guard `revision-artifacts/phase1/compare_old_new.py`: every old table value survives
except documented items (old 7-detector PH ranks superseded by the mandated 11-detector
ranking; N-29 corrections).
**New defect N-29 (double rounding):** OC-SVM IMS raw lead printed 180.3, source 180.2496 h
-> 180.2; denoiser aggregate and Kalman mean lead printed 75.7, source 75.6469 h -> 75.6
(table and D.1 prose). Response to Review impact: check for these values.
**G3 added** (verified: `rg3_raw_invariance.csv`, 99 cells, max |dev| 0.000 h).
**D18 added** (verified): Hotelling T2 collapses in 2 of 5 draws at 20%, mean 134.9 h,
range 58.0-186.1 h, single run (test 3, 315.9 -> 59.7 h). The requested clause "no chart's
lead changes in any draw at 5%" is FALSE (3σ/CUSUM/IF move in some draws); written instead:
Hotelling and EWMA unchanged in every draw, no chart's per-draw mean moves > 0.83 h.
**ONGC fixed** (verified, factor 1 post-fix): the requested "nine of eleven ~34-35 h" is
not what the data say -- seven detectors 34.9-35.3 h, CUSUM 33.9 h, Hotelling T2 30.4 h,
RMS-trend 22.8 h, Deep SVDD none. Written as "nine of eleven 30-35 h" with that breakdown
in D.2; §7.2 corrected likewise. NOTE for author: most of these ONGC alarms are invalid
under the gate (pre-onset FAR 39-95%); only Hotelling T2 (6.5%) and RMS-trend (0.1%)
clear tau=10%. The text reports raw lead; not changed here.
**verify_tables.py**: 895 values (floor 558), all OK; new XJTU-SY guard; checks for
imsdet (with PH/L re-derivation), mechanism, compute, conformal (a), prose G3/D18/ONGC/N-29.
Negative tests (`revision-artifacts/phase1/negative_tests.py`): all 7 guards go red on a
wrong source or tampered value.

### Phase 2 — forest plot ✅ 29 pages (no change)
`paper/make_forest.py` -> `paper/files/fig_forest.pdf` (vector), label `fig:crossdataset` kept.
Panels IMS | XJTU-SY | FEMTO | Ferrara | ONGC; ±1 h band shaded; ONGC hollow. IMS shows the
three per-run differences + median (IMS bootstrap CIs are printed nowhere, so by constraint 4
they are not drawn). Rendered at 300 dpi and in-page at 150 dpi: legible. One-class SVM has no
colour in `config.PLOT["method_colors"]`; drawn black explicitly (flag: N-25 family). Optional
slopegraph not built (PH ranking already one table; would add height).
