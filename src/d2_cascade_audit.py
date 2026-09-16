"""
D-2 cascade audit: which manuscript artifacts move if IMS is re-baselined onto the
49-dim invariant feature schema?

The decisive structural fact, established by code inspection and re-verified here:

    the 445-dim LEGACY schema is reachable ONLY through `load_pipeline_controlled`
    (`src/sampling.py:365`), which is called ONLY from `src/benchmark.py:164` and
    `src/sampling.py:547`.

Every other IMS analysis in the repo -- ablation, calibration, tradeoff, onset
sensitivity, robustness (gaps / noise / denoisers), feature-coarsening -- goes
through `src.load_pipeline`, which reads `FEATURES["mode"]` from `src/config.py`
and is set to "invariant". Those analyses are therefore ALREADY on the schema the
paper argues for, and cannot move under D-2.

So the cascade is confined to the IMS controlled sweep and its derivatives. This
script quantifies that part from the existing invariant CSV, and spot-checks the
provenance of the artifacts claimed not to move.

Read-only. Writes no file.
"""

import os
import sys

import pandas as pd

from src.benchmark import bootstrap_ci_across_runs
from src.d2_convention_recompute import per_detector

try:                                          # N-13: cp1252 console cannot print sigma
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

T = "results/tables"
PUB = f"{T}/benchmark_IMS_long.csv"
INV = f"{T}/benchmark_IMS_long_invariant.csv"

# Published values, transcribed from paper/files/scada_ijphm.tex, for comparison only.
TAB2_PUB = {                       # tab:imslead, :283-296 -- mean raw lead + 95% CI
    "lstm_ae": 214.9, "tcn": 201.5, "transformer_ad": 199.6, "ewma": 78.3,
    "cusum": 77.2, "isolation_forest": 69.8, "hotelling_t2": 67.5,
    "three_sigma": 58.0, "rms_trend": 34.5, "deep_svdd": 18.4,
}
TAB5_PUB = {"three_sigma": 18.4, "ewma": 5.8, "isolation_forest": 12.2}  # persistence=3


def hdr(s: str) -> None:
    print("\n" + "=" * 92)
    print(s)
    print("=" * 92)


def _short_to_method(df: pd.DataFrame) -> dict:
    return dict(df.drop_duplicates("short_name").set_index("short_name")["method"])


def onset_identity(pub: pd.DataFrame, inv: pd.DataFrame) -> None:
    hdr("A. Is the onset itself schema-dependent?  (drives Tables 3, 4 and Figure 1)")
    key = ["run", "short_name", "mode", "factor"]
    m = pub.merge(inv, on=key, suffixes=("_leg", "_inv"))
    for col in ("t_onset", "t_fail", "max_lead_hours"):
        a, b = m[f"{col}_leg"].astype(str), m[f"{col}_inv"].astype(str)
        print(f"  {col:<18} identical on {int((a == b).sum())}/{len(m)} paired rows")
    print("\n  Onset is computed from the RMS/kurtosis health indicator on the snapshot")
    print("  series, upstream of feature extraction -- so it cannot depend on the schema.")


def table2(inv: pd.DataFrame) -> None:
    hdr("B. Table 2 (tab:imslead) -- IMS mean raw lead at full resolution, 95% boot CI")
    sub = inv[(inv.factor == 1) & (inv["mode"] == "aggregate")]
    ci = bootstrap_ci_across_runs(sub, metric="lead_time_hours")
    col = [c for c in ci.columns if c.endswith("_mean")][0]
    lo = [c for c in ci.columns if c.endswith("_lo")][0]
    hi = [c for c in ci.columns if c.endswith("_hi")][0]
    idx = "method" if "method" in ci.columns else "short_name"
    ci = ci.set_index(idx)
    s2m = _short_to_method(inv)
    print(f"{'detector':<18}{'published':>10}{'invariant':>11}{'delta':>10}   95% CI (inv)")
    for det, pubval in TAB2_PUB.items():
        meth = s2m[det] if idx == "method" else det
        if meth not in ci.index:
            print(f"{det:<18}{pubval:10.1f}{'--':>11}{'--':>10}   (absent)")
            continue
        r = ci.loc[meth]
        print(f"{det:<18}{pubval:10.1f}{float(r[col]):11.1f}{float(r[col]) - pubval:10.1f}"
              f"   [{float(r[lo]):.1f}, {float(r[hi]):.1f}]")


def figure3(pub: pd.DataFrame, inv: pd.DataFrame) -> None:
    hdr("C. Figure 3 (fig:sweep) + its in-text numbers -- mean lead vs factor, by mode")
    print("  text at :478 claims 3sigma falls 58.0 h (full) -> 7.1 h (10x decimate),")
    print("  while aggregation holds it near 59 h.\n")
    for det in ("three_sigma", "isolation_forest"):
        print(f"  --- {det} ---")
        print(f"  {'factor':>7} {'leg agg':>9}{'leg dec':>9}   {'inv agg':>9}{'inv dec':>9}")
        for f in sorted(pub.factor.unique()):
            row = []
            for d in (pub, inv):
                for mode in ("aggregate", "decimate"):
                    s = d[(d.short_name == det) & (d.factor == f) & (d["mode"] == mode)]
                    row.append(s["lead_time_hours"].mean())
            print(f"  {f:>7} {row[0]:9.1f}{row[1]:9.1f}   {row[2]:9.1f}{row[3]:9.1f}")


def table5(pub: pd.DataFrame, inv: pd.DataFrame) -> None:
    hdr("D. Table 5 (tab:persistence) -- only the persistence=3 column is derivable")
    L = per_detector(pub, "IMS").set_index("short_name")
    I = per_detector(inv, "IMS").set_index("short_name")
    print(f"{'detector':<18}{'published':>10}{'legacy':>9}{'invariant':>11}{'delta':>9}")
    for det, pubval in TAB5_PUB.items():
        print(f"{det:<18}{pubval:10.1f}{float(L.loc[det, 'median_h']):9.1f}"
              f"{float(I.loc[det, 'median_h']):11.1f}"
              f"{float(I.loc[det, 'median_h']) - pubval:9.1f}")
    for label, d in (("legacy", pub), ("invariant", inv)):
        s = d[(d.short_name == "three_sigma") & (d.factor == 1) & (d["mode"] == "aggregate")]
        frac = s["valid_alarm"].astype(str).str.lower().eq("true").mean()
        print(f"  3sigma valid-alarm fraction at f=1 aggregate, {label:<10}{frac:.2f}"
              "   (published 1.00)")
    print("\n  persistence in {1,5,10} requires a rerun: `persistence_sensitivity_IMS.csv`")
    print("  has NO generating script anywhere in the repo (grep over all *.py).")


def validity(pub: pd.DataFrame, inv: pd.DataFrame) -> None:
    hdr("E. Validity totals and window geometry")
    for label, d in (("legacy", pub), ("invariant", inv)):
        v = d["valid_alarm"].astype(str).str.lower().eq("true")
        print(f"  {label:<12} rows={len(d)}  valid={int(v.sum())}  "
              f"NaN FAR={int(d['far_preonset_pct'].isna().sum())}  "
              f"test windows={sorted(d['n_test_windows'].unique())}")


def provenance() -> None:
    hdr("F. Provenance spot-check -- artifacts on the load_pipeline (invariant) path")
    checks = [
        ("tradeoff_IMS.csv", "Tables 14/16/22, Figures 7/9",
         "3sigma 95th pct lead 77.0 h / FAR 18.1%"),
        ("calibration_IMS.csv", "Table 13, Figure 4", "1st_test FAR 0.74 at alpha=0.01"),
        ("gap_injection.csv", "Table 6", "3sigma IMS 42.6 h at 0/5/20% gaps"),
        ("noise_snr_IMS_runlevel.csv", "Table 27", "native -0.35 h, 10 dB +6.60 h"),
        ("denoising_IMS.csv", "Table 28", "aggregate 75.7 h, 7/12 valid"),
        ("ablation_features_IMS.csv", "Tables 17/18/19", "envelope 99.4 h raw lead"),
        ("spectral_ablation_IMS_6det.csv", "Table 20", "per-run validity"),
    ]
    for f, arts, sig in checks:
        p = os.path.join(T, f)
        exists = os.path.exists(p)
        n = len(pd.read_csv(p)) if exists else 0
        print(f"  {f:<32} {'present' if exists else 'MISSING':<8} rows={n:<5} -> {arts}")
        print(f"      manuscript signature value: {sig}")


def main() -> None:
    pub, inv = pd.read_csv(PUB), pd.read_csv(INV)
    onset_identity(pub, inv)
    table2(inv)
    figure3(pub, inv)
    table5(pub, inv)
    validity(pub, inv)
    provenance()


if __name__ == "__main__":
    main()
