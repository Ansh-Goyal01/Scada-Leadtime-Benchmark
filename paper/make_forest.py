"""Forest plot of the central result (Phase 2 of the shortening plan; replaces the
cross-dataset bar chart, label fig:crossdataset).

x: run-level aggregate - decimate lead-time difference (h); y: detector.
Panels: IMS | XJTU-SY | FEMTO | Ferrara | ONGC.
  XJTU-SY / FEMTO / Ferrara : mean and 95% bootstrap CI over runs (printed in tab:crossds)
  IMS                       : the three per-run differences and their median
                              (printed in tab:imsongc; IMS bootstrap CIs are not printed
                              anywhere, so by constraint 4 they are not drawn)
  ONGC                      : n=1 descriptive median, hollow markers (tab:imsongc, minutes)
Shaded band: the +-1 h equivalence margin. Sources are the same post-N-20 files as the
tables (make_shortened_tables.py). Output: paper/files/fig_forest.pdf (vector text).

    python paper/make_forest.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import logging
import matplotlib
matplotlib.use("Agg")
logging.getLogger("fontTools").setLevel(logging.WARNING)   # silence font-subsetting chatter
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import make_shortened_tables as mst  # noqa: E402
import verify_tables as vt  # noqa: E402
from src.config import PLOT  # noqa: E402

OUT = HERE / "files" / "fig_forest.pdf"
ORDER = mst.DET_ORDER
SHORT = {"3sigma": "three_sigma", "ewma": "ewma", "cusum": "cusum", "hotelling": "hotelling_t2",
         "isoforest": "isolation_forest", "deepsvdd": "deep_svdd", "ocsvm": "one_class_svm",
         "lstmae": "lstm_ae", "tcnae": "tcn", "transformerad": "transformer_ad", "rmstrend": "rms_trend"}
LABEL = {"3sigma": r"$3\sigma$", "ewma": "EWMA", "cusum": "CUSUM", "hotelling": r"Hotelling $T^2$",
         "isoforest": "Iso. Forest", "deepsvdd": "Deep SVDD", "ocsvm": "One-class SVM",
         "lstmae": "LSTM-AE", "tcnae": "TCN-AE", "transformerad": "Transformer-AD",
         "rmstrend": "RMS-trend"}


def colour(k):
    # config.PLOT["method_colors"] has no one-class SVM entry; black, set here explicitly
    # rather than letting matplotlib's default cycle collide with another detector (N-25).
    return PLOT["method_colors"].get(SHORT[k], "#000000")


def main():
    src = mst.runlevel_sources()
    eq = vt.index(vt.load("n20_d15_bootstrap_new_11det.csv"), ds_field="dataset")
    ongc = {r["short_name"]: float(r[vt.ONGC_MINUTES_COL]) for r in vt.load(vt.ONGC_MINUTES)}
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "font.family": "serif",
                         "mathtext.fontset": "cm", "pdf.fonttype": 42, "axes.linewidth": 0.6,
                         "xtick.major.width": 0.6, "ytick.major.width": 0.6})
    panels = [("IMS", "IMS ($n=3$)", (-10, 85)), ("XJTU-SY", "XJTU-SY ($n=10$)", (-1.15, 1.15)),
              ("FEMTO", "FEMTO ($n=6$)", (-1.15, 1.15)), ("Ferrara", "Ferrara ($n=6$)", (-1.15, 1.15)),
              ("ONGC", "ONGC ($n=1$)", (-1.15, 1.15))]
    fig, axes = plt.subplots(1, 5, figsize=(7.0, 2.25), sharey=True,
                             gridspec_kw=dict(width_ratios=[1.35, 1, 1, 1, 1], wspace=0.08))
    y = {k: len(ORDER) - 1 - i for i, k in enumerate(ORDER)}
    for ax, (ds, title, xlim) in zip(axes, panels):
        ax.axvspan(-1, 1, color="#DDDDDD", zorder=0, lw=0)
        ax.axvline(0, color="#555555", lw=0.6, zorder=1)
        for k in ORDER:
            c, yy = colour(k), y[k]
            if ds == "IMS":
                runs = [float(v) for v in src[("IMS", k)]["run_diffs"].replace("+", "").split(",")]
                ax.plot([min(runs), max(runs)], [yy, yy], color=c, lw=0.8, zorder=2)
                ax.scatter(runs, [yy] * 3, s=7, color=c, zorder=3, lw=0)
                ax.scatter([src[("IMS", k)]["median"]], [yy], marker="D", s=16, color=c,
                           edgecolor="white", lw=0.4, zorder=4)
            elif ds == "ONGC":
                ax.scatter([ongc[SHORT[k]] / 60.0], [yy], s=16, facecolor="white", edgecolor=c,
                           lw=0.9, zorder=3)
            else:
                e = eq[(ds, k)]
                lo, hi, mu = float(e["ci_lo_h"]), float(e["ci_hi_h"]), float(e["mean_diff_h"])
                ax.plot([lo, hi], [yy, yy], color=c, lw=1.1, zorder=2, solid_capstyle="butt")
                ax.scatter([mu], [yy], s=14, color=c, zorder=3, lw=0)
        ax.set_xlim(*xlim)
        ax.set_title(title, pad=3)
        ax.tick_params(axis="y", length=0)
        ax.grid(False)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_yticks([y[k] for k in ORDER])
    axes[0].set_yticklabels([LABEL[k] for k in ORDER])
    axes[0].set_ylim(-0.7, len(ORDER) - 0.3)
    fig.supxlabel("Run-level aggregate $-$ decimate lead-time difference (h); shaded: $\\pm 1$ h margin",
                  fontsize=7, y=0.02)
    fig.subplots_adjust(left=0.13, right=0.995, top=0.90, bottom=0.2)
    fig.savefig(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
