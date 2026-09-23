"""Final submission pass, Part 1: restate every validity count under Eq. 5.

Every restated number is read from the results/tables/eq5_*.csv files written by
src/eq5_validity.py; none is typed. Each edit is guarded: the old text must occur
exactly once.

    python revision-artifacts/final2/apply_part1.py
"""
import math
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "paper", "files", "scada_ijphm.tex")
TAB = os.path.join(ROOT, "results", "tables")


def csv(name):
    return pd.read_csv(os.path.join(TAB, name))


def f2(v):
    return f"{v:.2f}"


def f3(v):
    return f"{v:.3f}"


# ------------------------------------------------------------------ values
aud = csv("eq5_validity_audit.csv").set_index("site")
head = aud.loc["S6.3 five window-magnitude detectors, all modes x factors"]
N_VALID, N_SC = int(head.eq5_valid), int(head.eq5_scoreable)
N_EMPTY, N_NOON = int(head.excluded_empty_pre), int(head.excluded_no_onset)
N_ALL = int(head.published_den)
assert (N_VALID, N_SC, N_EMPTY, N_NOON, N_ALL) == (48, 230, 170, 50, 450), (N_VALID, N_SC)

pb = csv("eq5_xjtu_perbearing.csv").set_index("run")
sc = pb[pb.status == "scoreable"]
TOT_V, TOT_D = int(sc.eq5_valid_of_5.sum()), 5 * len(sc)
NONE_V = int((sc.eq5_valid_of_5 == 0).sum())
# the replacement examples must rest on scoreable bearings, and mean == best on all of them
assert set(sc.index) == {"Bearing1_1", "Bearing1_4", "Bearing2_1", "Bearing2_3", "Bearing2_4"}
assert (sc.mean_valid_lead_h.fillna(0) == sc.best_valid_lead_h.fillna(0)).all()
L23, L21 = sc.loc["Bearing2_3", "mean_valid_lead_h"], sc.loc["Bearing2_1", "mean_valid_lead_h"]

gap = csv("eq5_gap_table4b.csv")
sweep = csv("eq5_femto_training_sweep.csv")
pers = csv("eq5_persistence_IMS.csv")


def gcell(ds, det, g):
    v = gap[(gap.dataset == ds) & (gap.short_name == det) & (gap.gap == g)].mean_valid_lead_h.iloc[0]
    return "--" if pd.isna(v) else f"{v:.1f}"


def gdelta(ds, det):
    a = gap[(gap.dataset == ds) & (gap.short_name == det) & (gap.gap == 0.0)].mean_valid_lead_h.iloc[0]
    b = gap[(gap.dataset == ds) & (gap.short_name == det) & (gap.gap == 0.2)].mean_valid_lead_h.iloc[0]
    return b - a


def sw(det, t):
    return sweep[(sweep.short_name == det) & (sweep.train_fraction == t)].valid_frac.iloc[0]


# ------------------------------------------------------------------ edits
EDITS = []


def edit(old, new):
    EDITS.append((old, new))


# Eq. 5: state the no-onset case, which the paper's rule did not name.
edit(r"and it is excluded from the validity denominator rather than counted as valid.",
     r"and it is excluded from the validity denominator rather than counted as valid, as is a run "
     r"with no detectable onset. Every validity count in Section~\ref{sec:results} is over scoreable "
     r"evaluations, with the exclusions stated.")

# Section 6.3 headline
edit(r"209/450 evaluations yield a valid alarm, and the shortest-lived",
     rf"{N_VALID} of {N_SC} scoreable evaluations yield a valid alarm ({N_EMPTY + N_NOON} of {N_ALL} "
     rf"are excluded under Eq.~(\ref{{eq:valid}}): {N_EMPTY} because the onset precedes the first "
     rf"scored window, {N_NOON} because Bearing1\_2 has no detectable onset), and the shortest-lived")

seq = aud.loc["S6.3 deep models at seq-len 15 (bearings with a valid alarm)"]
assert seq.note == "excluded bearing(s): Bearing2_5" and int(seq.eq5_valid) == 0
assert int(seq.eq5_scoreable) == 2
edit(r"Halving the sequence length to 15 windows makes only one more short bearing usable, and the "
     r"deep models still yield a valid alarm on at most one of the ten bearings.",
     r"Halving the sequence length to 15 windows makes only one more short bearing usable, "
     r"Bearing2\_5, whose onset precedes the first scored window, so it cannot be scored; on the two "
     r"scoreable bearings the deep models still yield no valid alarm.")

# Per-bearing paragraph
edit(r"they differ only where detectors disagree (Bearing2\_2: 1.00~h mean vs.\ 1.08~h oracle). "
     r"The 209/450 valid-alarm figure hides strong heterogeneity. Long-degrading bearings such as "
     r"Bearing2\_3 (533~min life) and Bearing1\_3 (158~min) are warnable with multi-hour or near-hour "
     r"lead, whereas the two shortest-lived, abrupt-failure bearings, Bearing2\_4 (42~min) and "
     r"Bearing1\_1 (123~min, sudden end), yield no valid alarm for any detector (2/10 bearings)",
     rf"they differ only where valid detectors disagree, which happens on none of the scoreable "
     rf"bearings here. Only {len(sc)} of the ten bearings are scoreable at full resolution: "
     rf"Bearing1\_2 has no detectable onset, and on Bearing1\_3, 1\_5, 2\_2 and 2\_5 the onset precedes "
     rf"the first scored window. The {N_VALID}/{N_SC} valid-alarm figure hides strong heterogeneity. "
     rf"Long-degrading bearings such as Bearing2\_3 (533~min life) and Bearing2\_1 (491~min) are "
     rf"warnable, with {f2(L23)} and {f2(L21)}~h of lead, whereas two abrupt-failure bearings, "
     rf"Bearing2\_4 (42~min, the shortest-lived) and Bearing1\_1 (123~min, sudden end), yield no valid "
     rf"alarm for any detector ({NONE_V} of the {len(sc)} scoreable bearings)")

# Table 7
LIFE = {"Bearing1_1": 123, "Bearing1_2": 161, "Bearing1_3": 158, "Bearing1_4": 122,
        "Bearing1_5": 52, "Bearing2_1": 491, "Bearing2_2": 161, "Bearing2_3": 533,
        "Bearing2_4": 42, "Bearing2_5": 339}
new_rows = []
for run in pb.index:
    r = pb.loc[run]
    name = run.replace("_", r"\_")
    cd = run[7]
    if r.status == "scoreable":
        v = int(r.eq5_valid_of_5)
        mean = "--" if v == 0 else f2(r.mean_valid_lead_h)
        best = "0.00" if v == 0 else f2(r.best_valid_lead_h)
        new_rows.append(rf"		{name} & {cd} & {LIFE[run]} & {v} & {mean} & {best} \\")
    else:
        tag = "a" if r.status == "no_onset" else "b"
        new_rows.append(rf"		{name} & {cd} & {LIFE[run]} & n.s.$^{tag}$ & -- & -- \\")
OLD_TABLE = r"""	\caption{XJTU-SY per-bearing summary at full resolution (aggregate). ``Valid/5'' counts the detectors (of five) that produce a valid alarm; ``Mean valid'' is the mean lead over those detectors; ``Best'' is the oracle maximum over the five. Two bearings are warned by no detector (0/5).}
	\label{tab:perbearing}
	\begin{tabular}{l c r c r r}
		\hline \hline
		\textbf{Bearing} & \textbf{Cd.} & \textbf{Life} & \textbf{V/5} & \textbf{Mean} & \textbf{Best} \\
		\hline
		Bearing1\_1 & 1 & 123 & 0 & -- & 0.00 \\
		Bearing1\_2 & 1 & 161 & 1 & 0.67 & 0.67 \\
		Bearing1\_3 & 1 & 158 & 4 & 1.03 & 1.03 \\
		Bearing1\_4 & 1 & 122 & 2 & 0.68 & 0.68 \\
		Bearing1\_5 & 1 & 52 & 3 & 0.35 & 0.35 \\
		Bearing2\_1 & 2 & 491 & 3 & 0.67 & 0.67 \\
		Bearing2\_2 & 2 & 161 & 2 & 1.00 & 1.08 \\
		Bearing2\_3 & 2 & 533 & 1 & 3.45 & 3.45 \\
		Bearing2\_4 & 2 & 42 & 0 & -- & 0.00 \\
		Bearing2\_5 & 2 & 339 & 4 & 2.30 & 2.30 \\
		\hline
		\multicolumn{4}{l}{Total (full-res, aggregate)} & \multicolumn{2}{r}{20/50} \\
		\multicolumn{4}{l}{Bearings with no valid detector} & \multicolumn{2}{r}{2/10} \\"""
NEW_TABLE = (r"""	\caption{XJTU-SY per-bearing summary at full resolution (aggregate). V/5 counts the detectors (of five) that produce a valid alarm (Eq.~\ref{eq:valid}); Mean is the mean lead over those detectors; Best is the oracle maximum over them. n.s.: not scoreable, and excluded from the totals---$^a$no detectable onset; $^b$onset at or before the first scored window, so the pre-onset region is empty.}
	\label{tab:perbearing}
	\begin{tabular}{l c r c r r}
		\hline \hline
		\textbf{Bearing} & \textbf{Cd.} & \textbf{Life (min)} & \textbf{V/5} & \textbf{Mean (h)} & \textbf{Best (h)} \\
		\hline
""" + "\n".join(new_rows) + rf"""
		\hline
		\multicolumn{{4}}{{l}}{{Total ({len(sc)} scoreable bearings)}} & \multicolumn{{2}}{{r}}{{{TOT_V}/{TOT_D}}} \\
		\multicolumn{{4}}{{l}}{{Scoreable bearings with no valid detector}} & \multicolumn{{2}}{{r}}{{{NONE_V}/{len(sc)}}} \\""")
edit(OLD_TABLE, NEW_TABLE)

# Table 4(b) XJTU-SY columns and caption
for det, lab in (("three_sigma", r"$3\sigma$"), ("ewma", "EWMA"), ("cusum", "CUSUM"),
                 ("hotelling_t2", r"Hot.\ $T^2$"), ("isolation_forest", r"Iso.\ Forest")):
    ims = " & ".join(gcell("IMS", det, g) for g in (0.0, 0.05, 0.2))
    pub = " & ".join(f"{v:.1f}" for v in
                     gap[(gap.dataset == "XJTU-SY") & (gap.short_name == det)]
                     .sort_values("gap").published_mean_valid_lead_h)
    new = " & ".join(gcell("XJTU-SY", det, g) for g in (0.0, 0.05, 0.2))
    edit(rf"		{lab} & {ims} & {pub} \\", rf"		{lab} & {ims} & {new} \\")
edit(r"averaged over the runs with a valid alarm and then over \emph{five independent gap draws} per level.}",
     r"averaged over the runs with a valid alarm (Eq.~\ref{eq:valid}) and then over \emph{five "
     r"independent gap draws} per level. XJTU-SY Bearing1\_3, 1\_5, 2\_2 and 2\_5 are not scoreable at "
     r"full resolution and are excluded; --: no valid alarm on the six that remain.}")

# Section 6.2 gap prose
xd = {d: gdelta("XJTU-SY", d) for d in ("three_sigma", "ewma", "cusum", "isolation_forest")}
edit(r"At 20\% every Table~\ref{tab:robust}b detector on both datasets stays inside the $\pm 1$~h margin but one: "
     r"the across-draw mean change is $+0.83$~h for $3\sigma$ on IMS and $-0.04$~h on XJTU-SY, $-0.08$ and "
     r"$-0.12$~h for EWMA, $-0.67$ and $-0.02$~h for CUSUM, and $-0.92$ and $-0.07$~h for Isolation Forest.",
     rf"At 20\% every Table~\ref{{tab:robust}}b detector with a valid alarm stays inside the $\pm 1$~h "
     rf"margin on both datasets but one: the across-draw mean change is $+0.83$~h for $3\sigma$ on IMS and "
     rf"${xd['three_sigma']:+.2f}$~h on XJTU-SY, $-0.08$ and ${xd['ewma']:+.2f}$~h for EWMA, $-0.67$ and "
     rf"${xd['cusum']:+.2f}$~h for CUSUM, and $-0.92$ and ${xd['isolation_forest']:+.2f}$~h for Isolation "
     rf"Forest; Hotelling $T^2$ has no valid alarm on a scoreable XJTU-SY bearing.")
x = gap[(gap.dataset == "XJTU-SY") & (gap.gap > 0) & gap.mean_valid_lead_h.notna()]
spread = math.ceil(((x.draw_max_h - x.draw_min_h).max()) * 100) / 100
xs = gap[(gap.dataset == "XJTU-SY") & gap.mean_valid_lead_h.notna()]
move = int((xs.groupby("short_name").n_valid_max.max() - xs.groupby("short_name").n_valid_min.min()).max())
n_sc = int(xs.n_scoreable_runs.max())
assert move == 2 and n_sc == 6, (move, n_sc)
edit(r"and move by at most two bearings on XJTU-SY;",
     rf"and move by at most two of the {n_sc} scoreable bearings on XJTU-SY;")
edit(r"by less than 3.4~h on IMS and 0.37~h on XJTU-SY.",
     rf"by less than 3.4~h on IMS and {spread:.2f}~h on XJTU-SY.")

# Section 6.10 steps at the coarsest factor
ab = aud.loc["S6.10 feature-group ablation repeated at every factor"].note
assert "f=20:2-2" in ab and "f=5:3-3" in ab and "f=10:3-3" in ab, ab
edit(r"valid fractions move in steps of 1/3,",
     r"valid fractions move in steps of 1/3 (1/2 at $f=20$, where test~2 is not scoreable),")

# Section 6.12 training sweep
t20 = sweep[sweep.train_fraction == 0.2]
assert set(t20.n_scoreable) == {5} and set(sweep[sweep.train_fraction > 0.2].n_scoreable) == {6}
edit(r"these are the only three N/A cells, the other 297 of the 300 (detector, bearing, $T$) cells being "
     r"genuine evaluations. Valid-alarm fractions use the full $n=6$ with an N/A counted as no valid alarm, "
     r"the conservative choice;",
     r"these are the only three N/A cells among the 300 (detector, bearing, $T$) cells. At $T=0.20$ the "
     r"onset of Bearing2\_2 precedes the first scored window, so its ten cells are not scoreable "
     r"(Eq.~\ref{eq:valid}). Valid-alarm fractions are over $n=6$ bearings ($n=5$ at $T=0.20$), with an "
     r"N/A counted as no valid alarm, the conservative choice;")
ts = [sw("three_sigma", t) for t in (0.2, 0.3, 0.4, 0.5, 0.6)]
hot = [sw("hotelling_t2", t) for t in (0.2, 0.3, 0.4, 0.5, 0.6)]
ew = [sw("ewma", t) for t in (0.2, 0.3, 0.4, 0.5, 0.6)]
cu = [sw("cusum", t) for t in (0.2, 0.3, 0.4, 0.5, 0.6)]
iso = [sw("isolation_forest", t) for t in (0.2, 0.3, 0.4, 0.5, 0.6)]
assert ts[0] == max(ts) and ts[2] == ts[3] == ts[4]
assert hot[2] == hot[3] == hot[4] and hot[1] == min(hot)
assert cu[3] == max(cu) and cu[4] == cu[2] == cu[1] and cu[0] == min(cu)
assert iso[1] == min(iso) and iso[4] == iso[3]
edit(r"The four SPC charts are at or near their best at the \emph{smallest} training fraction---$3\sigma$ at "
     r"1.00, EWMA and Hotelling $T^2$ at 0.667, CUSUM at 0.500---and more commissioning data does not improve "
     r"them: $3\sigma$ falls to 0.833 at $T=0.30$ and 0.667 from $T=0.40$ on, Hotelling $T^2$ falls to 0.500, "
     r"EWMA is flat at 0.667, and CUSUM is flat at 0.500 apart from a one-bearing rise to 0.667 at $T=0.50$. "
     r"Isolation Forest starts and ends at 0.667 but dips to 0.167 at $T=0.30$; only the naive RMS-trend "
     r"baseline rises with $T$,",
     rf"More commissioning data does not systematically improve the four SPC charts: $3\sigma$ is at its "
     rf"best at the \emph{{smallest}} training fraction ({ts[0]:.2f}) and falls to {f3(ts[1])} at $T=0.30$ "
     rf"and {f3(ts[2])} from $T=0.40$ on; Hotelling $T^2$ starts at {f3(hot[0])}, falls to {f3(hot[1])} at "
     rf"$T=0.30$ and settles at {f3(hot[2])}; EWMA stays within {f3(min(ew))}--{f3(max(ew))}; and CUSUM "
     rf"stays within {f3(cu[0])}--{f3(cu[1])} apart from a one-bearing rise to {f3(cu[3])} at $T=0.50$. "
     rf"Isolation Forest starts at {f3(iso[0])}, dips to {f3(iso[1])} at $T=0.30$ and ends at {f3(iso[4])}; "
     rf"only the naive RMS-trend baseline rises steadily with $T$,")
spc = sweep[sweep.short_name.isin(["three_sigma", "ewma", "cusum", "hotelling_t2"])]
base = float(spc.valid_frac.mean())
edit(r"dashed: the SPC baseline (${\approx}0.62$). The three N/A cells at $T=0.20$ (Bearing3\_1, 20 training "
     r"windows) count as no valid alarm.}",
     rf"dashed: the SPC baseline (${{\approx}}{base:.2f}$). The three N/A cells at $T=0.20$ (Bearing3\_1, 20 "
     rf"training windows) count as no valid alarm; at $T=0.20$ fractions are over five bearings, Bearing2\_2 "
     rf"being not scoreable (Eq.~\ref{{eq:valid}}).}}")

# Table 4(a) "all factors" row and its prose, from the row-level persistence rerun
p3 = pers[pers.short_name == "three_sigma"].set_index("persistence")
old_all = r"		$3\sigma$ valid-alarm frac., all factors & 0.67 & 0.67 & 0.53 & 0.33 \\"
new_all = (r"		$3\sigma$ valid-alarm frac., all factors & "
           + " & ".join(f2(p3.loc[p, "valid_frac_all_factors"]) for p in (1, 3, 5, 10)) + r" \\")
edit(old_all, new_all)
assert all(p3.loc[p, "n_scoreable_all"] == 13 for p in (1, 3, 5, 10))
assert all(abs(p3.loc[p, "valid_frac_f1"] - 2 / 3) < 1e-12 for p in (1, 3, 5, 10))
edit(r"at persistence $\in \{1,3,5,10\}$ windows.",
     r"at persistence $\in \{1,3,5,10\}$ windows; pooled fractions are over the 13 scoreable "
     r"aggregate evaluations (test~2 at $f \in \{10,20\}$ has an empty pre-onset region).")
edit(r"but, pooled over the sampling sweep, falls from 0.67 to 0.33 by persistence 10,",
     rf"but, pooled over the sampling sweep, falls from {f2(p3.loc[1, 'valid_frac_all_factors'])} to "
     rf"{f2(p3.loc[10, 'valid_frac_all_factors'])} by persistence 10,")


def main():
    with open(TEX, encoding="utf-8", newline="") as fh:
        src = fh.read()
    nl = "\r\n" if "\r\n" in src else "\n"
    for old, new in EDITS:
        o, n = old.replace("\n", nl), new.replace("\n", nl)
        assert src.count(o) == 1, f"expected once, found {src.count(o)}: {old[:90]!r}"
        src = src.replace(o, n)
    with open(TEX, "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    print(f"applied {len(EDITS)} edits")
    for old, new in EDITS:
        print("-" * 80)
        print("OLD:", old)
        print("NEW:", new)


if __name__ == "__main__":
    main()
