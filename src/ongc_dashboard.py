# src/ongc_dashboard.py
"""
ONGC Solar Turbine — Explainable Predictive Maintenance Dashboard
=================================================================
5-tab industrial monitoring dashboard for LPC vibration data.

Usage:
    from src.ongc_dashboard import launch_ongc_dashboard
    launch_ongc_dashboard(
        before_file="data/raw/ONGC/Before_Shutdown.xlsx",
        after_file="data/raw/ONGC/After_Shutdown.xlsx",
        port=8050
    )

Then open: http://127.0.0.1:8050
"""

import numpy as np
import pandas as pd
import os
import copy
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# ── Channel definitions ───────────────────────────────────────────────────────
CHANNELS = {
    'LPC_DE_X_Vib':  {'label': 'Drive End — X Axis',     'short': 'DE-X',   'unit': 'mm/s', 'color': '#3b82f6', 'type': 'vibration'},
    'LPC_DE_Y_Vib':  {'label': 'Drive End — Y Axis',     'short': 'DE-Y',   'unit': 'mm/s', 'color': '#ef4444', 'type': 'vibration'},
    'LPC_NDE_X_Vib': {'label': 'Non-Drive End — X Axis', 'short': 'NDE-X',  'unit': 'mm/s', 'color': '#22c55e', 'type': 'vibration'},
    'LPC_NDE_Y_Vib': {'label': 'Non-Drive End — Y Axis', 'short': 'NDE-Y',  'unit': 'mm/s', 'color': '#f59e0b', 'type': 'vibration'},
    'Ncp':           {'label': 'Compressor Speed',        'short': 'Speed',  'unit': 'RPM',  'color': '#a855f7', 'type': 'speed'},
}

ISO_ALERT  = 7.1
ISO_ALARM  = 11.2
ISO_DANGER = 18.0


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def launch_ongc_dashboard(before_file: str,
                           after_file: str,
                           port: int = 8050,
                           debug: bool = False):
    """Launch the ONGC monitoring dashboard."""
    try:
        import dash
        import dash_bootstrap_components as dbc
    except ImportError:
        raise ImportError("pip install dash dash-bootstrap-components")

    print(f"\n{'─'*60}")
    print("  Loading ONGC Solar Turbine data ...")
    print(f"{'─'*60}")

    data = _load_and_process(before_file, after_file)
    app  = _build_app(data)

    print(f"\n{'='*60}")
    print(f"  Dashboard ready  →  http://127.0.0.1:{port}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    app.run(debug=debug, port=port, use_reloader=False)


# ─────────────────────────────────────────────────────────────────────────────
# Data loading and processing
# ─────────────────────────────────────────────────────────────────────────────

def _parse_ts(s) -> pd.Timestamp:
    if isinstance(s, pd.Timestamp): return s
    if pd.isna(s): return pd.NaT
    s = str(s).strip().replace('# ', ' ').replace('#', ' ')
    for fmt in ['%d-%m-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S', '%d-%m-%Y %H:%M',
                '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M']:
        try: return pd.to_datetime(s, format=fmt)
        except: pass
    try: return pd.to_datetime(s)
    except: return pd.NaT


def _load_file(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    # Drop fully-empty columns and de-duplicate any repeated column names
    # so that pd.concat later in _load_and_process has a unique Index.
    df = df.dropna(axis=1, how='all')
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    df = df.rename(columns={df.columns[0]: 'timestamp'})
    # Rename sensor columns to standard names
    col_map = {}
    for i, col in enumerate(df.columns[1:], 1):
        col_str = str(col).strip()
        if 'DE_X' in col_str or col_str == df.columns[1]:
            col_map[col] = 'LPC_DE_X_Vib'
        elif 'DE_Y' in col_str:
            col_map[col] = 'LPC_DE_Y_Vib'
        elif 'NDE_X' in col_str:
            col_map[col] = 'LPC_NDE_X_Vib'
        elif 'NDE_Y' in col_str:
            col_map[col] = 'LPC_NDE_Y_Vib'
        elif 'Ncp' in col_str or 'ncp' in col_str.lower() or 'speed' in col_str.lower() or 'rpm' in col_str.lower():
            col_map[col] = 'Ncp'
    df = df.rename(columns=col_map)
    df['timestamp'] = df['timestamp'].apply(_parse_ts)
    df = df.dropna(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    return df


def _load_and_process(before_path: str, after_path: str) -> Dict:
    df_b = _load_file(before_path)
    df_a = _load_file(after_path)
    shutdown_time = df_b['timestamp'].max()

    df_b['phase'] = 'operating'
    df_a['phase'] = 'post_shutdown'
    for col in df_b.columns:
        if col not in df_a.columns:
            df_a[col] = np.nan

    df = pd.concat([df_b, df_a], ignore_index=True)
    df = df.sort_values('timestamp').reset_index(drop=True)

    sensor_cols = [c for c in CHANNELS.keys() if c in df.columns]
    vib_cols    = [c for c in sensor_cols if CHANNELS[c]['type'] == 'vibration']

    # Baseline — first 2 days of operating data
    op_df  = df[df['phase'] == 'operating'].copy()
    b_end  = op_df['timestamp'].min() + pd.Timedelta(days=2)
    b_data = op_df[op_df['timestamp'] <= b_end]

    baseline = {}
    for col in sensor_cols:
        s  = b_data[col].dropna()
        mu = float(s.mean())
        sd = float(s.std()) + 1e-12
        baseline[col] = {
            'mean':   mu, 'std':    sd,
            'ucl_3s': mu + 3*sd, 'lcl_3s': max(0.0, mu - 3*sd),
            'ucl_2s': mu + 2*sd, 'lcl_2s': max(0.0, mu - 2*sd),
        }

    # Anomaly scoring — train on first 40% of operating data
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import RobustScaler

    X_op  = op_df[vib_cols].ffill().bfill().values
    n_tr  = max(50, int(len(X_op) * 0.40))
    scaler = RobustScaler()
    X_tr_s = scaler.fit_transform(X_op[:n_tr])
    X_op_s = scaler.transform(X_op)
    iforest = IsolationForest(n_estimators=200, contamination='auto',
                               random_state=42, n_jobs=-1)
    iforest.fit(X_tr_s)
    raw = -iforest.decision_function(X_op_s)
    lo, hi = raw.min(), raw.max()
    scores_norm = (raw - lo) / (hi - lo + 1e-12)
    score_series = pd.Series(scores_norm, index=op_df['timestamp'].values, name='IF_Score')

    # 3σ violation rate (fraction of vib channels above UCL per timestep)
    ucl_viol = pd.Series(0.0, index=op_df.index)
    for col in vib_cols:
        ucl_viol += (op_df[col] > baseline[col]['ucl_3s']).astype(float)
    ucl_viol = ucl_viol / len(vib_cols)
    ucl_series = pd.Series(ucl_viol.values, index=op_df['timestamp'].values, name='UCL_Rate')

    # First alarm (IF score > 95th percentile, sustained 5 steps)
    thr_95 = float(np.percentile(scores_norm, 95))
    above  = scores_norm > thr_95
    first_alarm = None
    for i in range(len(above) - 4):
        if np.all(above[i:i+5]):
            first_alarm = op_df['timestamp'].iloc[i]
            break

    lead_hours = ((shutdown_time - first_alarm).total_seconds() / 3600
                  if first_alarm else 0.0)

    # Failure evolution (σ deviations at each window)
    windows_h  = [24, 12, 6, 3, 1, 0]
    win_labels = ['T−24h', 'T−12h', 'T−6h', 'T−3h', 'T−1h', 'Shutdown']
    evo_data   = {}
    for h, lbl in zip(windows_h, win_labels):
        t_win = shutdown_time - pd.Timedelta(hours=h)
        mask  = ((op_df['timestamp'] >= t_win - pd.Timedelta(minutes=5)) &
                 (op_df['timestamp'] <= t_win + pd.Timedelta(minutes=5)))
        w = op_df[mask]
        if len(w) == 0:
            idx = (op_df['timestamp'] - t_win).abs().idxmin()
            w   = op_df.iloc[[idx]]
        evo_data[lbl] = {}
        for col in vib_cols:
            val = float(w[col].mean())
            dev = (val - baseline[col]['mean']) / baseline[col]['std']
            evo_data[lbl][col] = round(dev, 2)

    # DRI — rolling mean z-score across all vib channels
    z_all = pd.DataFrame(index=op_df.index)
    for col in vib_cols:
        z_all[col] = (op_df[col] - baseline[col]['mean']) / baseline[col]['std']
    dri_raw    = z_all.mean(axis=1)
    dri_smooth = dri_raw.rolling(window=360, min_periods=1).mean()
    dri_series = pd.Series(dri_smooth.values, index=op_df['timestamp'].values, name='DRI')

    # Fault propagation sequence
    fault_seq = []
    for col in vib_cols:
        ucl    = baseline[col]['ucl_3s']
        exceed = op_df[op_df[col] > ucl]
        if len(exceed) > 0:
            meta = CHANNELS.get(col, {})
            fault_seq.append({
                'col':   col,
                'label': meta.get('label', col),
                'short': meta.get('short', col),
                'first': exceed['timestamp'].iloc[0],
                'peak':  float(op_df[col].max()),
                'ucl':   ucl,
            })
    fault_seq.sort(key=lambda x: x['first'])

    # Channel contributions (deviation-based %)
    contribs = []
    total_dev = 0.0
    for col in vib_cols:
        s   = op_df[col].dropna()
        dev = max(0.0, float(s.max()) - baseline[col]['mean'])
        total_dev += dev
        # Behavior classification
        vals  = s.values
        z     = (vals - baseline[col]['mean']) / baseline[col]['std']
        slope = float(np.polyfit(np.arange(len(z)), z, 1)[0]) if len(z) > 1 else 0
        osc   = float(np.std(np.diff(vals))) if len(vals) > 1 else 0
        if z.max() < 1.5:
            behavior = 'Normal'
        elif slope > 0.0005 and z[-len(z)//4:].mean() > 1:
            behavior = 'Gradual Drift'
        elif osc > baseline[col]['std'] * 0.5 and z.max() > 3:
            behavior = 'Oscillatory'
        elif z.max() > 5 and z[-len(z)//4:].mean() < 2:
            behavior = 'Sudden Spike'
        else:
            behavior = 'Sustained High'

        meta = CHANNELS.get(col, {})
        contribs.append({
            'col': col, 'label': meta.get('label', col),
            'short': meta.get('short', col), 'unit': meta.get('unit', ''),
            'color': meta.get('color', '#aaa'),
            'behavior': behavior, 'peak': float(s.max()),
            'mean': baseline[col]['mean'], 'dev': dev, 'pct': 0.0,
        })

    for c in contribs:
        c['pct'] = (c['dev'] / total_dev * 100) if total_dev > 0 else 0.0
    contribs.sort(key=lambda x: x['dev'], reverse=True)

    # Natural language explanation
    top2   = contribs[:2]
    top_str = ' and '.join(f"{c['label']} ({c['behavior']})" for c in top2)
    seq_str = ''
    if len(fault_seq) >= 2:
        seq_str = (f" {fault_seq[0]['short']} exceeded control limits first at "
                   f"{fault_seq[0]['first'].strftime('%d-%b %H:%M')}, "
                   f"followed by {fault_seq[1]['short']}.")
    nl = (f"⚠️ Emergency Shutdown — High Vibration. "
          f"Anomaly driven by {top_str}.{seq_str} "
          f"System raised alert {lead_hours:.1f} hours before shutdown. "
          f"Drive End bearing vibration peaked at "
          f"{contribs[0]['peak']:.1f} mm/s "
          f"({contribs[0]['peak']/contribs[0]['mean']*100:.0f}% of baseline). "
          f"Recommend immediate inspection of Drive End bearing assembly, "
          f"lubrication system, and shaft alignment.")

    # Peak violations
    n_channels_alarm = sum(
        1 for col in vib_cols
        if float(op_df[col].max()) > baseline[col]['ucl_3s']
    )

    print(f"  Processed: {len(df)} rows | "
          f"Shutdown: {shutdown_time} | "
          f"First alarm: {first_alarm} | "
          f"Lead time: {lead_hours:.1f}h")

    return {
        'df': df, 'op_df': op_df,
        'shutdown_time': shutdown_time,
        'baseline': baseline,
        'sensor_cols': sensor_cols,
        'vib_cols': vib_cols,
        'score_series': score_series,
        'ucl_series': ucl_series,
        'thr_95': thr_95,
        'first_alarm': first_alarm,
        'lead_hours': lead_hours,
        'evo_data': evo_data,
        'win_labels': win_labels,
        'dri_series': dri_series,
        'fault_seq': fault_seq,
        'contribs': contribs,
        'nl': nl,
        'n_channels_alarm': n_channels_alarm,
    }


# ─────────────────────────────────────────────────────────────────────────────
# App builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_app(D: Dict):
    import dash
    from dash import dcc, html, Input, Output, State
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go

    # ── Theme ─────────────────────────────────────────────────────────────────
    BG     = '#0a0b0f'
    CARD   = '#12141c'
    CARD2  = '#1a1d2b'
    BORDER = '#1e2235'
    TEXT   = '#dde2f5'
    MUTED  = '#5a6180'
    ACCENT = '#4f8ef7'
    GREEN  = '#22c55e'
    RED    = '#ef4444'
    ORANGE = '#f59e0b'
    PURPLE = '#a855f7'
    YELLOW = '#eab308'
    PLOT   = '#0d0f17'
    GRID   = '#151824'

    BASE_LAYOUT = dict(
        paper_bgcolor=CARD, plot_bgcolor=PLOT,
        font=dict(color=TEXT, family='Inter, sans-serif', size=11),
        margin=dict(l=55, r=20, t=40, b=50),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=CARD2, font_color=TEXT, bordercolor=BORDER),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=TEXT, size=10),
                    orientation='h', y=-0.18,
                    itemclick='toggle', itemdoubleclick='toggleothers'),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID,
                   tickfont=dict(color=MUTED, size=10),
                   title_font=dict(color=MUTED)),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID,
                   tickfont=dict(color=MUTED, size=10),
                   title_font=dict(color=MUTED)),
    )

    def bl(title=''):
        lo = copy.deepcopy(BASE_LAYOUT)
        if title:
            lo['title'] = dict(text=title, font=dict(size=11, color=MUTED), x=0.01)
        return lo

    shutdown_str   = str(D['shutdown_time'])
    first_alarm_str = str(D['first_alarm']) if D['first_alarm'] else None

    # ── Helper: add shutdown + alarm vlines to any figure ────────────────────
    def add_event_lines(fig, show_alarm=True, row=None, col=None):
        kw = dict(row=row, col=col) if row else {}
        fig.add_vline(x=shutdown_str, line_dash='solid',
                      line_color=RED, line_width=2.5,
                      annotation_text='⚡ SHUTDOWN',
                      annotation_font_color=RED,
                      annotation_font_size=10,
                      annotation_position='top left', **kw)
        if show_alarm and first_alarm_str:
            fig.add_vline(x=first_alarm_str, line_dash='dash',
                          line_color=GREEN, line_width=2,
                          annotation_text=f'Alert ({D["lead_hours"]:.1f}h lead)',
                          annotation_font_color=GREEN,
                          annotation_font_size=10,
                          annotation_position='top right', **kw)

    # ── Reusable panel wrapper ────────────────────────────────────────────────
    def panel(title, children, style_extra=None):
        s = {'background': CARD, 'border': f'1px solid {BORDER}',
             'borderRadius': '10px', 'padding': '16px 18px', 'marginBottom': '14px'}
        if style_extra:
            s.update(style_extra)
        return html.Div([
            html.Div(title, style={'fontSize': '10px', 'color': MUTED,
                                   'fontWeight': '700', 'letterSpacing': '2px',
                                   'textTransform': 'uppercase', 'marginBottom': '10px'}),
            children,
        ], style=s)

    def kpi(label, value, sub='', color=TEXT):
        return html.Div([
            html.Div(label, style={'fontSize': '9px', 'color': MUTED,
                                   'fontWeight': '700', 'letterSpacing': '1.5px',
                                   'textTransform': 'uppercase', 'marginBottom': '6px'}),
            html.Div(value, style={'fontSize': '24px', 'fontWeight': '800',
                                   'color': color, 'fontFamily': 'monospace',
                                   'lineHeight': '1'}),
            html.Div(sub, style={'fontSize': '10px', 'color': MUTED, 'marginTop': '4px'}),
        ], style={'background': CARD, 'border': f'1px solid {BORDER}',
                  'borderTop': f'2px solid {color}',
                  'borderRadius': '8px', 'padding': '14px 16px', 'flex': '1'})

    def graph(gid, height='360px'):
        return dcc.Graph(id=gid,
                         config={'scrollZoom': True, 'displaylogo': False,
                                 'displayModeBar': True,
                                 'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                                 'toImageButtonOptions': {'format': 'png',
                                                          'scale': 2,
                                                          'filename': gid}},
                         style={'height': height})

    # ── Channel checklist options ─────────────────────────────────────────────
    vib_opts = [
        {'label': html.Span(CHANNELS[c]['short'],
                            style={'color': CHANNELS[c]['color'],
                                   'fontSize': '12px', 'fontFamily': 'monospace'}),
         'value': c}
        for c in D['vib_cols'] if c in CHANNELS
    ]
    all_opts = [
        {'label': html.Span(CHANNELS[c]['short'],
                            style={'color': CHANNELS[c]['color'],
                                   'fontSize': '12px', 'fontFamily': 'monospace'}),
         'value': c}
        for c in D['sensor_cols'] if c in CHANNELS
    ]

    # ── Tab styles ────────────────────────────────────────────────────────────
    tab_style = {
        'background': CARD2, 'color': MUTED,
        'border': f'1px solid {BORDER}', 'borderBottom': 'none',
        'padding': '8px 16px', 'fontSize': '11px', 'fontWeight': '600',
        'letterSpacing': '0.5px',
    }
    tab_selected = {**tab_style, 'background': CARD, 'color': TEXT,
                    'borderTop': f'2px solid {ACCENT}'}

    dd_style = {'background': PLOT, 'color': TEXT,
                'border': f'1px solid {BORDER}', 'fontSize': '11px',
                'borderRadius': '6px'}

    # ── App ───────────────────────────────────────────────────────────────────
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        title='ONGC Solar Turbine Monitor',
        suppress_callback_exceptions=True,
    )

    app.layout = html.Div(style={
        'background': BG, 'minHeight': '100vh',
        'fontFamily': 'Inter, sans-serif', 'color': TEXT,
        'display': 'flex', 'flexDirection': 'column',
    }, children=[

        # ── Top bar ───────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span('◈ ', style={'color': ACCENT}),
                html.Span('ONGC SOLAR TURBINE MONITOR', style={
                    'color': ACCENT, 'fontSize': '11px',
                    'fontWeight': '700', 'letterSpacing': '3px'}),
            ]),
            html.Div(
                f"LPC Bearing Vibration  —  "
                f"08-Nov-2023 to 13-Nov-2023  —  "
                f"Emergency Shutdown: {D['shutdown_time'].strftime('%d-%b-%Y %H:%M')}",
                style={'color': MUTED, 'fontSize': '12px'}
            ),
            html.Div('● LIVE', style={'color': GREEN, 'fontSize': '11px',
                                      'fontWeight': '700', 'letterSpacing': '2px'}),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between',
            'alignItems': 'center', 'background': '#080a10',
            'padding': '10px 20px', 'borderBottom': f'1px solid {BORDER}',
        }),

        # ── KPI bar ───────────────────────────────────────────────────────────
        html.Div([
            kpi('Lead Time to Shutdown',
                f"{D['lead_hours']:.1f}h",
                f"Alert: {D['first_alarm'].strftime('%d-%b %H:%M') if D['first_alarm'] else 'N/A'}",
                GREEN),
            kpi('Peak Vibration',
                f"{max(D['op_df'][c].max() for c in D['vib_cols']):.1f} mm/s",
                'Drive End — Y Axis', RED),
            kpi('Channels in Alarm',
                f"{D['n_channels_alarm']}/4",
                'Exceeded UCL (3σ)', ORANGE),
            kpi('Event Type',
                'ESD', 'Emergency Shutdown', RED),
            kpi('Data Points',
                f"{len(D['op_df']):,}",
                '10-sec sampling, 5 days', MUTED),
        ], style={
            'display': 'flex', 'gap': '10px',
            'padding': '12px 16px',
            'background': '#080a10',
            'borderBottom': f'1px solid {BORDER}',
        }),

        # ── Tabs ──────────────────────────────────────────────────────────────
        html.Div([
            dcc.Tabs(
                id='main-tabs', value='tab-overview',
                style={'background': CARD2},
                children=[
                    dcc.Tab(label='① Overview',          value='tab-overview',   style=tab_style, selected_style=tab_selected),
                    dcc.Tab(label='② Parameter Trends',  value='tab-trends',     style=tab_style, selected_style=tab_selected),
                    dcc.Tab(label='③ Failure Evolution', value='tab-evolution',  style=tab_style, selected_style=tab_selected),
                    dcc.Tab(label='④ Correlation',       value='tab-corr',       style=tab_style, selected_style=tab_selected),
                    dcc.Tab(label='⑤ Anomaly Score',     value='tab-score',      style=tab_style, selected_style=tab_selected),
                ],
            ),
            html.Div(id='tab-content', style={
                'padding': '16px', 'flex': '1', 'overflowY': 'auto',
            }),
        ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column',
                  'overflow': 'hidden', 'minHeight': '0'}),

        # ── Footer ────────────────────────────────────────────────────────────
        html.Div([
            html.Span(
                'ONGC Solar Turbine LPC  —  Predictive Maintenance Platform  —  '
                'NASA IMS Benchmark + Real SCADA Data',
                style={'fontSize': '10px', 'color': MUTED}
            ),
            html.Button(
                '⬇ Export Report',
                id='btn-export',
                n_clicks=0,
                style={
                    'background': f'rgba(79,142,247,0.15)',
                    'color': ACCENT,
                    'border': f'1px solid {ACCENT}',
                    'borderRadius': '6px',
                    'padding': '5px 14px',
                    'fontSize': '11px',
                    'fontWeight': '700',
                    'cursor': 'pointer',
                }
            ),
            html.Div(id='export-status', style={
                'fontSize': '11px', 'color': GREEN, 'marginLeft': '10px'
            }),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between',
            'alignItems': 'center',
            'background': '#080a10', 'padding': '8px 20px',
            'borderTop': f'1px solid {BORDER}',
        }),
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB ROUTING CALLBACK
    # ─────────────────────────────────────────────────────────────────────────

    @app.callback(
        Output('tab-content', 'children'),
        Input('main-tabs', 'value'),
    )
    def render_tab(tab):
        if tab == 'tab-overview':
            return _tab_overview(D, BG, CARD, CARD2, BORDER, TEXT, MUTED,
                                 ACCENT, GREEN, RED, ORANGE, PURPLE, PLOT, GRID,
                                 panel, graph, kpi, all_opts, vib_opts, dd_style)
        elif tab == 'tab-trends':
            return _tab_trends(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                                GREEN, RED, ORANGE, PLOT, panel, graph,
                                all_opts, vib_opts, dd_style)
        elif tab == 'tab-evolution':
            return _tab_evolution(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                                   GREEN, RED, ORANGE, PURPLE, PLOT, panel, graph)
        elif tab == 'tab-corr':
            return _tab_correlation(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                                     GREEN, RED, ORANGE, PURPLE, PLOT, panel, graph,
                                     all_opts, dd_style)
        elif tab == 'tab-score':
            return _tab_score(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                               GREEN, RED, ORANGE, PURPLE, PLOT, panel, graph)
        return html.Div('Select a tab')

    # ─────────────────────────────────────────────────────────────────────────
    # OVERVIEW CALLBACKS
    # ─────────────────────────────────────────────────────────────────────────

    @app.callback(
        Output('overview-main-chart', 'figure'),
        Input('overview-channel-select', 'value'),
    )
    def cb_overview_main(selected):
        selected = selected or D['sensor_cols'][:4]
        fig = go.Figure()
        op  = D['op_df']

        # Shaded regions: normal / degrading / critical
        t_start  = str(op['timestamp'].min())
        onset_t  = str(D['shutdown_time'] - pd.Timedelta(hours=72))
        critical_t = str(D['shutdown_time'] - pd.Timedelta(hours=24))

        fig.add_vrect(x0=t_start, x1=onset_t,
                      fillcolor='rgba(34,197,94,0.04)',
                      layer='below', line_width=0,
                      annotation_text='Normal', annotation_font_color='#22c55e',
                      annotation_font_size=9)
        fig.add_vrect(x0=onset_t, x1=critical_t,
                      fillcolor='rgba(245,158,11,0.06)',
                      layer='below', line_width=0,
                      annotation_text='Degrading', annotation_font_color='#f59e0b',
                      annotation_font_size=9)
        fig.add_vrect(x0=critical_t, x1=shutdown_str,
                      fillcolor='rgba(239,68,68,0.08)',
                      layer='below', line_width=0,
                      annotation_text='Critical', annotation_font_color=RED,
                      annotation_font_size=9)

        for col in selected:
            if col not in op.columns:
                continue
            meta   = CHANNELS.get(col, {})
            color  = meta.get('color', ACCENT)
            label  = meta.get('label', col)
            unit   = meta.get('unit', '')
            ch_type = meta.get('type', '')
            s      = op[['timestamp', col]].dropna()

            fig.add_trace(go.Scatter(
                x=list(s['timestamp']), y=list(s[col]),
                name=label,
                line=dict(color=color, width=1.4),
                opacity=0.9,
                hovertemplate=f'<b>{label}</b><br>%{{x}}<br>%{{y:.2f}} {unit}<extra></extra>',
            ))

            # UCL / LCL control lines
            if col in D['baseline'] and ch_type == 'vibration':
                ucl = D['baseline'][col]['ucl_3s']
                lcl = D['baseline'][col]['lcl_3s']
                mu  = D['baseline'][col]['mean']
                x_range = [str(op['timestamp'].min()), str(D['shutdown_time'])]
                fig.add_trace(go.Scatter(
                    x=x_range, y=[ucl, ucl], mode='lines',
                    line=dict(color=RED, width=1, dash='dash'),
                    showlegend=False,
                    hovertemplate=f'UCL (3σ) = {ucl:.2f} mm/s<extra></extra>',
                ))
                fig.add_trace(go.Scatter(
                    x=x_range, y=[mu, mu], mode='lines',
                    line=dict(color=MUTED, width=0.8, dash='dot'),
                    showlegend=False,
                    hovertemplate=f'Baseline Mean = {mu:.2f} mm/s<extra></extra>',
                ))
                # ISO thresholds (only once)
                if col == D['vib_cols'][0]:
                    for iso_val, iso_label, iso_color in [
                        (ISO_ALERT, 'ISO Alert 7.1', '#22c55e'),
                        (ISO_ALARM, 'ISO Alarm 11.2', '#f59e0b'),
                        (ISO_DANGER, 'ISO Danger 18.0', '#ef4444'),
                    ]:
                        fig.add_trace(go.Scatter(
                            x=x_range, y=[iso_val, iso_val], mode='lines',
                            line=dict(color=iso_color, width=0.8, dash='dashdot'),
                            name=iso_label, showlegend=True,
                            opacity=0.5,
                            hovertemplate=f'{iso_label} = {iso_val} mm/s<extra></extra>',
                        ))

        # Event lines
        fig.add_vline(x=shutdown_str, line_dash='solid',
                      line_color=RED, line_width=2.5,
                      annotation_text='⚡ SHUTDOWN',
                      annotation_font_color=RED, annotation_font_size=10)
        if first_alarm_str:
            fig.add_vline(x=first_alarm_str, line_dash='dash',
                          line_color=GREEN, line_width=2,
                          annotation_text=f'Alert ({D["lead_hours"]:.1f}h lead)',
                          annotation_font_color=GREEN, annotation_font_size=10)

        lo = bl()
        lo.update(xaxis_title='Time', yaxis_title='Vibration (mm/s) / Speed (RPM)',
                  showlegend=True)
        fig.update_layout(**lo)
        return fig

    @app.callback(
        Output('overview-channel-select', 'value'),
        [Input('overview-btn-all', 'n_clicks'),
         Input('overview-btn-vib', 'n_clicks'),
         Input('overview-btn-none', 'n_clicks')],
        prevent_initial_call=True,
    )
    def cb_overview_toggle(n_all, n_vib, n_none):
        from dash import ctx
        t = ctx.triggered_id
        if t == 'overview-btn-all':  return D['sensor_cols']
        if t == 'overview-btn-vib':  return D['vib_cols']
        if t == 'overview-btn-none': return []
        return D['sensor_cols'][:4]

    # ─────────────────────────────────────────────────────────────────────────
    # TRENDS CALLBACKS
    # ─────────────────────────────────────────────────────────────────────────

    @app.callback(
        Output('trends-chart', 'figure'),
        [Input('trends-channel-dd', 'value'),
         Input('trends-time-range', 'value')],
    )
    def cb_trends(col, time_range_h):
        if not col: col = D['vib_cols'][0]
        meta  = CHANNELS.get(col, {})
        color = meta.get('color', ACCENT)
        label = meta.get('label', col)
        unit  = meta.get('unit', '')
        op    = D['op_df'].copy()

        # Apply time window
        time_range_h = time_range_h or 120
        if time_range_h < 200:
            cutoff = D['shutdown_time'] - pd.Timedelta(hours=time_range_h)
            op = op[op['timestamp'] >= cutoff]

        s       = op[['timestamp', col]].dropna()
        trend   = s[col].rolling(window=360, min_periods=1).mean()
        mu      = D['baseline'][col]['mean'] if col in D['baseline'] else s[col].mean()
        sigma   = D['baseline'][col]['std']  if col in D['baseline'] else s[col].std()
        ucl_3s  = D['baseline'][col]['ucl_3s'] if col in D['baseline'] else mu + 3*sigma
        lcl_3s  = D['baseline'][col]['lcl_3s'] if col in D['baseline'] else max(0, mu - 3*sigma)

        fig = go.Figure()

        # Control band
        fig.add_hrect(y0=lcl_3s, y1=ucl_3s,
                      fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:],16)},0.04)',
                      line_width=0, layer='below')

        # Raw signal
        fig.add_trace(go.Scatter(
            x=list(s['timestamp']), y=list(s[col]),
            name='Raw Signal', line=dict(color=color, width=1.0), opacity=0.4,
            hovertemplate=f'%{{x}}<br>{label}: %{{y:.2f}} {unit}<extra></extra>',
        ))

        # Rolling mean
        fig.add_trace(go.Scatter(
            x=list(s['timestamp']), y=list(trend),
            name='1-hr Rolling Mean', line=dict(color=color, width=2.5),
            hovertemplate=f'%{{x}}<br>Trend: %{{y:.2f}} {unit}<extra></extra>',
        ))

        # Control lines
        x_range = [str(op['timestamp'].min()), str(D['shutdown_time'])]
        for val, lbl, c, dash in [
            (ucl_3s, f'UCL 3σ = {ucl_3s:.2f}', RED, 'dash'),
            (mu,     f'Mean = {mu:.2f}',         MUTED, 'dot'),
            (lcl_3s, f'LCL 3σ = {lcl_3s:.2f}',  ORANGE, 'dash'),
        ]:
            fig.add_trace(go.Scatter(
                x=x_range, y=[val, val], mode='lines',
                name=lbl, line=dict(color=c, width=1.2, dash=dash),
                hovertemplate=f'{lbl}<extra></extra>',
            ))

        # ISO lines for vibration
        if meta.get('type') == 'vibration':
            for iso_val, iso_lbl, iso_c in [
                (ISO_ALERT,  f'ISO Alert {ISO_ALERT}',   '#22c55e'),
                (ISO_ALARM,  f'ISO Alarm {ISO_ALARM}',   '#f59e0b'),
                (ISO_DANGER, f'ISO Danger {ISO_DANGER}', '#ef4444'),
            ]:
                fig.add_trace(go.Scatter(
                    x=x_range, y=[iso_val, iso_val], mode='lines',
                    name=iso_lbl, line=dict(color=iso_c, width=1, dash='dashdot'),
                    opacity=0.6,
                    hovertemplate=f'{iso_lbl} mm/s<extra></extra>',
                ))

        # Event lines
        if D['shutdown_time'] >= op['timestamp'].min():
            fig.add_vline(x=shutdown_str, line_dash='solid',
                          line_color=RED, line_width=2,
                          annotation_text='⚡ SHUTDOWN',
                          annotation_font_color=RED, annotation_font_size=10)
        if first_alarm_str and D['first_alarm'] >= op['timestamp'].min():
            fig.add_vline(x=first_alarm_str, line_dash='dash',
                          line_color=GREEN, line_width=2,
                          annotation_text='Alert',
                          annotation_font_color=GREEN, annotation_font_size=10)

        lo = bl()
        lo.update(xaxis_title='Time', yaxis_title=f'{label} ({unit})', showlegend=True)
        fig.update_layout(**lo)
        return fig

    # ─────────────────────────────────────────────────────────────────────────
    # EVOLUTION CALLBACKS
    # ─────────────────────────────────────────────────────────────────────────

    @app.callback(
        Output('evo-heatmap', 'figure'),
        Input('main-tabs', 'value'),
    )
    def cb_evo_heatmap(tab):
        if tab != 'tab-evolution':
            return go.Figure()

        evo      = D['evo_data']
        labels   = D['win_labels']
        channels = D['vib_cols']
        z_matrix = []
        y_labels = []

        for col in channels:
            row = [evo[lbl].get(col, 0.0) for lbl in labels]
            z_matrix.append(row)
            meta = CHANNELS.get(col, {})
            y_labels.append(meta.get('short', col))

        z_arr = np.array(z_matrix)

        # Colorscale: blue(normal) → white → red(critical)
        colorscale = [
            [0.0,  '#1d4ed8'],
            [0.3,  '#3b82f6'],
            [0.5,  '#f8fafc'],
            [0.7,  '#f59e0b'],
            [0.85, '#ef4444'],
            [1.0,  '#7f1d1d'],
        ]

        fig = go.Figure(go.Heatmap(
            z=z_arr,
            x=labels,
            y=y_labels,
            colorscale=colorscale,
            zmid=0,
            zmin=-2,
            zmax=max(10, float(z_arr.max())),
            text=np.round(z_arr, 1),
            texttemplate='%{text}σ',
            textfont=dict(size=11, color='white'),
            hovertemplate='<b>%{y}</b> at <b>%{x}</b><br>Deviation: %{z:.2f}σ<extra></extra>',
            colorbar=dict(
                title=dict(text='Deviation (σ)', font=dict(color=MUTED)),
                tickfont=dict(color=MUTED), thickness=12,
            ),
        ))

        lo = copy.deepcopy(BASE_LAYOUT)
        lo.update(
            title=dict(text='Parameter Deviation from Baseline (σ units) — Failure Evolution',
                       font=dict(size=11, color=MUTED), x=0.01),
            margin=dict(l=120, r=60, t=50, b=60),
            xaxis=dict(gridcolor=GRID, tickfont=dict(color=TEXT, size=11),
                       title_font=dict(color=MUTED)),
            yaxis=dict(gridcolor=GRID, tickfont=dict(color=TEXT, size=11),
                       title_font=dict(color=MUTED)),
        )
        lo.pop('legend', None)
        lo.pop('hovermode', None)
        fig.update_layout(**lo)
        return fig

    @app.callback(
        Output('evo-dri', 'figure'),
        Input('main-tabs', 'value'),
    )
    def cb_evo_dri(tab):
        if tab != 'tab-evolution':
            return go.Figure()

        dri = D['dri_series']
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=list(dri.index), y=list(dri.values),
            name='DRI (Deterioration Rate Index)',
            line=dict(color=PURPLE, width=2.0),
            fill='tozeroy', fillcolor='rgba(168,85,247,0.07)',
            hovertemplate='%{x}<br>DRI: %{y:.3f}σ<extra></extra>',
        ))

        fig.add_hline(y=0, line_color=MUTED, line_width=1)
        fig.add_hline(y=2, line_dash='dot', line_color=ORANGE,
                      opacity=0.7, annotation_text='2σ — Attention')
        fig.add_hline(y=4, line_dash='dash', line_color=RED,
                      opacity=0.7, annotation_text='4σ — Critical')

        fig.add_vline(x=shutdown_str, line_dash='solid',
                      line_color=RED, line_width=2,
                      annotation_text='⚡ SHUTDOWN',
                      annotation_font_color=RED, annotation_font_size=10)
        if first_alarm_str:
            fig.add_vline(x=first_alarm_str, line_dash='dash',
                          line_color=GREEN, line_width=2,
                          annotation_text='Alert',
                          annotation_font_color=GREEN, annotation_font_size=10)

        lo = bl()
        lo.update(xaxis_title='Time',
                  yaxis_title='DRI — Mean σ Deviation (all vib channels)',
                  showlegend=False)
        fig.update_layout(**lo)
        return fig

    # ─────────────────────────────────────────────────────────────────────────
    # CORRELATION CALLBACKS
    # ─────────────────────────────────────────────────────────────────────────

    @app.callback(
        [Output('corr-overlay', 'figure'),
         Output('corr-lag',     'figure'),
         Output('corr-rolling', 'figure'),
         Output('corr-scatter', 'figure'),
         Output('corr-insight', 'children')],
        [Input('corr-a', 'value'),
         Input('corr-b', 'value'),
         Input('corr-window-slider', 'value'),
         Input('corr-time-range', 'value')],
    )
    def cb_correlation(col_a, col_b, roll_w, time_range_h):
        empty = go.Figure()
        empty.update_layout(**bl())

        if not col_a or not col_b:
            return empty, empty, empty, empty, 'Select channels A and B.'

        op = D['op_df'].copy()
        time_range_h = time_range_h or 120
        if time_range_h < 200:
            cutoff = D['shutdown_time'] - pd.Timedelta(hours=time_range_h)
            op = op[op['timestamp'] >= cutoff]

        if col_a not in op.columns or col_b not in op.columns:
            return empty, empty, empty, empty, 'Channel not available.'

        s_a   = op[['timestamp', col_a]].dropna().set_index('timestamp')[col_a]
        s_b   = op[['timestamp', col_b]].dropna().set_index('timestamp')[col_b]
        idx   = s_a.index.intersection(s_b.index)
        s_a   = s_a.loc[idx]
        s_b   = s_b.loc[idx]
        meta_a = CHANNELS.get(col_a, {}); meta_b = CHANNELS.get(col_b, {})
        ca    = meta_a.get('color', ACCENT); cb_col = meta_b.get('color', PURPLE)
        la    = meta_a.get('label', col_a);  lb    = meta_b.get('label', col_b)
        ua    = meta_a.get('unit', '');      ub    = meta_b.get('unit', '')

        if len(idx) < 10:
            return empty, empty, empty, empty, 'Not enough overlapping data.'

        a_vals = s_a.values.astype(float)
        b_vals = s_b.values.astype(float)
        a_n    = (a_vals - a_vals.mean()) / (a_vals.std() + 1e-12)
        b_n    = (b_vals - b_vals.mean()) / (b_vals.std() + 1e-12)

        from scipy import stats as scipy_stats
        r_val, p_val = scipy_stats.pearsonr(a_vals, b_vals)

        # ── Overlay (normalized) ──────────────────────────────────────────────
        fig_ov = go.Figure()
        fig_ov.add_trace(go.Scatter(
            x=list(idx), y=list(a_n),
            name=f'{meta_a.get("short", col_a)} (norm)',
            line=dict(color=ca, width=1.8),
            hovertemplate=f'%{{x}}<br>{la}: %{{y:.3f}}σ<extra></extra>',
        ))
        fig_ov.add_trace(go.Scatter(
            x=list(idx), y=list(b_n),
            name=f'{meta_b.get("short", col_b)} (norm)',
            line=dict(color=cb_col, width=1.8),
            hovertemplate=f'%{{x}}<br>{lb}: %{{y:.3f}}σ<extra></extra>',
        ))
        fig_ov.add_hline(y=0, line_color=MUTED, line_width=0.8)
        if D['shutdown_time'] >= idx.min():
            fig_ov.add_vline(x=shutdown_str, line_dash='solid',
                             line_color=RED, line_width=1.5,
                             annotation_text='Shutdown',
                             annotation_font_color=RED, annotation_font_size=9)
        if first_alarm_str and D['first_alarm'] >= idx.min():
            fig_ov.add_vline(x=first_alarm_str, line_dash='dash',
                             line_color=GREEN, line_width=1.5)
        lo_ov = bl('Normalized Overlay — do they move together?')
        lo_ov.update(xaxis_title='Time', yaxis_title='z-score', showlegend=True)
        fig_ov.update_layout(**lo_ov)

        # ── Lagged cross-correlation ──────────────────────────────────────────
        lag_max  = 30
        lags     = list(range(-lag_max, lag_max + 1))
        lag_corrs = []
        for lag in lags:
            if lag < 0:
                c = float(np.corrcoef(a_n[:lag], b_n[-lag:])[0, 1])
            elif lag == 0:
                c = float(np.corrcoef(a_n, b_n)[0, 1])
            else:
                c = float(np.corrcoef(a_n[lag:], b_n[:-lag])[0, 1])
            lag_corrs.append(c if np.isfinite(c) else 0.0)

        sig      = 1.96 / np.sqrt(max(len(idx), 1))
        bar_cols = [RED if c > sig else (ACCENT if c < -sig else MUTED)
                    for c in lag_corrs]
        best_idx = int(np.argmax(np.abs(lag_corrs)))
        best_lag = lags[best_idx]
        best_r   = lag_corrs[best_idx]

        fig_lag = go.Figure()
        fig_lag.add_trace(go.Bar(
            x=lags, y=lag_corrs, marker_color=bar_cols,
            hovertemplate='Lag=%{x}<br>r=%{y:.3f}<extra></extra>', name='CCF',
        ))
        fig_lag.add_hline(y=sig,  line_dash='dot', line_color=GREEN,
                          opacity=0.7, annotation_text='95% CI')
        fig_lag.add_hline(y=-sig, line_dash='dot', line_color=GREEN, opacity=0.7)
        fig_lag.add_hline(y=0, line_color=MUTED, line_width=0.8)
        lo_lag = bl('Lagged Cross-Correlation')
        lo_lag.update(xaxis_title=f'Lag (windows)  ·  {meta_a.get("short",col_a)} → {meta_b.get("short",col_b)}',
                      yaxis_title='Pearson r', showlegend=False)
        lo_lag.pop('legend', None)
        fig_lag.update_layout(**lo_lag)

        # ── Rolling correlation ───────────────────────────────────────────────
        both     = pd.DataFrame({'a': s_a, 'b': s_b}).dropna()
        roll_w   = roll_w or 360
        roll_cor = both['a'].rolling(window=roll_w, min_periods=1).corr(both['b'])

        fig_roll = go.Figure()
        fig_roll.add_trace(go.Scatter(
            x=list(both.index), y=list(roll_cor.values),
            name=f'Rolling r (w={roll_w})',
            line=dict(color=ACCENT, width=2.0),
            fill='tozeroy', fillcolor='rgba(79,142,247,0.07)',
            hovertemplate='%{x}<br>r=%{y:.3f}<extra></extra>',
        ))
        fig_roll.add_hline(y=0.5,  line_dash='dot', line_color=GREEN,
                           opacity=0.5, annotation_text='r=0.5')
        fig_roll.add_hline(y=-0.5, line_dash='dot', line_color=RED,
                           opacity=0.5, annotation_text='r=-0.5')
        fig_roll.add_hline(y=0, line_color=MUTED, line_width=0.8)
        if D['shutdown_time'] >= both.index.min():
            fig_roll.add_vline(x=shutdown_str, line_dash='solid',
                               line_color=RED, line_width=1.5)
        if first_alarm_str and D['first_alarm'] >= both.index.min():
            fig_roll.add_vline(x=first_alarm_str, line_dash='dash',
                               line_color=GREEN, line_width=1.5)
        lo_roll = bl('Rolling Correlation Over Time')
        lo_roll.update(xaxis_title='Time', yaxis_title='Rolling r',
                       showlegend=False)
        fig_roll.update_layout(**lo_roll)

        # ── Scatter colored by time ───────────────────────────────────────────
        n       = len(a_vals)
        t_norm  = np.linspace(0, 1, n)
        fig_sc  = go.Figure()
        fig_sc.add_trace(go.Scatter(
            x=list(a_vals), y=list(b_vals), mode='markers',
            marker=dict(
                color=t_norm,
                colorscale=[[0, ACCENT], [0.5, PURPLE], [1, RED]],
                size=3, opacity=0.6,
                showscale=True,
                colorbar=dict(
                    title=dict(text='Time', font=dict(color=MUTED, size=10)),
                    tickvals=[0, 0.5, 1], ticktext=['Start', 'Mid', 'End'],
                    tickfont=dict(color=MUTED), thickness=8, len=0.7,
                ),
            ),
            hovertemplate=(f'<b>{la}</b>: %{{x:.2f}} {ua}<br>'
                           f'<b>{lb}</b>: %{{y:.2f}} {ub}<extra></extra>'),
            name=f'{meta_a.get("short",col_a)} vs {meta_b.get("short",col_b)}',
        ))
        # Regression line
        slope, intercept = np.polyfit(a_vals, b_vals, 1)
        x_line = np.linspace(a_vals.min(), a_vals.max(), 100)
        fig_sc.add_trace(go.Scatter(
            x=list(x_line), y=list(slope * x_line + intercept),
            mode='lines', name=f'Fit (slope={slope:.3f})',
            line=dict(color=ORANGE, width=2),
        ))
        p_str = f'{p_val:.4f}' if p_val >= 0.0001 else '<0.0001'
        fig_sc.add_annotation(
            x=0.97, y=0.97, xref='paper', yref='paper',
            text=f'r = {r_val:.3f}<br>p = {p_str}',
            showarrow=False, align='right', xanchor='right', yanchor='top',
            font=dict(size=12, color=GREEN if abs(r_val) > 0.5 else ORANGE,
                      family='monospace'),
            bgcolor=CARD2, bordercolor=BORDER, borderpad=8, borderwidth=1,
        )
        lo_sc = bl()
        lo_sc.update(xaxis_title=f'{la} ({ua})',
                     yaxis_title=f'{lb} ({ub})', showlegend=False)
        lo_sc.pop('legend', None)
        fig_sc.update_layout(**lo_sc)

        # ── Insight text ──────────────────────────────────────────────────────
        strength  = ('weakly' if abs(r_val) < 0.3 else
                     'moderately' if abs(r_val) < 0.6 else 'strongly')
        direction = 'positively' if r_val > 0 else 'negatively'
        if best_lag == 0:
            lag_msg = 'They respond simultaneously.'
        elif best_lag > 0:
            lag_msg = (f'➜ {meta_a.get("short",col_a)} leads '
                       f'{meta_b.get("short",col_b)} by ~{best_lag} windows. '
                       f'Changes in {la} appear first.')
        else:
            lag_msg = (f'➜ {meta_b.get("short",col_b)} leads '
                       f'{meta_a.get("short",col_a)} by ~{abs(best_lag)} windows. '
                       f'Changes in {lb} appear first.')

        causal = ('⚠️ Strong influence — likely share a causal link or common excitation source.'
                  if abs(best_r) > 0.5 else
                  'ℹ️ No dominant influence detected at tested lags.')

        insight = (f'📊 {la} and {lb} are {direction} {strength} correlated '
                   f'(r = {r_val:.3f}, p = {p_str}). {lag_msg} '
                   f'Peak lagged r = {best_r:.3f} at lag {best_lag}. {causal}')

        return fig_ov, fig_lag, fig_roll, fig_sc, insight

    # ─────────────────────────────────────────────────────────────────────────
    # ANOMALY SCORE CALLBACKS
    # ─────────────────────────────────────────────────────────────────────────

    @app.callback(
        Output('score-main', 'figure'),
        Input('main-tabs', 'value'),
    )
    def cb_score(tab):
        if tab != 'tab-score':
            return go.Figure()

        sc  = D['score_series']
        ucl = D['ucl_series']
        fig = go.Figure()

        # Alarm shading
        thr  = D['thr_95']
        above = (sc > thr).values
        ts_list = list(sc.index)
        in_alarm, a_start = False, None
        for ts_i, is_alm in zip(ts_list, above):
            if is_alm and not in_alarm:
                a_start, in_alarm = str(ts_i), True
            elif not is_alm and in_alarm:
                fig.add_vrect(x0=a_start, x1=str(ts_i),
                              fillcolor=RED, opacity=0.08,
                              layer='below', line_width=0)
                in_alarm = False
        if in_alarm and a_start:
            fig.add_vrect(x0=a_start, x1=str(ts_list[-1]),
                          fillcolor=RED, opacity=0.08,
                          layer='below', line_width=0)

        # IF score
        fig.add_trace(go.Scatter(
            x=ts_list, y=list(sc.values),
            name='Isolation Forest Score',
            line=dict(color=PURPLE, width=2.0),
            hovertemplate='%{x}<br>IF Score: %{y:.4f}<extra></extra>',
        ))

        # UCL violation rate
        fig.add_trace(go.Scatter(
            x=list(ucl.index), y=list(ucl.values),
            name='3σ UCL Violation Rate (fraction of channels)',
            line=dict(color=ORANGE, width=1.5, dash='dot'),
            yaxis='y2',
            hovertemplate='%{x}<br>UCL Violation Rate: %{y:.2f}<extra></extra>',
        ))

        # Threshold
        fig.add_hline(y=thr, line_dash='dash', line_color=RED, line_width=1.8,
                      annotation_text=f'95th Percentile Threshold = {thr:.4f}',
                      annotation_font_color=RED, annotation_font_size=9,
                      annotation_position='bottom right')

        fig.add_vline(x=shutdown_str, line_dash='solid',
                      line_color=RED, line_width=2.5,
                      annotation_text='⚡ SHUTDOWN',
                      annotation_font_color=RED, annotation_font_size=10)
        if first_alarm_str:
            fig.add_vline(x=first_alarm_str, line_dash='dash',
                          line_color=GREEN, line_width=2,
                          annotation_text=f'First Alert — {D["lead_hours"]:.1f}h lead',
                          annotation_font_color=GREEN, annotation_font_size=10)

        lo = bl()
        lo.update(
            xaxis_title='Time',
            yaxis_title='Isolation Forest Anomaly Score (normalized)',
            yaxis2=dict(
                title='UCL Violation Rate', overlaying='y', side='right',
                range=[0, 1.2], showgrid=False,
                tickfont=dict(color=ORANGE), title_font=dict(color=ORANGE),
            ),
            showlegend=True,
        )
        fig.update_layout(**lo)
        return fig

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORT REPORT CALLBACK
    # ─────────────────────────────────────────────────────────────────────────

    @app.callback(
        Output('export-status', 'children'),
        Input('btn-export', 'n_clicks'),
        prevent_initial_call=True,
    )
    def cb_export(n_clicks):
        try:
            path = _generate_report(D)
            return f'✓ Report saved: {path}'
        except Exception as e:
            return f'✗ Export failed: {e}'

    return app


# ─────────────────────────────────────────────────────────────────────────────
# TAB LAYOUT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _tab_overview(D, BG, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                   GREEN, RED, ORANGE, PURPLE, PLOT, GRID,
                   panel, graph, kpi, all_opts, vib_opts, dd_style):
    from dash import dcc, html

    btn_style_base = {
        'border': f'1px solid', 'borderRadius': '6px',
        'padding': '5px 12px', 'fontSize': '11px',
        'fontWeight': '700', 'cursor': 'pointer', 'marginRight': '8px',
    }

    return html.Div([
        # Controls row
        html.Div([
            html.Div([
                html.Div('Show Channels:', style={'color': MUTED, 'fontSize': '11px',
                                                   'marginBottom': '6px'}),
                dcc.Checklist(
                    id='overview-channel-select',
                    options=all_opts,
                    value=[c['value'] for c in vib_opts],
                    inline=True,
                    inputStyle={'marginRight': '4px', 'cursor': 'pointer'},
                    labelStyle={'marginRight': '16px', 'cursor': 'pointer',
                                'display': 'inline-flex', 'alignItems': 'center',
                                'fontSize': '12px'},
                ),
            ], style={'flex': '1'}),
            html.Div([
                html.Button('All', id='overview-btn-all', n_clicks=0,
                    style={**btn_style_base, 'background': f'rgba(34,197,94,0.15)',
                           'color': GREEN, 'borderColor': GREEN}),
                html.Button('Vibration Only', id='overview-btn-vib', n_clicks=0,
                    style={**btn_style_base, 'background': f'rgba(79,142,247,0.15)',
                           'color': ACCENT, 'borderColor': ACCENT}),
                html.Button('None', id='overview-btn-none', n_clicks=0,
                    style={**btn_style_base, 'background': f'rgba(239,68,68,0.15)',
                           'color': RED, 'borderColor': RED, 'marginRight': '0'}),
            ], style={'alignSelf': 'flex-end'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between',
                  'background': CARD, 'border': f'1px solid {BORDER}',
                  'borderRadius': '10px', 'padding': '14px 16px',
                  'marginBottom': '14px'}),

        # Main chart
        panel('② Individual MR — Multi-Parameter Trend Monitor',
              graph('overview-main-chart', height='380px')),

        # Root cause + fault sequence row
        html.Div([
            # Root cause contribution
            html.Div([
                html.Div('ROOT CAUSE ANALYSIS', style={
                    'fontSize': '10px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '2px', 'marginBottom': '12px'}),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div(c['short'], style={
                                'fontSize': '12px', 'color': c['color'],
                                'fontWeight': '700', 'fontFamily': 'monospace',
                                'marginBottom': '2px'}),
                            html.Div(c['behavior'], style={
                                'fontSize': '10px', 'color': MUTED}),
                        ], style={'flex': '1'}),
                        html.Div([
                            html.Div(f"{c['pct']:.0f}%", style={
                                'fontSize': '16px', 'fontWeight': '800',
                                'color': c['color'], 'fontFamily': 'monospace'}),
                            # Progress bar
                            html.Div(style={
                                'width': f"{min(c['pct'], 100):.0f}%",
                                'height': '4px',
                                'background': c['color'],
                                'borderRadius': '2px',
                                'marginTop': '4px',
                            }),
                        ], style={'textAlign': 'right', 'minWidth': '60px'}),
                    ], style={'display': 'flex', 'alignItems': 'center',
                              'padding': '8px 0',
                              'borderBottom': f'1px solid {BORDER}'})
                    for c in D['contribs']
                ]),
            ], style={'background': CARD, 'border': f'1px solid {BORDER}',
                      'borderRadius': '10px', 'padding': '16px 18px',
                      'flex': '1', 'marginRight': '12px'}),

            # Fault propagation sequence
            html.Div([
                html.Div('FAULT PROPAGATION SEQUENCE', style={
                    'fontSize': '10px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '2px', 'marginBottom': '12px'}),
                html.Div([
                    html.Div([
                        html.Div(f"#{i+1}", style={
                            'width': '24px', 'height': '24px',
                            'borderRadius': '50%',
                            'background': CHANNELS.get(f['col'], {}).get('color', ACCENT),
                            'display': 'flex', 'alignItems': 'center',
                            'justifyContent': 'center',
                            'fontSize': '11px', 'fontWeight': '800',
                            'color': 'white', 'flexShrink': '0',
                        }),
                        html.Div([
                            html.Div(f['label'], style={
                                'fontSize': '12px', 'color': TEXT,
                                'fontWeight': '600'}),
                            html.Div(
                                f"First exceeded UCL at {f['first'].strftime('%d-%b %H:%M')}",
                                style={'fontSize': '10px', 'color': MUTED}),
                            html.Div(
                                f"Peak: {f['peak']:.1f} mm/s (UCL: {f['ucl']:.1f})",
                                style={'fontSize': '10px', 'color': ORANGE,
                                       'fontFamily': 'monospace'}),
                        ], style={'marginLeft': '10px'}),
                    ], style={'display': 'flex', 'alignItems': 'flex-start',
                              'padding': '8px 0',
                              'borderBottom': f'1px solid {BORDER}'})
                    for i, f in enumerate(D['fault_seq'])
                ]),
            ], style={'background': CARD, 'border': f'1px solid {BORDER}',
                      'borderRadius': '10px', 'padding': '16px 18px',
                      'flex': '1', 'marginRight': '12px'}),

            # NL explanation
            html.Div([
                html.Div('AI EXPLANATION', style={
                    'fontSize': '10px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '2px', 'marginBottom': '12px'}),
                html.Div(D['nl'], style={
                    'fontSize': '12px', 'color': TEXT, 'lineHeight': '1.8'}),
                html.Div(style={'height': '16px'}),
                html.Div('RECOMMENDED ACTION', style={
                    'fontSize': '10px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '2px', 'marginBottom': '8px'}),
                *[html.Div(f'• {action}', style={
                    'fontSize': '11px', 'color': ORANGE,
                    'marginBottom': '4px', 'lineHeight': '1.6'})
                  for action in [
                      'Inspect Drive End bearing assembly',
                      'Check and replenish lubrication system',
                      'Verify shaft alignment',
                      'Inspect bearing housing for wear',
                      'Schedule immediate maintenance shutdown',
                  ]],
            ], style={'background': CARD, 'border': f'1px solid {BORDER}',
                      'borderRadius': '10px', 'padding': '16px 18px',
                      'flex': '1'}),
        ], style={'display': 'flex', 'marginBottom': '14px'}),
    ])


def _tab_trends(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                GREEN, RED, ORANGE, PLOT, panel, graph,
                all_opts, vib_opts, dd_style):
    from dash import dcc, html
    return html.Div([
        html.Div([
            html.Div([
                html.Div('Select Channel:', style={'color': MUTED, 'fontSize': '10px',
                    'fontWeight': '700', 'letterSpacing': '1px',
                    'textTransform': 'uppercase', 'marginBottom': '5px'}),
                dcc.Dropdown(id='trends-channel-dd',
                    options=all_opts,
                    value=D['vib_cols'][1] if len(D['vib_cols']) > 1 else D['vib_cols'][0],
                    clearable=False, style=dd_style),
            ], style={'flex': '1', 'marginRight': '16px'}),
            html.Div([
                html.Div('Time Window (hours before shutdown):', style={
                    'color': MUTED, 'fontSize': '10px', 'fontWeight': '700',
                    'letterSpacing': '1px', 'textTransform': 'uppercase',
                    'marginBottom': '5px'}),
                dcc.Slider(
                    id='trends-time-range',
                    min=6, max=200, step=6, value=120,
                    marks={6: '6h', 24: '24h', 48: '48h',
                           72: '72h', 120: '5 days', 200: 'Full'},
                    tooltip={'placement': 'bottom', 'always_visible': False},
                ),
            ], style={'flex': '2'}),
        ], style={'display': 'flex', 'alignItems': 'center',
                  'background': CARD, 'border': f'1px solid {BORDER}',
                  'borderRadius': '10px', 'padding': '14px 18px',
                  'marginBottom': '14px'}),
        panel('Individual Channel — Trend + Control Limits + ISO Thresholds',
              graph('trends-chart', height='500px')),
    ])


def _tab_evolution(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                    GREEN, RED, ORANGE, PURPLE, PLOT, panel, graph):
    from dash import dcc, html
    return html.Div([
        html.Div(D['nl'], style={
            'background': f'rgba(239,68,68,0.06)',
            'border': f'1px solid rgba(239,68,68,0.25)',
            'borderRadius': '10px', 'padding': '14px 18px',
            'fontSize': '12px', 'color': TEXT, 'lineHeight': '1.8',
            'marginBottom': '14px',
        }),
        panel('Parameter Deviation Heatmap — σ units from baseline (deeper red = more deviated)',
              graph('evo-heatmap', height='240px')),
        panel('Deterioration Rate Index (DRI) — rolling mean σ deviation across all vibration channels',
              graph('evo-dri', height='280px')),
    ])


def _tab_correlation(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
                      GREEN, RED, ORANGE, PURPLE, PLOT, panel, graph,
                      all_opts, dd_style):
    from dash import dcc, html
    vib_only = [o for o in all_opts if D['channel_meta'] and
                CHANNELS.get(o['value'], {}).get('type') == 'vibration']\
               if hasattr(D, 'channel_meta') else all_opts

    return html.Div([
        # Channel selectors + controls
        html.Div([
            html.Div([
                html.Div('Channel A', style={'color': MUTED, 'fontSize': '10px',
                    'fontWeight': '700', 'letterSpacing': '1px',
                    'textTransform': 'uppercase', 'marginBottom': '5px'}),
                dcc.Dropdown(id='corr-a',
                    options=all_opts,
                    value=D['vib_cols'][0],
                    clearable=False, style=dd_style),
            ], style={'flex': '1', 'marginRight': '12px'}),
            html.Div([
                html.Div('Channel B', style={'color': MUTED, 'fontSize': '10px',
                    'fontWeight': '700', 'letterSpacing': '1px',
                    'textTransform': 'uppercase', 'marginBottom': '5px'}),
                dcc.Dropdown(id='corr-b',
                    options=all_opts,
                    value=D['vib_cols'][1] if len(D['vib_cols']) > 1 else D['vib_cols'][0],
                    clearable=False, style=dd_style),
            ], style={'flex': '1', 'marginRight': '20px'}),
            html.Div([
                html.Div('Rolling Window Size (samples):', style={
                    'color': MUTED, 'fontSize': '10px', 'fontWeight': '700',
                    'letterSpacing': '1px', 'textTransform': 'uppercase',
                    'marginBottom': '5px'}),
                dcc.Slider(id='corr-window-slider',
                    min=60, max=2160, step=60, value=360,
                    marks={60: '10m', 360: '1h', 720: '2h',
                           1440: '4h', 2160: '6h'},
                    tooltip={'placement': 'bottom', 'always_visible': False}),
            ], style={'flex': '2', 'marginRight': '20px'}),
            html.Div([
                html.Div('Time Window (hours before shutdown):', style={
                    'color': MUTED, 'fontSize': '10px', 'fontWeight': '700',
                    'letterSpacing': '1px', 'textTransform': 'uppercase',
                    'marginBottom': '5px'}),
                dcc.Slider(id='corr-time-range',
                    min=6, max=200, step=6, value=120,
                    marks={6: '6h', 24: '24h', 72: '72h', 120: 'All'},
                    tooltip={'placement': 'bottom', 'always_visible': False}),
            ], style={'flex': '2'}),
        ], style={'display': 'flex', 'alignItems': 'flex-end',
                  'background': CARD, 'border': f'1px solid {BORDER}',
                  'borderRadius': '10px', 'padding': '14px 18px',
                  'marginBottom': '14px'}),

        # Insight text
        html.Div(id='corr-insight', style={
            'background': f'rgba(79,142,247,0.06)',
            'border': f'1px solid rgba(79,142,247,0.2)',
            'borderRadius': '10px', 'padding': '12px 16px',
            'fontSize': '12px', 'color': TEXT, 'lineHeight': '1.8',
            'marginBottom': '14px',
        }),

        # Charts
        panel('Normalized Overlay — Both channels on same z-score axis',
              graph('corr-overlay', height='280px')),
        html.Div([
            html.Div(
                panel('Lagged Cross-Correlation',
                      graph('corr-lag', height='260px')),
                style={'flex': '1', 'marginRight': '12px'}),
            html.Div(
                panel('Rolling Correlation Over Time',
                      graph('corr-rolling', height='260px')),
                style={'flex': '1'}),
        ], style={'display': 'flex'}),
        panel('Scatter Plot — A vs B (color = time progression)',
              graph('corr-scatter', height='300px')),
    ])


def _tab_score(D, CARD, CARD2, BORDER, TEXT, MUTED, ACCENT,
               GREEN, RED, ORANGE, PURPLE, PLOT, panel, graph):
    from dash import dcc, html
    first_alarm = D['first_alarm']
    shutdown    = D['shutdown_time']

    return html.Div([
        html.Div([
            html.Div([
                html.Div('ANOMALY DETECTION METHOD', style={
                    'fontSize': '9px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '1.5px', 'textTransform': 'uppercase',
                    'marginBottom': '6px'}),
                html.Div('Isolation Forest (200 estimators)', style={
                    'fontSize': '13px', 'fontWeight': '700',
                    'color': PURPLE, 'fontFamily': 'monospace'}),
                html.Div('Trained on first 40% of operating data (normal baseline)',
                         style={'fontSize': '10px', 'color': MUTED}),
            ], style={'flex': '1', 'background': CARD,
                      'border': f'1px solid {BORDER}', 'borderRadius': '8px',
                      'padding': '14px 16px'}),
            html.Div([
                html.Div('ALERT THRESHOLD', style={
                    'fontSize': '9px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '1.5px', 'textTransform': 'uppercase',
                    'marginBottom': '6px'}),
                html.Div(f"{D['thr_95']:.4f}", style={
                    'fontSize': '22px', 'fontWeight': '800',
                    'color': RED, 'fontFamily': 'monospace'}),
                html.Div('95th percentile of training scores',
                         style={'fontSize': '10px', 'color': MUTED}),
            ], style={'flex': '1', 'background': CARD,
                      'border': f'1px solid {BORDER}',
                      'borderTop': f'2px solid {RED}',
                      'borderRadius': '8px', 'padding': '14px 16px'}),
            html.Div([
                html.Div('FIRST ALERT', style={
                    'fontSize': '9px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '1.5px', 'textTransform': 'uppercase',
                    'marginBottom': '6px'}),
                html.Div(first_alarm.strftime('%d-%b %H:%M') if first_alarm else 'N/A',
                         style={'fontSize': '18px', 'fontWeight': '800',
                                'color': GREEN, 'fontFamily': 'monospace'}),
                html.Div('First sustained score > threshold',
                         style={'fontSize': '10px', 'color': MUTED}),
            ], style={'flex': '1', 'background': CARD,
                      'border': f'1px solid {BORDER}',
                      'borderTop': f'2px solid {GREEN}',
                      'borderRadius': '8px', 'padding': '14px 16px'}),
            html.Div([
                html.Div('VALID LEAD TIME', style={
                    'fontSize': '9px', 'color': MUTED, 'fontWeight': '700',
                    'letterSpacing': '1.5px', 'textTransform': 'uppercase',
                    'marginBottom': '6px'}),
                html.Div(f"{D['lead_hours']:.1f}h", style={
                    'fontSize': '28px', 'fontWeight': '800',
                    'color': GREEN, 'fontFamily': 'monospace'}),
                html.Div('Before emergency shutdown',
                         style={'fontSize': '10px', 'color': MUTED}),
            ], style={'flex': '1', 'background': CARD,
                      'border': f'1px solid {BORDER}',
                      'borderTop': f'2px solid {GREEN}',
                      'borderRadius': '8px', 'padding': '14px 16px'}),
        ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '14px'}),

        panel('Anomaly Score Timeline — Isolation Forest (purple) + 3σ UCL Violation Rate (orange)',
              graph('score-main', height='420px')),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# HTML Report Generator
# ─────────────────────────────────────────────────────────────────────────────

def _generate_report(D: Dict) -> str:
    """Generate a professional HTML alert report and save to results/figures/."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import base64, io

    def fig_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                    facecolor='#0d0f17')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    plt.style.use('dark_background')

    # Figure 1 — Vibration trends
    fig1, axes = plt.subplots(len(D['vib_cols']), 1,
                               figsize=(14, 3 * len(D['vib_cols'])),
                               sharex=True)
    if len(D['vib_cols']) == 1:
        axes = [axes]

    op = D['op_df']
    for ax, col in zip(axes, D['vib_cols']):
        meta  = CHANNELS.get(col, {})
        color = meta.get('color', '#4f8ef7')
        label = meta.get('label', col)
        s     = op[['timestamp', col]].dropna()
        trend = s[col].rolling(360, min_periods=1).mean()

        ax.plot(s['timestamp'], s[col], color=color, alpha=0.3, linewidth=0.8)
        ax.plot(s['timestamp'], trend,  color=color, linewidth=2.0, label=label)

        if col in D['baseline']:
            ucl = D['baseline'][col]['ucl_3s']
            mu  = D['baseline'][col]['mean']
            ax.axhline(ucl, color='#ef4444', linewidth=1.2, linestyle='--',
                       label=f'UCL 3σ = {ucl:.1f}')
            ax.axhline(mu,  color='#5a6180', linewidth=0.8, linestyle=':')

        ax.axvline(D['shutdown_time'], color='#ef4444', linewidth=2, linestyle='-')
        if D['first_alarm']:
            ax.axvline(D['first_alarm'], color='#22c55e', linewidth=1.5,
                       linestyle='--')
        ax.set_ylabel(f"{meta.get('short', col)}\n(mm/s)",
                      color='#9ca3af', fontsize=9)
        ax.legend(loc='upper left', fontsize=8)
        ax.set_facecolor('#0d0f17')
        ax.tick_params(colors='#6b7280')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b\n%H:%M'))

    fig1.suptitle('LPC Bearing Vibration — Full 5-Day Trend',
                  color='#dde2f5', fontsize=13, fontweight='bold')
    plt.tight_layout()
    img1 = fig_to_base64(fig1)
    plt.close()

    # Figure 2 — Failure evolution heatmap
    evo    = D['evo_data']
    labels = D['win_labels']
    vcols  = D['vib_cols']
    z_mat  = np.array([[evo[lbl].get(c, 0.0) for lbl in labels] for c in vcols])
    ylbls  = [CHANNELS.get(c, {}).get('short', c) for c in vcols]

    fig2, ax2 = plt.subplots(figsize=(12, 3))
    im = ax2.imshow(z_mat, cmap='RdBu_r', aspect='auto',
                    vmin=-2, vmax=max(10, float(z_mat.max())))
    ax2.set_xticks(range(len(labels))); ax2.set_xticklabels(labels, color='#dde2f5')
    ax2.set_yticks(range(len(ylbls)));  ax2.set_yticklabels(ylbls,  color='#dde2f5')
    for i in range(len(vcols)):
        for j in range(len(labels)):
            ax2.text(j, i, f'{z_mat[i,j]:.1f}σ',
                     ha='center', va='center', color='white', fontsize=10, fontweight='bold')
    plt.colorbar(im, ax=ax2, label='Deviation (σ)')
    ax2.set_title('Failure Evolution Heatmap — Parameter Deviation from Baseline',
                  color='#dde2f5', fontsize=11, fontweight='bold')
    ax2.set_facecolor('#0d0f17')
    fig2.patch.set_facecolor('#0d0f17')
    plt.tight_layout()
    img2 = fig_to_base64(fig2)
    plt.close()

    # Build HTML report
    shutdown   = D['shutdown_time']
    fa         = D['first_alarm']
    lead       = D['lead_hours']
    report_ts  = shutdown.strftime('%Y%m%d_%H%M')
    event_str  = shutdown.strftime('%d-%b-%Y %H:%M:%S')
    alert_str  = fa.strftime('%d-%b-%Y %H:%M') if fa else 'N/A'

    # Peak values table rows
    peak_rows = ''
    for col in D['vib_cols']:
        meta    = CHANNELS.get(col, {})
        s       = op[['timestamp', col]].dropna()
        peak    = float(s[col].max())
        peak_t  = s.loc[s[col].idxmax(), 'timestamp'].strftime('%d-%b %H:%M')
        ucl     = D['baseline'][col]['ucl_3s'] if col in D['baseline'] else 0
        exceed  = 'YES' if peak > ucl else 'NO'
        color   = '#ef4444' if exceed == 'YES' else '#22c55e'
        peak_rows += f"""
        <tr>
          <td>{meta.get('label', col)}</td>
          <td class="mono">{peak:.1f} mm/s</td>
          <td class="mono">{ucl:.1f} mm/s</td>
          <td class="mono">{peak_t}</td>
          <td style="color:{color};font-weight:700">{exceed}</td>
        </tr>"""

    # Fault sequence rows
    seq_rows = ''
    for i, f in enumerate(D['fault_seq']):
        seq_rows += f"""
        <tr>
          <td>#{i+1}</td>
          <td>{f['label']}</td>
          <td class="mono">{f['first'].strftime('%d-%b %H:%M')}</td>
          <td class="mono">{f['peak']:.1f} mm/s</td>
          <td class="mono">{f['ucl']:.1f} mm/s</td>
        </tr>"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ONGC Alert Report — {event_str}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',sans-serif; background:#f8fafc; color:#1e293b; padding:0; }}
  .header {{ background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 100%); color:white; padding:32px 48px; }}
  .header-top {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; }}
  .badge {{ display:inline-block; background:rgba(239,68,68,0.2); border:1px solid rgba(239,68,68,0.5); color:#fca5a5; font-size:11px; font-weight:700; letter-spacing:2px; padding:4px 12px; border-radius:4px; }}
  .header h1 {{ font-size:26px; font-weight:800; margin:8px 0 4px; }}
  .header-sub {{ color:#94a3b8; font-size:13px; }}
  .kpi-row {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; padding:24px 48px; background:#0f172a; }}
  .kpi {{ background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:16px; }}
  .kpi-label {{ font-size:9px; color:#64748b; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px; }}
  .kpi-value {{ font-size:24px; font-weight:800; font-family:monospace; }}
  .kpi-sub {{ font-size:10px; color:#475569; margin-top:4px; }}
  .section {{ padding:32px 48px; border-bottom:1px solid #e2e8f0; }}
  .section-title {{ font-size:13px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#64748b; margin-bottom:16px; }}
  .explanation-box {{ background:#fef3c7; border:1px solid #fbbf24; border-left:4px solid #f59e0b; border-radius:8px; padding:16px 20px; font-size:13px; line-height:1.8; color:#1e293b; }}
  table {{ width:100%; border-collapse:collapse; font-size:12px; }}
  th {{ background:#f1f5f9; padding:10px 14px; text-align:left; font-size:10px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#64748b; border-bottom:2px solid #e2e8f0; }}
  td {{ padding:10px 14px; border-bottom:1px solid #f1f5f9; }}
  tr:hover td {{ background:#f8fafc; }}
  .mono {{ font-family:monospace; font-weight:600; }}
  .img-container {{ margin-top:12px; }}
  img {{ width:100%; border-radius:8px; }}
  .actions {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }}
  .action-item {{ background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; padding:10px 14px; font-size:12px; color:#1e40af; font-weight:600; }}
  .footer {{ background:#0f172a; color:#475569; text-align:center; padding:20px; font-size:11px; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <div>
      <div class="badge">⚡ EMERGENCY SHUTDOWN — HIGH VIBRATION</div>
      <h1>ONGC Solar Turbine — LPC Bearing Alert Report</h1>
      <div class="header-sub">
        Automated Predictive Maintenance Analysis &nbsp;|&nbsp;
        Generated: {pd.Timestamp.now().strftime('%d-%b-%Y %H:%M')}
      </div>
    </div>
    <div style="text-align:right">
      <div style="font-size:11px;color:#64748b;margin-bottom:4px;">EVENT TIME</div>
      <div style="font-size:20px;font-weight:800;font-family:monospace;color:#fca5a5">{event_str}</div>
    </div>
  </div>
</div>

<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-label">Valid Lead Time</div>
    <div class="kpi-value" style="color:#22c55e">{lead:.1f}h</div>
    <div class="kpi-sub">Before emergency shutdown</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">First Alert</div>
    <div class="kpi-value" style="color:#4f8ef7;font-size:16px">{alert_str}</div>
    <div class="kpi-sub">Isolation Forest detection</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Peak Vibration</div>
    <div class="kpi-value" style="color:#ef4444">{max(D['op_df'][c].max() for c in D['vib_cols']):.1f} mm/s</div>
    <div class="kpi-sub">Drive End — Y Axis</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Channels in Alarm</div>
    <div class="kpi-value" style="color:#f59e0b">{D['n_channels_alarm']}/4</div>
    <div class="kpi-sub">Exceeded UCL (3σ baseline)</div>
  </div>
</div>

<div class="section">
  <div class="section-title">Automated Explanation</div>
  <div class="explanation-box">{D['nl']}</div>
</div>

<div class="section">
  <div class="section-title">Vibration Trend — Full 5-Day History</div>
  <div class="img-container"><img src="data:image/png;base64,{img1}"></div>
</div>

<div class="section">
  <div class="section-title">Failure Evolution Heatmap — Parameter Deviation (σ units)</div>
  <div class="img-container"><img src="data:image/png;base64,{img2}"></div>
</div>

<div class="section">
  <div class="section-title">Peak Values & Control Limit Violations</div>
  <table>
    <tr>
      <th>Channel</th><th>Peak Value</th>
      <th>UCL (3σ)</th><th>Peak Time</th><th>UCL Exceeded</th>
    </tr>
    {peak_rows}
  </table>
</div>

<div class="section">
  <div class="section-title">Fault Propagation Sequence</div>
  <table>
    <tr>
      <th>Rank</th><th>Channel</th>
      <th>First UCL Exceedance</th><th>Peak Value</th><th>UCL</th>
    </tr>
    {seq_rows}
  </table>
</div>

<div class="section">
  <div class="section-title">Recommended Maintenance Actions</div>
  <div class="actions">
    <div class="action-item">🔧 Inspect Drive End bearing assembly — replace if worn</div>
    <div class="action-item">🛢️ Check and replenish lubrication system</div>
    <div class="action-item">📐 Verify shaft alignment and balance</div>
    <div class="action-item">🏠 Inspect bearing housing for cracks or wear</div>
    <div class="action-item">🔩 Check coupling between turbine and compressor</div>
    <div class="action-item">📊 Review operating history for abnormal loads</div>
  </div>
</div>

<div class="footer">
  ONGC Solar Turbine Predictive Maintenance Platform &nbsp;|&nbsp;
  LPC Bearing Vibration Analysis &nbsp;|&nbsp;
  Report generated: {pd.Timestamp.now().strftime('%d-%b-%Y %H:%M:%S')}
</div>

</body>
</html>"""

    # Save
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'results', 'figures'
    )
    os.makedirs(out_dir, exist_ok=True)
    filename = f'ONGC_Report_{report_ts}.html'
    path     = os.path.join(out_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"Report saved → {path}")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Channel meta shortcut (used in tab builders)
# ─────────────────────────────────────────────────────────────────────────────
CHANNELS_META = CHANNELS   # alias for use inside _tab_* functions