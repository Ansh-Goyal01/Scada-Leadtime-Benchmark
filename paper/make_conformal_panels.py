# paper/make_conformal_panels.py
"""
Re-plot the four conformal-calibration panels for the manuscript.

Why this exists rather than calling src.calibration._plot_calibration: that function
draws an in-plot title, which RD-11..RD-14 removed from every manuscript figure (the
LaTeX caption carries it), and it pins the legend to "upper left", where it sits on top
of the shaded +/-1 std band in the XJTU-SY and FEMTO panels (audit item D16). This
re-plots from the saved calibration CSVs with no title and the legend in the lower-right
corner, which is empty in all four panels because every curve lies above the diagonal.

No detectors are re-run: the calibration CSVs written by src.calibration are the input.
Panel geometry (885x734 px at 150 dpi) matches the figures it replaces, so
paper/make_panels.py composes the same 2x2 grid.

    python paper/make_conformal_panels.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TAB = os.path.join(ROOT, "results", "tables")
FILES = os.path.join(ROOT, "paper", "files")

PANELS = [("IMS", "fig_conf_ims.png"),
          ("XJTU-SY", "fig_conf_xjtu.png"),
          ("FEMTO", "fig_conf_femto.png"),
          ("ONGC", "fig_conf_ongc.png")]


def panel(dataset, out_name):
    long_p = os.path.join(TAB, f"calibration_{dataset}.csv")
    pooled_p = os.path.join(TAB, f"calibration_{dataset}_pooled.csv")
    if not (os.path.exists(long_p) and os.path.exists(pooled_p)):
        print(f"skip {out_name}: missing calibration_{dataset}[_pooled].csv")
        return
    long, pooled = pd.read_csv(long_p), pd.read_csv(pooled_p)

    fig, ax = plt.subplots(figsize=(5.9, 4.89))
    amax = float(pooled["alpha"].max())
    ax.plot([0, amax], [0, amax], "k--", linewidth=1.2, label="Perfect calibration")

    for _, sub in long.groupby("run"):
        sub = sub.sort_values("alpha")
        ax.plot(sub["alpha"], sub["empirical_far"], "-", alpha=0.35,
                linewidth=1.0, color="#90A4AE")

    m = pooled.sort_values("alpha")
    ax.plot(m["alpha"], m["empirical_far_mean"], "o-", color="#1976D2",
            linewidth=2, markersize=7, label="Conformal IF (mean across runs)")
    if m["empirical_far_std"].notna().any():
        lo = (m["empirical_far_mean"] - m["empirical_far_std"]).clip(lower=0)
        hi = m["empirical_far_mean"] + m["empirical_far_std"]
        ax.fill_between(m["alpha"], lo, hi, alpha=0.15, color="#1976D2")

    ax.set_xlabel("Target FAR (α)", fontsize=11)
    ax.set_ylabel("Empirical FAR on pre-onset normal data", fontsize=11)
    # No in-plot title (RD-11..RD-14). Legend lower-right: every curve lies above the
    # diagonal, so that corner is the one region guaranteed clear of data and band.
    ax.legend(fontsize=9, loc="lower right", framealpha=0.95)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FILES, out_name)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out_name)


if __name__ == "__main__":
    for ds, nm in PANELS:
        panel(ds, nm)
