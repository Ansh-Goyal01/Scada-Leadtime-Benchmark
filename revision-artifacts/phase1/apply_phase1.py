"""Phase 1 manuscript edits: splice generated tables in, remove merged-away floats,
repoint references, add the two protected sentences (G3, D18), correct N-29 and the
ONGC case-study sentences. Every replacement is asserted to match exactly once.

Run: python revision-artifacts/phase1/apply_phase1.py
"""
import pathlib

TEX = pathlib.Path(__file__).resolve().parents[2] / "paper/files/scada_ijphm.tex"
s = TEX.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:90])
    s = s.replace(old, new)


def replace_float(label, new):
    global s
    i = s.index("\\label{" + label + "}")
    a = s.rindex("\\begin{table", 0, i)
    env = "table*" if s.startswith("\\begin{table*}", a) else "table"
    b = s.index("\\end{" + env + "}", i) + len("\\end{" + env + "}")
    s = s[:a] + new + s[b:]


# ---------------------------------------------------------------- floats
sub("\\begin{document}\n", "\\input{gen/conformal_values}\n\\begin{document}\n")
replace_float("tab:imslead", "\\input{gen/tab_imsdet}")
replace_float("tab:crossds", "\\input{gen/tab_crossds}")
replace_float("tab:equiv", "% tab:equiv merged into tab:crossds (Phase 1, M1)")
replace_float("tab:imssweep", "\\input{gen/tab_imsongc}")
replace_float("tab:holm", "% tab:holm merged into the tab:crossds caption (Phase 1, M1)")
replace_float("tab:gatedcontrast", "\\input{gen/tab_gatedcontrast}")
replace_float("tab:conformal", "% tab:conformal values moved into the fig:conformal caption (Phase 1, M5)")
replace_float("tab:farbudget", "% tab:farbudget merged into tab:imsdet (Phase 1, M2)")
replace_float("tab:tradeoff", "\\input{gen/tab_tradeoff}")
replace_float("tab:phrank", "% tab:phrank merged into tab:imsdet (Phase 1, M2)")
replace_float("tab:compute", "% tab:compute merged into tab:hyperparams (Phase 1, M4)")
replace_float("tab:hyperparams", "\\input{gen/tab_hyperparams}")
replace_float("tab:denoise", "% tab:denoise merged into tab:mechanism (Phase 1, M3)")
replace_float("tab:noise", "\\input{gen/tab_mechanism}")
replace_float("tab:ongc", "% tab:ongc merged into tab:imsongc (Phase 1, M1)")
sub("(d) ONGC turbine ($n=1$ case study, Appendix~D.2): the real historian stream tracks the diagonal closely, a modest 1.5--2$\\times$ above target, consistent with a mostly-stationary normal region.}",
    "(d) ONGC turbine ($n=1$ case study, Appendix~D.2): the real historian stream tracks the diagonal closely, a modest 1.5--2$\\times$ above target, consistent with a mostly-stationary normal region. \\ConformalPanelA}")

# ---------------------------------------------------------------- references
sub("in the result tables throughout (Tables~\\ref{tab:imslead}, \\ref{tab:crossds}, \\ref{tab:holm}, \\ref{tab:farbudget}, \\ref{tab:tradeoff}, and~\\ref{tab:phrank}; Figure~\\ref{fig:mintrain})",
    "in the result tables throughout (Tables~\\ref{tab:imsdet}, \\ref{tab:crossds}, \\ref{tab:imsongc} and~\\ref{tab:tradeoff}; Figure~\\ref{fig:mintrain})")
sub("(Section~\\ref{sec:tradeoff}, Table~\\ref{tab:farbudget})", "(Section~\\ref{sec:tradeoff}, Table~\\ref{tab:imsdet})")
sub("Table~\\ref{tab:imslead} reports the mean raw", "Table~\\ref{tab:imsdet} reports the mean raw")
sub("which does not survive the Holm correction across the family (Table~\\ref{tab:holm})",
    "which does not survive the Holm correction across the family (Table~\\ref{tab:crossds})")
sub("Table~\\ref{tab:equiv} reports the full equivalence family", "Table~\\ref{tab:crossds} also reports the full equivalence family")
sub("Table~\\ref{tab:imssweep} gives the run-level test", "Table~\\ref{tab:imsongc} gives the run-level test")
sub("sign-test $p$-values (Table~\\ref{tab:holm})", "sign-test $p$-values (Tables~\\ref{tab:crossds} and~\\ref{tab:imsongc})")
sub("(marked $\\ddagger$ in Table~\\ref{tab:holm})", "(marked $\\ddagger$ in Table~\\ref{tab:crossds})")
sub("Table~\\ref{tab:conformal} reports the empirical pre-onset false-alarm rate of the conformal Isolation Forest against the target $\\alpha$ on each IMS run, and Figure~\\ref{fig:conformal}a plots it.",
    "Figure~\\ref{fig:conformal}a plots the empirical pre-onset false-alarm rate of the conformal Isolation Forest against the target $\\alpha$ on each IMS run, with the exact values in its caption.")
sub("rather than fixing $\\tau=10\\%$ silently (Table~\\ref{tab:farbudget})", "rather than fixing $\\tau=10\\%$ silently (Table~\\ref{tab:imsdet})")
sub("The strict $\\tau=0.05$ column of Table~\\ref{tab:farbudget}", "The strict $\\tau=0.05$ column of Table~\\ref{tab:imsdet}")
sub("a ranking the raw-lead column of Table~\\ref{tab:imslead}", "a ranking the raw-lead column of Table~\\ref{tab:imsdet}")
sub("(Section~\\ref{sec:saxena}, Table~\\ref{tab:phrank})", "(Section~\\ref{sec:saxena}, Table~\\ref{tab:imsdet})", 2)
sub("flags as uncalibrated (Table~\\ref{tab:conformal})", "flags as uncalibrated (Figure~\\ref{fig:conformal}a)")
sub("($n=3$; Table~\\ref{tab:imssweep})", "($n=3$; Table~\\ref{tab:imsongc})")
sub("descriptive case study with no inference (Table~\\ref{tab:ongc})", "descriptive case study with no inference (Table~\\ref{tab:imsongc})")
sub("nothing is significant (Table~\\ref{tab:holm})", "nothing is significant (Table~\\ref{tab:crossds})")
sub("breaks the conformal exchangeability assumption (Table~\\ref{tab:conformal})",
    "breaks the conformal exchangeability assumption (Figure~\\ref{fig:conformal}a)")
sub("the per-detector median differences of Table~\\ref{tab:ongc} in", "the per-detector ONGC median differences of Table~\\ref{tab:imsongc} in")
sub("Table~\\ref{tab:compute} reports the wall-clock training", "Table~\\ref{tab:hyperparams}(b) reports the wall-clock training")
sub("(Table~\\ref{tab:noise})", "(Table~\\ref{tab:mechanism}a)", 2)
sub("(Table~\\ref{tab:denoise})", "(Table~\\ref{tab:mechanism}b)", 2)
sub("violates the conformal guarantee (Table~\\ref{tab:conformal})", "violates the conformal guarantee (Figure~\\ref{fig:conformal}a)")

# ---------------------------------------------------------------- M2 consequences (11-detector ranking)
sub("on IMS the detectors PH ranks first by raw lead (Hotelling $T^2$, Isolation Forest, and the exponentially weighted moving average (EWMA) chart) each have no valid operating point at a 10\\% false-alarm budget, whereas our metric identifies $3\\sigma$ as the deployable choice.",
    "on IMS the seven detectors PH ranks highest by raw lead---the deep models, the one-class SVM, Hotelling $T^2$, Isolation Forest and the exponentially weighted moving average (EWMA) chart---each have no valid operating point at a 10\\% false-alarm budget, whereas our metric identifies $3\\sigma$, PH's eighth, as the deployable choice.")
sub("The disagreement is not marginal: on IMS the detectors the prognostic horizon ranks first by raw lead (Hotelling $T^2$, Isolation Forest, and EWMA) each have no valid operating point at a 10\\% false-alarm budget, while our metric identifies $3\\sigma$ as the deployable choice.",
    "The disagreement is not marginal: on IMS the seven detectors the prognostic horizon ranks highest by raw lead each have no valid operating point at a 10\\% false-alarm budget, while our metric identifies $3\\sigma$, PH's eighth, as the deployable choice.")
sub("Table~\\ref{tab:phrank} ranks the seven non-sequence detectors on IMS by their best raw lead (PH) and by their best lead at an operating point within the $\\tau=10\\%$ budget ($L$). The two rankings are nearly inverted at the top. The four detectors PH ranks highest (Hotelling $T^2$ 176.9~h, Isolation Forest 174.7~h, EWMA 89.1~h, and CUSUM 65.0~h) each have no valid operating point under a 10\\% false-alarm budget, so their gated lead is $L=0$. The detector PH ranks only fourth, $3\\sigma$ (77.0~h raw), is the one that actually clears the budget (56.3~h of lead at 8.9\\% pre-onset FAR) and is the correct recommendation; Deep SVDD, ranked last of the seven by PH, rises to a valid 14.8~h. The three deep reconstruction models (omitted from the sweep) would sit above all of these by PH, with raw leads of 183--198~h (Table~\\ref{tab:imslead}), while alarming through 61--100\\% of every pre-onset region, i.e.\\ $L=0$: the most extreme illustration that PH rewards precisely the detectors a false-alarm-budgeted operator must avoid.",
    "Table~\\ref{tab:imsdet} ranks all eleven detectors on IMS by their best raw lead over the swept thresholds (PH) and by their best lead at an operating point within the $\\tau=10\\%$ budget ($L$). The two rankings are nearly inverted at the top. The seven detectors PH ranks highest---LSTM-AE 199.6~h, TCN-AE 185.4~h, Transformer-AD 184.0~h, the one-class SVM 180.2~h, Hotelling $T^2$ 176.9~h, Isolation Forest 174.7~h and EWMA 89.1~h---each have no valid operating point under a 10\\% false-alarm budget, so their gated lead is $L=0$; the deep models alarm through 61--100\\% of every pre-onset region. The detector PH ranks only eighth, $3\\sigma$ (77.0~h raw), is the one that actually clears the budget (56.3~h of lead at 8.9\\% pre-onset FAR) and is the correct recommendation; CUSUM (65.0~h, PH's ninth) also scores $L=0$, while Deep SVDD, ranked last by PH, rises to a valid 14.8~h. PH rewards precisely the detectors a false-alarm-budgeted operator must avoid.")

# ---------------------------------------------------------------- protected additions
# G3 (verified: rg3_raw_invariance.csv, 99 rows, max |dev| 0.0 h, 0 NaN mismatches)
sub("which contains no onset term. Test 1 agrees across all three definitions",
    "which contains no onset term: re-running the full benchmark under the pca1 and kurt\\_only indicators leaves every raw-lead aggregate$-$decimate difference exactly unchanged, a maximum absolute deviation of 0.000~h across all 99 dataset $\\times$ detector $\\times$ indicator cells. Test 1 agrees across all three definitions")
# D18 (verified: d18_gap_injection_multiseed.csv; seeds 101 and 104 collapse 3rd_test 315.9 -> 59.7 h;
# at 5% Hotelling and EWMA unchanged in every draw, max per-draw deviation 0.83 h)
sub("At 5\\% missing, Hotelling $T^2$ is unchanged in all five draws.",
    "It collapses in 2 of the 5 draws at 20\\%, giving an across-draw mean of 134.9~h over a range of 58.0--186.1~h, and the collapse is driven by a single run (test~3 falls from 315.9 to 59.7~h). At 5\\% missing, Hotelling $T^2$ and EWMA are unchanged in every draw, and no chart's per-draw mean lead moves by more than 0.83~h.")

# ---------------------------------------------------------------- N-29 double-rounding correction
sub("(76.0 and 75.7~h vs.\\ aggregation's 75.7~h)", "(76.0 and 75.6~h vs.\\ aggregation's 75.6~h)")
sub("at statistically indistinguishable lead times (76.0 vs.\\ 75.7~h)", "at statistically indistinguishable lead times (76.0 vs.\\ 75.6~h)")

# ---------------------------------------------------------------- ONGC (verified: n20_rerun_long_ONGC.csv, factor 1)
sub("has nine of its eleven detectors alarm 34--35~h ahead of the labeled failure (RMS-trend ${\\sim}23$~h, and Deep SVDD not before failure at all)",
    "has nine of its eleven detectors alarm 30--35~h ahead of the labeled failure (RMS-trend 22.8~h, and Deep SVDD not before failure at all)")
sub("every detector achieves a long warning: $3\\sigma$, EWMA, Hotelling $T^2$, and Isolation Forest each alarm roughly 35~h before the labeled failure, and even the naive RMS-trend baseline gives ${\\sim}22.8$~h. More to the point of this paper, the aggregate-vs-decimate difference is at most about a minute for every detector (Table~\\ref{tab:ongc}).",
    "nine of the eleven detectors alarm 30--35~h before the labeled failure (seven within 34.9--35.3~h, CUSUM at 33.9~h and Hotelling $T^2$ at 30.4~h), the naive RMS-trend baseline gives 22.8~h, and Deep SVDD does not alarm before failure. More to the point of this paper, the aggregate-vs-decimate difference is at most about a minute for every detector (Table~\\ref{tab:imsongc}).")

for dead in ("tab:equiv", "tab:holm", "tab:imssweep", "tab:ongc", "tab:imslead", "tab:farbudget",
             "tab:phrank", "tab:conformal", "tab:compute", "tab:noise", "tab:denoise"):
    assert "\\ref{" + dead + "}" not in s, dead
TEX.write_text(s, encoding="utf-8")
print("Phase 1 edits applied")
