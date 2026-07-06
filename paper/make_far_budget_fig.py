# -*- coding: utf-8 -*-
"""
STEP 11 figure: best VALID lead time per detector vs the false-alarm budget tau,
plotted from the exact values already published in Table XVII (tab:farsens) of
scada_journal.tex. No new experimental number is introduced and no intermediate
tau point is invented -- only the three budgets tau in {0.05, 0.10, 0.20} that
Table XVII already reports. Run from repo root:

    python paper/make_far_budget_fig.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(ROOT, "paper", "figs")
os.makedirs(FIGS, exist_ok=True)

TAU = [0.05, 0.10, 0.20]

# --- values copied verbatim from Table XVII (tab:farsens) -------------------
#     Detector            tau=0.05  tau=0.10  tau=0.20
FARSENS = {
    "3σ":               [0.0,  56.3, 77.0],
    "EWMA":             [0.0,   0.0,  0.0],
    "CUSUM":            [0.0,   0.0, 65.0],
    "Hotelling T²":     [0.0,   0.0, 73.9],
    "Isolation Forest": [0.0,   0.0, 53.4],
    "Deep SVDD":        [14.8, 14.8, 14.8],
    "RMS-trend":        [34.7, 34.7, 34.7],
}

COLORS = {
    "3σ":               "#2196F3",
    "EWMA":             "#4CAF50",
    "CUSUM":            "#00838F",
    "Hotelling T²":     "#FF9800",
    "Isolation Forest": "#E91E63",
    "Deep SVDD":        "#607D8B",
    "RMS-trend":        "#9C27B0",
}
MARKERS = {
    "3σ": "o", "EWMA": "s", "CUSUM": "D", "Hotelling T²": "^",
    "Isolation Forest": "v", "Deep SVDD": "P", "RMS-trend": "X",
}


def main():
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for name, vals in FARSENS.items():
        ax.plot(TAU, vals, marker=MARKERS[name], color=COLORS[name],
                linewidth=1.8, markersize=7, label=name)
    ax.set_xlabel("False-alarm budget  τ  (pre-onset FAR)")
    ax.set_ylabel("Best valid lead time (h)")
    ax.set_xticks(TAU)
    ax.set_xticklabels(["0.05", "0.10", "0.20"])
    ax.set_xlim(0.035, 0.215)
    ax.set_ylim(-3, 82)
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.legend(loc="upper left", fontsize=8, ncol=2, framealpha=0.9)
    ax.set_title("Recommended detector vs false-alarm budget (IMS, from Table XVII)",
                 fontsize=10)
    fig.tight_layout()
    out = os.path.join(FIGS, "fig_far_budget_detector.png")
    fig.savefig(out, dpi=200)
    print("wrote", out)


if __name__ == "__main__":
    main()
