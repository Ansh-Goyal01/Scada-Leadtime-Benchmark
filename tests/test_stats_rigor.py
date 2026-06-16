# tests/test_stats_rigor.py
"""
Unit tests for src/stats_rigor.py — the run-level statistical foundation that
replaces the pseudoreplicated 15-pair Wilcoxon test.

These tests lock in the properties the paper's claims now rest on:
  * the exact sign test cannot manufacture significance at n=3 (p floors at 0.25);
  * its direction/sign accounting is correct;
  * Holm adjustment is monotone, order-preserving, and never less conservative
    than the raw p-values;
  * run_level_diffs genuinely collapses within-run pseudoreplicate factors.
"""

import numpy as np
import pandas as pd
import pytest

from src.stats_rigor import (
    run_level_diffs,
    exact_sign_test,
    holm_bonferroni,
    ims_runlevel_table,
    family_holm,
)


# ──────────────────────────── exact sign test ──────────────────────────────────

def test_sign_test_n3_floor():
    """3/3 concordant diffs is the most extreme possible at n=3 → p == 0.25.
    This is the structural reason 'significant' (p<0.05) is impossible at n=3 and
    why the original p=0.003 had to be removed."""
    res = exact_sign_test([1.0, 2.0, 3.0])
    assert res["n_effective"] == 3
    assert res["all_same_sign"] is True
    assert res["p_value"] == pytest.approx(0.25)
    # No vector of length 3 can beat this floor.
    assert res["p_value"] >= 0.25 - 1e-12


def test_sign_test_floor_is_minimum_over_random_n3():
    rng = np.random.RandomState(0)
    for _ in range(200):
        d = rng.normal(size=3)
        assert exact_sign_test(d)["p_value"] >= 0.25 - 1e-9


def test_sign_test_sign_accounting():
    res = exact_sign_test([5.0, -1.0, 2.0, 3.0])
    assert res["n_pos"] == 3
    assert res["n_neg"] == 1
    assert res["median"] == pytest.approx(2.5)
    assert res["all_same_sign"] is False


def test_sign_test_drops_zeros():
    res = exact_sign_test([0.0, 0.0, 4.0, 5.0])
    assert res["n_zero"] == 2
    assert res["n_effective"] == 2
    # 2/2 concordant → 2 * P(X<=0 | n=2) = 2 * 0.25 = 0.5
    assert res["p_value"] == pytest.approx(0.5)


def test_sign_test_all_zero_is_one():
    res = exact_sign_test([0.0, 0.0, 0.0])
    assert res["n_effective"] == 0
    assert res["p_value"] == 1.0


def test_sign_test_pvalue_never_exceeds_one():
    # 1 vs 1 split → 2 * P(X<=1 | n=2) = 2*0.75 = 1.5, must cap at 1.0
    res = exact_sign_test([1.0, -1.0])
    assert res["p_value"] == 1.0


def test_sign_test_large_concordant_is_significant():
    """Sanity: with enough independent runs all-positive, the test CAN reject —
    confirming the floor is an n=3 property, not a defect of the test."""
    res = exact_sign_test([1.0] * 10)
    assert res["p_value"] < 0.05


# ──────────────────────────── Holm–Bonferroni ──────────────────────────────────

def test_holm_monotonic_in_sorted_order():
    p = [0.001, 0.01, 0.02, 0.04, 0.5]
    adj, _ = holm_bonferroni(p)
    s = np.argsort(p)
    sorted_adj = adj[s]
    assert np.all(np.diff(sorted_adj) >= -1e-12), "Holm adjusted p must be non-decreasing"


def test_holm_order_preserving_roundtrip():
    """Adjusted p returned in input order; shuffling inputs shuffles outputs the same way."""
    p = np.array([0.04, 0.001, 0.5, 0.01, 0.02])
    adj, rej = holm_bonferroni(p)
    perm = [2, 0, 4, 1, 3]
    adj2, rej2 = holm_bonferroni(p[perm])
    assert np.allclose(adj2, adj[perm], equal_nan=True)
    assert np.array_equal(rej2, rej[perm])


def test_holm_at_least_as_conservative_as_raw():
    p = [0.001, 0.01, 0.02, 0.04, 0.5]
    adj, _ = holm_bonferroni(p)
    assert np.all(adj >= np.array(p) - 1e-12)


def test_holm_step_down_stops_rejecting():
    """Once a hypothesis is retained, all larger-p ones are retained too."""
    p = [0.001, 0.04, 0.045, 0.9]  # m=4: 0.001*4=0.004 reject; 0.04*3=0.12 retain → rest retain
    _, rej = holm_bonferroni(p, alpha=0.05)
    assert rej[0] is np.True_ or rej[0] == True
    assert not rej[1] and not rej[2] and not rej[3]


def test_holm_handles_nan():
    p = [0.001, np.nan, 0.5]
    adj, rej = holm_bonferroni(p)
    assert np.isnan(adj[1]) and rej[1] == False
    # family size excludes NaN → m=2, so 0.001*2 = 0.002 still rejects
    assert rej[0] == True


def test_holm_single_pvalue_unchanged():
    adj, rej = holm_bonferroni([0.03])
    assert adj[0] == pytest.approx(0.03)
    assert rej[0] == True


# ──────────────────────────── run_level_diffs ──────────────────────────────────

def _toy_long():
    """2 runs × 3 factors × 2 modes; within a run every factor shares the SAME diff,
    so collapsing factors must yield exactly one diff per run (not three)."""
    rows = []
    run_diff = {"runA": 4.0, "runB": -1.0}
    for run, dec in [("runA", 10.0), ("runB", 20.0)]:
        for factor in (1, 2, 5):
            rows.append(dict(dataset="DS", method="m", run=run, mode="decimate",
                             factor=factor, lead_time_hours=dec))
            rows.append(dict(dataset="DS", method="m", run=run, mode="aggregate",
                             factor=factor, lead_time_hours=dec + run_diff[run]))
    return pd.DataFrame(rows)


def test_run_level_diffs_collapses_pseudoreplicates():
    rl = run_level_diffs(_toy_long())
    # 2 runs → exactly 2 rows, NOT 6 (the pseudoreplicate count).
    assert len(rl) == 2
    diffs = dict(zip(rl["run"], rl["diff"]))
    assert diffs["runA"] == pytest.approx(4.0)
    assert diffs["runB"] == pytest.approx(-1.0)


def test_runlevel_table_and_family_holm_integration():
    tab = ims_runlevel_table(_toy_long())
    assert tab["n_runs"].iloc[0] == 2
    fam = family_holm([tab])
    assert "holm_p" in fam.columns
    assert fam["family_size"].iloc[0] == len(fam)


def test_run_level_diffs_missing_mode_returns_empty():
    df = _toy_long()
    df = df[df["mode"] == "aggregate"]  # drop decimate
    assert run_level_diffs(df).empty
