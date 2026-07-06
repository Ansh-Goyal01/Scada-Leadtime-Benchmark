# -*- coding: utf-8 -*-
"""
STEP 14 numeric-integrity proof. Compares the multiset of numeric tokens between the
committed HEAD version of paper/scada_journal.tex and the reframed working copy.

- "BRAND-NEW" tokens (value absent from HEAD entirely) are the real risk: every one
  must be justified (the tau* grid is pure rho/k arithmetic; nothing else should appear).
- Count deltas for values that already existed are benign (a published number re-stated
  in the new abstract/summary simply appears more or fewer times).
"""
import subprocess, re, io
from collections import Counter

old = subprocess.check_output(
    ["git", "show", "HEAD:paper/scada_journal.tex"], cwd=r"C:\scada").decode("utf-8")
new = io.open(r"C:\scada\paper\scada_journal.tex", encoding="utf-8").read()

num = re.compile(r"\d+\.\d+|\d+")
co, cn = Counter(num.findall(old)), Counter(num.findall(new))
added = cn - co      # positive where new count > old count
removed = co - cn    # positive where old count > new count
brand_new = {t: c for t, c in added.items() if co[t] == 0}

print("=== BRAND-NEW numeric values (absent from HEAD) - must all be justified ===")
if brand_new:
    for t, c in sorted(brand_new.items()):
        print(f"  +{c}  {t}")
else:
    print("  (none) - every numeric value in the reframed paper already existed in HEAD.")

print("\n=== count increased (value already existed, now stated more often) ===")
for t, c in sorted({t: c for t, c in added.items() if co[t] > 0}.items(),
                   key=lambda x: (-x[1], x[0])):
    print(f"  new has +{c} of '{t}'  (HEAD had {co[t]}, now {cn[t]})")

print("\n=== count decreased (value stated fewer times / prose removed) ===")
for t, c in sorted(removed.items(), key=lambda x: (-x[1], x[0])):
    print(f"  new has -{c} of '{t}'  (HEAD had {co[t]}, now {cn[t]})")
