# paper/make_print_figures.py
"""
Re-plot Figure 3 (IMS sampling sweep) and Figure 5 (trade-off panels) at their printed size.

The previous versions were rasters drawn at a larger canvas and scaled down by LaTeX:
fig_sweep.png (make_figures.fig_leadtime_vs_sampling, 8.6 x 3.1 in) and
fig_tradeoff_panels.png (two 8 x 5.5 in panels tiled by make_panels.py), so an 8 pt legend
printed at roughly 3.5 pt. Here each figure is drawn at the full 7.0 in text width of the
IJPHM template and saved as vector PDF, so the fonts print at the size set below.

Same data, same aggregation, same colours (src.config.PLOT["method_colors"]); no detector
is re-run. Figure 3 additionally shades the few-windows regime at the largest factors, which
the text says is annotated rather than hidden.

    python paper/make_print_figures.py
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
sys.path.insert(0, os.path.join(ROOT, "paper"))
from src.config import PLOT                                            # noqa: E402
from make_tradeoff_panels import LABELLED_PERCENTILES, _overlaps      # noqa: E402

TAB = os.path.join(ROOT, "results", "tables")
FILES = os.path.join(ROOT, "paper", "files")
TEXT_WIDTH_IN = 7.0          # \textwidth in the IJPHM class
FONT_PT = 7.5
FEW_WINDOWS_FROM_MIN = 1000  # factors at which only one or two IMS runs keep enough windows
COLORS = PLOT["method_colors"]

plt.rcParams.update({"font.size": FONT_PT, "axes.labelsize": FONT_PT, "axes.titlesize": FONT_PT + 0.5,
                     "xtick.labelsize": FONT_PT - 0.5, "ytick.labelsize": FONT_PT - 0.5,
                     "legend.fontsize": FONT_PT - 1, "pdf.fonttype": 42})


def _need_colours(names, what):
    missing = sorted(set(names) - set(COLORS))
    if missing:
        raise SystemExit(f"{what}: no colour assigned for {missing}")


def fig_sweep():
    """Figure 3: IMS lead time vs effective logging interval, aggregate and decimate."""
    long = pd.read_csv(os.path.join(TAB, "benchmark_IMS_long_invariant.csv"))
    g = (long.groupby(["mode", "factor", "effective_interval_min", "method", "short_name"])
         ["lead_time_hours"].mean().reset_index())
    _need_colours(g.short_name.unique(), "fig_sweep")
    fig, axes = plt.subplots(1, 2, figsize=(TEXT_WIDTH_IN, 2.05), sharey=True)
    xmax = g.effective_interval_min.max()
    for ax, mode in zip(axes, ["aggregate", "decimate"]):
        for (m, sn), ms in g[g["mode"] == mode].groupby(["method", "short_name"]):
            ms = ms.sort_values("effective_interval_min")
            ax.plot(ms.effective_interval_min, ms.lead_time_hours, "o-", ms=2.6, lw=1.1,
                    color=COLORS[sn], label=m)
        ax.axvspan(FEW_WINDOWS_FROM_MIN * 0.93, xmax * 1.12, color="0.88", zorder=0, lw=0)
        ax.text(FEW_WINDOWS_FROM_MIN * 1.04, 0.97, "few\nwindows", transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=FONT_PT - 1.5, color="0.35")
        ax.set_xscale("log")
        ax.set_xlabel("Effective logging interval (min)")
        ax.set_title(mode.capitalize(), fontweight="bold", pad=3)
        ax.grid(alpha=0.3, which="both", lw=0.4)
    axes[0].set_ylabel("Detection lead time (h)")
    h, lbl = axes[0].get_legend_handles_labels()
    fig.legend(h, lbl, loc="center left", bbox_to_anchor=(0.795, 0.5), frameon=True,
               handlelength=1.6, borderaxespad=0.0)
    fig.tight_layout(pad=0.3, w_pad=0.6, rect=(0, 0, 0.79, 1))
    out = os.path.join(FILES, "fig_sweep.pdf")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)


# (dx, dy) in points with the matching text alignment; kept small so every label stays
# visibly attached to its marker at print size (make_tradeoff_panels' offsets reach 29 pt).
_NEAR = [(3, 2, "left", "bottom"), (3, -2, "left", "top"), (-3, 2, "right", "bottom"),
         (-3, -2, "right", "top"), (0, 4, "center", "bottom"), (0, -4, "center", "top"),
         (6, 7, "left", "bottom"), (6, -7, "left", "top"), (-6, 7, "right", "bottom"),
         (-6, -7, "right", "top")]


def _place_near(fig, ax, pending):
    """Label operating points next to their markers, inside the axes, clear of other markers
    and labels. Percentiles that land on the same point of one detector share one label."""
    merged = {}
    for x, y, text, color in pending:
        merged.setdefault((color, round(x, 6), round(y, 6)), []).append(text)
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    box = ax.get_window_extent(rend)
    pts = [ax.transData.transform((x, y)) for (_, x, y) in merged]
    taken, dropped = [], []
    for (color, x, y), texts in sorted(merged.items(), key=lambda kv: (-kv[0][2], kv[0][1])):
        me = ax.transData.transform((x, y))
        text = "/".join(sorted(texts, key=float))
        for dx, dy, ha, va in _NEAR:
            ann = ax.annotate(text, (x, y), textcoords="offset points", xytext=(dx, dy), ha=ha, va=va,
                              fontsize=FONT_PT - 1.5, color=color, zorder=5,
                              path_effects=[pe.withStroke(linewidth=1.8, foreground="white")])
            bb = ann.get_window_extent(rend)
            inside = box.x0 <= bb.x0 and bb.x1 <= box.x1 and box.y0 <= bb.y0 and bb.y1 <= box.y1
            hits_marker = any(bb.x0 - 2 <= px <= bb.x1 + 2 and bb.y0 - 2 <= py <= bb.y1 + 2
                              for px, py in pts if (px, py) != tuple(me))
            if inside and not hits_marker and not any(_overlaps(bb, t) for t in taken):
                taken.append(bb)
                break
            ann.remove()
        else:
            dropped.append(text)
    if dropped:
        print(f"   {ax.get_title(loc='left')}: {len(dropped)} label(s) not placeable cleanly: {dropped}")


def _tradeoff_axis(ax, csv_name, title):
    agg = pd.read_csv(os.path.join(TAB, csv_name))
    _need_colours(agg.short_name.unique(), csv_name)
    pending = []
    for sn, sub in agg.groupby("short_name"):
        sub = sub.sort_values("far_preonset_pct_mean")
        ax.plot(sub.far_preonset_pct_mean, sub.lead_time_hours_mean, "o-", color=COLORS[sn],
                lw=1.1, ms=2.8, label=sub["method"].iloc[0], zorder=3)
        pending += [(r.far_preonset_pct_mean, r.lead_time_hours_mean, f"{r.percentile:g}", COLORS[sn])
                    for r in sub.itertuples() if float(r.percentile) in LABELLED_PERCENTILES]
    ax.axvline(10.0, color="#FF9800", lw=1.1, ls=":", label="10% FAR budget")
    ax.set_title(title, fontweight="bold", loc="left", pad=3)
    ax.set_xlabel("Pre-onset FAR (%), lower is better")
    ax.grid(True, alpha=0.3, lw=0.4)
    ax.margins(x=0.07, y=0.09)
    return pending


def fig_tradeoffs():
    """Figure 5: lead time vs pre-onset FAR, threshold percentile swept; (a) IMS, (b) XJTU-SY."""
    fig, axes = plt.subplots(1, 2, figsize=(TEXT_WIDTH_IN, 2.35))
    pend = [_tradeoff_axis(axes[0], "tradeoff_IMS.csv", "(a) IMS"),
            _tradeoff_axis(axes[1], "tradeoff_XJTU-SY.csv", "(b) XJTU-SY")]
    axes[0].set_ylabel("Lead time (h), higher is better")
    seen = {}
    for ax in axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            seen.setdefault(l, h)
    seen["10% FAR budget"] = seen.pop("10% FAR budget")          # budget line last
    fig.legend(list(seen.values()), list(seen), loc="center left", bbox_to_anchor=(0.795, 0.5),
               frameon=True, handlelength=1.6, borderaxespad=0.0)
    fig.tight_layout(pad=0.3, w_pad=0.8, rect=(0, 0, 0.79, 1))
    for ax, p in zip(axes, pend):
        _place_near(fig, ax, p)
    out = os.path.join(FILES, "fig_tradeoff_panels.pdf")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    fig_sweep()
    fig_tradeoffs()
