"""Guarded manuscript edits: every old string must occur exactly once. Overwritten per batch;
each batch's old/new text is appended to revision-artifacts/final2/edit_log.md.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
LOG = ROOT / "revision-artifacts" / "final2" / "edit_log.md"
BATCH = "Last corrections, layout: compact sequence-length scope in S6.3 (22 pages)"
EDITS = [
    (r"Only the three longest-lived bearings form a length-30 sequence anywhere in the sweep, Bearing2\_5 "
     r"only at $f=2$, so each deep sequence model is N/A in 76/90 cells,",
     r"Only the three longest-lived bearings form a length-30 sequence (Bearing2\_5 only at $f=2$), so each "
     r"deep sequence model is N/A in 76/90 cells,"),
    (r"At full resolution, halving the sequence length to 15 windows adds only Bearing2\_5, whose onset "
     r"precedes the first scored window, so it cannot be scored;",
     r"Halving the sequence length to 15 windows adds Bearing2\_5 at full resolution, but its onset "
     r"precedes the first scored window, so it cannot be scored;"),
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
