content = open(r'C:\scada\src\ongc_dashboard.py', encoding='utf-8').read()

# Remove duplicate interval - keep only one
while content.count("dcc.Interval(id='init-trigger'") > 1:
    idx = content.find("dcc.Interval(id='init-trigger'")
    end = content.find('\n', idx) + 1
    content = content[:idx] + content[end:]

print("Intervals remaining:", content.count("dcc.Interval(id='init-trigger'"))

open(r'C:\scada\src\ongc_dashboard.py', 'w', encoding='utf-8').write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')