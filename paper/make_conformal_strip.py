"""Conformal calibration as a 1x4 print-sized strip (Phase 5 height discipline; replaces the
2x2 raster composite fig_conformal_panels.png, which occupied 0.70 of a page).

Same data and encodings as paper/make_conformal_panels.py -- the calibration CSVs written
by src.calibration (FEMTO/ONGC files are N-20-invariant: calibration never resamples; see
verify_tables.check_calibration_invariance): diagonal = perfect calibration, grey = one line
per run/bearing, blue = mean across runs with a +-1 std band. Drawn at print size
(7.0 x 1.95 in, 7 pt text) as vector PDF so it stays legible when set at \\textwidth.

    python paper/make_conformal_strip.py
"""
import logging
import os

import matplotlib
matplotlib.use("Agg")
logging.getLogger("fontTools").setLevel(logging.WARNING)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(ROOT, "results", "tables")
OUT = os.path.join(ROOT, "paper", "files", "fig_conformal_strip.pdf")
PANELS = [("IMS", "(a) IMS"), ("XJTU-SY", "(b) XJTU-SY"),
          ("FEMTO", "(c) FEMTO/PRONOSTIA"), ("ONGC", "(d) ONGC ($n=1$)")]


def main():
    plt.rcParams.update({"font.size": 7, "font.family": "serif", "mathtext.fontset": "cm",
                         "pdf.fonttype": 42, "axes.linewidth": 0.6})
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 1.95))
    for ax, (ds, title) in zip(axes, PANELS):
        long = pd.read_csv(os.path.join(TAB, "calibration_%s.csv" % ds))
        pooled = pd.read_csv(os.path.join(TAB, "calibration_%s_pooled.csv" % ds)).sort_values("alpha")
        amax = float(pooled["alpha"].max())
        ax.plot([0, amax], [0, amax], "k--", lw=0.9, label="Perfect calibration")
        for _, sub in long.groupby("run"):
            sub = sub.sort_values("alpha")
            ax.plot(sub["alpha"], sub["empirical_far"], "-", alpha=0.45, lw=0.7, color="#90A4AE")
        ax.plot(pooled["alpha"], pooled["empirical_far_mean"], "o-", color="#1976D2", lw=1.3,
                ms=3, label="Mean across runs")
        if pooled["empirical_far_std"].notna().any():
            lo = (pooled["empirical_far_mean"] - pooled["empirical_far_std"]).clip(lower=0)
            hi = pooled["empirical_far_mean"] + pooled["empirical_far_std"]
            ax.fill_between(pooled["alpha"], lo, hi, alpha=0.15, color="#1976D2", lw=0)
        ax.set_title(title, pad=3)
        ax.set_xlabel(r"Target FAR ($\alpha$)")
        ax.grid(True, alpha=0.3, lw=0.4)
        ax.tick_params(length=2, pad=1.5)
    axes[0].set_ylabel("Empirical pre-onset FAR")
    axes[3].legend(fontsize=6, loc="lower right", framealpha=0.95, handlelength=1.6)
    fig.tight_layout(pad=0.3, w_pad=0.6)
    fig.savefig(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
