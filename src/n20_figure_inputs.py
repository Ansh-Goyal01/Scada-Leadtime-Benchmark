# src/n20_figure_inputs.py
"""
N-20 / D-10: regenerate the Figure 2 inputs for the datasets the resampling fix changed.

paper/make_figures.py::fig_crossdataset reads
    femto_runlevel_test.csv, ferrara_runlevel_test.csv   (stats_rigor.ims_runlevel_table)
    benchmark_ONGC_paired_test.csv                        (benchmark.paired_test_aggregate_vs_decimate)
all produced before the fix. This script first REPLAYS each generator on the published long files and
requires a match with the published file, then writes the post-fix versions with an _n20 suffix from
results/tables/n20_rerun_long_<DS>_main.csv (the ten detectors the published files contain).

Entry point:  python -m src.n20_figure_inputs
"""

import io
import os
import sys

import numpy as np
import pandas as pd

from src.config import PATHS

T = PATHS["results_tables"]


def _p(name):
    return os.path.join(T, name)


def _same(a, b):
    a = a.reset_index(drop=True)
    b = b.reset_index(drop=True)
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        return False
    for c in a.columns:
        if a[c].dtype.kind in "fc" or b[c].dtype.kind in "fc":
            if not np.allclose(a[c].astype(float), b[c].astype(float), equal_nan=True,
                               rtol=0, atol=1e-9):
                return False
        elif not (a[c].astype(str) == b[c].astype(str)).all():
            return False
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from src.stats_rigor import ims_runlevel_table
    from src.benchmark import paired_test_aggregate_vs_decimate

    jobs = [
        ("FEMTO", "femto_runlevel_test.csv", ims_runlevel_table),
        ("Ferrara", "ferrara_runlevel_test.csv", ims_runlevel_table),
        ("ONGC", "benchmark_ONGC_paired_test.csv", paired_test_aggregate_vs_decimate),
    ]
    for ds, fname, gen in jobs:
        published = pd.read_csv(_p(fname))
        replay = gen(pd.read_csv(_p(f"benchmark_{ds}_long.csv")))
        replay_rt = pd.read_csv(io.StringIO(replay.to_csv(index=False)))
        ok = _same(published, replay_rt)
        print(f"{ds}: replay of {fname} matches published: {ok}")
        if not ok:
            raise SystemExit(f"replay mismatch for {fname} -- not writing the post-fix file")
        new = gen(pd.read_csv(_p(f"n20_rerun_long_{ds}_main.csv")))
        out = fname.replace(".csv", "_n20.csv")
        new.to_csv(_p(out), index=False)
        print(f"   wrote {out}")


if __name__ == "__main__":
    main()
