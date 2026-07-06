# CHANGES — IJPHM reframe of `paper/scada_journal.tex`

Branch: `ijphm-reframe` (do not merge to main). Reframe is **structure/emphasis/framing
only** — no experimental number was invented or altered. The reframe was applied by a
single deterministic transform (`paper/reframe_ijphm.py`) that *moves exact substrings*
and never retypes a table cell; the new figure is `paper/make_far_budget_fig.py`.

Compiles cleanly with `tools/tectonic.exe`: **23 pages, zero undefined references, zero
undefined citations** (verified on the final pass of `scada_journal.log`).

---

## 1. Structural changes (by STEP)

| STEP | Change | Result |
|------|--------|--------|
| 1 | Retitle | New title: *"A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing Anomaly Detection --- and What It Reveals About SCADA-Rate Logging"* (+ matching `\markboth`). |
| 2 | Abstract rewritten | Metric-first (gate → latch-on proof → Saxena-PH inversion), then SCADA null as *validation*. Says "nine detectors", "four inferential datasets". Every number retained. |
| 3 | Contributions reordered | New order: (1) gated metric, (2) formal proof gating changes the answer vs Saxena PH, (3) controlled SCADA-sampling methodology, (4) multi-dataset null "statistically honest by construction", (5) validation. Old C5 overclaim softened: "regardless of commissioning data volume" → "within the tested training-fraction range [0.20, 0.60] on short-lived bearings; whether a crossover exists on long-runway assets remains open." |
| 4 | Scope paragraph added | New "Scope of claims" paragraph after Contributions (steady-condition rolling-element bearings; bin-averaged vs decimated; metric is failure-mode-agnostic). |
| 5 | ONGC demoted | Removed from headline dataset count and main Results flow. Its results subsection + `tab:ongc_paired` + `fig:calib_ongc` + the `\textbf{ONGC.}` description moved **verbatim** to **Appendix E** (Supplementary — Single-Asset Case Study). One honest ONGC paragraph added to Discussion (~35 h warning, agg-dec at most ~1 min, n=1, excluded from inferential family). Table I caption + ONGC *Role* label updated ("case study (App.~E)"; Runs count `1` preserved). `fig:cross` kept (ONGC bars already hatched/separated per its caption). |
| 6 | Deep SVDD demoted (Option B) | Headline set reduced to **nine** (4 SPC charts + Isolation Forest + 3 reconstruction AEs + RMS-trend). Deep SVDD moved out of the headline detector list into an "Additionally evaluated (not in the headline nine)" note carrying the requested wording ("no valid alarm on any FEMTO bearing at any training fraction … omitted from the headline set; full numbers in the appendix"). Appendix F added. **Holm `N=40` family kept exactly as computed** (10 detectors x 4 datasets), with a caption footnote clarifying headline-vs-full-evaluated set. Deep SVDD numbers retained in every result table (see section 3 for rationale). |
| 7 | IMS relabel justification → Appendix C | Section III paragraph replaced by one sentence pointing to Appendix C; full justification (with `21.5%`, `2004-04-08`, `2004-04-18 02:42`, `~0.068`, `~0.228`, `100%`) moved **verbatim** to Appendix C. |
| 8 | Mechanism → Appendix D | `noise` + `denoise` tables and prose moved **verbatim** to Appendix D ("Mechanism — Generic Smoothing vs Historian Averaging"). Discussion left with the single sentence: "The IMS trend is reproduced by an ordinary moving-average or Kalman filter on the decimated stream (Appendix D) …". |
| 9 | Results reordered | New order: (A) IMS lead/CI + onset sensitivity → (B) **XJTU-SY n=10 primary** → (C) FEMTO n=6 → (D) Ferrara n=6 → (E) IMS aggregate-vs-decimate → (F) Holm → (G) conformal → (H) trade-off + budget → (I) ablations → (J) spectral → (K) Saxena PH → (L) min-training. Achieved by relocating the "Aggregate vs decimate on IMS" subsection to after Ferrara. Added the primary-dataset sentence at the end of Section III. |
| 10 | tau*(k,rho) grid added | New `tab:taustar_grid` after the cost-ratio paragraph. Entries are tau*=rho/k clipped to [0,1] for k,rho in {1e2,1e3,1e4}. **Pure arithmetic from Eq. (6)** — no experimental number. |
| 11 | FAR-budget figure added | New `fig:farbudget` (`figs/fig_far_budget_detector.png`) from `make_far_budget_fig.py`, plotting **exactly** the best-valid-lead values already in Table XVII (`tab:farsens`) at tau in {0.05,0.10,0.20}; one line per detector. No intermediate tau invented. |
| 12 | Consistency pass | "ten detectors"/"five datasets" reframed to "nine headline detectors"/"four inferential datasets" in abstract, intro, Discussion summary, Threats, Conclusion. `\ref{sec:mechanism}` usages replaced with literal "Appendix D". All cross-refs resolve (log clean). |
| 13 | Compiled | `tectonic -X compile` → 23 pp, no errors, no undefined refs/citations. |

### Appendix layout (final)
A Reproducibility · B 49-dim feature space · **C IMS relabel justification** · **D Mechanism** ·
**E Supplementary — ONGC case study** (desc + results subsection + `tab:ongc_paired` + `fig:calib_ongc`) ·
**F Additional detector — Deep SVDD**.

---

## 2. Numeric-integrity proof

**No `git diff` baseline exists** because `paper/` is gitignored (`.gitignore:42`, "kept
local … not published"); the `.tex` was never committed. The equivalent — and stronger —
proof is the transform's built-in gate, which ran against the *actual* pre-reframe bytes:

- **Table cells: `273 / 273` distinct data rows byte-identical.** The transform extracts
  every line matching `^.*&.*\\` (a table data row) from the original and asserts each is
  present in the output with >= its original count; it **refuses to write** otherwise.
  Result: `OK: every original data row present with >= original count.` No table value
  was moved-and-mangled — moves are exact-substring relocations.
- **Only added data rows:** the tau*(k,rho) grid (3 data rows + its rho-label header) — all
  pure `rho/k` arithmetic, plus the ONGC Table-I *Role* relabel (its `1`/`10 s` preserved).
- **Prose headline numbers consistent with their unchanged tables** (grep counts, prose +
  table): `+18.4`x8, `+12.2`x8, `+5.8`x8, `+5.4`x6, `+4.6`x6, `14.8`x11, `N{=}40`x10,
  `p{=}0.25`x7, `<=1 min`x2, `~35 h`x9. Every result figure in the rewritten
  abstract/contributions/summary/conclusion is a value that already appears in a
  (byte-identical) table.

### Numbers introduced by the reframe (all justified, none experimental)
| Value(s) | Where | Justification |
|----------|-------|---------------|
| `1.00, 0.10, 0.01` (tau* grid) | `tab:taustar_grid` | tau*=rho/k clipped to [0,1]; k,rho in {1e2,1e3,1e4}. Direct from Eq. (6). |
| line coords in `fig:farbudget` | new figure | Copied verbatim from Table XVII (`tab:farsens`): 3sig 0/56.3/77.0; EWMA 0/0/0; CUSUM 0/0/65.0; Hot.T2 0/0/73.9; IF 0/0/53.4; Deep SVDD 14.8/14.8/14.8; RMS-trend 34.7/34.7/34.7. |

**No experimental number was invented or altered.**

---

## 3. Deep SVDD scope (Option B — chosen with the user)

Deep SVDD was demoted from the **headline count** (now nine) and given the requested
appendix note + FEMTO caveat, but its **released numbers are retained in every result
table** rather than physically deleted, because in the trade-off / FAR-budget /
PH-ranking tables it is the paper's near-zero-false-alarm deployable operating point
(14.8 h at <=0.6 % FAR; at tau=0.05 the only within-budget detector besides the naive RMS
baseline). Deleting those rows would force the strict-budget recommendation onto the
naive baseline — weakening a genuine result and brushing the "do not weaken / preserve
honesty" ABSOLUTE RULES — and would add avoidable numeric-handling risk. The Holm `N=40`
family is untouched. See NOTES.md for the full rationale and the one place this deviates
from a literal reading of STEP 6.

---

## 4. Files
- `paper/scada_journal.tex` — reframed source (compiles to `scada_journal.pdf`, 23 pp).
- `paper/scada_journal.pdf` — submission-ready PDF.
- `paper/figs/fig_far_budget_detector.png` — new STEP-11 figure.
- `paper/reframe_ijphm.py` — the deterministic transform (self-verifying).
- `paper/make_far_budget_fig.py` — the STEP-11 figure generator (values from Table XVII).
- `paper/verify_numbers.py` — numeric-token diff helper (needs a tracked baseline; see NOTES).
- `INVENTORY.md` — pre-reframe structure snapshot.
- `NOTES.md` — flagged ambiguities and decisions.
