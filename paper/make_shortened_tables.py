"""Generate the consolidated result tables of the shortened manuscript (Phase 1).

Every number is read from a released result file; nothing is typed. Each table is
written to paper/files/gen/<name>.tex and \\input by scada_ijphm.tex. Source files
follow results/tables/MANIFEST.md and the N-20 provenance rule (post-fix files for
FEMTO, Ferrara and ONGC; IMS/XJTU-SY files are N-20-invariant).

    python paper/make_shortened_tables.py        # writes gen/*.tex, asserts derivations

Tables
  tab:crossds       XJTU-SY / FEMTO / Ferrara x 11: median, mean [95% CI], n+/n-, p
                    (absorbs tab:equiv and tab:holm)
  tab:imsongc       IMS x 11 per-run differences, median, n+/n-, p; ONGC median (min)
                    (absorbs tab:imssweep and tab:ongc)
  tab:gatedcontrast raw vs gated, per dataset, side by side
  tab:imsdet        IMS x 11: raw lead + CI, PH, best valid lead at tau = .05/.10/.20
                    (absorbs tab:imslead, tab:farbudget, tab:phrank)
  tab:tradeoff      IMS threshold sweep, now with the one-class SVM row
  tab:mechanism     noise injection (a) + denoisers (b)  (absorbs tab:noise, tab:denoise)
  tab:hyperparams   fixed protocol (a) + compute cost (b) (absorbs tab:compute)
  conformal_values  panel (a) values for the fig:conformal caption (replaces tab:conformal)
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify_tables as vt  # noqa: E402  (shared loaders, key_of, gated stats)

GEN = HERE / "files" / "gen"
DET_ORDER = ["3sigma", "ewma", "cusum", "hotelling", "isoforest", "deepsvdd", "ocsvm",
             "lstmae", "tcnae", "transformerad", "rmstrend"]
NAME = {"3sigma": r"$3\sigma$", "ewma": "EWMA", "cusum": "CUSUM", "hotelling": r"Hotelling $T^2$",
        "isoforest": r"Iso.\ Forest", "deepsvdd": "Deep SVDD", "ocsvm": "One-class SVM",
        "lstmae": "LSTM-AE", "tcnae": "TCN-AE", "transformerad": "Transf.-AD", "rmstrend": "RMS-trend"}
SEQ = {"lstmae", "tcnae", "transformerad"}


# ------------------------------------------------------------------ formatting
def m(x: str) -> str:
    """Wrap a signed number in math mode so the minus renders as a minus."""
    return "$%s$" % x


def signed(v: float, d: int) -> str:
    s = "%+.*f" % (d, v)
    if v < 0 and s.startswith("+"):
        s = "-" + s[1:]
    return m(s)


def plainsigned(v: float, d: int) -> str:
    """Published crossds style: negatives signed (incl. '-0.00'), non-negatives bare."""
    return m("-%.*f" % (d, abs(v))) if v < 0 else "%.*f" % (d, v)


def zero_or_signed(v: float, d: int) -> str:
    """Published imssweep/ongc style: a value rounding to zero is bare, else signed."""
    return "%.*f" % (d, 0.0) if round(v, d) == 0 else signed(v, d)


def counts(npos, nneg, same, star=""):
    return "%s/%s%s%s" % (npos, nneg, r"$^{\mathrm{s}}$" if same else "", star)


def write(name: str, body: str) -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / (name + ".tex")).write_text(body.strip() + "\n", encoding="utf-8")


# ------------------------------------------------------------------ sources
def runlevel_sources():
    """(dataset, key) -> dict(median, n_pos, n_neg, same, p, run_diffs)."""
    files = {"XJTU-SY": "xjtu_sy_runlevel_test.csv", "FEMTO": "femto_runlevel_test_n20.csv",
             "Ferrara": "ferrara_runlevel_test_n20.csv", "IMS": "ims_runlevel_test_invariant.csv"}
    out = {}
    for ds, fn in files.items():
        for r in vt.load(fn):
            k = vt.key_of(r["method"])
            if k:
                out[(ds, k)] = dict(median=float(r["median_diff"]), n_pos=r["n_pos"], n_neg=r["n_neg"],
                                    same=r["all_same_sign"] in ("True", "true"),
                                    p=float(r["sign_test_p"]), run_diffs=r["run_diffs"])
    for r in vt.load_holm_family():         # n20_raw_contrast_old_vs_new.csv, arm new
        if vt.key_of(r["method"]) == "ocsvm":
            out[(r["dataset"], "ocsvm")] = dict(
                median=float(r["median_diff_h"]), n_pos=r["n_pos"], n_neg=r["n_neg"],
                same=r["all_same_sign"] in ("True", "true"), p=float(r["sign_test_p"]),
                run_diffs=r["run_diffs"])
    return out


def holm_family_checks():
    rows = vt.load_holm_family()
    assert len(rows) == 44, len(rows)
    assert all(abs(float(r["holm_p"]) - 1.0) < 1e-12 for r in rows)
    assert not any(r["holm_reject"] == "True" for r in rows)
    lo = min((float(r["sign_test_p"]), r["dataset"], r["method"]) for r in rows)
    assert abs(lo[0] - 0.125) < 1e-12 and lo[1] == "FEMTO" and "Transformer" in lo[2], lo
    return {(r["dataset"], vt.key_of(r["method"])): float(r["sign_test_p"]) for r in rows}


# ------------------------------------------------------------------ tab:crossds
def tab_crossds(src, holm):
    eq = vt.index(vt.load("n20_d15_bootstrap_new_11det.csv"), ds_field="dataset")
    rows, widest = [], 0.0
    for ds, n in (("XJTU-SY", 10), ("FEMTO", 6), ("Ferrara", 6)):
        rows.append(r"\multicolumn{5}{l}{\emph{%s} ($n=%d$)} \\" % (ds, n))
        for k in DET_ORDER:
            s, e = src[(ds, k)], eq[(ds, k)]
            assert abs(s["p"] - holm[(ds, k)]) < 1e-12, (ds, k)   # the Holm raw p IS this p
            lo, hi = float(e["ci_lo_h"]), float(e["ci_hi_h"])
            assert -1.0 < lo and hi < 1.0, (ds, k)                  # equivalent at delta = 1 h
            widest = max(widest, abs(lo), abs(hi))
            name = NAME[k] + (r"$^\ddagger$" if ds == "XJTU-SY" and k in SEQ else "")
            rows.append(r"%s & %s & %s\,[%s,\,%s] & %s & %.3f \\" % (
                name, plainsigned(s["median"], 2), signed(float(e["mean_diff_h"]), 3),
                signed(lo, 3), signed(hi, 3), counts(s["n_pos"], s["n_neg"], s["same"]), s["p"]))
        rows.append(r"\hline")
    assert widest < 0.6, widest
    write("tab_crossds", r"""
\begin{table}[t] \footnotesize
	\begin{center}
	\caption{Run-level aggregate$-$decimate lead-time contrast on the three multi-bearing campaigns, collapsing the five sampling factors to one difference per run. Med., Mean: run-level median and mean difference (h), with the 95\%% bootstrap CI over runs; $n_+/n_-$: non-zero runs ($^{\mathrm{s}}$: all of one sign); $p$: exact two-sided sign test. $^\ddagger$: length-30 sequence models, $n=3$ on XJTU-SY. Equivalent at $\delta=1$~h when the CI lies inside $[-\delta,+\delta]$: all 33 cells. Holm over $N=44$ (these 33 tests and the eleven IMS tests of Table~\ref{tab:imsongc}): every adjusted $p$ is 1.00. IMS and ONGC are outside the equivalence family.}
	\label{tab:crossds}
	\setlength{\tabcolsep}{2.5pt}
	\begin{tabular}{l r r c r}
		\hline \hline
		\textbf{Detector} & \textbf{Med.} & \textbf{Mean [95\%% CI]} & $n_+/n_-$ & $p$ \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\end{center}
\end{table}
""" % "\n".join("\t\t" + r for r in rows[:-1]))


# ------------------------------------------------------------------ tab:imsongc
IMS_ORDER = ["3sigma", "isoforest", "ewma", "cusum", "hotelling", "deepsvdd", "ocsvm",
             "rmstrend", "lstmae", "tcnae", "transformerad"]
ONGC_KEY = {"3sigma": "three_sigma", "ewma": "ewma", "cusum": "cusum", "hotelling": "hotelling_t2",
            "isoforest": "isolation_forest", "deepsvdd": "deep_svdd", "ocsvm": "one_class_svm",
            "lstmae": "lstm_ae", "tcnae": "tcn", "transformerad": "transformer_ad", "rmstrend": "rms_trend"}


def tab_imsongc(src, holm):
    ongc = {r["short_name"]: float(r[vt.ONGC_MINUTES_COL]) for r in vt.load(vt.ONGC_MINUTES)}
    assert len(ongc) == 11 and max(abs(v) for v in ongc.values()) <= 1.5
    rows = []
    for k in IMS_ORDER:
        s = src[("IMS", k)]
        assert abs(s["p"] - holm[("IMS", k)]) < 1e-12, k
        runs = [float(x) for x in s["run_diffs"].replace("+", "").split(",")]
        run_txt = ",".join("0.0" if round(v, 1) == 0 else "%+.1f" % v for v in runs)
        # Published IMS convention: a detector with tied runs is not sign-consistent
        # (Deep SVDD: one positive run, two ties), stricter than the file's flag.
        ties = sum(1 for v in runs if round(v, 1) == 0)
        same = s["same"] and ties == 0
        star = r"$^\ast$" if s["same"] and ties else ""
        rows.append(r"%s & %s & %s & %s & %.2f & %s \\" % (
            NAME[k].replace("Transf.-AD", "Transformer-AD"), m(run_txt), zero_or_signed(s["median"], 1),
            counts(s["n_pos"], s["n_neg"], same, star), s["p"], zero_or_signed(ongc[ONGC_KEY[k]], 1)))
    write("tab_imsongc", r"""
\begin{table}[t] \footnotesize
	\begin{center}
	\caption{IMS controlled sweep ($n=3$) and the ONGC case study ($n=1$). IMS: run differences (h) for tests 1, 2, 3, each collapsing the five within-run sampling factors to one mean aggregate$-$decimate difference, with the run-level median, $n_+/n_-$ and the exact two-sided sign-test $p$, which floors at 0.25 at $n=3$ ($^\ast$: one positive run and two ties, not counted as sign-consistent). ONGC: descriptive median over the five sampling factors, in minutes; no inference.}
	\label{tab:imsongc}
	\setlength{\tabcolsep}{2.5pt}
	\begin{tabular}{l l r c r r}
		\hline \hline
		 & \multicolumn{4}{c}{\textbf{IMS} (h)} & \textbf{ONGC} \\
		\textbf{Detector} & \textbf{Run diffs} & \textbf{Med.} & $n_+/n_-$ & $p$ & \textbf{(min)} \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\end{center}
\end{table}
""" % "\n".join("\t\t" + r for r in rows))


# ------------------------------------------------------------------ tab:gatedcontrast
def tab_gated():
    raw, gated = vt._gated_stats("raw"), vt._gated_stats("gated_D7")
    rows = []
    for ds in vt.GATED_ORDER:
        cells = []
        for st in (raw[ds], gated[ds]):
            med, npos, nneg, nzero, neff, ndet = st
            assert ndet == 11
            cells += [signed(med, 3), "%d/%d/%d" % (npos, nneg, nzero), "%.1f" % neff]
        rows.append(r"%s & %s \\" % (ds, " & ".join(cells)))
    write("tab_gatedcontrast", r"""
\begin{table}[t] \footnotesize
	\begin{center}
	\caption{Aggregate$-$decimate contrast under the raw and the gated ($\tau=10\%%$ pre-onset FAR) metric, post-N-20 reruns, all eleven detectors. Med.: median across detectors of each detector's run-level median difference (h); $n_+/n_-/0$: detectors by the sign of that median; $\bar{n}_{\text{eff}}$: mean effective sample size once zero-difference runs are dropped.}
	\label{tab:gatedcontrast}
	\setlength{\tabcolsep}{3pt}
	\begin{tabular}{l r c r | r c r}
		\hline \hline
		 & \multicolumn{3}{c|}{\textbf{Raw lead}} & \multicolumn{3}{c}{\textbf{Gated lead}} \\
		\textbf{Dataset} & \textbf{Med.} & $n_+/n_-/0$ & $\bar{n}_{\text{eff}}$ & \textbf{Med.} & $n_+/n_-/0$ & $\bar{n}_{\text{eff}}$ \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\end{center}
\end{table}
""" % "\n".join("\t\t" + r for r in rows))


# ------------------------------------------------------------------ tab:imsdet
D9_KEY = {"lstm_ae": "lstmae", "tcn": "tcnae", "transformer_ad": "transformerad", "one_class_svm": "ocsvm",
          "hotelling_t2": "hotelling", "isolation_forest": "isoforest", "ewma": "ewma",
          "three_sigma": "3sigma", "cusum": "cusum", "rms_trend": "rmstrend", "deep_svdd": "deepsvdd"}


def imslead_source():
    src = {}
    for r in vt.load("benchmark_IMS_leadtime_ci_invariant.csv"):
        if r["mode"] == "aggregate" and float(r["factor"]) == 1 and vt.key_of(r["method"]):
            src[vt.key_of(r["method"])] = r
    for r in vt.load("d3_ocsvm_leadtime_ci.csv"):
        if (r["dataset"] == "IMS" and r["mode"] == "aggregate" and float(r["factor"]) == 1
                and vt.key_of(r["method"]) == "ocsvm"):
            src["ocsvm"] = r
    return src


def tradeoff_source():
    src = {}
    for fn in ("tradeoff_IMS.csv", "tradeoff_IMS_deepmodels.csv", "d3_ocsvm_tradeoff.csv"):
        for r in vt.load(fn):
            k = vt.key_of(r["method"])
            if k and r.get("dataset", "IMS") == "IMS":
                src[(k, float(r["percentile"]))] = (float(r["lead_time_hours_mean"]),
                                                    float(r["far_preonset_pct_mean"]))
    return src


def tab_imsdet():
    d9 = sorted(vt.load("d9_tables_14_22_eleven.csv"), key=lambda r: int(r["PH_rank"]))
    lead, trade = imslead_source(), tradeoff_source()
    assert len(d9) == 11 and set(lead) == set(DET_ORDER), sorted(lead)
    rows = []
    for r in d9:
        k = D9_KEY[r["short_name"]]
        # derivation check: PH is the best raw lead over the three swept percentiles,
        # and L(tau) the best lead among percentiles whose mean FAR is within tau
        lds = [trade[(k, p)] for p in (95.0, 99.0, 99.5)]
        assert abs(float(r["PH_h"]) - max(ld for ld, _ in lds)) < 1e-9, k
        for col, tau in (("L_tau05_h", 5), ("L_tau10_h", 10), ("L_tau20_h", 20)):
            ok = [ld for ld, far in lds if far <= tau]
            assert abs(float(r[col]) - (max(ok) if ok else 0.0)) < 1e-9, (k, tau)
        valid10 = float(r["L_tau10_h"]) > 0
        name = NAME[k].replace("Transf.-AD", "Transformer-AD") + ("" if valid10 else r"$^\dagger$")
        if k == "rmstrend":
            name += r"$^\ast$"
        ld = lead[k]
        rows.append(r"%s & %.1f & [%.1f, %.1f] & %.1f & %.1f & %.1f & %.1f \\" % (
            name, float(ld["lead_time_hours_mean"]), float(ld["lead_time_hours_lo"]),
            float(ld["lead_time_hours_hi"]), float(r["PH_h"]), float(r["L_tau05_h"]),
            float(r["L_tau10_h"]), float(r["L_tau20_h"])))
    lorder = sorted((r for r in d9 if float(r["L_tau10_h"]) > 0), key=lambda r: int(r["L_rank"]))
    assert [D9_KEY[r["short_name"]] for r in lorder] == ["3sigma", "rmstrend", "deepsvdd"]
    assert int(next(r for r in d9 if r["short_name"] == "three_sigma")["PH_rank"]) == 8
    write("tab_imsdet", r"""
\begin{table}[t] \footnotesize
	\begin{center}
	\caption{IMS, all eleven detectors, in prognostic-horizon order (PH rank 1--11). Raw: mean ungated lead (h) at full resolution and the default 97.5th-percentile threshold, with 95\%% bootstrap CI over the $n=3$ runs. PH: Saxena prognostic horizon, the best raw lead over the 95th, 99th and 99.5th percentiles. $L_\tau$: best lead at an operating point whose pre-onset FAR, \emph{averaged across the three runs}, is within budget $\tau$ (0.0 = none), so a zero does not exclude a valid point on a single run. $^\dagger$: no valid operating point at $\tau=0.10$. Gated order at $\tau=0.10$: $3\sigma$, RMS-trend, Deep SVDD, then eight tied at 0. $^\ast$: valid only at the loosest threshold and on one of three runs.}
	\label{tab:imsdet}
	\setlength{\tabcolsep}{2pt}
	\begin{tabular}{l r c r r r r}
		\hline \hline
		\textbf{Detector} & \textbf{Raw} & \textbf{95\%% CI} & \textbf{PH} & $L_{0.05}$ & $L_{0.10}$ & $L_{0.20}$ \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\end{center}
\end{table}
""" % "\n".join("\t\t" + r for r in rows))


# ------------------------------------------------------------------ tab:tradeoff
TRADE_ORDER = ["3sigma", "ewma", "cusum", "hotelling", "isoforest", "deepsvdd", "rmstrend",
               "lstmae", "tcnae", "transformerad", "ocsvm"]
TRADE_NAME = dict(NAME, hotelling=r"Hot.\ $T^2$", isoforest=r"Iso.\ For.", ocsvm="OC-SVM")


def tab_tradeoff():
    src = tradeoff_source()
    rows = []
    for k in TRADE_ORDER:
        cells = []
        for p in (95.0, 99.0, 99.5):
            ld, far = src[(k, p)]
            cells += ["%.1f" % ld, "%.1f%s" % (far, r"$\dagger$" if far > 10 else "")]
        rows.append(r"%s & %s \\" % (TRADE_NAME[k], " & ".join(cells)))
    write("tab_tradeoff", r"""
\begin{table}[t] \small
	\setlength{\tabcolsep}{4pt}
	\begin{center}
	\caption{IMS lead-time--vs--false-alarm trade-off (mean across runs) at three threshold percentiles: lead (Ld, h) and pre-onset FAR (\%%). $\dagger$: pre-onset FAR above the $\tau=10\%%$ budget, so the operating point is invalid under the gated metric. The three deep reconstruction models and the one-class SVM are listed so the ``no valid operating point'' claim can be checked per threshold: all twelve of their entries are daggered.}
	\label{tab:tradeoff}
	\begin{tabular}{l r r r r r r}
		\hline \hline
		 & \multicolumn{2}{c}{\textbf{95th}} & \multicolumn{2}{c}{\textbf{99th}} & \multicolumn{2}{c}{\textbf{99.5th}} \\
		\textbf{Method} & Ld & FAR & Ld & FAR & Ld & FAR \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\end{center}
\end{table}
""" % "\n".join("\t\t" + r for r in rows))


# ------------------------------------------------------------------ tab:mechanism
DENOISE_ROWS = [("aggregate", "Aggregate (historian)"), ("decimate", "Decimate (raw)"),
                ("median", "Decimate + median"), ("moving", "Decimate + moving avg"),
                ("kalman", "Decimate + Kalman"), ("wavelet", "Decimate + wavelet")]
MAG = {"three_sigma", "ewma", "cusum", "hotelling_t2"}


def tab_mechanism():
    noise = []
    for r in vt.load("noise_snr_IMS_runlevel.csv"):
        label = "None (native)" if r["snr_db"] == "inf" else "%d dB" % float(r["snr_db"])
        noise.append(r"%s & %s & %s & %s/3 \\" % (label, m(r["run_diffs"]),
                                                   signed(float(r["mean_diff"]), 2), r["n_pos"]))
    rows = vt.load("denoising_IMS.csv")
    names = sorted({r["denoiser"] for r in rows})
    den = []
    for key, label in DENOISE_ROWS:
        match = [n for n in names if n == key] or [n for n in names if n.startswith(key)]
        assert len(match) == 1, (key, names)
        sub = [r for r in rows if r["denoiser"] == match[0] and r["short_name"] in MAG]
        assert len(sub) == 12, (key, len(sub))
        # published convention: mean lead over ALL twelve chart-runs, valid or not
        lead = statistics.mean(float(r["lead_time_hours"]) for r in sub)
        nvalid = sum(1 for r in sub if r["valid_alarm"] == "True")
        den.append(r"%s & %.1f & %d/12 \\" % (label, lead, nvalid))
    write("tab_mechanism", r"""
\begin{table}[t] \small
	\setlength{\tabcolsep}{4pt}
	\begin{center}
	\caption{IMS mechanism tests at sampling factor 5, the four magnitude SPC charts. (a) Noise injection: aggregate$-$decimate lead-time difference (h) collapsed to one mean per run (tests 1, 2, 3; $n=3$), its mean, and the runs with a positive sign. (b) Denoisers applied to the decimated stream: mean lead (h) over the twelve chart-runs (four charts $\times$ three runs) and the valid alarms among them, against raw aggregation and raw decimation.}
	\label{tab:mechanism}
	\textbf{(a) Noise injection}\\[2pt]
	\begin{tabular}{l l r c}
		\hline \hline
		\textbf{SNR} & \textbf{Per-run [t1, t2, t3]} & \textbf{Mean} & \textbf{Sign} \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\\[6pt]\textbf{(b) Denoisers}\\[2pt]
	\begin{tabular}{l r r}
		\hline \hline
		\textbf{Stream / denoiser} & \textbf{Mean lead} & \textbf{Valid} \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\end{center}
\end{table}
""" % ("\n".join("\t\t" + r for r in noise), "\n".join("\t\t" + r for r in den)))


# ------------------------------------------------------------------ tab:hyperparams
COMPUTE_ORDER = ["3sigma", "ewma", "cusum", "rmstrend", "hotelling", "ocsvm", "isoforest",
                 "deepsvdd", "lstmae", "tcnae", "transformerad"]


def fmt_train(sec: float) -> str:
    if sec < 0.001:
        return "$<1$ ms"
    if sec < 0.1:
        return "%d ms" % round(sec * 1000)
    if sec < 10:
        return "%.2f s" % sec
    return "%.1f s" % sec


def fmt_inf(us: float) -> str:
    return "%.1f" % us if us < 10 else "%d" % round(us)


def tab_hyperparams():
    src = {}
    for fn in ("compute_cost_IMS_invariant.csv", "compute_cost_IMS_extra_invariant.csv"):
        for r in vt.load(fn):
            k = vt.key_of(r["method"])
            assert (r["n_train_windows"], r["n_test_windows"], r["repeats"]) == ("631", "506", "5")
            src[k] = (fmt_train(float(r["train_seconds"])), fmt_inf(float(r["inference_us_per_window"])))
    assert set(src) == set(COMPUTE_ORDER), sorted(src)
    cells = [r"%s & %s & %s" % (NAME[k], *src[k]) for k in COMPUTE_ORDER]
    pairs = [cells[i:i + 2] for i in range(0, len(cells), 2)]
    rows = [(" & ".join(p) if len(p) == 2 else p[0] + " & & &") + r" \\" for p in pairs]
    static = (GEN / "hyperparams_static.tex").read_text(encoding="utf-8")
    write("tab_hyperparams", r"""
\begin{table}[t] \small
	\begin{center}
	\caption{(a) Fixed hyperparameter protocol, from \texttt{config.py}; onset tolerances are in samples of the health-indicator series, and the pre-onset FAR is measured over the full window $t < t_o$ (Eq.~\ref{eq:valid}). (b) Compute cost on the largest IMS run (631 train / 506 test windows, 49 features, one core of an Intel Core i5-13420H, median of five repeats): training time and inference in $\mu$s per window.}
	\label{tab:hyperparams}
	\textbf{(a) Protocol}\\[2pt]
%s
	\\[6pt]\textbf{(b) Compute}\\[2pt]
	\setlength{\tabcolsep}{3pt}
	\begin{tabular}{l r r | l r r}
		\hline \hline
		\textbf{Detector} & \textbf{Train} & \textbf{Inf.} & \textbf{Detector} & \textbf{Train} & \textbf{Inf.} \\
		\hline
%s
		\hline \hline
	\end{tabular}
	\end{center}
\end{table}
""" % (static.strip(), "\n".join("\t\t" + r for r in rows)))


# ------------------------------------------------------------------ conformal line
def conformal_line():
    rows = vt.load("calibration_IMS.csv")
    parts = []
    for run, lab in (("1st_test", "test 1"), ("2nd_test", "test 2"), ("3rd_test", "test 3")):
        v = {float(r["alpha"]): float(r["empirical_far"]) for r in rows if r["run"] == run}
        parts.append("%s %s" % (lab, ", ".join("%.2f" % v[a] for a in (0.01, 0.05, 0.10, 0.20))))
    # a macro, not raw text: it is used inside a \caption (a moving argument)
    write("conformal_values", r"\newcommand{\ConformalPanelA}{Panel (a) empirical FAR at "
          r"$\alpha = 0.01, 0.05, 0.10, 0.20$: %s.}" % "; ".join(parts))


def main():
    src = runlevel_sources()
    holm = holm_family_checks()
    tab_crossds(src, holm)
    tab_imsongc(src, holm)
    tab_gated()
    tab_imsdet()
    tab_tradeoff()
    tab_mechanism()
    tab_hyperparams()
    conformal_line()
    print("wrote", sorted(p.name for p in GEN.glob("*.tex")))


if __name__ == "__main__":
    main()
