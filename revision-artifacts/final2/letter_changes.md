# Part 6 -- Response to Review changes (old -> new)

## 1

**Old:** A script in the 181-test suite re-derives 906 printed values from the released result files

**New:** A script in the 181-test suite re-derives 1039 printed values from the released result files

## 2

**Old:** a 181-test suite that includes a script re-deriving 906 printed values

**New:** a 181-test suite that includes a script re-deriving 1039 printed values

## 3

**Old:** The aggregate-versus-decimate contrast on ONGC uses raw lead and is unaffected.

### Figure defects

**New:** The aggregate-versus-decimate contrast on ONGC uses raw lead and is unaffected.

**9. Validity counts included alarms the gate could not evaluate.** Where the onset estimator places the onset at or before the first scored window, the pre-onset region is empty and the false-alarm rate is undefined. The submitted manuscript's XJTU-SY counts, and its per-bearing table, counted such alarms as valid whenever their lead was positive, and one bearing with no detectable onset was scored by a positional criterion the paper did not state. Equation 5 now states the rule explicitly — such alarms are excluded from the validity denominator — and every count is restated under it. The XJTU-SY figure of 209/450 becomes 48 of 230 scoreable evaluations, 220 being excluded (170 with an empty pre-onset region, 50 on the bearing with no detectable onset); in the per-bearing table five of the ten bearings cannot be scored at full resolution, and the total becomes 6/25 rather than 20/50. The same rule moves the pooled persistence fractions and the XJTU-SY gap columns of Table 4 and the smallest training fraction of the deep-model sweep; the FEMTO count and the gated contrast already applied it. No aggregate-versus-decimate result is affected, since those are computed on raw lead.

### Figure defects

## 4

**Old:** **9. The trade-off figure omitted

**New:** **10. The trade-off figure omitted

## 5

**Old:** **10. Detectors shared colours.**

**New:** **11. Detectors shared colours.**

## 6

**Old:** **11. The ONGC bars in Figure 2

**New:** **12. The ONGC bars in Figure 2

## 7

**Old:** **12. The Data and Code Availability section

**New:** **13. The Data and Code Availability section

## 8

**Old:** surfaced disclosure items 9, 10 and 11,

**New:** surfaced disclosure items 10, 11 and 12,

## 9

**Old:** Acting on this comment uncovered disclosure item 12.

**New:** Acting on this comment uncovered disclosure item 13.

## 10

**Old:** and the one-class SVM's prognostic horizon (Table 2) is 180.2 h, not 180.3 h (source 180.250 h).

**New:** and the one-class SVM's prognostic horizon (Table 2) is 180.2 h, not 180.3 h (source 180.250 h). Section 6.2 stated that the default onset moves by less than two percent of run span on every IMS run as k varies; on the second test it moves 5.4 percentage points (60.4% to 65.8% of span), and the text now gives the spread per run.

## 11

**Old:** Raw-waveform coarsening is named in Section 8 as the complementary study.

**New:** Raw-waveform coarsening is named in Section 8 as the complementary study. The practical-implications paragraph of Section 7.4 is aligned with Section 4.8 in the same way: it compares bin-averaged summary statistics with keeping every f-th stored value, bounded to the ±1 h margin on the datasets tested, and no longer refers to decimated raw samples.

## 12

**Old:** not by removing the sensitivity and ablation work: every sentence, number, table cell and citation of the longer intermediate draft is accounted for in the final version.

**New:** not by removing the sensitivity and ablation work: no result from the submitted version has been removed; the results that changed are the corrections disclosed above.

## 13

**Old:** and the compute table (Table 11);

**New:** and the compute table (Table 12);

## 14

**Old:** The scoping is quantitative: across bearings and training fractions these runs provide between 20 and 335 normal training windows,

**New:** The scoping is quantitative: across FEMTO bearings and training fractions the runs provide between 20 and 335 normal training windows,
