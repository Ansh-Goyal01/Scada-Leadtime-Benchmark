# src/dashboard.py
"""
SCADA Industrial Monitoring Dashboard — SPC Style
==================================================
Run from notebook:
    from src.dashboard import launch_dashboard
    launch_dashboard("2nd_test", "isolation_forest")

Then open: http://127.0.0.1:8050
"""

import numpy as np
import pandas as pd
import copy
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# ── Feature groups — sidebar cards ───────────────────────────────────────────
FEATURE_GROUPS = {
    "RMS":          {"prefix": "rms_",   "color": "#3b82f6", "icon": "〜"},
    "Kurtosis":     {"prefix": "kurt_",  "color": "#ef4444", "icon": "∧"},
    "Crest Factor": {"prefix": "crest_", "color": "#f59e0b", "icon": "▲"},
    "Skewness":     {"prefix": "skew_",  "color": "#22c55e", "icon": "↗"},
    "Peak-to-Peak": {"prefix": "p2p_",   "color": "#a855f7", "icon": "↕"},
    "Variance":     {"prefix": "var_",   "color": "#06b6d4", "icon": "σ²"},
}

# ── Bearing labels ────────────────────────────────────────────────────────────
BEARING_LABELS = {
    "ch0": "Bearing 1 — X",
    "ch1": "Bearing 1 — Y",
    "ch2": "Bearing 2 — X",
    "ch3": "Bearing 2 — Y",
    "ch4": "Bearing 3 — X",
    "ch5": "Bearing 3 — Y",
    "ch6": "Bearing 4 — X",
    "ch7": "Bearing 4 — Y",
}

BEARING_COLORS = {
    "ch0": "#3b82f6",
    "ch1": "#60a5fa",
    "ch2": "#ef4444",
    "ch3": "#f87171",
    "ch4": "#22c55e",
    "ch5": "#4ade80",
    "ch6": "#f59e0b",
    "ch7": "#fbbf24",
}


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def launch_dashboard(run_name: str = "2nd_test",
                     method: str = "isolation_forest",
                     port: int = 8050,
                     debug: bool = False):
    """
    Launch the SCADA SPC-style monitoring dashboard.
    Open http://127.0.0.1:8050 in your browser after running this.
    """
    try:
        import dash
        import dash_bootstrap_components as dbc
    except ImportError:
        raise ImportError(
            "Install dependencies: pip install dash dash-bootstrap-components"
        )

    from src import load_pipeline, run_experiment
    from src.config import DATASET, SPLIT

    print(f"\n{'─'*55}")
    print(f"  Loading experiment: {run_name}")
    print(f"{'─'*55}")

    summary_df, all_results, pipe = run_experiment(run_name)

    result = next(
        (r for r in all_results if r["short_name"] == method),
        all_results[0] if all_results else None
    )

    df           = pipe["df_full"].copy()
    failure_time = DATASET["failure_times"].get(run_name)
    df_train_end = pipe["ts_train"][-1] if len(pipe["ts_train"]) > 0 else None

    app = _build_app(
        df=df,
        result=result,
        failure_time=failure_time,
        run_name=run_name,
        summary_df=summary_df,
        df_train_end=df_train_end,
    )

    print(f"\n{'='*55}")
    print(f"  Dashboard →  http://127.0.0.1:{port}")
    print(f"  Ctrl+C to stop")
    print(f"{'='*55}\n")
    app.run(debug=debug, port=port, use_reloader=False)


# ─────────────────────────────────────────────────────────────────────────────
# App builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_app(df, result, failure_time, run_name, summary_df, df_train_end):
    import dash
    from dash import dcc, html, Input, Output
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    from scipy import stats as scipy_stats

    # ── Identify available columns ────────────────────────────────────────────
    all_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                if c != "hours_to_failure"]

    # Map each feature group → list of columns present in df
    group_cols: Dict[str, List[str]] = {}
    for gname, gmeta in FEATURE_GROUPS.items():
        cols = [c for c in all_cols if c.startswith(gmeta["prefix"])]
        if cols:
            group_cols[gname] = cols

    available_groups = list(group_cols.keys())
    default_group    = available_groups[0] if available_groups else None

    # Compute control limits (mean ± 3σ) from first 50% of each column
    def compute_limits(series: pd.Series):
        n_train = max(int(len(series) * 0.5), 2)
        train   = series.iloc[:n_train].dropna()
        mu      = float(train.mean())
        sigma   = float(train.std()) + 1e-12
        return mu, mu + 3 * sigma, mu - 3 * sigma   # mean, UCL, LCL

    col_limits: Dict[str, tuple] = {}
    for col in all_cols:
        col_limits[col] = compute_limits(df[col])

    # Anomaly score data
    t_fail     = pd.Timestamp(failure_time) if failure_time else None
    scores     = np.array(result["scores_test"],  dtype=float) if result else None
    timestamps = list(result["timestamps"])                     if result else None
    alarm      = np.array(result["alarm_signal"], dtype=bool)  if result else None
    threshold  = float(result["threshold"])                    if result else None

    # ── Theme ─────────────────────────────────────────────────────────────────
    BG      = "#0d0e14"
    SIDEBAR = "#0a0b10"
    CARD    = "#13151f"
    CARD2   = "#1a1d2b"
    BORDER  = "#1e2235"
    BORDER2 = "#252840"
    TEXT    = "#dde1f0"
    MUTED   = "#5a6178"
    ACCENT  = "#3b82f6"
    GREEN   = "#22c55e"
    RED     = "#ef4444"
    ORANGE  = "#f59e0b"
    PURPLE  = "#a855f7"
    PLOT    = "#0a0c12"
    GRID    = "#151824"
    HEADER  = "#0f1120"

    def base_layout(title="", height=None):
        lo = dict(
            paper_bgcolor=CARD,
            plot_bgcolor=PLOT,
            font=dict(color=TEXT, family="'Inter', 'Segoe UI', sans-serif", size=11),
            margin=dict(l=55, r=15, t=42, b=48),
            hovermode="x unified",
            hoverlabel=dict(bgcolor=CARD2, font_color=TEXT,
                            bordercolor=BORDER2, font_size=11),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT, size=10),
                itemclick="toggle",
                itemdoubleclick="toggle",
                orientation="h",
                y=-0.18,
            ),
            xaxis=dict(
                gridcolor=GRID, zerolinecolor=GRID,
                tickfont=dict(color=MUTED, size=10),
                title_font=dict(color=MUTED, size=11),
                linecolor=BORDER2,
            ),
            yaxis=dict(
                gridcolor=GRID, zerolinecolor=GRID,
                tickfont=dict(color=MUTED, size=10),
                title_font=dict(color=MUTED, size=11),
                linecolor=BORDER2,
            ),
        )
        if title:
            lo["title"] = dict(
                text=title,
                font=dict(size=11, color=MUTED, family="'Inter', sans-serif"),
                x=0.01, pad=dict(l=4),
            )
        if height:
            lo["height"] = height
        return lo

    # ── KPI values ────────────────────────────────────────────────────────────
    valid_rows = summary_df[summary_df["Valid Alarm"] == True]
    if len(valid_rows) > 0:
        best_row  = valid_rows.loc[valid_rows["VLT (hours)"].idxmax()]
        best_vlt  = f"{best_row['VLT (hours)']:.1f}h"
        best_far  = f"{best_row['FAR (%)']:.1f}%"
        best_name = str(best_row["Method"])
    else:
        best_vlt = best_far = best_name = "N/A"

    # ── Helpers ───────────────────────────────────────────────────────────────
    def kpi(label, value, sub, color=TEXT, border_color=BORDER2):
        return html.Div([
            html.Div(label, style={
                "fontSize": "9px", "color": MUTED, "fontWeight": "700",
                "letterSpacing": "1.8px", "textTransform": "uppercase",
                "marginBottom": "7px",
            }),
            html.Div(value, style={
                "fontSize": "26px", "fontWeight": "800", "color": color,
                "fontFamily": "'Courier New', monospace", "lineHeight": "1",
            }),
            html.Div(sub, style={
                "fontSize": "10px", "color": MUTED, "marginTop": "4px",
            }),
        ], style={
            "background": CARD, "border": f"1px solid {border_color}",
            "borderTop": f"2px solid {color}",
            "borderRadius": "6px", "padding": "14px 16px", "flex": "1",
        })

    def chart_card(panel_id, title, height="100%"):
        return html.Div([
            # Card header bar
            html.Div([
                html.Span(title, style={
                    "fontSize": "10px", "color": MUTED, "fontWeight": "700",
                    "letterSpacing": "1.5px", "textTransform": "uppercase",
                }),
                html.Div(id=f"{panel_id}-stats", style={
                    "fontSize": "10px", "color": MUTED,
                    "fontFamily": "'Courier New', monospace",
                }),
            ], style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center",
                "background": HEADER, "padding": "8px 14px",
                "borderBottom": f"1px solid {BORDER}",
            }),
            dcc.Graph(
                id=panel_id,
                config={
                    "scrollZoom": True,
                    "displayModeBar": True,
                    "displaylogo": False,
                    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                    "toImageButtonOptions": {
                        "format": "png", "filename": panel_id, "scale": 2
                    },
                },
                style={"height": height},
            ),
        ], style={
            "background": CARD, "border": f"1px solid {BORDER}",
            "borderRadius": "6px", "overflow": "hidden",
            "display": "flex", "flexDirection": "column",
            "flex": "1",
        })

    def sidebar_card(group_name, meta, is_active=False):
        color  = meta["color"]
        border = color if is_active else BORDER
        bg     = f"{color}18" if is_active else CARD
        cols   = group_cols.get(group_name, [])
        n      = len(cols)

        return html.Div([
            html.Div([
                html.Div(meta["icon"], style={
                    "fontSize": "20px", "color": color,
                    "marginBottom": "6px", "lineHeight": "1",
                }),
                html.Div(group_name, style={
                    "fontSize": "11px", "color": TEXT if is_active else MUTED,
                    "fontWeight": "700", "letterSpacing": "0.3px",
                }),
                html.Div(f"{n} channels", style={
                    "fontSize": "9px", "color": MUTED,
                    "marginTop": "2px", "letterSpacing": "0.5px",
                }),
            ], style={"textAlign": "center"}),
        ], id={"type": "sidebar-card", "index": group_name},
        n_clicks=0,
        style={
            "background": bg,
            "border": f"1px solid {border}",
            "borderLeft": f"3px solid {color}",
            "borderRadius": "6px", "padding": "12px 8px",
            "cursor": "pointer", "marginBottom": "8px",
            "transition": "all 0.15s ease",
        })

    def results_table_html():
        header_style = {
            "padding": "8px 12px", "fontSize": "9px", "color": MUTED,
            "fontWeight": "700", "letterSpacing": "1.5px",
            "textTransform": "uppercase", "borderBottom": f"1px solid {BORDER2}",
            "background": PLOT, "textAlign": "left",
        }
        hdr = html.Tr([
            html.Th("Method",      style=header_style),
            html.Th("Lead Time",   style=header_style),
            html.Th("FAR",         style=header_style),
            html.Th("Status",      style=header_style),
        ])
        rows = []
        for _, row in summary_df.iterrows():
            ok  = row.get("Valid Alarm", False)
            vlt = row.get("VLT (hours)", 0)
            far = row.get("FAR (%)", 0)
            cell = {"padding": "8px 12px", "fontSize": "11px",
                    "borderBottom": f"1px solid {BORDER}",
                    "color": TEXT}
            rows.append(html.Tr([
                html.Td(row["Method"], style=cell),
                html.Td(f"{vlt:.1f}h", style={**cell,
                    "color": GREEN if ok else RED,
                    "fontWeight": "700", "fontFamily": "monospace"}),
                html.Td(f"{far:.1f}%", style={**cell,
                    "color": GREEN if far < 10 else RED,
                    "fontFamily": "monospace"}),
                html.Td("✓ Valid" if ok else "✗ Missed", style={**cell,
                    "color": GREEN if ok else RED, "fontWeight": "600"}),
            ]))
        return html.Table(
            [html.Thead(hdr), html.Tbody(rows)],
            style={"width": "100%", "borderCollapse": "collapse"},
        )

    # ── App ───────────────────────────────────────────────────────────────────
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        title=f"SCADA — {run_name}",
        suppress_callback_exceptions=True,
    )

    # Dropdown options for correlation panel
    all_col_opts = [{"label": c, "value": c} for c in all_cols]

    app.layout = html.Div(style={
        "background": BG, "minHeight": "100vh",
        "fontFamily": "'Inter', 'Segoe UI', sans-serif",
        "color": TEXT, "display": "flex", "flexDirection": "column",
    }, children=[

        # ── Hidden state store for active group ───────────────────────────────
        dcc.Store(id="active-group", data=default_group),

        # ── Top bar ───────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("◈ ", style={"color": ACCENT}),
                html.Span("SCADA MONITOR", style={
                    "color": ACCENT, "fontSize": "11px", "fontWeight": "700",
                    "letterSpacing": "3px",
                }),
            ]),
            html.Div(
                f"IMS Bearing Dataset  —  {run_name.replace('_', ' ').upper()}  "
                f"—  Failure: {t_fail.strftime('%Y-%m-%d %H:%M') if t_fail else 'N/A'}",
                style={"color": MUTED, "fontSize": "12px"}
            ),
            html.Div("● LIVE", style={
                "color": GREEN, "fontSize": "11px",
                "fontWeight": "700", "letterSpacing": "2px",
            }),
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center",
            "background": SIDEBAR, "padding": "10px 20px",
            "borderBottom": f"1px solid {BORDER}",
        }),

        # ── KPI bar ───────────────────────────────────────────────────────────
        html.Div([
            kpi("Best Lead Time",    best_vlt,  best_name,        GREEN,  GREEN),
            kpi("False Alarm Rate",  best_far,  "at best method", ACCENT, ACCENT),
            kpi("Snapshots",         str(len(df)), run_name,      TEXT,   BORDER2),
            kpi("Channels",          str(len(all_cols)), "monitored", TEXT, BORDER2),
            kpi("Failure",
                t_fail.strftime("%b %d %H:%M") if t_fail else "N/A",
                str(t_fail.year) if t_fail else "",
                RED, RED),
        ], style={
            "display": "flex", "gap": "10px",
            "padding": "12px 16px",
            "background": SIDEBAR,
            "borderBottom": f"1px solid {BORDER}",
        }),

        # ── Main body: sidebar + grid ─────────────────────────────────────────
        html.Div([

            # ── Left sidebar ──────────────────────────────────────────────────
            html.Div([
                html.Div("FEATURE", style={
                    "fontSize": "9px", "color": MUTED, "fontWeight": "700",
                    "letterSpacing": "2px", "marginBottom": "10px",
                    "paddingLeft": "4px",
                }),
                html.Div(
                    id="sidebar-cards",
                    children=[
                        sidebar_card(gname, FEATURE_GROUPS[gname],
                                     is_active=(gname == default_group))
                        for gname in available_groups
                    ]
                ),
                html.Hr(style={"borderColor": BORDER, "margin": "14px 0"}),
                html.Div("BEARINGS", style={
                    "fontSize": "9px", "color": MUTED, "fontWeight": "700",
                    "letterSpacing": "2px", "marginBottom": "10px",
                    "paddingLeft": "4px",
                }),
                *[
                    html.Div([
                        html.Div(style={
                            "width": "8px", "height": "8px",
                            "borderRadius": "50%",
                            "background": list(BEARING_COLORS.values())[i*2],
                            "display": "inline-block", "marginRight": "7px",
                        }),
                        html.Span(f"Bearing {i+1}", style={
                            "fontSize": "11px", "color": MUTED,
                        }),
                    ], style={"marginBottom": "6px", "display": "flex",
                              "alignItems": "center"})
                    for i in range(4)
                ],
            ], style={
                "width": "130px", "minWidth": "130px",
                "background": SIDEBAR, "padding": "14px 10px",
                "borderRight": f"1px solid {BORDER}",
                "overflowY": "auto",
            }),

            # ── 2×2 Chart grid ────────────────────────────────────────────────
            html.Div([

                # Row 1
                html.Div([
                    # Panel A: Individual MR / Time-series
                    html.Div([
                        chart_card("panel-ts",
                                   "Individual MR — Trend Monitor",
                                   height="350px"),
                    ], style={"flex": "1", "marginRight": "8px",
                               "display": "flex"}),

                    # Panel B: Correlation Analysis
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span("Process Correlation Analysis",
                                          style={"fontSize": "10px", "color": MUTED,
                                                 "fontWeight": "700",
                                                 "letterSpacing": "1.5px",
                                                 "textTransform": "uppercase"}),
                                html.Div(id="corr-stats", style={
                                    "fontSize": "10px", "color": MUTED,
                                    "fontFamily": "'Courier New', monospace",
                                }),
                            ], style={
                                "display": "flex", "justifyContent": "space-between",
                                "alignItems": "center",
                                "background": HEADER, "padding": "8px 14px",
                                "borderBottom": f"1px solid {BORDER}",
                            }),
                            # Channel selectors
                            html.Div([
                                html.Div([
                                    html.Div("Channel A", style={
                                        "fontSize": "9px", "color": MUTED,
                                        "fontWeight": "700", "letterSpacing": "1px",
                                        "textTransform": "uppercase",
                                        "marginBottom": "4px",
                                    }),
                                    dcc.Dropdown(
                                        id="corr-a",
                                        options=all_col_opts,
                                        value=all_cols[0] if all_cols else None,
                                        clearable=False,
                                        style={"fontSize": "11px"},
                                    ),
                                ], style={"flex": "1", "marginRight": "8px"}),
                                html.Div([
                                    html.Div("Channel B", style={
                                        "fontSize": "9px", "color": MUTED,
                                        "fontWeight": "700", "letterSpacing": "1px",
                                        "textTransform": "uppercase",
                                        "marginBottom": "4px",
                                    }),
                                    dcc.Dropdown(
                                        id="corr-b",
                                        options=all_col_opts,
                                        value=all_cols[1] if len(all_cols) > 1 else all_cols[0],
                                        clearable=False,
                                        style={"fontSize": "11px"},
                                    ),
                                ], style={"flex": "1"}),
                            ], style={
                                "display": "flex", "padding": "8px 10px",
                                "background": CARD2,
                                "borderBottom": f"1px solid {BORDER}",
                            }),
                            dcc.Graph(
                                id="panel-corr",
                                config={
                                    "scrollZoom": True,
                                    "displayModeBar": True,
                                    "displaylogo": False,
                                    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                },
                                style={"height": "290px"},
                            ),
                        ], style={
                            "background": CARD, "border": f"1px solid {BORDER}",
                            "borderRadius": "6px", "overflow": "hidden",
                            "display": "flex", "flexDirection": "column",
                            "flex": "1",
                        }),
                    ], style={"flex": "1", "display": "flex"}),

                ], style={"display": "flex", "marginBottom": "8px"}),

                # Row 2
                html.Div([
                    # Panel C: Anomaly Score
                    html.Div([
                        chart_card("panel-score",
                                   "Anomaly Score + Alarm Timeline",
                                   height="310px"),
                    ], style={"flex": "1", "marginRight": "8px",
                               "display": "flex"}),

                    # Panel D: Results + Influence
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span("Method Comparison + Influence",
                                          style={"fontSize": "10px", "color": MUTED,
                                                 "fontWeight": "700",
                                                 "letterSpacing": "1.5px",
                                                 "textTransform": "uppercase"}),
                            ], style={
                                "background": HEADER, "padding": "8px 14px",
                                "borderBottom": f"1px solid {BORDER}",
                            }),
                            html.Div([
                                results_table_html(),
                                html.Hr(style={"borderColor": BORDER,
                                               "margin": "10px 0"}),
                                html.Div(id="influence-text", style={
                                    "fontSize": "11px", "color": TEXT,
                                    "lineHeight": "1.7", "padding": "4px 2px",
                                }),
                            ], style={"padding": "10px 14px", "overflowY": "auto"}),
                        ], style={
                            "background": CARD, "border": f"1px solid {BORDER}",
                            "borderRadius": "6px", "overflow": "hidden",
                            "display": "flex", "flexDirection": "column",
                            "flex": "1", "height": "310px",
                        }),
                    ], style={"flex": "1", "display": "flex"}),

                ], style={"display": "flex"}),

            ], style={
                "flex": "1", "padding": "12px",
                "display": "flex", "flexDirection": "column",
                "overflowY": "auto",
            }),

        ], style={"display": "flex", "flex": "1", "overflow": "hidden",
                  "minHeight": "0"}),

        # ── Footer ────────────────────────────────────────────────────────────
        html.Div(
            "SCADA Lead-Time-Aware Anomaly Detection  •  NASA IMS Bearing Dataset",
            style={
                "textAlign": "center", "color": MUTED, "fontSize": "10px",
                "padding": "8px", "background": SIDEBAR,
                "borderTop": f"1px solid {BORDER}",
            }
        ),
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # CALLBACKS
    # ─────────────────────────────────────────────────────────────────────────

    # Update active group store when a sidebar card is clicked
    @app.callback(
        Output("active-group", "data"),
        [Input({"type": "sidebar-card", "index": g}, "n_clicks")
         for g in available_groups],
        prevent_initial_call=True,
    )
    def update_active_group(*args):
        from dash import ctx
        trigger = ctx.triggered_id
        if isinstance(trigger, dict):
            return trigger.get("index", default_group)
        return default_group

    # Update sidebar card styles when active group changes
    @app.callback(
        Output("sidebar-cards", "children"),
        Input("active-group", "data"),
    )
    def update_sidebar(active):
        return [
            sidebar_card(gname, FEATURE_GROUPS[gname],
                         is_active=(gname == active))
            for gname in available_groups
        ]

    # ── Panel A: Individual MR Time-Series ───────────────────────────────────
    @app.callback(
        [Output("panel-ts", "figure"),
         Output("panel-ts-stats", "children")],
        Input("active-group", "data"),
    )
    def cb_timeseries(active_group):
        if not active_group or active_group not in group_cols:
            active_group = default_group

        cols  = group_cols.get(active_group, [])
        color = FEATURE_GROUPS.get(active_group, {}).get("color", ACCENT)
        fig   = go.Figure()

        stat_parts = []

        for col in cols:
            s = df[col].dropna()
            if len(s) == 0:
                continue

            mu, ucl, lcl = col_limits[col]

            # Extract channel suffix (ch0, ch1, etc.)
            prefix = FEATURE_GROUPS[active_group]["prefix"]
            ch_key = col[len(prefix):]                 # e.g. "ch0"
            label  = BEARING_LABELS.get(ch_key, col)
            c      = BEARING_COLORS.get(ch_key, color)

            # Main signal line
            fig.add_trace(go.Scatter(
                x=list(s.index), y=list(s.values),
                name=label,
                line=dict(color=c, width=1.5),
                opacity=0.9,
                hovertemplate=f"<b>{label}</b>  %{{x}}<br>{active_group}: %{{y:.5f}}<extra></extra>",
            ))

            # UCL line
            fig.add_trace(go.Scatter(
                x=[s.index[0], s.index[-1]],
                y=[ucl, ucl],
                mode="lines",
                line=dict(color=RED, width=1.0, dash="dash"),
                showlegend=False,
                hovertemplate=f"UCL = {ucl:.4f}<extra></extra>",
            ))

            # Mean line
            fig.add_trace(go.Scatter(
                x=[s.index[0], s.index[-1]],
                y=[mu, mu],
                mode="lines",
                line=dict(color=MUTED, width=0.8, dash="dot"),
                showlegend=False,
                hovertemplate=f"Mean = {mu:.4f}<extra></extra>",
            ))

            # LCL line (only if positive — physical lower bound)
            if lcl > 0:
                fig.add_trace(go.Scatter(
                    x=[s.index[0], s.index[-1]],
                    y=[lcl, lcl],
                    mode="lines",
                    line=dict(color=ORANGE, width=1.0, dash="dash"),
                    showlegend=False,
                    hovertemplate=f"LCL = {lcl:.4f}<extra></extra>",
                ))

            # Right-side annotation for current value
            last_val = float(s.iloc[-1])
            fig.add_annotation(
                x=s.index[-1], y=last_val,
                text=f" {last_val:.4f}",
                showarrow=False,
                xanchor="left",
                font=dict(color=c, size=9, family="'Courier New', monospace"),
                xref="x", yref="y",
            )

            stat_parts.append(f"{label[:6]}: μ={mu:.3f} UCL={ucl:.3f}")

        # Failure line
        if t_fail:
            fig.add_vline(
                x=t_fail.timestamp() * 1000, line_dash="dash",
                line_color=RED, line_width=2,
                annotation_text="⚡ FAILURE",
                annotation_font_color=RED,
                annotation_font_size=10,
                annotation_position="top left",
            )

        # Training end line
        if df_train_end:
            fig.add_vline(
                x=df_train_end.timestamp() * 1000, line_dash="dot",
                line_color=MUTED, line_width=1,
                annotation_text="Train end",
                annotation_font_color=MUTED,
                annotation_font_size=9,
            )

        # UCL / LCL legend annotations
        fig.add_annotation(
            x=0.01, y=1.02, xref="paper", yref="paper",
            text=(
                f"<span style='color:{RED}'>─ ─</span> UCL/LCL (±3σ train)  "
                f"<span style='color:{MUTED}'>· · ·</span> Mean"
            ),
            showarrow=False,
            font=dict(size=9, color=MUTED),
            align="left",
        )

        lo = base_layout()
        lo.update(
            xaxis_title="Time",
            yaxis_title=active_group,
            showlegend=True,
        )
        fig.update_layout(**lo)

        stats_str = "  |  ".join(stat_parts[:2]) if stat_parts else ""
        return fig, stats_str

    # ── Panel B: Correlation Analysis ────────────────────────────────────────
    @app.callback(
        [Output("panel-corr", "figure"),
         Output("corr-stats", "children")],
        [Input("corr-a", "value"),
         Input("corr-b", "value")],
    )
    def cb_correlation(col_a, col_b):
        fig = go.Figure()

        if not col_a or not col_b:
            fig.update_layout(**base_layout())
            return fig, ""

        if col_a not in df.columns or col_b not in df.columns:
            fig.update_layout(**base_layout())
            return fig, ""

        s_a = df[col_a].dropna()
        s_b = df[col_b].dropna()
        idx = s_a.index.intersection(s_b.index)

        if len(idx) < 5:
            fig.update_layout(**base_layout())
            return fig, "Not enough data"

        a_vals = s_a.loc[idx].values.astype(float)
        b_vals = s_b.loc[idx].values.astype(float)

        # Pearson r and p-value
        r_val, p_val = scipy_stats.pearsonr(a_vals, b_vals)

        # Color by time
        n       = len(a_vals)
        t_norm  = np.linspace(0, 1, n)

        fig.add_trace(go.Scatter(
            x=list(a_vals), y=list(b_vals),
            mode="markers",
            marker=dict(
                color=t_norm,
                colorscale=[[0, ACCENT], [0.5, PURPLE], [1, RED]],
                size=4, opacity=0.65,
                showscale=True,
                colorbar=dict(
                    title=dict(text="Time", font=dict(color=MUTED, size=10)),
                    thickness=8,
                    tickvals=[0, 0.5, 1],
                    ticktext=["Start", "Mid", "End"],
                    tickfont=dict(color=MUTED, size=9),
                    len=0.7,
                ),
            ),
            hovertemplate=(
                f"<b>{col_a}</b>: %{{x:.5f}}<br>"
                f"<b>{col_b}</b>: %{{y:.5f}}<extra></extra>"
            ),
            name="Observations",
        ))

        # Regression line
        slope, intercept = np.polyfit(a_vals, b_vals, 1)
        x_line = np.linspace(a_vals.min(), a_vals.max(), 100)
        y_line = slope * x_line + intercept

        fig.add_trace(go.Scatter(
            x=list(x_line), y=list(y_line),
            mode="lines",
            line=dict(color=ORANGE, width=2.0, dash="solid"),
            name=f"Fit  (slope={slope:.3f})",
            hovertemplate=f"Regression: y = {slope:.3f}x + {intercept:.3f}<extra></extra>",
        ))

        # Annotation box — like the "Process Capability" box in the reference
        p_str = f"{p_val:.4f}" if p_val >= 0.0001 else "<0.0001"
        strength = (
            "Strong" if abs(r_val) > 0.7 else
            "Moderate" if abs(r_val) > 0.4 else "Weak"
        )
        direction = "Positive" if r_val > 0 else "Negative"
        ann_color = GREEN if abs(r_val) > 0.5 else ORANGE

        fig.add_annotation(
            x=0.97, y=0.97,
            xref="paper", yref="paper",
            text=(
                f"r = {r_val:.4f}<br>"
                f"p-value = {p_str}<br>"
                f"{direction} {strength}"
            ),
            showarrow=False,
            align="right",
            font=dict(size=11, color=ann_color,
                      family="'Courier New', monospace"),
            bgcolor=CARD2,
            bordercolor=ann_color,
            borderwidth=1,
            borderpad=8,
            xanchor="right",
            yanchor="top",
        )

        lo = base_layout()
        lo.update(
            xaxis_title=col_a,
            yaxis_title=col_b,
            showlegend=True,
            margin=dict(l=55, r=70, t=20, b=48),
        )
        fig.update_layout(**lo)

        stats_str = f"r={r_val:.3f}  p={p_str}"
        return fig, stats_str

    # ── Panel C: Anomaly Score ────────────────────────────────────────────────
    @app.callback(
        [Output("panel-score", "figure"),
         Output("panel-score-stats", "children")],
        Input("active-group", "data"),
    )
    def cb_score(_):
        fig = go.Figure()

        if scores is None or timestamps is None:
            fig.add_annotation(
                text="Run experiment first — no anomaly scores available",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(color=MUTED, size=13),
            )
            fig.update_layout(**base_layout())
            return fig, ""

        ts_str = [str(t) for t in timestamps]

        # Alarm shading
        if alarm is not None:
            in_alarm, a_start = False, None
            for ts_i, is_alarm in zip(ts_str, alarm):
                if is_alarm and not in_alarm:
                    a_start, in_alarm = ts_i, True
                elif not is_alarm and in_alarm:
                    fig.add_vrect(
                        x0=a_start, x1=ts_i,
                        fillcolor=RED, opacity=0.10,
                        layer="below", line_width=0,
                    )
                    in_alarm = False
            if in_alarm and a_start:
                fig.add_vrect(
                    x0=a_start, x1=ts_str[-1],
                    fillcolor=RED, opacity=0.10,
                    layer="below", line_width=0,
                )

        # Score line
        fig.add_trace(go.Scatter(
            x=ts_str, y=list(scores),
            name="Anomaly Score",
            line=dict(color=PURPLE, width=2.0),
            hovertemplate="%{x}<br>Score: %{y:.5f}<extra></extra>",
        ))

        # Threshold
        if threshold is not None:
            fig.add_hline(
                y=threshold,
                line_dash="dash", line_color=RED, line_width=1.8,
                annotation_text=f"Threshold = {threshold:.5f}",
                annotation_font_color=RED,
                annotation_font_size=10,
                annotation_position="bottom right",
            )

        # Failure line
        if t_fail:
            fig.add_vline(
                x=t_fail.timestamp() * 1000, line_color=RED, line_width=2.5,
                annotation_text="⚡ FAILURE",
                annotation_font_color=RED,
                annotation_font_size=11,
                annotation_position="top left",
            )

        # First alarm line
        if result and result.get("FAT") and result.get("VLT_hours", 0) > 0:
            fat = result["FAT"]
            vlt = result["VLT_hours"]
            fig.add_vline(
                x=pd.Timestamp(fat).timestamp() * 1000, line_dash="dash",
                line_color=GREEN, line_width=2,
                annotation_text=f"First Alarm  {vlt:.1f}h lead",
                annotation_font_color=GREEN,
                annotation_font_size=10,
                annotation_position="top right",
            )

        lo = base_layout()
        lo.update(
            xaxis_title="Time",
            yaxis_title="Anomaly Score (Isolation Forest)",
            showlegend=True,
        )
        fig.update_layout(**lo)

        vlt_str = (f"Lead Time: {result['VLT_hours']:.1f}h"
                   if result and result.get("VLT_hours", 0) > 0 else "")
        return fig, vlt_str

    # ── Panel D: Influence text ───────────────────────────────────────────────
    @app.callback(
        Output("influence-text", "children"),
        [Input("corr-a", "value"),
         Input("corr-b", "value")],
    )
    def cb_influence(col_a, col_b):
        if not col_a or not col_b:
            return "Select channels A and B in the correlation panel."
        if col_a not in df.columns or col_b not in df.columns:
            return "Invalid channel selection."

        s_a = df[col_a].dropna()
        s_b = df[col_b].dropna()
        idx = s_a.index.intersection(s_b.index)
        if len(idx) < 10:
            return "Not enough overlapping data."

        a    = s_a.loc[idx].values.astype(float)
        b    = s_b.loc[idx].values.astype(float)
        r, p = scipy_stats.pearsonr(a, b)

        # Lagged cross-correlation to find lead-lag
        a_n = (a - a.mean()) / (a.std() + 1e-12)
        b_n = (b - b.mean()) / (b.std() + 1e-12)

        lag_max = 20
        lags, lag_corrs = list(range(-lag_max, lag_max + 1)), []
        for lag in lags:
            if lag < 0:
                c = float(np.corrcoef(a_n[:lag], b_n[-lag:])[0, 1])
            elif lag == 0:
                c = float(np.corrcoef(a_n, b_n)[0, 1])
            else:
                c = float(np.corrcoef(a_n[lag:], b_n[:-lag])[0, 1])
            lag_corrs.append(c if np.isfinite(c) else 0.0)

        best_idx = int(np.argmax(np.abs(lag_corrs)))
        best_lag = lags[best_idx]
        best_r   = lag_corrs[best_idx]

        strength  = ("weakly" if abs(r) < 0.3 else
                     "moderately" if abs(r) < 0.6 else "strongly")
        direction = "positively" if r > 0 else "negatively"

        if best_lag == 0:
            lag_msg = "They respond simultaneously."
        elif best_lag > 0:
            lag_msg = (f"➜ {col_a} leads {col_b} by ~{best_lag} windows. "
                       f"Changes in {col_a} appear first.")
        else:
            lag_msg = (f"➜ {col_b} leads {col_a} by ~{abs(best_lag)} windows. "
                       f"Changes in {col_b} appear first.")

        causal = (
            "⚠️ Strong influence — these channels likely share a causal link."
            if abs(best_r) > 0.5 else
            "ℹ️ No dominant influence detected at tested lags."
        )

        return (
            f"📊 {col_a} and {col_b} are {direction} "
            f"{strength} correlated (r = {r:.3f}, p = {p:.4f}). "
            f"{lag_msg} Peak lagged r = {best_r:.3f} at lag {best_lag}. {causal}"
        )

    return app


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    launch_dashboard("2nd_test", "isolation_forest", port=8050, debug=False)

