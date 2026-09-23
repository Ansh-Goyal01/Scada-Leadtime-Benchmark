"""Guarded manuscript edits: every old string must occur exactly once. Overwritten per batch;
each batch's old/new text is appended to revision-artifacts/final2/edit_log.md.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
LOG = ROOT / "revision-artifacts" / "final2" / "edit_log.md"
BATCH = "Part 2: internal tracking IDs removed from Data Availability"
EDITS = [
    (r"(the pre-D-2 legacy feature schema, or the pre-N-20 rerun)",
     r"(an earlier feature schema, or results computed before the aggregation bin width was corrected)"),
    (r"together with the full post-N-20 sampling sweep",
     r"together with the full sampling sweep"),
    (r"both of which are the pre-N-20 arm, retained as provenance",
     r"both of which were computed before the aggregation bin width was corrected, retained as provenance"),
    (r"the aggregate-vs-decimate contrast is taken from the post-N-20 files named above",
     r"the aggregate-vs-decimate contrast is taken from the corrected files named above"),
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
