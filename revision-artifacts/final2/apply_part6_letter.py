"""Final submission pass, Part 6: minimal factual edits to the Response to Review.

Every edit is guarded (old text occurs exactly once) and logged with old and new text to
revision-artifacts/final2/letter_changes.md. Restated numbers are read from the Eq. 5 audit.

    python revision-artifacts/final2/apply_part6_letter.py
"""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
LETTER = ROOT / "IJPHM-Response-to-Review-FINAL.md"
LOG = ROOT / "revision-artifacts" / "final2" / "letter_changes.md"
TAB = ROOT / "results" / "tables"

aud = pd.read_csv(TAB / "eq5_validity_audit.csv").set_index("site")
h = aud.loc["S6.3 five window-magnitude detectors, all modes x factors"]
t7 = aud.loc["Table 7 total (full resolution, aggregate)"]
V, SC, E, O, ALL = (int(h.eq5_valid), int(h.eq5_scoreable), int(h.excluded_empty_pre),
                    int(h.excluded_no_onset), int(h.published_den))
PUB = int(h.published_valid)
T7V, T7S, T7P, T7D = int(t7.eq5_valid), int(t7.eq5_scoreable), int(t7.published_valid), int(t7.published_den)
assert (PUB, ALL, V, SC, E, O) == (209, 450, 48, 230, 170, 50)
assert (T7P, T7D, T7V, T7S) == (20, 50, 6, 25)

VERIFY_COUNT = 1039        # paper/verify_tables.py, measured in Part 7 before release
TESTS = 181                # pytest --collect-only, measured

NEW_ITEM_9 = (
    "**9. Validity counts included alarms the gate could not evaluate.** Where the onset estimator "
    "places the onset at or before the first scored window, the pre-onset region is empty and the "
    "false-alarm rate is undefined. The submitted manuscript's XJTU-SY counts, and its per-bearing "
    "table, counted such alarms as valid whenever their lead was positive, and one bearing with no "
    "detectable onset was scored by a positional criterion the paper did not state. Equation 5 now "
    "states the rule explicitly — such alarms are excluded from the validity denominator — and every "
    f"count is restated under it. The XJTU-SY figure of {PUB}/{ALL} becomes {V} of {SC} scoreable "
    f"evaluations, {E + O} being excluded ({E} with an empty pre-onset region, {O} on the bearing with "
    f"no detectable onset); in the per-bearing table five of the ten bearings cannot be scored at full "
    f"resolution, and the total becomes {T7V}/{T7S} rather than {T7P}/{T7D}. The same rule moves the "
    "pooled persistence fractions and the XJTU-SY gap columns of Table 4 and the smallest training "
    "fraction of the deep-model sweep; the FEMTO count and the gated contrast already applied it. "
    "No aggregate-versus-decimate result is affected, since those are computed on raw lead."
)

EDITS = [
    # opening and closing: counts (tag unchanged: v1.3.0 was never pushed and is recreated)
    ("A script in the 181-test suite re-derives 906 printed values from the released result files",
     f"A script in the {TESTS}-test suite re-derives {VERIFY_COUNT} printed values from the released "
     "result files"),
    ("a 181-test suite that includes a script re-deriving 906 printed values",
     f"a {TESTS}-test suite that includes a script re-deriving {VERIFY_COUNT} printed values"),
    # new disclosure item 9, after item 8
    ("The aggregate-versus-decimate contrast on ONGC uses raw lead and is unaffected.\n\n### Figure defects",
     "The aggregate-versus-decimate contrast on ONGC uses raw lead and is unaffected.\n\n"
     + NEW_ITEM_9 + "\n\n### Figure defects"),
    # renumber 9-12 -> 10-13
    ("**9. The trade-off figure omitted", "**10. The trade-off figure omitted"),
    ("**10. Detectors shared colours.**", "**11. Detectors shared colours.**"),
    ("**11. The ONGC bars in Figure 2", "**12. The ONGC bars in Figure 2"),
    ("**12. The Data and Code Availability section", "**13. The Data and Code Availability section"),
    # cross-references to the renumbered items
    ("surfaced disclosure items 9, 10 and 11,", "surfaced disclosure items 10, 11 and 12,"),
    ("Acting on this comment uncovered disclosure item 12.", "Acting on this comment uncovered disclosure item 13."),
    # smaller corrections: the onset-stability claim was in the submitted paper
    ("and the one-class SVM's prognostic horizon (Table 2) is 180.2 h, not 180.3 h (source 180.250 h).",
     "and the one-class SVM's prognostic horizon (Table 2) is 180.2 h, not 180.3 h (source 180.250 h). "
     "Section 6.2 stated that the default onset moves by less than two percent of run span on every IMS "
     "run as k varies; on the second test it moves 5.4 percentage points (60.4% to 65.8% of span), and "
     "the text now gives the spread per run."),
    # D9/F4 coarsening-level response: S7.4 aligned with S4.8
    ("Raw-waveform coarsening is named in Section 8 as the complementary study.",
     "Raw-waveform coarsening is named in Section 8 as the complementary study. The practical-implications "
     "paragraph of Section 7.4 is aligned with Section 4.8 in the same way: it compares bin-averaged "
     "summary statistics with keeping every f-th stored value, bounded to the ±1 h margin on the datasets "
     "tested, and no longer refers to decimated raw samples."),
    # Reviewer D length: no intermediate draft was ever sent
    ("not by removing the sensitivity and ablation work: every sentence, number, table cell and citation "
     "of the longer intermediate draft is accounted for in the final version.",
     "not by removing the sensitivity and ablation work: no result from the submitted version has been "
     "removed; the results that changed are the corrections disclosed above."),
    # table renumbering (Part 5 layout: protocol/compute table is now Table 12)
    ("and the compute table (Table 11);", "and the compute table (Table 12);"),
    # Reviewer F: the 20-335 window range is FEMTO's (manuscript S4.5 corrected in Part 4)
    ("The scoping is quantitative: across bearings and training fractions these runs provide between 20 "
     "and 335 normal training windows,",
     "The scoping is quantitative: across FEMTO bearings and training fractions the runs provide between "
     "20 and 335 normal training windows,"),
]


def main():
    s = LETTER.read_text(encoding="utf-8")
    for old, new in EDITS:
        assert s.count(old) == 1, (s.count(old), old[:90])
        s = s.replace(old, new)
    LETTER.write_text(s, encoding="utf-8")
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write("# Part 6 -- Response to Review changes (old -> new)\n")
        for k, (old, new) in enumerate(EDITS, 1):
            fh.write(f"\n## {k}\n\n**Old:** {old}\n\n**New:** {new}\n")
    print(f"applied {len(EDITS)} letter edits")


if __name__ == "__main__":
    main()
