# src/diagnostic_console.py
"""
SCADA Diagnostic Console — alarm-centred, explainable, multi-parameter.
======================================================================

Industrial HMI for predictive maintenance (MetroPT-3 compressor, C-MAPSS turbofan).

Workflow:
    alarm fires -> pin the moment -> see every parameter -> toggle / overlay ->
    read how they relate -> probable cause + recommended fix + downloadable PDF.

Stack: Dash + Plotly + Flask (NOT React/Recharts). All visual styling lives in the
``index_string`` CSS below and in the Plotly figure builders. Run:

    python -m src.diagnostic_console        # http://127.0.0.1:8050

Design language: dark, dense, information-rich industrial SCADA (Grafana Enterprise /
SIMATIC WinCC / ABB Ability), tabbed, high-contrast controls.
"""

from __future__ import annotations

import io
import logging
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd

from src.console_data import MachineBundle, GROUP_ORDER
from src.diagnosis import extract_alarms, diagnose, AlarmEvent, Diagnosis

logger = logging.getLogger(__name__)

# ── Color system ──────────────────────────────────────────────────────────────
BG       = "#0A0F1A"
PANEL    = "#0F1623"
PANEL_2  = "#0B111C"
CARD_BRD = "#1E2D3D"
CTRLBAR  = "#111827"
CTRL     = "#1A2332"
CTRL_BRD = "#2D4A6B"
TEXT     = "#E2E8F0"
MUTED    = "#64748B"
PLACE    = "#94A3B8"
ACCENT   = "#00D4FF"
OK       = "#10B981"
WARN     = "#F59E0B"
CRIT     = "#EF4444"
BLUE     = "#3B82F6"
GRID     = "#1E293B"

MONO    = "'JetBrains Mono', ui-monospace, 'Cascadia Code', monospace"
DISPLAY = "'Orbitron', 'JetBrains Mono', sans-serif"
BODY    = "'Inter', 'Segoe UI', system-ui, sans-serif"

SEV_COLOR  = {"warning": WARN, "critical": CRIT}
CONF_COLOR = {"high": OK, "moderate": BLUE, "low": WARN}
# Paper's four datasets are primary (the console reports their FAR-gated lead-time
# metric); MetroPT-3 + C-MAPSS are retained as secondary illustrations.
PAPER_DATASETS = ["IMS", "ONGC", "XJTU-SY", "FEMTO"]
DATASETS   = PAPER_DATASETS + ["MetroPT-3", "C-MAPSS"]
TABS = [("overview", "Overview"), ("trends", "Parameter Trends"),
        ("diagnosis", "Diagnosis"), ("relationships", "Relationships"), ("report", "Report")]
KPI_ICON = {"machine": ("⚙", ACCENT), "source": ("⛁", "#A855F7"),
            "alarms": ("⚠", CRIT), "event": ("◆", WARN)}


def _base_layout(**kw) -> dict:
    base = dict(
        paper_bgcolor=PANEL, plot_bgcolor=PANEL_2,
        font=dict(color=TEXT, family=BODY, size=12),
        margin=dict(l=58, r=18, t=34, b=40),
        xaxis=dict(gridcolor=GRID, griddash="dot", zerolinecolor=GRID, linecolor=CARD_BRD,
                   tickfont=dict(family=MONO, size=10)),
        yaxis=dict(gridcolor=GRID, griddash="dot", zerolinecolor=GRID, linecolor=CARD_BRD,
                   title=dict(font=dict(color=MUTED, size=11))),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.2, font=dict(size=11)),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0F1623", bordercolor=CARD_BRD,
                        font=dict(color=TEXT, family=MONO, size=12)),
    )
    base.update(kw)
    return base


# ── Data service ──────────────────────────────────────────────────────────────

class _Service:
    def __init__(self, metropt_kw=None, cmapss_kw=None):
        self._bundles: Dict[Tuple, MachineBundle] = {}
        self._alarms: Dict[Tuple, dict] = {}
        self._metropt_kw = metropt_kw or {}
        self._cmapss_kw = cmapss_kw or {}

    def units(self, dataset):
        if dataset in PAPER_DATASETS:
            from src.datasets import default_runs
            return [{"label": r, "value": r} for r in default_runs(dataset)]
        if dataset == "C-MAPSS":
            try:
                b = self.bundle("C-MAPSS", None)
                return [{"label": f"Engine #{u}", "value": u}
                        for u in b.meta.get("units_available", [b.meta.get("unit", 1)])]
            except Exception:
                return [{"label": "Engine #1", "value": 1}]
        return [{"label": "Air Production Unit (APU)", "value": "APU"}]

    def bundle(self, dataset, unit):
        key = (dataset, unit)
        if key in self._bundles:
            return self._bundles[key]
        if dataset in PAPER_DATASETS:
            from src.console_paper_adapter import load_machine_bundle
            from src.datasets import default_runs
            run = unit if unit not in (None, "", "APU") else default_runs(dataset)[0]
            b = load_machine_bundle(dataset, run)
        elif dataset == "MetroPT-3":
            from src.metropt_preprocessing import load_metropt
            b = load_metropt(**self._metropt_kw)
        elif dataset == "C-MAPSS":
            from src.cmapss_preprocessing import load_cmapss
            kw = dict(self._cmapss_kw)
            if unit not in (None, "APU"):
                kw["unit"] = int(unit)
            b = load_cmapss(**kw)
        else:
            raise ValueError(f"Unknown dataset {dataset!r}")
        self._bundles[key] = b
        return b

    def alarms(self, dataset, unit, percentile):
        key = (dataset, unit, round(float(percentile), 2))
        if key in self._alarms:
            return self._alarms[key]
        res = extract_alarms(self.bundle(dataset, unit), percentile=percentile, persistence=3)
        self._alarms[key] = res
        return res


SERVICE: Optional[_Service] = None


# ── Figure helpers ────────────────────────────────────────────────────────────

def _empty_fig(msg):
    import plotly.graph_objects as go
    fig = go.Figure(); fig.update_layout(**_base_layout())
    fig.add_annotation(text=msg, showarrow=False, font=dict(color=MUTED, size=13),
                       xref="paper", yref="paper", x=0.5, y=0.5)
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return fig


def _xv(x):
    return x.isoformat() if hasattr(x, "isoformat") else x


def _vmark(fig, x, color, label=None, width=1.5, dash=None):
    x = _xv(x)
    fig.add_shape(type="line", xref="x", yref="paper", x0=x, x1=x, y0=0, y1=1,
                  line=dict(color=color, width=width, dash=dash))
    if label:
        fig.add_annotation(x=x, xref="x", y=1.0, yref="paper", yanchor="bottom",
                           text=label, showarrow=False, font=dict(color=color, size=13))


def _band(fig, x0, x1, color="rgba(239,68,68,0.10)"):
    fig.add_shape(type="rect", xref="x", yref="paper", x0=_xv(x0), x1=_xv(x1),
                  y0=0, y1=1, fillcolor=color, line_width=0, layer="below")


def _decimate(df, max_points=6000):
    return df if len(df) <= max_points else df.iloc[::int(np.ceil(len(df) / max_points))]


def _alarm_spans(b, res):
    al = res.get("alarm")
    if al is None:
        return []
    spans, i, n = [], 0, len(al)
    tv = b.df[b.time_col]
    while i < n:
        if al[i]:
            j = i
            while j < n and al[j]:
                j += 1
            spans.append((tv.iloc[i], tv.iloc[min(j - 1, n - 1)]))
            i = j
        else:
            i += 1
    return spans


def build_overlay(b, params, alarm, normalize, spans=None, title=None):
    import plotly.graph_objects as go
    if not params:
        return _empty_fig("Toggle one or more parameters in the legend to plot them")
    df = _decimate(b.df); t = df[b.time_col]
    fig = go.Figure()
    k = max(5, int(len(b.df) * 0.2)); base = b.df.iloc[:k]
    for (ws, we) in (spans or []):
        _band(fig, ws, we)
    for c in params:
        if c not in b.df.columns:
            continue
        meta = b.parameters[c]; y = pd.to_numeric(df[c], errors="coerce")
        if normalize:
            mu = float(pd.to_numeric(base[c], errors="coerce").mean())
            sd = float(pd.to_numeric(base[c], errors="coerce").std()) or 1.0
            y = (y - mu) / sd
        fig.add_trace(go.Scattergl(x=t, y=y, name=meta["label"], mode="lines",
                      line=dict(color=meta["color"], width=2.5),
                      hovertemplate=f"<b>{meta['label']}</b>: %{{y:.2f}}<extra></extra>"))
    for (ws, we) in b.failure_windows:
        if ws == we:
            _vmark(fig, ws, CRIT, "failure", dash="dot")
        else:
            _band(fig, ws, we, "rgba(239,68,68,0.16)")
    if alarm is not None:
        _vmark(fig, alarm.time, CRIT, "◆", width=2)
    fig.update_layout(**_base_layout(showlegend=False))
    fig.update_yaxes(title_text="z-score (σ from baseline)" if normalize else "sensor value")
    fig.update_xaxes(title_text="time" if b.time_kind == "datetime" else "cycle")
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=12, color=MUTED, family=MONO), x=0.5))
    return fig


def build_health_fig(b, res, alarm):
    import plotly.graph_objects as go
    score = res["score"]; thr = res["threshold"]; df = b.df
    idx = np.arange(len(score))
    keep = idx[::int(np.ceil(len(idx) / 6000))] if len(idx) > 6000 else idx
    t = df[b.time_col].iloc[keep]
    fig = go.Figure()
    for (ws, we) in _alarm_spans(b, res):
        _band(fig, ws, we, "rgba(239,68,68,0.12)")
    fig.add_trace(go.Scattergl(x=t, y=score[keep], mode="lines", name="health score",
                  line=dict(color=ACCENT, width=2.4),
                  fill="tozeroy", fillcolor="rgba(0,212,255,0.12)"))
    fig.add_hline(y=thr, line=dict(color=CRIT, width=1.6, dash="dash"))
    fig.add_annotation(x=t.iloc[0] if len(t) else 0, y=thr, xanchor="left", yanchor="bottom",
                       text=f"alarm threshold = {thr:.2f}", showarrow=False,
                       font=dict(color=CRIT, size=10, family=MONO))
    if alarm is not None:
        _vmark(fig, alarm.time, ACCENT, "◆ selected", width=2)
    fig.update_layout(**_base_layout(showlegend=False))
    fig.update_yaxes(title_text="deviation score (σ)")
    fig.update_xaxes(title_text="time" if b.time_kind == "datetime" else "cycle")
    return fig


def build_contrib(diag):
    import plotly.graph_objects as go
    if diag is None or not diag.contributions:
        return _empty_fig("Select an alarm to see what drove it")
    cs = list(reversed(diag.contributions))
    n = len(cs)
    colors = []
    for r, c in enumerate(cs):
        # red spectrum for above-baseline, blue spectrum for below
        if c.direction == "up":
            colors.append(["#7F1D1D", "#B91C1C", "#EF4444", "#F87171"][min(3, int(abs(c.z)))])
        elif c.direction == "down":
            colors.append(["#1E3A8A", "#1D4ED8", "#3B82F6", "#60A5FA"][min(3, int(abs(c.z)))])
        else:
            colors.append(MUTED)
    fig = go.Figure(go.Bar(
        x=[c.z for c in cs], y=[c.label for c in cs], orientation="h",
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.10)", width=1)),
        text=[f"{c.z:+.1f}σ · {c.pct:.0f}%" for c in cs], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:+.2f}σ from baseline<extra></extra>"))
    fig.update_layout(**_base_layout(margin=dict(l=8, r=30, t=10, b=34), height=max(210, 38 * n)))
    fig.update_xaxes(title_text="deviation from baseline (σ)"); fig.update_yaxes(automargin=True)
    return fig


def build_relationship(b, params, alarm):
    import plotly.graph_objects as go
    sel = [c for c in params if c in b.df.columns]
    if len(sel) < 2:
        return _empty_fig("Toggle at least two parameters to see their correlation")
    if alarm is not None:
        half = max(10, int(len(b.df) * 0.04))
        sub = b.df.iloc[max(0, alarm.index - half):min(len(b.df), alarm.index + half)]
        title = "correlation around the selected alarm"
    else:
        sub = b.df; title = "correlation over the full record"
    corr = sub[sel].apply(pd.to_numeric, errors="coerce").corr().values
    labels = [b.parameters[c]["label"] for c in sel]
    fig = go.Figure(go.Heatmap(
        z=corr, x=labels, y=labels, zmin=-1, zmax=1,
        colorscale=[[0, "#3B82F6"], [0.5, "#05070D"], [1, "#EF4444"]],
        colorbar=dict(title="r", outlinecolor=CARD_BRD), text=np.round(corr, 2),
        texttemplate="%{text}", textfont=dict(size=11, color="#FFFFFF", family=MONO),
        hovertemplate="%{y} vs %{x}<br>r = %{z:.2f}<extra></extra>"))
    fig.update_layout(**_base_layout(margin=dict(l=10, r=10, t=30, b=10)))
    fig.update_xaxes(tickangle=-35, automargin=True); fig.update_yaxes(automargin=True)
    fig.update_layout(title=dict(text=title, font=dict(size=12, color=MUTED, family=MONO), x=0.5))
    return fig


def build_scatter(b, diag):
    import plotly.graph_objects as go
    if diag is None or len(diag.contributions) < 2:
        return _empty_fig("Select an alarm to compare its two strongest parameters")
    cx, cy = diag.contributions[0], diag.contributions[1]
    x = pd.to_numeric(b.df[cx.col], errors="coerce"); y = pd.to_numeric(b.df[cy.col], errors="coerce")
    ai = diag.alarm.index; half = max(10, int(len(b.df) * 0.03))
    colors = np.where(np.arange(len(b.df)) < ai - half, BLUE,
                      np.where(np.arange(len(b.df)) > ai + half, OK, CRIT))
    fig = go.Figure(go.Scattergl(x=x, y=y, mode="markers",
                    marker=dict(size=6, color=colors, line=dict(width=0)),
                    hovertemplate=f"{cx.label}: %{{x:.2f}}<br>{cy.label}: %{{y:.2f}}<extra></extra>"))
    fig.add_trace(go.Scattergl(x=[x.iloc[ai]], y=[y.iloc[ai]], mode="markers",
                  marker=dict(size=15, color=CRIT, symbol="diamond", line=dict(color="white", width=1.5)),
                  hovertemplate="alarm<extra></extra>"))
    fig.update_layout(**_base_layout(margin=dict(l=58, r=12, t=30, b=46), showlegend=False))
    fig.update_xaxes(title_text=b.label(cx.col)); fig.update_yaxes(title_text=b.label(cy.col))
    fig.update_layout(title=dict(text="early → blue · alarm → red · after → green",
                                 font=dict(size=11, color=MUTED, family=MONO), x=0.5))
    return fig


# ── PDF report ────────────────────────────────────────────────────────────────

def build_pdf(b, diag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import textwrap, datetime

    sev_col = CRIT if diag.alarm.severity == "critical" else WARN
    atime = (diag.alarm.time.strftime("%Y-%m-%d %H:%M") if hasattr(diag.alarm.time, "strftime")
             else f"cycle {int(diag.alarm.time)}")
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69)); fig.patch.set_facecolor("white")
        ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.add_patch(plt.Rectangle((0, 0.93), 1, 0.07, color="#0A0F1A"))
        ax.text(0.06, 0.965, "SCADA Diagnostic Report", color="#00D4FF", fontsize=20,
                fontweight="bold", va="center")
        ax.text(0.06, 0.943, "explainable predictive maintenance", color="#94A3B8", fontsize=9, va="center")
        ax.text(0.94, 0.965, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                color="#cbd5e1", fontsize=9, ha="right", va="center")
        y = 0.89
        ax.text(0.06, y, f"Machine:  {b.unit_label}", fontsize=11, color="#0A0F1A"); y -= 0.026
        ax.text(0.06, y, f"Alarm:  {atime}     Severity:  {diag.alarm.severity.upper()}",
                fontsize=11, color=sev_col, fontweight="bold"); y -= 0.036
        ax.add_patch(plt.Rectangle((0.06, y - 0.062), 0.88, 0.07, color="#f1f5f9", ec="#cbd5e1"))
        ax.text(0.08, y - 0.012, "PROBABLE CAUSE", fontsize=8.5, color="#64748b", fontweight="bold")
        for i, line in enumerate(textwrap.wrap(diag.cause, 86)):
            ax.text(0.08, y - 0.034 - i * 0.02, line, fontsize=12, color="#0A0F1A", fontweight="bold")
        y -= 0.092
        ax.text(0.06, y, f"Signature: {diag.signature or 'none (generic)'}      "
                         f"Confidence: {diag.confidence}", fontsize=10, color="#334155"); y -= 0.012
        cax = fig.add_axes([0.10, y - 0.215, 0.82, 0.2])
        cs = list(reversed(diag.contributions[:6]))
        cax.barh([c.label for c in cs], [c.z for c in cs],
                 color=["#EF4444" if c.direction == "up" else "#3B82F6" for c in cs])
        cax.axvline(0, color="#94a3b8", lw=0.8); cax.set_xlabel("deviation from baseline (σ)", fontsize=9)
        cax.set_title("What drove this alarm", fontsize=10, loc="left", color="#0A0F1A")
        cax.tick_params(labelsize=8)
        for s in cax.spines.values():
            s.set_color("#cbd5e1")
        y -= 0.25
        ax.text(0.06, y, "SNAPSHOT AT ALARM", fontsize=8.5, color="#64748b", fontweight="bold"); y -= 0.02
        ax.text(0.06, y, f"{'Parameter':24s}{'At alarm':>11s}{'Baseline':>11s}{'Deviation':>12s}",
                fontsize=9, family="monospace", color="#334155"); y -= 0.019
        for c in diag.contributions[:6]:
            ax.text(0.06, y, f"{c.label[:24]:24s}{c.value:>11.2f}{c.baseline:>11.2f}{c.z:>+10.2f} sd",
                    fontsize=9, family="monospace", color="#0A0F1A"); y -= 0.017
        y -= 0.018
        ax.text(0.06, y, "WHY", fontsize=8.5, color="#64748b", fontweight="bold"); y -= 0.02
        for line in textwrap.wrap(diag.explanation, 92):
            ax.text(0.06, y, line, fontsize=10, color="#0A0F1A"); y -= 0.019
        y -= 0.016
        ax.text(0.06, y, "RECOMMENDED ACTION", fontsize=8.5, color="#0e7490", fontweight="bold"); y -= 0.02
        for line in textwrap.wrap(diag.recommendation, 92):
            ax.text(0.06, y, line, fontsize=10.5, color="#0A0F1A"); y -= 0.019
        ax.text(0.06, 0.02, f"Data source: {'SIMULATED fixture' if b.source == 'fixture' else 'field data'}"
                            "  ·  generated by SCADA Diagnostic Console", fontsize=8, color="#94a3b8")
        pdf.savefig(fig, facecolor="white"); plt.close(fig)
    return buf.getvalue()


# ── UI primitives ─────────────────────────────────────────────────────────────

def _card(title, children, **style):
    from dash import html
    base = {"backgroundColor": PANEL, "border": f"1px solid {CARD_BRD}",
            "borderRadius": "12px", "padding": "16px"}
    base.update(style)
    head = [] if title is None else [html.Div(title, className="card-title")]
    return html.Div(head + (children if isinstance(children, list) else [children]),
                    className="panel-card", style=base)


def _kpi(label, vid, sid, key):
    from dash import html
    icon, col = KPI_ICON[key]
    return html.Div([
        html.Span(icon, className="kpi-icon", style={"color": col}),
        html.Div(label, className="kpi-label"),
        html.Div(id=vid, className="kpi-value"),
        html.Div(id=sid, className="kpi-sub"),
    ], className="kpi-card", style={"borderLeft": f"4px solid {col}"})


def _pill(text, color):
    from dash import html
    return html.Span(text, className="badge", style={"color": color, "borderColor": color,
                     "boxShadow": f"0 0 10px -2px {color}"})


def _ordered_cols(b):
    cols = []
    for g in GROUP_ORDER:
        for c in b.param_cols():
            if b.parameters[c]["group"] == g:
                cols.append(c)
    return cols


def _apply_toggle(active, triggered_id, default, all_cols):
    """Pure toggle logic (unit-tested). Pill click toggles; anything else resets to default."""
    if isinstance(triggered_id, dict):
        name = triggered_id.get("name")
        active = list(active or [])
        if name in active:
            active.remove(name)
        elif name:
            active.append(name)
    else:
        active = list(default)
    return [c for c in all_cols if c in active]


def _render_pills(tab, b, active):
    from dash import html
    pills = []
    for col in _ordered_cols(b):
        meta = b.parameters[col]; on = col in active
        pills.append(html.Button(
            id={"type": f"{tab}-pill", "name": col}, n_clicks=0,
            className="legend-pill" + (" on" if on else ""),
            children=[html.Span(className="pill-dot", style={"backgroundColor": meta["color"],
                      "boxShadow": f"0 0 8px {meta['color']}" if on else "none"}),
                      html.Span(meta["label"])],
            style={"borderColor": meta["color"] if on else CARD_BRD,
                   "opacity": 1 if on else 0.35}))
    return html.Div(pills, className="legend-wrap")


# ── Layout ────────────────────────────────────────────────────────────────────

def _control_bar():
    from dash import dcc, html
    def field(label, comp, w):
        return html.Div([html.Label(label, className="ctrl-label"), comp], style={"width": w})
    return html.Div([
        field("DATASET", dcc.Dropdown(id="dataset", options=[{"label": d, "value": d} for d in DATASETS],
              value="MetroPT-3", clearable=False, className="ddark"), "180px"),
        field("MACHINE / UNIT", dcc.Dropdown(id="unit", clearable=False, className="ddark"), "230px"),
        field("ALARM (CLICK TO DIAGNOSE)", dcc.Dropdown(id="alarm", className="ddark",
              placeholder="No alarm selected"), "340px"),
        field("SENSITIVITY (PERCENTILE)", dcc.Slider(id="percentile", min=90, max=99.5, step=0.5,
              value=99, marks={90: "90", 95: "95", 99: "99"}, tooltip={"placement": "bottom"}), "220px"),
        html.Div(id="status-pill", style={"marginLeft": "auto", "alignSelf": "center"}),
    ], className="control-bar")


def _panel_overview():
    from dash import dcc, html
    kpis = html.Div([
        _kpi("MACHINE", "kpi-machine", "kpi-machine-sub", "machine"),
        _kpi("DATA SOURCE", "kpi-source", "kpi-source-sub", "source"),
        _kpi("ACTIVE ALARMS", "kpi-alarms", "kpi-alarms-sub", "alarms"),
        _kpi("SELECTED EVENT", "kpi-event", "kpi-event-sub", "event"),
    ], className="kpi-row")
    return html.Div([
        kpis,
        _card("Machine health score & alarms",
              dcc.Loading(dcc.Graph(id="health-fig", config={"displaylogo": False},
                          style={"height": "320px"}), color=ACCENT)),
        html.Div(_card("Detected alarms", html.Div(id="alarm-table")), style={"marginTop": "12px"}),
    ], id="panel-overview", className="tab-panel")


def _panel_trends():
    from dash import dcc, html
    return html.Div(_card("Parameter trends over time", [
        dcc.Loading(dcc.Graph(id="trends-fig", config={"displaylogo": False},
                    style={"height": "500px"}), color=ACCENT),
        html.Div([
            dcc.Checklist(id="trends-norm", options=[{"label": " normalize to σ", "value": "z"}],
                          value=["z"], className="mini-check"),
        ], style={"margin": "8px 0 2px"}),
        html.Div(id="trends-pills"),
    ]), id="panel-trends", className="tab-panel")


def _panel_diagnosis():
    from dash import dcc, html
    left = _card("Root-cause diagnosis", [
        html.Div(id="diag-cause", className="diag-cause"),
        html.Div(id="diag-badges", style={"marginBottom": "12px"}),
        dcc.Graph(id="contrib", config={"displaylogo": False, "displayModeBar": False},
                  style={"height": "260px"}),
        html.Div(id="diag-explain", className="diag-explain"),
        html.Div("RECOMMENDED ACTION", className="diag-fix-title"),
        html.Div(id="diag-fix", className="diag-fix"),
    ])
    right = _card("Snapshot at the selected alarm", html.Div(id="snapshot-table"))
    return html.Div(html.Div([
        html.Div(left, style={"flex": "1.1", "minWidth": 0}),
        html.Div(right, style={"flex": "1", "minWidth": 0}),
    ], className="row-flex"), id="panel-diagnosis", className="tab-panel")


def _panel_relationships():
    from dash import dcc, html
    note = html.Div("Lines share a σ-scale so different units are comparable — parameters that rise "
                    "and fall together are related. The heatmap quantifies strength (r→+1 together, "
                    "r→−1 opposite). Toggle lines with the legend pills.", className="rel-note")
    left = _card("Compare parameters", [
        note,
        dcc.Loading(dcc.Graph(id="rel-multiline", config={"displaylogo": False},
                    style={"height": "380px"}), color=ACCENT),
        html.Div(dcc.Checklist(id="rel-norm", options=[{"label": " normalize to σ", "value": "z"}],
                 value=["z"], className="mini-check"), style={"margin": "8px 0 2px"}),
        html.Div(id="rel-pills"),
    ])
    right = html.Div([
        _card("Correlation strength",
              dcc.Graph(id="relationship", config={"displaylogo": False, "displayModeBar": False},
                        style={"height": "300px"})),
        html.Div(_card("Two strongest signals",
                 dcc.Graph(id="scatter", config={"displaylogo": False, "displayModeBar": False},
                           style={"height": "260px"})), style={"marginTop": "12px"}),
    ])
    return html.Div(html.Div([
        html.Div(left, style={"flex": "1.4", "minWidth": 0}),
        html.Div(right, style={"flex": "1", "minWidth": 0}),
    ], className="row-flex"), id="panel-relationships", className="tab-panel")


def _panel_report():
    from dash import dcc, html
    return html.Div(_card("Downloadable diagnostic report", [
        html.Div("Generate a one-page PDF for the selected alarm — probable cause, ranked parameter "
                 "contributions, snapshot table, the reasoning, and the recommended action.",
                 className="rel-note", style={"maxWidth": "760px"}),
        html.Div(id="report-preview", style={"margin": "6px 0 16px"}),
        html.Button("⬇  DOWNLOAD PDF REPORT", id="btn-pdf", n_clicks=0, className="dl-btn"),
        dcc.Download(id="download-pdf"),
    ]), id="panel-report", className="tab-panel")


def _build_layout(app):
    from dash import dcc, html
    header = html.Div([
        html.Div([
            html.Span("◆", style={"color": ACCENT, "fontSize": "20px", "marginRight": "10px",
                                  "textShadow": f"0 0 12px {ACCENT}"}),
            html.Span("SCADA DIAGNOSTIC CONSOLE", className="app-title"),
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            html.Span(className="live-dot"),
            html.Span("LIVE", className="live-text"),
            html.Span(id="header-status", className="meta-pill"),
        ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
    ], className="app-header")

    tabs = dcc.Tabs(id="tabs", value="overview", className="tabs-bar", children=[
        dcc.Tab(label=lbl, value=val, className="tab", selected_className="tab--sel") for val, lbl in TABS])

    panels = html.Div([_panel_overview(), _panel_trends(), _panel_diagnosis(),
                       _panel_relationships(), _panel_report()], className="panels")

    body = html.Div([_control_bar(), tabs, panels], style={"padding": "16px 22px"})
    app.layout = html.Div([dcc.Store(id="trends-active"), dcc.Store(id="rel-active"),
                           html.Div(id="sim-banner"), header, body], className="app-root")


# ── Callbacks ─────────────────────────────────────────────────────────────────

def _register_callbacks(app):
    from dash import Input, Output, State, html, dcc, ctx, ALL

    @app.callback([Output(f"panel-{v}", "style") for v, _ in TABS], Input("tabs", "value"))
    def _show(active):
        return [{"display": "block"} if v == active else {"display": "none"} for v, _ in TABS]

    @app.callback(Output("unit", "options"), Output("unit", "value"), Input("dataset", "value"))
    def _units(dataset):
        opts = SERVICE.units(dataset)
        return opts, opts[0]["value"]

    @app.callback(Output("alarm", "options"), Output("alarm", "value"),
                  Input("dataset", "value"), Input("unit", "value"), Input("percentile", "value"))
    def _alarms(dataset, unit, percentile):
        try:
            res = SERVICE.alarms(dataset, unit, percentile)
        except Exception as e:
            logger.warning("alarm computation failed: %s", e)
            return [], None
        opts = []
        for e in res["events"]:
            tstr = (e.time.strftime("%Y-%m-%d %H:%M") if hasattr(e.time, "strftime")
                    else f"cycle {int(e.time)}")
            mark = "●" if e.severity == "critical" else "○"
            opts.append({"label": f"{mark} {tstr} — {e.severity} — {e.top_param_label}", "value": e.index})
        return opts, (opts[0]["value"] if opts else None)

    def _pills_cb(tab):
        def cb(clicks, dataset, unit, active):
            try:
                b = SERVICE.bundle(dataset, unit)
            except Exception:
                return html.Div(), []
            default = b.health_params[:6] or b.param_cols(important_only=True)[:6]
            new_active = _apply_toggle(active, ctx.triggered_id, default, _ordered_cols(b))
            return _render_pills(tab, b, new_active), new_active
        return cb

    app.callback(Output("trends-pills", "children"), Output("trends-active", "data"),
                 Input({"type": "trends-pill", "name": ALL}, "n_clicks"),
                 Input("dataset", "value"), Input("unit", "value"),
                 State("trends-active", "data"))(_pills_cb("trends"))
    app.callback(Output("rel-pills", "children"), Output("rel-active", "data"),
                 Input({"type": "rel-pill", "name": ALL}, "n_clicks"),
                 Input("dataset", "value"), Input("unit", "value"),
                 State("rel-active", "data"))(_pills_cb("rel"))

    @app.callback(
        Output("sim-banner", "children"), Output("header-status", "children"),
        Output("status-pill", "children"),
        Output("kpi-machine", "children"), Output("kpi-machine-sub", "children"),
        Output("kpi-source", "children"), Output("kpi-source-sub", "children"),
        Output("kpi-alarms", "children"), Output("kpi-alarms-sub", "children"),
        Output("kpi-event", "children"), Output("kpi-event-sub", "children"),
        Output("health-fig", "figure"), Output("alarm-table", "children"),
        Input("dataset", "value"), Input("unit", "value"),
        Input("percentile", "value"), Input("alarm", "value"))
    def _overview(dataset, unit, percentile, alarm_idx):
        try:
            b = SERVICE.bundle(dataset, unit); res = SERVICE.alarms(dataset, unit, percentile)
        except Exception as e:
            d = "—"
            return (None, "data error", None, d, "", d, "", d, "", d, "",
                    _empty_fig(f"Could not load data: {e}"), "")
        is_sim = b.source == "fixture"
        banner = None
        if is_sim:
            banner = html.Div([html.B("SIMULATED demo data. "),
                f"Synthetic stand-in for {dataset}; drop the real file in data/raw/ to use field data."],
                className="sim-banner")
        n = len(res["events"]); crit = sum(1 for e in res["events"] if e.severity == "critical")
        alarm = next((e for e in res["events"] if e.index == alarm_idx), None)
        if alarm is not None:
            pill = html.Span("ALARM ACTIVE", className="badge pulse-crit",
                             style={"color": CRIT, "borderColor": CRIT})
            ev_val = (alarm.time.strftime("%Y-%m-%d %H:%M") if hasattr(alarm.time, "strftime")
                      else f"cycle {int(alarm.time)}")
            ev_sub = f"{alarm.severity} · {alarm.top_param_label}"
        else:
            pill = _pill("MONITORING", OK); ev_val, ev_sub = "none", "select an alarm"
        return (banner, f"{b.unit_label}  ·  {len(b.df):,} samples", pill,
                dataset, b.unit_label[:26], "SIMULATED" if is_sim else "REAL",
                "synthetic fixture" if is_sim else "field data",
                str(n), f"{crit} critical · p{percentile}", ev_val, ev_sub,
                build_health_fig(b, res, alarm), _alarm_table(b, res, alarm_idx))

    @app.callback(Output("trends-fig", "figure"),
                  Input("trends-active", "data"), Input("trends-norm", "value"),
                  Input("alarm", "value"), Input("dataset", "value"),
                  Input("unit", "value"), Input("percentile", "value"))
    def _trends(active, norm, alarm_idx, dataset, unit, percentile):
        try:
            b = SERVICE.bundle(dataset, unit); res = SERVICE.alarms(dataset, unit, percentile)
        except Exception as e:
            return _empty_fig(f"Could not load data: {e}")
        alarm = next((e for e in res["events"] if e.index == alarm_idx), None)
        return build_overlay(b, active or [], alarm, normalize=bool(norm), spans=_alarm_spans(b, res))

    @app.callback(
        Output("diag-cause", "children"), Output("diag-badges", "children"),
        Output("contrib", "figure"), Output("diag-explain", "children"),
        Output("diag-fix", "children"), Output("snapshot-table", "children"),
        Input("dataset", "value"), Input("unit", "value"),
        Input("percentile", "value"), Input("alarm", "value"))
    def _diagnosis(dataset, unit, percentile, alarm_idx):
        try:
            b = SERVICE.bundle(dataset, unit); res = SERVICE.alarms(dataset, unit, percentile)
        except Exception as e:
            return "—", None, _empty_fig(str(e)), "", "", ""
        alarm = next((e for e in res["events"] if e.index == alarm_idx), None)
        if alarm is None:
            return ("No alarm selected", None, _empty_fig("Select an alarm to diagnose"),
                    "Pick a detected alarm to see which parameters drove it and the probable cause.",
                    "", "")
        diag = diagnose(b, alarm)
        return (diag.cause, _badges(diag), build_contrib(diag), diag.explanation,
                diag.recommendation, _snapshot_table(b, diag))

    @app.callback(
        Output("rel-multiline", "figure"), Output("relationship", "figure"), Output("scatter", "figure"),
        Input("rel-active", "data"), Input("rel-norm", "value"), Input("alarm", "value"),
        Input("dataset", "value"), Input("unit", "value"), Input("percentile", "value"))
    def _relationships(active, norm, alarm_idx, dataset, unit, percentile):
        try:
            b = SERVICE.bundle(dataset, unit); res = SERVICE.alarms(dataset, unit, percentile)
        except Exception as e:
            ef = _empty_fig(str(e)); return ef, ef, ef
        alarm = next((e for e in res["events"] if e.index == alarm_idx), None)
        params = active or b.health_params
        multi = build_overlay(b, params, alarm, normalize=bool(norm), spans=_alarm_spans(b, res),
                              title="parameters on a shared σ scale — overlapping lines are related")
        diag = diagnose(b, alarm) if alarm is not None else None
        return multi, build_relationship(b, params, alarm), build_scatter(b, diag)

    @app.callback(Output("report-preview", "children"),
                  Input("dataset", "value"), Input("unit", "value"),
                  Input("percentile", "value"), Input("alarm", "value"))
    def _report_preview(dataset, unit, percentile, alarm_idx):
        try:
            b = SERVICE.bundle(dataset, unit); res = SERVICE.alarms(dataset, unit, percentile)
        except Exception as e:
            return html.Span(str(e), style={"color": CRIT})
        alarm = next((e for e in res["events"] if e.index == alarm_idx), None)
        if alarm is None:
            return html.Span("Select an alarm (top bar) to enable the report.", style={"color": MUTED})
        diag = diagnose(b, alarm)
        atime = (alarm.time.strftime("%Y-%m-%d %H:%M") if hasattr(alarm.time, "strftime")
                 else f"cycle {int(alarm.time)}")
        return html.Div([
            html.Div([html.B("Report ready for: "), b.unit_label]),
            html.Div([html.B("Alarm: "), f"{atime} ({alarm.severity})"]),
            html.Div([html.B("Probable cause: "), diag.cause]),
        ], style={"lineHeight": "1.7", "color": TEXT, "fontSize": "13px"})

    @app.callback(Output("download-pdf", "data"), Input("btn-pdf", "n_clicks"),
                  State("dataset", "value"), State("unit", "value"),
                  State("percentile", "value"), State("alarm", "value"), prevent_initial_call=True)
    def _download(n, dataset, unit, percentile, alarm_idx):
        if not n:
            return None
        b = SERVICE.bundle(dataset, unit); res = SERVICE.alarms(dataset, unit, percentile)
        alarm = next((e for e in res["events"] if e.index == alarm_idx), None)
        if alarm is None:
            return None
        diag = diagnose(b, alarm); pdf = build_pdf(b, diag)
        tag = (alarm.time.strftime("%Y%m%d_%H%M") if hasattr(alarm.time, "strftime")
               else f"cycle{int(alarm.time)}")
        return dcc.send_bytes(lambda buf: buf.write(pdf),
                              f"diagnostic_report_{dataset.replace('-', '')}_{tag}.pdf")


def _badges(diag):
    from dash import html
    items = []
    if diag.signature:
        items.append(_pill(diag.signature, ACCENT))
    items.append(_pill(f"confidence: {diag.confidence}", CONF_COLOR.get(diag.confidence, MUTED)))
    items.append(_pill(diag.alarm.severity, SEV_COLOR.get(diag.alarm.severity, MUTED)))
    return html.Div(items, style={"display": "flex", "gap": "8px", "flexWrap": "wrap"})


def _alarm_table(b, res, selected_idx):
    from dash import html
    if not res["events"]:
        return html.Div("No alarms at this sensitivity — lower the percentile to detect earlier.",
                        style={"color": MUTED, "fontSize": "13px"})
    scores = [e.score for e in res["events"]]; smax = max(scores) or 1.0
    rows = [html.Tr([html.Th(h, className=f"th-{a}") for h, a in
                     [("Time", "l"), ("Severity", "l"), ("Driven by", "l"), ("Score", "r")]])]
    for i, e in enumerate(res["events"]):
        tstr = (e.time.strftime("%Y-%m-%d %H:%M") if hasattr(e.time, "strftime")
                else f"cycle {int(e.time)}")
        sel = (e.index == selected_idx)
        spark = html.Div(html.Div(className="spark-fill",
                         style={"width": f"{100*e.score/smax:.0f}%",
                                "backgroundColor": SEV_COLOR.get(e.severity, MUTED)}),
                         className="spark")
        rows.append(html.Tr([
            html.Td(tstr, className="td-l mono"),
            html.Td(_pill(e.severity, SEV_COLOR.get(e.severity, MUTED)), className="td-l"),
            html.Td(e.top_param_label, className="td-l"),
            html.Td([spark, html.Span(f"{e.score:.2f}", className="mono")], className="td-r"),
        ], className="alarm-row" + (" sel" if sel else "")))
    return html.Table(rows, className="data-table")


def _snapshot_table(b, diag):
    from dash import html
    rows = [html.Tr([html.Th(h, className=f"th-{a}") for h, a in
                     [("Parameter", "l"), ("At alarm", "r"), ("Baseline", "r"),
                      ("Deviation", "r"), ("", "l")]])]
    for c in diag.contributions:
        arrow = "▲" if c.direction == "up" else ("▼" if c.direction == "down" else "—")
        acol = CRIT if c.direction == "up" else (BLUE if c.direction == "down" else MUTED)
        unit = f" {c.unit}" if c.unit else ""
        hot = c.pct > 15
        rows.append(html.Tr([
            html.Td(c.label, className="td-l"),
            html.Td(f"{c.value:.2f}{unit}", className="td-r mono"),
            html.Td(f"{c.baseline:.2f}{unit}", className="td-r mono", style={"color": MUTED}),
            html.Td(f"{c.z:+.2f}σ", className="td-r mono", style={"color": acol}),
            html.Td(f"{arrow} {c.pct:.0f}%", className="td-l", style={"color": acol}),
        ], style={"backgroundColor": "rgba(239,68,68,0.06)" if hot else "transparent"}))
    return html.Table(rows, className="data-table")


# ── Global CSS ────────────────────────────────────────────────────────────────

_INDEX_CSS = """
<!DOCTYPE html><html><head>{%metas%}<title>SCADA Diagnostic Console</title>{%favicon%}{%css%}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&family=Orbitron:wght@600;800&display=swap" rel="stylesheet">
<style>
  body { margin:0; background:#0A0F1A; }
  .app-root { background:#0A0F1A; min-height:100vh; color:#E2E8F0; font-family:'Inter',system-ui,sans-serif; }
  .mono { font-family:'JetBrains Mono',monospace; }

  /* header */
  .app-header { display:flex; justify-content:space-between; align-items:center; padding:14px 22px;
     border-bottom:1px solid #1E2D3D; background:#0F1623;
     background-image:repeating-linear-gradient(0deg, rgba(0,212,255,0.03) 0, rgba(0,212,255,0.03) 1px, transparent 1px, transparent 3px); }
  .app-title { font-family:'Orbitron','JetBrains Mono',sans-serif; font-weight:800; font-size:20px;
     letter-spacing:.08em; color:#E2E8F0; text-shadow:0 0 14px rgba(0,212,255,0.45); }
  .live-dot { width:9px; height:9px; border-radius:50%; background:#10B981; display:inline-block;
     box-shadow:0 0 8px #10B981; animation:blink 1.6s ease-in-out infinite; }
  .live-text { color:#10B981; font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
     letter-spacing:.12em; }
  .meta-pill { background:#111827; border:1px solid #1E2D3D; border-radius:999px; padding:4px 12px;
     color:#94A3B8; font-size:12px; font-family:'JetBrains Mono',monospace; }
  @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:.35;} }
  @keyframes pulseCrit { 0%,100%{box-shadow:0 0 6px -2px #EF4444;} 50%{box-shadow:0 0 16px 1px #EF4444;} }
  .pulse-crit { animation:pulseCrit 1.3s ease-in-out infinite; }

  /* sim banner */
  .sim-banner { background:#3b2f0b; color:#fcd34d; border:1px solid #F59E0B; padding:8px 22px; font-size:13px; }

  /* control bar */
  .control-bar { display:flex; gap:18px; align-items:flex-end; flex-wrap:wrap; background:#111827;
     border:1px solid #1E2D3D; border-radius:12px; padding:14px 18px; margin:0 0 12px;
     box-shadow:inset 0 1px 0 rgba(255,255,255,0.03); }
  .ctrl-label { display:block; margin-bottom:5px; color:#64748B; font-size:10px; font-weight:700;
     letter-spacing:.1em; font-family:'JetBrains Mono',monospace; }

  /* dropdowns — dark bg, light text, cyan focus */
  .ddark .Select-control { background:#1A2332 !important; border:1px solid #2D4A6B !important;
     border-radius:8px !important; min-height:38px; transition:border-color .12s, box-shadow .12s; }
  .ddark .is-focused:not(.is-open) > .Select-control,
  .ddark .Select-control:hover { border-color:#00D4FF !important; box-shadow:0 0 0 2px rgba(0,212,255,0.18) !important; }
  .ddark .Select-value-label, .ddark .Select-value, .ddark .has-value .Select-value-label { color:#E2E8F0 !important; }
  .ddark .Select-placeholder { color:#94A3B8 !important; }
  .ddark .Select-input > input { color:#E2E8F0 !important; }
  .ddark .Select-menu-outer { background:#1A2332 !important; border:1px solid #2D4A6B !important; }
  .ddark .Select-option { background:#1A2332 !important; color:#E2E8F0 !important; }
  .ddark .Select-option.is-focused { background:#1E3A5F !important; color:#fff !important; }
  .ddark .Select-option.is-selected { background:#173049 !important; }
  .ddark .Select-arrow { border-color:#94A3B8 transparent transparent !important; }
  .ddark .Select-clear { color:#94A3B8 !important; }
  .ddark .VirtualizedSelectOption { background:#1A2332; color:#E2E8F0; }
  .ddark .VirtualizedSelectFocusedOption { background:#1E3A5F; color:#fff; }

  /* slider */
  .rc-slider-rail { background:#2D4A6B !important; }
  .rc-slider-track { background:linear-gradient(90deg,#1E3A5F,#00D4FF) !important; }
  .rc-slider-handle { border:2px solid #00D4FF !important; background:#0A0F1A !important;
     box-shadow:0 0 10px #00D4FF !important; }
  .rc-slider-mark-text { color:#64748B !important; font-family:'JetBrains Mono',monospace; }

  /* tabs */
  .tabs-bar { border-bottom:1px solid #1E2D3D !important; }
  .tab { background:#0F1623 !important; color:#64748B !important; border:1px solid #1E2D3D !important;
     border-bottom:none !important; border-radius:9px 9px 0 0 !important; padding:11px 22px !important;
     font-family:'JetBrains Mono',monospace !important; font-size:11px !important; font-weight:700 !important;
     letter-spacing:.12em !important; text-transform:uppercase; }
  .tab--sel { background:#0B111C !important; color:#E2E8F0 !important; border-top:2px solid #00D4FF !important;
     box-shadow:0 -2px 12px -4px #00D4FF; }
  .panels { background:#0B111C; border:1px solid #1E2D3D; border-top:none; border-radius:0 0 12px 12px; padding:16px; }
  .tab-panel { animation:fadeUp .15s ease; }
  @keyframes fadeUp { from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:none;} }
  .row-flex { display:flex; gap:12px; align-items:flex-start; }

  /* cards */
  .panel-card { transition:border-color .1s, box-shadow .1s; }
  .panel-card:hover { border-color:#27496b; box-shadow:0 0 14px -6px #00D4FF; }
  .card-title { color:#64748B; font-size:12px; font-weight:700; letter-spacing:.06em;
     text-transform:uppercase; margin-bottom:12px; font-family:'JetBrains Mono',monospace; }

  /* kpi */
  .kpi-row { display:flex; gap:12px; margin-bottom:12px; }
  .kpi-card { position:relative; flex:1; min-width:0; background:#0F1623; border:1px solid #1E2D3D;
     border-radius:12px; padding:16px; transition:box-shadow .1s; }
  .kpi-card:hover { box-shadow:0 0 16px -7px #00D4FF; }
  .kpi-icon { position:absolute; top:12px; right:14px; font-size:16px; opacity:.45; }
  .kpi-label { color:#64748B; font-size:10px; font-weight:700; letter-spacing:.1em;
     font-family:'JetBrains Mono',monospace; }
  .kpi-value { color:#fff; font-size:23px; font-weight:800; margin-top:4px; line-height:1.1; }
  .kpi-sub { color:#64748B; font-size:12px; margin-top:3px; }

  /* badges */
  .badge { border:1px solid; border-radius:999px; padding:3px 11px; font-size:11px; font-weight:700;
     text-transform:uppercase; letter-spacing:.04em; white-space:nowrap;
     font-family:'JetBrains Mono',monospace; }

  /* legend pills */
  .legend-wrap { display:flex; flex-wrap:wrap; gap:8px; margin-top:6px; }
  .legend-pill { display:inline-flex; align-items:center; gap:8px; background:#111827; border:1px solid;
     border-radius:999px; padding:6px 13px; color:#E2E8F0; font-size:12.5px; cursor:pointer;
     transition:opacity .1s, box-shadow .1s; }
  .legend-pill.on:hover { box-shadow:0 0 10px -3px currentColor; }
  .pill-dot { width:11px; height:11px; border-radius:50%; display:inline-block; }

  /* diagnosis text */
  .diag-cause { font-size:18px; font-weight:800; color:#fff; margin-bottom:6px; }
  .diag-explain { color:#94A3B8; font-size:13.5px; margin-top:10px; line-height:1.55; }
  .diag-fix-title { color:#00D4FF; font-size:11px; font-weight:800; text-transform:uppercase;
     letter-spacing:.05em; margin-top:14px; font-family:'JetBrains Mono',monospace; }
  .diag-fix { color:#E2E8F0; font-size:13.5px; margin-top:5px; line-height:1.55;
     background:rgba(0,212,255,0.07); border:1px solid #1E2D3D; border-radius:8px; padding:10px 12px; }
  .rel-note { color:#64748B; font-size:12.5px; line-height:1.5; margin-bottom:10px; }

  /* tables */
  .data-table { width:100%; border-collapse:collapse; font-size:13px; }
  .th-l,.th-r { color:#64748B; font-size:10px; font-weight:700; letter-spacing:.05em; text-transform:uppercase;
     padding:8px 10px; border-bottom:1px solid #1E2D3D; font-family:'JetBrains Mono',monospace; }
  .th-r { text-align:right; } .th-l { text-align:left; }
  .td-l,.td-r { padding:9px 10px; border-bottom:1px solid #16202e; color:#E2E8F0; }
  .td-r { text-align:right; } .td-l { text-align:left; }
  .alarm-row:nth-child(odd) { background:#0F1623; }
  .alarm-row:nth-child(even) { background:#111827; }
  .alarm-row:hover { box-shadow:inset 3px 0 0 #00D4FF; background:#13202f; }
  .alarm-row.sel { box-shadow:inset 3px 0 0 #00D4FF; background:rgba(0,212,255,0.08); }
  .spark { display:inline-block; width:54px; height:7px; background:#16202e; border-radius:4px;
     overflow:hidden; margin-right:8px; vertical-align:middle; }
  .spark-fill { height:100%; border-radius:4px; }

  /* download button */
  .dl-btn { background:linear-gradient(90deg,#00D4FF,#0891b2); color:#06121f; border:none;
     border-radius:9px; padding:12px 22px; font-weight:800; font-size:13px; cursor:pointer;
     font-family:'JetBrains Mono',monospace; letter-spacing:.04em; box-shadow:0 0 16px -4px #00D4FF; }
  .dl-btn:hover { filter:brightness(1.08); }

  .mini-check label { color:#64748B; font-size:12px; cursor:pointer; font-family:'JetBrains Mono',monospace; }
  .mini-check input { margin-right:6px; accent-color:#00D4FF; }
  ::-webkit-scrollbar { width:9px; height:9px; }
  ::-webkit-scrollbar-thumb { background:#2D4A6B; border-radius:8px; }
  ::-webkit-scrollbar-track { background:#0B111C; }
</style></head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
"""


def build_app(metropt_kw=None, cmapss_kw=None):
    try:
        import dash
    except ImportError:
        raise ImportError("pip install dash plotly")
    global SERVICE
    SERVICE = _Service(metropt_kw=metropt_kw, cmapss_kw=cmapss_kw)
    app = dash.Dash(__name__, index_string=_INDEX_CSS, title="SCADA Diagnostic Console",
                    suppress_callback_exceptions=True)
    _build_layout(app)
    _register_callbacks(app)
    return app


def launch_console(port=8050, debug=False, metropt_kw=None, cmapss_kw=None):
    app = build_app(metropt_kw=metropt_kw, cmapss_kw=cmapss_kw)
    print(f"\n{'='*64}\n  SCADA Diagnostic Console  ->  http://127.0.0.1:{port}\n"
          f"  Ctrl+C to stop\n{'='*64}\n")
    app.run(debug=debug, port=port, use_reloader=False)


if __name__ == "__main__":
    launch_console()
