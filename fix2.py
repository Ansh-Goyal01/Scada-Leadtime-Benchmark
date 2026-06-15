content = open(r'C:\scada\src\ongc_dashboard.py', encoding='utf-8').read()

# Add interval component to layout
content = content.replace(
    '        # Top bar\n        html.Div([',
    '        dcc.Interval(id=\'init-trigger\', interval=500, max_intervals=1),\n\n        # Top bar\n        html.Div(['
)

# Fix evo-heatmap callback
content = content.replace(
    "    @app.callback(Output('evo-heatmap', 'figure'),\n                  Input('main-tabs', 'value'))\n    def cb_heatmap(tab):",
    "    @app.callback(Output('evo-heatmap', 'figure'),\n                  [Input('main-tabs', 'value'), Input('init-trigger', 'n_intervals')])\n    def cb_heatmap(tab, _):"
)

# Fix evo-dri callback
content = content.replace(
    "    @app.callback(Output('evo-dri', 'figure'),\n                  Input('main-tabs', 'value'))\n    def cb_dri(tab):",
    "    @app.callback(Output('evo-dri', 'figure'),\n                  [Input('main-tabs', 'value'), Input('init-trigger', 'n_intervals')])\n    def cb_dri(tab, _):"
)

# Fix score callback
content = content.replace(
    "    @app.callback(Output('score-chart', 'figure'),\n                  Input('main-tabs', 'value'))\n    def cb_score(tab):",
    "    @app.callback(Output('score-chart', 'figure'),\n                  [Input('main-tabs', 'value'), Input('init-trigger', 'n_intervals')])\n    def cb_score(tab, _):"
)

open(r'C:\scada\src\ongc_dashboard.py', 'w', encoding='utf-8').write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK — all fixes applied')
except SyntaxError as e:
    print(f'Syntax error at line {e.lineno}: {e.msg}')