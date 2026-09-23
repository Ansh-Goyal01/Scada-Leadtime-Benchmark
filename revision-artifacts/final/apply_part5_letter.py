"""Final pass, Part 5 -- audit corrections to IJPHM-Response-to-Review-FINAL.md.

Every replacement is an exact-match edit (asserted unique) so nothing else in the letter moves.
Each was checked against the final PDF (revision-artifacts/phase6/measure/sections_text.json)
and the result files; the evidence is recorded next to each change in letter_changes.md.
Writes: IJPHM-Response-to-Review-FINAL.md (in place), revision-artifacts/final/letter_changes.md
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
LETTER = ROOT / "IJPHM-Response-to-Review-FINAL.md"
LOG = ROOT / "revision-artifacts" / "final" / "letter_changes.md"

text = LETTER.read_text(encoding="utf-8")
box_start = text.index("> **FOR THE AUTHOR")
box_end = text.index("---\n\n## Opening")
AUTHOR_BOX = text[box_start:box_end]

ITEM4_OLD = ("Re-running with five independent draws shows the claim holds at 5% missing rows, where no chart's lead "
             "changes in any draw. At 20% it holds for the univariate charts but fails for Hotelling T², which collapses "
             "in 2 of 5 draws — a single run's alarm survives or does not depending on which rows are removed. Table 4(b) "
             "now reports across-draw means with ranges, and the text states the Hotelling T² vulnerability.")
ITEM4_NEW = ("Re-running with five independent draws shows the claim holds at 5% missing rows: on IMS, Hotelling T² and "
             "EWMA are unchanged in every draw, and no chart's per-draw mean lead moves by more than 0.83 h on either "
             "dataset. At 20% it holds for the univariate charts and Isolation Forest, whose across-draw mean lead changes "
             "by at most 0.92 h on IMS and XJTU-SY, but fails for Hotelling T² on IMS, which collapses in 2 of 5 draws "
             "(across-draw mean 134.9 h, range 58.0–186.1 h, against 186.1 h without gaps) — a single run's alarm "
             "survives or does not depending on which rows are removed. Table 4(b) now reports across-draw means, and the "
             "text gives the ranges and states the Hotelling T² vulnerability.")

NEW_ITEM8 = ("**8. The ONGC case study reported raw lead as if it were detection quality.** Nine of the eleven detectors "
             "alarm 30–35 h before the labeled shutdown, but under the paper's own gated metric at τ = 10% only "
             "Hotelling T² (pre-onset false-alarm rate 6.5%) and the RMS-trend baseline (0.1%) have valid alarms; the "
             "other eight alarming detectors exceed the budget, at 11.7% (Isolation Forest) to 95.2% (CUSUM). The "
             "data-derived onset lies only about 6 h before the shutdown, so their first alarms precede it by 28–29 h "
             "and count as pre-onset false alarms. That verdict is itself ambiguous: the onset estimator is "
             "systematically late under gradual degradation (the bias analysis Reviewer G requested, Section 4.3), so "
             "some of those alarms may be genuine early detection, and with a single asset and no ground-truth "
             "defect-initiation time the case study cannot distinguish the two. Appendix D.2 and Section 7.2 now state "
             "both readings. The aggregate-versus-decimate contrast on ONGC uses raw lead and is unaffected.\n\n")

EDITS = [
    ("Author box deleted (its three items resolved: Appendix C count -> change 14; Table 4(b) figures -> change 4; "
     "release tag -> v1.3.0 here and in submission/SUBMISSION_CHECKLIST.md)",
     AUTHOR_BOX, ""),
    ("Release tag, verifier count and test count (verify_tables.py: 906 values; pytest --collect-only: 181)",
     "All analyses are reproducible from the public repository at tag v1.2.3. A script in the test suite re-derives "
     "558 printed table values from the released result files and fails on any mismatch.",
     "All analyses are reproducible from the public repository at tag v1.3.0. A script in the 181-test suite "
     "re-derives 906 printed values from the released result files and fails on any mismatch."),
    ("Disclosure 1: 78 is the smallest IMS run (test windows 172 / 78 / 506 per run)",
     "The IMS results were produced on the 445-dimensional path, on 78 test windows.",
     "The IMS results were produced on the 445-dimensional path, on runs with as few as 78 test windows."),
    ("Disclosure 4: 5% claim replaced by the verified statement; 20% verified per chart from "
     "d18_gap_injection_multiseed.csv (3sigma +0.83/-0.04, EWMA -0.08/-0.12, CUSUM -0.67/-0.02, IF -0.92/-0.07 h; "
     "Hotelling IMS -51.2 h); Table 4(b) prints means only, the ranges are in the text",
     ITEM4_OLD, ITEM4_NEW),
    ("Disclosure 8 (new): ONGC gating finding (Part 1); items 8-11 renumbered 9-12",
     "### Figure defects\n\n**8. The trade-off figure",
     NEW_ITEM8 + "### Figure defects\n\n**9. The trade-off figure"),
    ("renumber", "**9. Detectors shared colours.**", "**10. Detectors shared colours.**"),
    ("renumber", "**10. The ONGC bars in Figure 2", "**11. The ONGC bars in Figure 2"),
    ("renumber", "**11. The Data and Code Availability section", "**12. The Data and Code Availability section"),
    ("cross-reference to the renumbered figure items",
     "surfaced disclosure items 8, 9 and 10,", "surfaced disclosure items 9, 10 and 11,"),
    ("cross-reference to the renumbered reproducibility item",
     "Acting on this comment uncovered disclosure item 11.", "Acting on this comment uncovered disclosure item 12."),
    ("Smaller corrections: ONGC breakdown verified from n20_rerun_long_ONGC.csv (factor 1); N-29 double rounding added",
     "The ONGC case study stated that every detector alarmed roughly 35 h ahead, when nine of eleven do, with RMS-trend "
     "at about 23 h and Deep SVDD not alarming before failure.",
     "The ONGC case study stated that every detector alarmed roughly 35 h ahead; nine of eleven alarm 30–35 h ahead "
     "(seven within 34.9–35.3 h, CUSUM at 33.9 h and Hotelling T² at 30.4 h), RMS-trend at 22.8 h, and Deep SVDD does "
     "not alarm before failure (disclosure item 8 gives the gated reading). Two values were double-rounded: the "
     "historian-averaging arm of the denoiser comparison (Table 15b) is 75.6 h, not 75.7 h (source 75.647 h), and the "
     "one-class SVM's prognostic horizon (Table 2) is 180.2 h, not 180.3 h (source 180.250 h)."),
    ("One-class SVM coverage: Tables 10 and 14 carry Deep SVDD but not the one-class SVM",
     "One-class SVM now appears alongside Deep SVDD in every table covering the additionally-evaluated detectors.",
     "One-class SVM now appears alongside Deep SVDD in the results tables (Tables 2, 5, 6 and 9) and the compute "
     "table (Table 11); the feature-group ablation (Table 10) and the relabel contrast (Table 14) report Deep SVDD "
     "without it."),
    ("Equivalence method: no TOST p-values or 'untestable' marks exist in the paper; Table 5 uses CI inclusion + "
     "sign-test p",
     "TOST results are reported where the non-zero-difference count supports them; the remaining cells are marked "
     "untestable rather than given a p-value that could not have reached significance.",
     "Equivalence is judged by whether each run-level 95% bootstrap interval lies inside ±δ, and the exact sign-test "
     "p-value is reported beside each cell (Table 5)."),
    ("Appendix C count resolved from Table 14 / Appendix C text: six of the ten detectors",
     "for most detectors the third test becomes a guaranteed miss and the effective n falls, while others retain n = 3.",
     "for six of the ten detectors in that table the third test becomes a guaranteed miss and the effective n falls, "
     "while the other four retain n = 3."),
    ("Reviewer D length passage: counts from the submitted PDF (paper/Scada__IJPHM.pdf: 24 pages, 29 tables, "
     "11 figures) and the final build (22 pages, 15 tables, 6 figures)",
     "Tables are consolidated from 30 to 23 and figures from 11 to 6, with no result removed.\n\n"
     "I should be direct about the net effect: the paper is 30 pages against 24 as submitted. The reduction in "
     "repetition is real and every cut the reviewer named was made, but the revision also adds an equivalence "
     "analysis, a gated-metric contrast table, an architecture table, a signal-theoretic section, an onset-estimator "
     "analysis, Appendix C, a per-dataset coarsening statement, scoping paragraphs and three related-work paragraphs "
     "— all requested by the reviewers. I judged that removing the sensitivity and ablation work to reclaim pages "
     "would be the wrong trade.",
     "Tables are consolidated from 29 to 15 and figures from 11 to 6, with no result removed.\n\n"
     "The net effect: the revised paper is 22 pages against 24 as submitted, with 15 tables against 29 and 6 figures "
     "against 11. It is shorter although the revision adds an equivalence analysis, a gated-metric contrast table, an "
     "architecture table, a signal-theoretic section, an onset-estimator analysis, Appendix C, a per-dataset "
     "coarsening statement, scoping paragraphs and three related-work paragraphs — all requested by the reviewers. "
     "The pages were recovered by merging tables that reported overlapping results, redrawing figures at print size "
     "and removing repetition, not by removing the sensitivity and ablation work: every sentence, number, table cell "
     "and citation of the longer intermediate draft is accounted for in the final version."),
    ("Gated-vs-raw power cost: 195 was the pre-N-20 count; post-fix raw non-zero differences = 171 "
     "(rf2_gated_contrast_n20.csv / n20_raw_contrast_old_vs_new.csv 'new' arm, four inferential datasets)",
     "falls from 195 to 98", "falls from 171 to 98"),
    ("Reviewer F tables: counts updated; merged Table 5 described",
     "the three per-dataset sign-test tables are one table with a dataset column; the four conformal calibration "
     "figures are one four-panel figure. Tables fall from 30 to 23 and figures from 11 to 6, with no result removed.",
     "the three per-dataset sign-test tables, the equivalence table and the Holm table are one table grouped by "
     "dataset (Table 5); the four conformal calibration figures are one four-panel figure. Tables fall from 29 to 15 "
     "and figures from 11 to 6, with no result removed."),
    ("Holm table: now merged into Table 5 / Table 6 (renumbering map: T8 holm -> T5 caption)",
     "The Holm correction table, the densest, is restructured from a 45-row list into an 11 × 4 matrix. Its "
     "adjusted-p and rejection columns were identical in every row, so they are replaced by a single sentence in the "
     "caption.",
     "The Holm correction table, the densest, was a 45-row list. Its raw p-values are now a column of Table 5 (Table 6 "
     "for IMS), eleven detectors by four datasets, and its adjusted-p and rejection columns, identical in every row, "
     "are replaced by a single sentence in the Table 5 caption."),
    ("Reviewer G onset sensitivity: Isolation Forest's gated IMS median stays +3.43 h under pca1 "
     "(rg3_contrast_by_indicator.csv); the gated IMS statement is not in the manuscript",
     "while on IMS every positive gated median falls to zero under both alternatives. We therefore state that "
     "raw-lead non-destruction does not depend on the onset definition, whereas any gated directional pattern on IMS "
     "does and is not claimed.",
     "while on IMS the positive gated medians of CUSUM, EWMA and Hotelling T² fall to zero under both alternatives and "
     "Isolation Forest's under the kurtosis-only indicator (under the first principal component it is unchanged, at "
     "+3.43 h). The manuscript therefore claims only that raw-lead non-destruction does not depend on the onset "
     "definition; it claims no gated directional pattern on IMS, which does depend on it."),
    ("Closing: release tag and verifier count",
     "The analyses are reproducible from the public repository at tag v1.2.3, with a pinned environment and a test "
     "suite that includes a script re-deriving 558 printed table values",
     "The analyses are reproducible from the public repository at tag v1.3.0, with a pinned environment and a "
     "181-test suite that includes a script re-deriving 906 printed values"),
]

log = ["# Response to Review -- audit changes (final pass, Part 5)", "",
       "Letter: IJPHM-Response-to-Review-FINAL.md. Each change is an exact replacement; the reason column is the "
       "evidence. Unlisted text was checked and left unchanged.", ""]
for i, (why, old, new) in enumerate(EDITS, 1):
    n = text.count(old)
    assert n == 1, (i, why, n)
    text = text.replace(old, new)
    log += ["## %d. %s" % (i, why), "", "**Old:**", "", "> " + old.strip().replace("\n", "\n> "), "",
            "**New:**", "", ("> " + new.strip().replace("\n", "\n> ")) if new.strip() else "> *(deleted)*", ""]
assert "FOR THE AUTHOR" not in text and "v1.2.3" not in text and "558" not in text
LETTER.write_text(text, encoding="utf-8", newline="\n")  # the letter is LF-only
LOG.write_text("\n".join(log) + "\n", encoding="utf-8", newline="\n")
print("applied", len(EDITS), "changes")
