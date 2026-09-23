"""Verify the numbers of the two protected additions (G3, D18) against result files.

G3 : rg3_raw_invariance.csv -- raw-lead aggregate-minus-decimate differences under the
     pca1 / kurt_only onset indicators versus the default rms_kurt.
D18: d18_gap_injection_multiseed.csv -- Hotelling T2 on IMS across five gap draws.
Run: python revision-artifacts/phase1/verify_g3_d18.py
"""
import pathlib
import pandas as pd

T = pathlib.Path(__file__).resolve().parents[2] / "results/tables"

g3 = pd.read_csv(T / "rg3_raw_invariance.csv")
print("G3 rows:", len(g3))
print(g3.groupby(["dataset", "indicator"]).size().to_string())
print("max |dev| row lead (h):", g3["max_abs_dev_row_lead_h"].abs().max(),
      "| max |dev| run diff (h):", g3["max_abs_dev_run_diff_h"].abs().max(),
      "| NaN mismatches:", int(g3["row_nan_mismatch"].sum()))

d = pd.read_csv(T / "d18_gap_injection_multiseed.csv")
print("\nD18 columns:", list(d.columns), "| gaps:", sorted(d["gap"].unique()),
      "| seeds:", sorted(d["gap_seed"].unique()))
ims = d[d["dataset"] == "IMS"]
base = ims[ims["gap"] == 0.0]
for gap in (0.05, 0.20):
    g = ims[ims["gap"] == gap]
    print("\nIMS gap", gap)
    for m, gm in g.groupby("short_name"):
        per_draw = gm[gm["valid"]].groupby("gap_seed")["lead"].mean()
        print("  %-18s per-draw mean valid lead: %s  -> mean %.1f, range %.1f-%.1f" % (
            m, [round(x, 1) for x in per_draw], per_draw.mean(), per_draw.min(), per_draw.max()))
    merged = g.merge(base[["run", "short_name", "lead", "valid"]].drop_duplicates(["run", "short_name"]),
                     on=["run", "short_name"], suffixes=("", "_base"))
    changed = merged[(merged["lead"] - merged["lead_base"]).abs() > 1e-9]
    print("  rows whose per-run lead differs from the no-gap run:",
          changed.groupby(["short_name", "gap_seed"]).size().to_dict())
    hot = merged[merged["short_name"] == "hotelling_t2"]
    for _, r in hot.sort_values(["gap_seed", "run"]).iterrows():
        print("    hotelling seed %s %-10s %7.1f -> %7.1f valid %s" % (
            r["gap_seed"], r["run"], r["lead_base"], r["lead"], r["valid"]))
