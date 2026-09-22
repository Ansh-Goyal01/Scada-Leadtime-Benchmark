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
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.config import PLOT   # noqa: E402

TAB = os.path.join(ROOT, "results", "tables")
FILES = os.path.join(ROOT, "paper", "files")

# The operating points named in the text and tabulated in Table 12. Only these
# are annotated in the trade-off panels (D16); the full sweep is still plotted.
LABELLED_PERCENTILES = {95.0, 99.0, 99.5}

# Offsets tried, in order, when a label would collide with one already placed
# or with the legend. Points, matching annotate(textcoords="offset points").
_OFFSETS = [(5, 4), (5, -11), (-20, 4), (-20, -11), (5, 14), (5, -21),
            (-22, 14), (-22, -21), (14, 22), (14, -29)]


def _overlaps(a, b, pad=1.0):
    return not (a.x1 + pad < b.x0 or b.x1 + pad < a.x0
                or a.y1 + pad < b.y0 or b.y1 + pad < a.y0)


def _place_labels(fig, ax, leg, pending):
    """Draw percentile labels, nudging each one until it clears the others.

    Subsetting to three percentiles removed most of the stacking, but points
    from different detectors still coincide. This does a greedy pass: the
    first offset that collides with nothing already placed wins; if every
    candidate collides the label is dropped rather than printed illegibly.

    The offsets only resolve label-vs-label and label-vs-legend collisions.
    They cannot resolve label-vs-curve: in the dense IMS elbow every candidate
    offset still lands on some detector's line, and although the label is drawn
    above the line (zorder 5 vs 3), an unhaloed digit sitting on a 1.8 pt
    coloured line is not readable at the 7 in printed width. Each label is
    therefore stroked with a white outline, which clears a band around the
    glyphs without hiding the curve.
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    taken = [leg.get_window_extent(rend)] if leg is not None else []
    dropped = 0
    # densest regions first, so crowded areas get the good offsets
    for x, y, text, color in sorted(pending, key=lambda t: (-t[1], t[0])):
        for off in _OFFSETS:
            ann = ax.annotate(text, (x, y), textcoords="offset points",
                              xytext=off, fontsize=7, color=color, zorder=5,
                              path_effects=[pe.withStroke(linewidth=2.2,
                                                          foreground="white")])
            bb = ann.get_window_extent(rend)
            if not any(_overlaps(bb, t) for t in taken):
                taken.append(bb)
                break
            ann.remove()
        else:
            dropped += 1
    if dropped:
        print(f"   note: {dropped} percentile label(s) dropped as uncleanly placeable")


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
    pending = []          # (x, y, text, colour) label requests, placed below
    for sn, sub in agg.groupby("short_name"):
        sub = sub.sort_values("far_preonset_pct_mean")
        color = colors[sn]
        ax.plot(sub["far_preonset_pct_mean"], sub["lead_time_hours_mean"],
                "o-", color=color, linewidth=1.8, markersize=6,
                label=sub["method"].iloc[0], zorder=3)
        # D16 audit: annotating all seven swept percentiles stacked the labels
        # into unreadable blobs wherever the curve turns. Label only the three
        # operating points the text and Table 12 actually discuss; the other
        # sweep points are still plotted as markers, just not named.
        for _, row in sub.iterrows():
            if float(row["percentile"]) not in LABELLED_PERCENTILES:
                continue
            pending.append((row["far_preonset_pct_mean"],
                            row["lead_time_hours_mean"],
                            f"{row['percentile']:g}", color))

    ax.axvline(10.0, color="#FF9800", linewidth=1.5, linestyle=":",
               label="10% FAR budget")
    ax.set_xlabel("Pre-onset False Alarm Rate (%)  — lower is better", fontsize=11)
    ax.set_ylabel("Detection Lead Time (hours)  — higher is better", fontsize=11)
    # No in-plot title: the LaTeX caption carries it (RD-11..RD-14).
    leg = ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _place_labels(fig, ax, leg, pending)
    out = os.path.join(FILES, out_name)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_name, f"({len(agg.short_name.unique())} detectors)")


if __name__ == "__main__":
    panel(["tradeoff_IMS"], "fig_tradeoff_ims.png")
    panel(["tradeoff_XJTU-SY"], "fig_tradeoff_xjtu.png")
