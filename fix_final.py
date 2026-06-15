content = open(r'C:\scada\src\ongc_dashboard.py', encoding='utf-8').read()

# The overview callback builds x like this:
# x=[str(t) for t in s['timestamp']]
# But s['timestamp'] contains pandas Timestamps which Dash rejects.
# Fix: use .astype(str).tolist() which forces string conversion at pandas level.

content = content.replace(
    "x=[str(t) for t in s['timestamp']]",
    "x=s['timestamp'].astype(str).tolist()"
)

# Fix all other timestamp index conversions
content = content.replace(
    "x=[str(t) for t in dri.index]",
    "x=dri.index.astype(str).tolist()"
)
content = content.replace(
    "x=[str(t) for t in sc.index]",
    "x=sc.index.astype(str).tolist()"
)
content = content.replace(
    "x=[str(t) for t in ucl.index]",
    "x=ucl.index.astype(str).tolist()"
)
content = content.replace(
    "x=[str(t) for t in idx]",
    "x=pd.DatetimeIndex(idx).astype(str).tolist()"
)
content = content.replace(
    "x=[str(t) for t in both.index]",
    "x=both.index.astype(str).tolist()"
)

open(r'C:\scada\src\ongc_dashboard.py', 'w', encoding='utf-8').write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK')
    remaining = content.count('[str(t) for t in')
    print(f'Remaining [str(t) for t in] patterns: {remaining}')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')