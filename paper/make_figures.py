# paper/make_figures.py
"""
Generate the figures for the ICSC paper into paper/figs/, plus copy the trade-off and
calibration figures already produced by the analysis CLIs. Run from repo root:

    python paper/make_figures.py
"""
import os
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(ROOT, "paper", "figs")
TAB = os.path.join(ROOT, "results", "tables")
RFIG = os.path.join(ROOT, "results", "figures")
os.makedirs(FIGS, exist_ok=True)

# Single source of truth for detector colours: src.config.PLOT["method_colors"],
# keyed by short_name. This module previously kept its own five-entry table keyed by
# the long display name, which (a) left the other five detectors to matplotlib's
# default cycle -- duplicating 3-sigma / Hotelling / EWMA -- and (b) painted
# RMS-Trend "#9C27B0", which is LSTM-AE's canonical colour. Resolve by short_name.
from src.config import PLOT as _PLOT

METHOD_COLORS = dict(_PLOT["method_colors"])


def _color_for(short_name):
    """Canonical colour for a detector. Returns None only for a genuinely unknown
    short_name, which is loud in review rather than silently recycled."""
    return METHOD_COLORS.get(short_name)


def fig_rms_degradation():
    """Fig 1: mean-RMS health indicator on IMS 2nd_test with onset + failure markers."""
    import sys
    sys.path.insert(0, ROOT)
    from src import load_pipeline
    from src.onset import health_indicator, onset_for_run
    import pandas as pd

    pipe = load_pipeline("2nd_test", dataset="IMS")
    df = pipe["df_full"]
    hi = health_indicator(df, kind="rms_mean")
    n = len(df)
    train_end = df.index[min(int(n * pipe["train_fraction"]), n - 1)]
    t_fail = pd.Timestamp(pipe["failure_time"])
    onset = onset_for_run(df, train_end=train_end, t_fail=t_fail)

    fig, ax = plt.subplots(figsize=(7, 3.1))
    ax.plot(hi.index, hi.values, color="#1565C0", linewidth=1.0, label="mean RMS")
    ax.axvspan(hi.index[0], train_end, alpha=0.08, color="green")
    ax.axvline(train_end, color="green", linestyle=":", linewidth=1.2, label="train boundary")
    if onset is not None:
        ax.axvline(onset, color="#FB8C00", linestyle="--", linewidth=1.6, label="degradation onset")
    ax.axvline(t_fail, color="#B71C1C", linestyle="-", linewidth=1.8, label="failure")
    ax.set_xlabel("Time")
    ax.set_ylabel("Health indicator $h(t)$ (mean RMS)")
    # No in-plot title (D13/D16): the LaTeX caption carries it - IJPHM house style.
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    plt.tight_layout()
    out = os.path.join(FIGS, "fig_rms_degradation.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_leadtime_vs_sampling():
    """Fig 2: lead time vs effective SCADA logging interval, aggregate vs decimate (IMS)."""
    # D-2: IMS is re-baselined onto the 49-dim invariant schema (legacy file kept for the letter).
    long = pd.read_csv(os.path.join(TAB, "benchmark_IMS_long_invariant.csv"))
    # mean across runs per (mode, factor, method)
    g = (long.groupby(["mode", "factor", "effective_interval_min",
                       "method", "short_name"])
         ["lead_time_hours"].mean().reset_index())
    modes = ["aggregate", "decimate"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
    for ax, mode in zip(axes, modes):
        sub = g[g["mode"] == mode]
        for (m, sn), ms in sub.groupby(["method", "short_name"]):
            ms = ms.sort_values("effective_interval_min")
            ax.plot(ms["effective_interval_min"], ms["lead_time_hours"],
                    "o-", markersize=4, linewidth=1.5,
                    color=_color_for(sn), label=m)
        ax.set_xscale("log")
        ax.set_xlabel("Effective logging interval (min)")
        ax.set_title(mode.capitalize(), fontsize=10, fontweight="bold")
        ax.grid(alpha=0.3, which="both")
    axes[0].set_ylabel("Detection lead time (h)")
    # Legend outside the axes: loc="best" landed it on the Decimate panel's data
    # and hid several detector lines.
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, fontsize=6.5, loc="center left",
               bbox_to_anchor=(1.005, 0.5), frameon=True, borderaxespad=0.0)
    # No in-plot suptitle (D13/D16): the caption carries it. Panel titles
    # ("Aggregate"/"Decimate") stay - they label the panels, not the figure.
    plt.tight_layout()
    out = os.path.join(FIGS, "fig_leadtime_vs_sampling.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_crossdataset():
    """Fig 5: median run-level lead-time difference (aggregate - decimate) per
    dataset x method, annotated with the unit of inference per dataset. No
    significance stars: after honoring run structure and Holm correction nothing
    is significant (see paper Sec. Multiple-comparison correction); the bars are
    trend magnitudes. IMS/XJTU come from the run-level tables; ONGC is the n=1
    descriptive case study from its Wilcoxon CSV (median diff only)."""
    runlevel = {}
    for ds, fname in [("IMS", "ims_runlevel_test_invariant.csv"),  # D-2
                      ("XJTU-SY", "xjtu_sy_runlevel_test.csv"),
                      ("FEMTO", "femto_runlevel_test_n20.csv"),  # N-20 post-fix
                      ("Ferrara", "ferrara_runlevel_test_n20.csv")]:  # N-20 post-fix
        p = os.path.join(TAB, fname)
        if os.path.exists(p):
            runlevel[ds] = pd.read_csv(p)
    # ONGC: single-asset case study — take the descriptive median diff (already in hours)
    ongc = None
    p_ongc = os.path.join(TAB, "benchmark_ONGC_paired_test_n20.csv")  # N-20 post-fix
    if os.path.exists(p_ongc):
        ongc = pd.read_csv(p_ongc)

    methods = ["3σ Rule (σ=3.0)", "EWMA (λ=0.2, k=3.0)", "CUSUM (k=0.5, h=5.0)",
               "Hotelling T²", "Isolation Forest", "Deep SVDD", "RMS-Trend (kσ)"]
    # Display labels use mathtext, not literal Greek/superscript characters: the
    # literals were emitted as UTF-8 and re-read as cp1252, which is what produced
    # the "3ĺf" / "Hot. TÂ²" mojibake (RD-11..RD-14). Mathtext removes the
    # encoding dependency entirely. The dict KEYS are data keys matching the
    # method column of the benchmark CSVs — do not touch them.
    short = {"3σ Rule (σ=3.0)": r"$3\sigma$", "EWMA (λ=0.2, k=3.0)": "EWMA",
             "CUSUM (k=0.5, h=5.0)": "CUSUM", "Hotelling T²": r"Hot. $T^2$",
             "Isolation Forest": "IsoForest", "Deep SVDD": "D.SVDD",
             "RMS-Trend (kσ)": "RMS-trend"}
    datasets = ["IMS", "ONGC", "XJTU-SY", "FEMTO", "Ferrara"]
    n_label = {"IMS": "n=3", "ONGC": "n=1, case study", "XJTU-SY": "n=10",
               "FEMTO": "n=6", "Ferrara": "n=6"}
    colors = {"IMS": "#E91E63", "ONGC": "#1565C0", "XJTU-SY": "#2E7D32",
              "FEMTO": "#F57F17", "Ferrara": "#6A1B9A"}

    def median_diff(ds, m):
        if ds == "ONGC":
            if ongc is None:
                return 0.0
            r = ongc[ongc.method == m]
            # The paired CSV is in HOURS (lead_time_hours); the former /60 drew ONGC 60x too small.
            return float(r["median_diff_agg_minus_dec"].iloc[0]) if len(r) else 0.0
        tbl = runlevel.get(ds)
        if tbl is None:
            return 0.0
        r = tbl[tbl.method == m]
        return float(r["median_diff"].iloc[0]) if len(r) else 0.0

    x = np.arange(len(methods))
    w = 0.16
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    n_ds = len(datasets)
    for i, ds in enumerate(datasets):
        vals = [median_diff(ds, m) for m in methods]
        # ONGC is the n=1 descriptive case study — hatch its bars so they are
        # visually distinct from the inferential datasets (IMS/XJTU/FEMTO).
        hatch = "//" if ds == "ONGC" else None
        ax.bar(x + (i - (n_ds - 1) / 2) * w, vals, w,
               label=f"{ds} ({n_label[ds]})", color=colors[ds],
               hatch=hatch, edgecolor="white" if hatch else "none", linewidth=0.0)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([short[m] for m in methods], fontsize=8)
    ax.set_ylabel("Median run-level lead-time $\\Delta$\n"
                  "(aggregate $-$ decimate), h")
    # No in-plot title: the LaTeX caption carries the description, and an in-plot
    # title can drift out of sync with it (same reason the mintrain title went).
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    out = os.path.join(FIGS, "fig_crossdataset.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_training_sweep():
    """Fig 8: valid-alarm fraction vs training fraction on FEMTO (n=6), one line per
    detector colored by family, with the SPC-chart baseline drawn as a dashed
    reference. There is no crossover: the deep models never reach the SPC baseline."""
    path = os.path.join(TAB, "femto_training_sweep.csv")
    if not os.path.exists(path):
        print("skip fig_training_sweep — run `python -m src.training_sweep` first")
        return
    df = pd.read_csv(path)

    # Detector families → colors. SPC/magnitude charts one hue, IF/SVDD another,
    # deep reconstruction a third (matches the paper's family framing).
    families = {
        "three_sigma": ("SPC", "#1565C0"), "ewma": ("SPC", "#1E88E5"),
        "cusum": ("SPC", "#42A5F5"), "hotelling_t2": ("SPC", "#90CAF9"),
        "isolation_forest": ("tree/one-class", "#2E7D32"),
        "deep_svdd": ("tree/one-class", "#66BB6A"),
        "lstm_ae": ("deep recon.", "#C62828"), "tcn": ("deep recon.", "#EF5350"),
        "transformer_ad": ("deep recon.", "#FF8A80"),
    }
    # Mathtext, not literal Greek/superscripts — see the note in fig_crossdataset.
    labels = {"three_sigma": r"$3\sigma$", "ewma": "EWMA", "cusum": "CUSUM",
              "hotelling_t2": r"Hot. $T^2$", "isolation_forest": "IsoForest",
              "deep_svdd": "Deep SVDD", "lstm_ae": "LSTM-AE", "tcn": "TCN-AE",
              "transformer_ad": "Transformer-AD"}

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    for sn, (fam, color) in families.items():
        sub = df[df.short_name == sn].sort_values("train_fraction")
        if sub.empty:
            continue
        ls = {"SPC": "-", "tree/one-class": "--", "deep recon.": ":"}[fam]
        ax.plot(sub["train_fraction"], sub["valid_frac"], marker="o", markersize=4,
                linewidth=1.6, linestyle=ls, color=color, label=labels[sn])

    # SPC-chart baseline = mean valid fraction over the four SPC charts, drawn as a
    # horizontal dashed reference the deep models are compared against.
    spc = df[df.short_name.isin(["three_sigma", "ewma", "cusum", "hotelling_t2"])]
    if not spc.empty:
        base = float(spc["valid_frac"].mean())
        ax.axhline(base, color="#1565C0", linestyle="--", linewidth=1.0, alpha=0.6)
        # Below the dashed baseline: at base+0.02 the label sat on the EWMA line
        # (0.667). The 0.50-0.62 band is clear at T=0.20 (D16).
        ax.text(0.205, base - 0.062, "SPC baseline $\\approx$ %.2f" % base,
                fontsize=7, color="#1565C0")
    ax.text(0.50, 0.06, "no crossover: deep models never reach the SPC baseline",
            fontsize=7.5, style="italic", ha="center", color="#555555")

    ax.set_xlabel("Training fraction $T$")
    ax.set_ylabel("Valid-alarm fraction ($n{=}6$ bearings)")
    ax.set_xlim(0.18, 0.62)
    ax.set_ylim(-0.02, 1.0)
    ax.set_xticks([0.2, 0.3, 0.4, 0.5, 0.6])
    # No in-plot title (RD-11..RD-14): the old title asserted the deep models
    # "match SPC charts", which the LaTeX caption correctly denies — there is no
    # crossover. The caption carries the title; that is IJPHM house style.
    ax.legend(fontsize=6.5, ncol=3, loc="upper right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIGS, "fig_training_sweep.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def copy_existing():
    for src_name, dst_name in [
        ("tradeoff_far_vlt_IMS.png", "fig_tradeoff.png"),
        ("calibration_curve_IMS.png", "fig_calibration.png"),
    ]:
        s = os.path.join(RFIG, src_name)
        if os.path.exists(s):
            shutil.copy(s, os.path.join(FIGS, dst_name))
            print("copied", dst_name)


if __name__ == "__main__":
    fig_rms_degradation()
    fig_leadtime_vs_sampling()
    fig_crossdataset()
    fig_training_sweep()
    copy_existing()
    print("Figures in", FIGS)
