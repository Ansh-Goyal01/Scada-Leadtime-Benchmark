"""Guarded manuscript edits: every old string must occur exactly once. Overwritten per batch;
each batch's old/new text is appended to revision-artifacts/final2/edit_log.md.
"""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
LOG = ROOT / "revision-artifacts" / "final2" / "edit_log.md"
BATCH = "Part 3: abstract equivalence wording, IMS equivalence sentence in S6.6"

b = pd.read_csv(ROOT / "results" / "tables" / "n20_d15_bootstrap_new_11det.csv")
multi = b[b.dataset.isin(["XJTU-SY", "FEMTO", "Ferrara"])]
assert len(multi) == 33
maxabs = multi[["ci_lo_h", "ci_hi_h"]].abs().to_numpy().max()
assert 0.5595 < maxabs < 0.6, maxabs                       # prints as 0.560
ims = b[b.dataset == "IMS (invariant re-baseline, D-2)"].set_index("method")
assert len(ims) == 11
cu, ho = ims.loc["CUSUM (k=0.5, h=5.0)"], ims.loc["Hotelling T²"]
assert cu.ci_lo_h > 1.0                                    # strictly beyond the +1 h margin
assert ho.ci_lo_h == 1.0                                   # on the margin, not beyond it
rest = ims.drop(["CUSUM (k=0.5, h=5.0)", "Hotelling T²"])
assert ((rest.ci_lo_h < 1.0) & (rest.ci_hi_h > 1.0)).all()  # nine straddle the margin: undecided

EDITS = [
    (r"none favouring decimation beyond $-0.45$~h; IMS is too wide to decide in 9 of 11 cells and favours "
     r"aggregation beyond the margin in 2.",
     r"every 95\% interval lying inside $\pm 0.6$~h; IMS is too wide to decide in 9 of 11 cells, favours "
     r"aggregation beyond the margin for CUSUM, and touches it for Hotelling $T^2$ (lower bound exactly "
     r"$+1.00$~h)."),
    (r"The powered campaigns are short-lived bearings",
     r"The campaigns that supply this statistical power are short-lived bearings"),
    (r"the defensible reading is a null result with a positive median direction for the "
     r"magnitude-monitoring detectors.",
     r"the defensible reading is a null result with a positive median direction for the "
     r"magnitude-monitoring detectors. Against the $\pm 1$~h margin the IMS intervals are too wide to "
     rf"decide for nine of the eleven detectors; CUSUM's lies wholly above it ([${cu.ci_lo_h:+.2f}$, "
     rf"${cu.ci_hi_h:+.2f}$]~h), favouring aggregation beyond the margin, and Hotelling $T^2$'s lower "
     rf"bound sits exactly on it ([${ho.ci_lo_h:+.2f}$, ${ho.ci_hi_h:+.2f}$]~h)."),
]


def main():
    s = TEX.read_bytes().decode("utf-8")
    for old, new in EDITS:
        assert s.count(old) == 1, (s.count(old), old[:80])
        s = s.replace(old, new)
    TEX.write_bytes(s.encode("utf-8"))
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"\n## {BATCH}\n")
        for old, new in EDITS:
            fh.write(f"\n- OLD: {old}\n- NEW: {new}\n")
    print(f"{BATCH}: applied {len(EDITS)}")


if __name__ == "__main__":
    main()
