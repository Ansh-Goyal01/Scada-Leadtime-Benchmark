"""Enforce the Data and Code Availability claim that no number in the
manuscript's tables is hand-edited.

Every value checked here is re-derived from a released file under
results/tables/ and compared against what the .tex actually prints, at the
precision it prints. If someone retypes a cell, or regenerates a result file
without updating the table, this fails.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "paper"))

TEX = ROOT / "paper" / "files" / "scada_ijphm.tex"

pytestmark = pytest.mark.skipif(
    not TEX.exists(), reason="manuscript source not present in this checkout"
)


def test_every_checked_table_number_matches_its_source_file():
    import verify_tables

    problems = verify_tables.run(verbose=False)
    assert not problems, "table cells disagree with their source files: " + "; ".join(
        "%s printed %s, source %s" % p for p in problems
    )


def test_verifier_actually_checks_a_meaningful_number_of_cells():
    """Guard against a silently-empty verifier after a table is restructured."""
    import verify_tables

    counts = {}
    for name, fn in verify_tables.CHECKS:
        counts[name] = fn([])
    for name, n in counts.items():
        assert n > 0, "%s checked 0 values - the parser no longer matches the table" % name
    total = sum(counts.values())
    assert total >= 250, "expected >=250 checked cells, got %d" % total
