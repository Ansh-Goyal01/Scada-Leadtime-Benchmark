content = open(r'C:\scada\src\ongc_dashboard.py', encoding='utf-8').read()

old = "    def bl(title=''):\n        import copy as _copy\n        lo = _copy.deepcopy(BASE_LAYOUT)\n        if title:\n            lo['title'] = dict(text=title, font=dict(size=11, color=MUTED), x=0.01)\n        return lo"

new = """    def bl(fig, title=''):
        fig.update_layout(
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
        if title:
            fig.update_layout(title=dict(
                text=title, font=dict(size=11, color=MUTED), x=0.01))"""

content = content.replace(old, new)

# Replace all lo = bl() and fig.update_layout(**lo) patterns
import re
# Pattern: lo = bl(...)\n...lo.update(...)\nfig.update_layout(**lo)
content = re.sub(r"lo = bl\((.*?)\)\n(.*?)lo\.update\((.*?)\)\n(.*?)fig\.update_layout\(\*\*lo\)",
                 lambda m: f"bl(fig, {m.group(1)})\n{m.group(2)}fig.update_layout({m.group(3)})",
                 content, flags=re.DOTALL)

# Simple replacements
content = content.replace('fig.update_layout(**lo)', '')
content = content.replace('lo = bl()\n', 'bl(fig)\n')
content = content.replace("lo = bl('", "bl(fig, '")

open(r'C:\scada\src\ongc_dashboard.py', 'w', encoding='utf-8').write(content)
print('Done')