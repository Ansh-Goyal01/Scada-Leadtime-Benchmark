"""Guarded manuscript edits: every old string must occur exactly once. Overwritten per batch;
each batch's old/new text is appended to revision-artifacts/final2/edit_log.md.

Batch: Part 1 layout -- the per-bearing paragraph repeats Table 7's n.s. notes.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
LOG = ROOT / "revision-artifacts" / "final2" / "edit_log.md"
BATCH = "Part 1 layout: per-bearing paragraph"
EDITS = [
    (r"they differ only where valid detectors disagree, which happens on none of the scoreable "
     r"bearings here. Only 5 of the ten bearings are scoreable at full resolution: Bearing1\_2 has no "
     r"detectable onset, and on Bearing1\_3, 1\_5, 2\_2 and 2\_5 the onset precedes the first scored "
     r"window.",
     r"they differ only where valid detectors disagree, which happens on none of the five scoreable "
     r"bearings (Table~\ref{tab:perbearing} marks the other five and why)."),
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
