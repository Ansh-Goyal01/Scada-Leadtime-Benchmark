"""Part 5 layout experiment: read the deep-architecture table* before the hyperparameter table
in Appendix A, so it is not held behind the earlier single-column float."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"
LOG = ROOT / "revision-artifacts" / "final2" / "edit_log.md"
BATCH = "Part 5 layout: Appendix A table* read before the single-column table (renumbers 11<->12)"


def main():
    s = TEX.read_bytes().decode("utf-8")
    a = s.find("\\input{gen/tab_hyperparams}")
    b0 = s.find("\\begin{table*}", a)
    b1 = s.find("\\end{table*}", b0) + len("\\end{table*}")
    assert 0 < a < b0 < b1 and "Deep-model architectures" in s[b0:b1]
    between = s[a + len("\\input{gen/tab_hyperparams}"):b0]
    assert between.strip() == "", repr(between)
    s = s[:a] + s[b0:b1] + "\n\n\\input{gen/tab_hyperparams}" + s[b1:]
    TEX.write_bytes(s.encode("utf-8"))
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"\n## {BATCH}\n")
    print(BATCH, "done")


if __name__ == "__main__":
    main()
