# src/n20_resample_fix.py
"""
Defect N-20 / decision D-10 — verify and propagate the aggregation-resampling fix.

The bug: ``load_pipeline`` resampled "aggregate" at ``max(1, round(base_min * factor))`` whole
minutes, while "decimate" kept every k-th row. With sub-minute native spacing (FEMTO and ONGC
10 s, Ferrara 5 s) aggregate landed on a coarser effective interval than decimate at the same
nominal factor. The fix resamples at native spacing x factor, in seconds.

Sub-commands:
    hash --tag pre|post     fingerprint load_pipeline outputs (all runs, both modes, every
                            factor) for IMS and XJTU-SY, whose native spacing is a whole
                            number of minutes, so the fix must be a no-op there
    compare                 pre vs post fingerprints -> results/tables/n20_pipeline_hash_check.csv
    rerun --dataset DS      run_benchmark (10 default detectors, then OC-SVM alone, as the
                            published sweeps did) -> results/tables/n20_rerun_long_<DS>.csv
    verify                  IMS/XJTU-SY reruns vs the published long files, byte level and
                            value level -> results/tables/n20_reproduction_check.csv

Nothing published is overwritten. Detector, onset and metric code are not touched.
"""

import argparse
import hashlib
import json
import logging
import os
import sys

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SEED = 42
OCSVM = "one_class_svm"
INVARIANT_DATASETS = ["IMS", "XJTU-SY"]       # whole-minute native spacing: must not move
PUBLISHED = {
    "IMS": "benchmark_IMS_long_invariant.csv",
    "XJTU-SY": "benchmark_XJTU-SY_long.csv",
}


def _tables():
    from src.config import PATHS
    return PATHS["results_tables"]


def _digest(arr):
    a = np.ascontiguousarray(np.asarray(arr))
    return hashlib.sha256(a.tobytes()).hexdigest()


def fingerprint(tag):
    """SHA-256 of every array load_pipeline returns, per (dataset, run, mode, factor)."""
    from src import load_pipeline
    from src.benchmark import compute_run_onset
    from src.config import SAMPLING, FEATURES, THRESHOLD
    from src.datasets import default_runs
    from src.sampling import derive_counts

    out = {}
    for ds in INVARIANT_DATASETS:
        for run in default_runs(ds):
            # Same window geometry as run_benchmark's standard path.
            base_min = compute_run_onset(run, dataset=ds)["base_min"]
            ovl = FEATURES["overlap"]
            window_minutes = SAMPLING["window_minutes"] or FEATURES["window_size"] * base_min
            persistence_minutes = (SAMPLING["persistence_minutes"]
                                   if SAMPLING["persistence_minutes"] is not None else
                                   THRESHOLD["alarm_persistence"]
                                   * FEATURES["window_size"] * (1.0 - ovl) * base_min)
            for mode in ("aggregate", "decimate"):
                for f in SAMPLING["factors"]:
                    if f == 1 and mode == "decimate":
                        continue
                    dmode = "none" if f == 1 else mode
                    c = derive_counts(base_min, f, window_minutes, persistence_minutes,
                                      ovl, SAMPLING["min_window_rows"])
                    key = f"{ds}|{run}|{mode}|{f}"
                    try:
                        p = load_pipeline(run, dataset=ds, window_size=c["window_rows"],
                                          downsample_factor=f, downsample_mode=dmode)
                    except Exception as e:          # the failure itself is fingerprinted
                        out[key] = {"error": f"{type(e).__name__}: {e}"}
                        continue
                    out[key] = {
                        "X_train": _digest(p["X_train"]),
                        "X_test": _digest(p["X_test"]),
                        "ts_test": _digest(p["ts_test"].asi8),
                        "features": hashlib.sha256(
                            "|".join(map(str, p["feature_names"])).encode()).hexdigest(),
                        "effective_interval_min": p["effective_interval_min"],
                    }
    path = os.path.join(_tables(), f"n20_pipeline_hashes_{tag}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    logger.info("Saved -> %s (%d keys)", path, len(out))
    return out


def compare():
    t = _tables()
    with open(os.path.join(t, "n20_pipeline_hashes_pre.json"), encoding="utf-8") as fh:
        pre = json.load(fh)
    with open(os.path.join(t, "n20_pipeline_hashes_post.json"), encoding="utf-8") as fh:
        post = json.load(fh)
    rows = [{"key": k, "present_both": k in pre and k in post,
             "identical": pre.get(k) == post.get(k)} for k in sorted(set(pre) | set(post))]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(t, "n20_pipeline_hash_check.csv"), index=False)
    print("pipeline fingerprints identical: %d / %d" % (df["identical"].sum(), len(df)))
    if not df["identical"].all():
        print(df[~df["identical"]].to_string(index=False))
    return df


def rerun(dataset):
    from src.benchmark import run_benchmark
    control = dataset == "IMS"
    main_df = run_benchmark(dataset=dataset, control=control, seeds=[SEED], save=False)
    oc_df = run_benchmark(dataset=dataset, methods=[OCSVM], control=control,
                          seeds=[SEED], save=False)
    main_path = os.path.join(_tables(), f"n20_rerun_long_{dataset}_main.csv")
    main_df.to_csv(main_path, index=False)
    df = pd.concat([main_df, oc_df], ignore_index=True)
    path = os.path.join(_tables(), f"n20_rerun_long_{dataset}.csv")
    df.to_csv(path, index=False)
    logger.info("Saved -> %s (%d rows) and %s", path, len(df), main_path)
    return df


def rerun_chunk(dataset, mode, factor, which):
    """One (mode, factor) cell in its own process, for memory-constrained datasets (ONGC).
    ``which`` is "main" (10 default detectors) or "ocsvm". Skips if the chunk already exists."""
    from src.benchmark import run_benchmark
    path = os.path.join(_tables(), "n20_chunks", f"{dataset}_{which}_{mode}_{factor}.csv")
    if os.path.exists(path):
        logger.info("chunk exists, skipped: %s", path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    methods = [OCSVM] if which == "ocsvm" else None
    df = run_benchmark(dataset=dataset, methods=methods, control=dataset == "IMS",
                       seeds=[SEED], modes=[mode], factors=[factor], save=False)
    df.to_csv(path + ".tmp", index=False)
    os.replace(path + ".tmp", path)          # atomic: a killed process leaves no chunk


def assemble(dataset):
    """Concatenate chunks in run_benchmark's own loop order (mode, then factor), main first."""
    from src.config import SAMPLING
    d = os.path.join(_tables(), "n20_chunks")
    parts = {"main": [], "ocsvm": []}
    for which in parts:
        for mode in SAMPLING["modes"]:
            for f in SAMPLING["factors"]:
                parts[which].append(
                    pd.read_csv(os.path.join(d, f"{dataset}_{which}_{mode}_{f}.csv")))
    main_df = pd.concat(parts["main"], ignore_index=True)
    main_df.to_csv(os.path.join(_tables(), f"n20_rerun_long_{dataset}_main.csv"), index=False)
    df = pd.concat([main_df] + parts["ocsvm"], ignore_index=True)
    df.to_csv(os.path.join(_tables(), f"n20_rerun_long_{dataset}.csv"), index=False)
    logger.info("assembled %s: %d rows", dataset, len(df))


def verify():
    """IMS / XJTU-SY post-fix reruns vs the published files: bytes and values."""
    t = _tables()
    rows = []
    for ds in INVARIANT_DATASETS:
        pub_path = os.path.join(t, PUBLISHED[ds])
        new_path = os.path.join(t, f"n20_rerun_long_{ds}_main.csv")
        pub, new = pd.read_csv(pub_path), pd.read_csv(new_path)
        common = [c for c in pub.columns if c in new.columns]
        extra = sorted(set(pub.columns) ^ set(new.columns))
        pub_c, new_c = pub[common], new[common]
        equal = pub_c.shape == new_c.shape and pub_c.equals(new_c)
        # Byte level: serialise both frames with the same writer, so a byte difference
        # reflects values, not a pandas-version formatting change.
        b_pub = pub_c.to_csv(index=False).encode()
        b_new = new_c.to_csv(index=False).encode()
        with open(pub_path, "rb") as fh:
            raw_pub = fh.read().replace(b"\r\n", b"\n")
        with open(new_path, "rb") as fh:
            raw_new = fh.read().replace(b"\r\n", b"\n")
        rows.append({
            "dataset": ds, "published_file": PUBLISHED[ds],
            "rows_pub": len(pub), "rows_new": len(new),
            "columns_only_in_one": ";".join(extra),
            "values_identical": bool(equal),
            "bytes_identical_common_columns": b_pub == b_new,
            "raw_file_bytes_identical": raw_pub == raw_new,
            "sha256_pub_common": hashlib.sha256(b_pub).hexdigest()[:16],
            "sha256_new_common": hashlib.sha256(b_new).hexdigest()[:16],
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(t, "n20_reproduction_check.csv"), index=False)
    print(df.to_string(index=False))
    return df


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    ap = argparse.ArgumentParser(description="N-20 resampling fix: verify and propagate")
    sp = ap.add_subparsers(dest="cmd", required=True)
    h = sp.add_parser("hash")
    h.add_argument("--tag", required=True, choices=["pre", "post"])
    sp.add_parser("compare")
    r = sp.add_parser("rerun")
    r.add_argument("--dataset", required=True)
    sp.add_parser("verify")
    c = sp.add_parser("chunk")
    c.add_argument("--dataset", required=True)
    c.add_argument("--mode", required=True, choices=["aggregate", "decimate"])
    c.add_argument("--factor", required=True, type=int)
    c.add_argument("--which", required=True, choices=["main", "ocsvm"])
    s = sp.add_parser("assemble")
    s.add_argument("--dataset", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "chunk":
        rerun_chunk(a.dataset, a.mode, a.factor, a.which)
        return 0
    if a.cmd == "assemble":
        assemble(a.dataset)
        return 0
    if a.cmd == "hash":
        fingerprint(a.tag)
    elif a.cmd == "compare":
        compare()
    elif a.cmd == "rerun":
        rerun(a.dataset)
    else:
        verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
