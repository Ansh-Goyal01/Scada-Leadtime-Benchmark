# paper/make_tradeoff_panels.py
"""
Re-plot the lead-time vs pre-onset-FAR trade-off panels for the manuscript.

Why this exists rather than calling src.tradeoff._plot_tradeoff: that function draws an
in-plot title, which RD-11..RD-14 removed from every manuscript figure (the LaTeX caption
carries the title -- IJPHM house style). The previous panels were produced by pixel-cropping
the title off the rendered PNG, which is fragile and had to be redone whenever the data
changed. This re-plots from the saved aggregate CSVs with no title at all, so no crop is
needed. Detector colours come from src.config.PLOT["method_colors"], the single source of
truth; five detectors used to be unassigned there and fell through to matplotlib's default
cycle, colliding with 3-sigma / Hotelling / EWMA.

No detectors are re-run: the aggregate CSVs written by src.tradeoff are the input.

    python paper/make_tradeoff_panels.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.config import PLOT   # noqa: E402

TAB = os.path.join(ROOT, "results", "tables")
FILES = os.path.join(ROOT, "paper", "files")


def panel(csv_names, out_name):
    """Plot one trade-off panel from one or more aggregate CSVs."""
    frames = []
    for n in csv_names:
        p = os.path.join(TAB, f"{n}.csv")
        if not os.path.exists(p):
            print(f"skip {out_name}: missing {n}.csv")
            return
        frames.append(pd.read_csv(p))
    agg = pd.concat(frames, ignore_index=True)

    colors = PLOT["method_colors"]
    missing = sorted(set(agg.short_name.unique()) - set(colors))
    if missing:
        raise SystemExit(f"{out_name}: no colour assigned for {missing} -- these would "
                         f"fall through to matplotlib's default cycle and collide.")

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for sn, sub in agg.groupby("short_name"):
        sub = sub.sort_values("far_preonset_pct_mean")
        color = colors[sn]
        ax.plot(sub["far_preonset_pct_mean"], sub["lead_time_hours_mean"],
                "o-", color=color, linewidth=1.8, markersize=6,
                label=sub["method"].iloc[0], zorder=3)
        for _, row in sub.iterrows():
            ax.annotate(f"{row['percentile']:g}",
                        (row["far_preonset_pct_mean"], row["lead_time_hours_mean"]),
                        textcoords="offset points", xytext=(5, 4), fontsize=7,
                        color=color)

    ax.axvline(10.0, color="#FF9800", linewidth=1.5, linestyle=":",
               label="10% FAR budget")
    ax.set_xlabel("Pre-onset False Alarm Rate (%)  — lower is better", fontsize=11)
    ax.set_ylabel("Detection Lead Time (hours)  — higher is better", fontsize=11)
    # No in-plot title: the LaTeX caption carries it (RD-11..RD-14).
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FILES, out_name)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_name, f"({len(agg.short_name.unique())} detectors)")


if __name__ == "__main__":
    panel(["tradeoff_IMS"], "fig_tradeoff_ims.png")
    panel(["tradeoff_XJTU-SY"], "fig_tradeoff_xjtu.png")
