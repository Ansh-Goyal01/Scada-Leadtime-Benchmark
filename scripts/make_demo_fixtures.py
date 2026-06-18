#!/usr/bin/env python
"""
Generate small, schema-accurate SYNTHETIC fixtures for the diagnostic console so
it is fully runnable and testable WITHOUT the multi-GB real downloads.

These are clearly synthetic and live under data/raw/_fixtures/. The real loaders
(src/metropt_preprocessing.py, src/cmapss_preprocessing.py) prefer the real files
when present and only fall back to these fixtures.

    python scripts/make_demo_fixtures.py

Outputs:
    data/raw/_fixtures/MetroPT3.csv
    data/raw/_fixtures/CMAPSS/{train,test,RUL}_FD001.txt
"""

import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX  = os.path.join(BASE, "data", "raw", "_fixtures")
SEED = 20200416


# ── MetroPT-3 compressor fixture ──────────────────────────────────────────────

def _ramp(n, lo, hi):
    """Smooth 0→1 ramp of length n, eased (slow start, faster middle)."""
    x = np.linspace(0, 1, n)
    return lo + (hi - lo) * (x ** 1.6)


def make_metropt(days=7, freq="1min"):
    rng = np.random.default_rng(SEED)
    idx = pd.date_range("2020-04-15", periods=int(days * 24 * 60), freq=freq)
    n = len(idx)

    # Healthy baselines with mild noise.
    oil_temp = 65.0 + rng.normal(0, 0.6, n)
    current  = 4.0 + rng.normal(0, 0.15, n)
    tp2      = 1.0 + rng.normal(0, 0.05, n)
    tp3      = 9.0 + rng.normal(0, 0.06, n)
    h1       = 8.6 + rng.normal(0, 0.05, n)
    dv_press = np.abs(rng.normal(0.02, 0.02, n))
    reserv   = 8.6 + rng.normal(0, 0.05, n)
    comp     = (rng.random(n) > 0.25).astype(int)
    dv_elec  = (rng.random(n) > 0.85).astype(int)
    oil_level = np.ones(n, dtype=int)
    caudal   = rng.poisson(2, n)

    # Inject two degradation events: air-leak / overwork signature →
    # reservoir & pneumatic pressure fall, motor current and oil temperature climb.
    def inject(start_frac, dur_frac, severity):
        s = int(start_frac * n); e = min(n, s + int(dur_frac * n)); m = e - s
        if m <= 0:
            return
        up = _ramp(m, 0, 1) * severity
        oil_temp[s:e] += 20 * up
        current[s:e]  += 3.0 * up
        reserv[s:e]   -= 2.2 * up
        tp3[s:e]      -= 1.5 * up
        h1[s:e]       -= 1.0 * up
        dv_press[s:e] += 0.6 * up

    inject(0.42, 0.06, 1.0)   # primary failure
    inject(0.78, 0.05, 0.8)   # second, milder event

    df = pd.DataFrame({
        "timestamp": idx,
        "TP2": tp2, "TP3": tp3, "H1": h1, "DV_pressure": dv_press,
        "Reservoirs": reserv, "Oil_temperature": oil_temp, "Motor_current": current,
        "COMP": comp, "DV_eletric": dv_elec, "Oil_level": oil_level,
        "Caudal_impulses": caudal,
    })
    out = os.path.join(FIX, "MetroPT3.csv")
    os.makedirs(FIX, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"  MetroPT-3 fixture -> {out}  ({len(df)} rows)")


# ── C-MAPSS turbofan fixture ──────────────────────────────────────────────────

# (col_index 1-based sensor, baseline, end-of-life delta, noise sd)
_CMAPSS_SENSORS = {
    1: (518.67, 0.0, 0.0), 2: (642.0, 0.7, 0.5), 3: (1590.0, 10.0, 6.0),
    4: (1400.0, 45.0, 9.0), 5: (14.62, 0.0, 0.0), 6: (21.6, 0.08, 0.28),
    7: (553.9, -2.5, 0.5), 8: (2388.0, 0.2, 0.05), 9: (9050.0, 160.0, 22.0),
    10: (1.3, 0.0, 0.0), 11: (47.5, 1.6, 0.25), 12: (521.7, -1.8, 0.6),
    13: (2388.0, 0.1, 0.04), 14: (8130.0, 22.0, 19.0), 15: (8.42, 0.22, 0.04),
    16: (0.03, 0.0, 0.0), 17: (392.0, 3.0, 1.0), 18: (2388.0, 0.0, 0.0),
    19: (100.0, 0.0, 0.0), 20: (39.0, -0.5, 0.15), 21: (23.4, -0.32, 0.10),
}


def make_cmapss(n_units=6):
    rng = np.random.default_rng(SEED + 1)
    rows = []
    lives = {}
    for u in range(1, n_units + 1):
        L = int(rng.integers(160, 260))
        lives[u] = L
        for c in range(1, L + 1):
            frac = c / L
            deg = frac ** 1.5
            op1 = float(rng.normal(0, 0.002))
            op2 = float(rng.normal(0, 0.0003))
            op3 = 100.0
            sensors = []
            for i in range(1, 22):
                base, delta, sd = _CMAPSS_SENSORS[i]
                val = base + delta * deg + (rng.normal(0, sd) if sd else 0.0)
                sensors.append(val)
            rows.append([u, c, op1, op2, op3] + sensors)

    def fmt(r):
        return " ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r)

    os.makedirs(os.path.join(FIX, "CMAPSS"), exist_ok=True)
    train = os.path.join(FIX, "CMAPSS", "train_FD001.txt")
    with open(train, "w") as f:
        f.write("\n".join(fmt(r) for r in rows) + "\n")
    print(f"  C-MAPSS fixture -> {train}  ({len(rows)} rows, {n_units} units)")

    # Minimal test + RUL files so the directory is schema-complete.
    test_rows, rul = [], []
    for u in range(1, min(3, n_units) + 1):
        L = lives[u]; cut = int(L * 0.6)
        for c in range(1, cut + 1):
            frac = c / L; deg = frac ** 1.5
            sensors = [_CMAPSS_SENSORS[i][0] + _CMAPSS_SENSORS[i][1] * deg for i in range(1, 22)]
            test_rows.append([u, c, 0.0, 0.0, 100.0] + sensors)
        rul.append(L - cut)
    with open(os.path.join(FIX, "CMAPSS", "test_FD001.txt"), "w") as f:
        f.write("\n".join(fmt(r) for r in test_rows) + "\n")
    with open(os.path.join(FIX, "CMAPSS", "RUL_FD001.txt"), "w") as f:
        f.write("\n".join(str(v) for v in rul) + "\n")


def main():
    print("Generating synthetic console fixtures (clearly labelled, dev/test only):")
    make_metropt()
    make_cmapss()
    print("Done.")


if __name__ == "__main__":
    main()
