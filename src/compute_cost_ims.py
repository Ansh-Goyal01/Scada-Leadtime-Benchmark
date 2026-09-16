"""
Table 25 (`tab:compute`) regenerated under decision D-2.

The published table reports per-detector train time and inference cost "on the largest
IMS run (631 train / 506 test windows, single CPU core, median of five repeats)". Those
timings were taken on the 445-dim LEGACY feature matrix; D-2 re-baselines IMS onto the
49-dim invariant schema, so the feature width -- and hence the cost -- changes.

Like Table 5's source file (defect N-15), Table 25 had no generator in the repo. This
is it.

Timing protocol, matching the caption: median of five repeats, `fit(X_train)` for the
train column and `score(X_test)` for inference, reported as microseconds per test
window. Single-threaded where the library honours it.

Usage
-----
    python -m src.compute_cost_ims                    # invariant (D-2 default)
    python -m src.compute_cost_ims --schema legacy    # the published 445-dim timings
    python -m src.compute_cost_ims --repeats 1        # quick check
"""

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

from src.benchmark import make_detectors
from src.config import EXPERIMENT, PATHS
from src.sampling import load_pipeline_controlled

try:                                       # N-13: cp1252 console cannot print sigma
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

RUN = "3rd_test"                           # the largest IMS run (506 test windows)
DETECTORS = ["three_sigma", "ewma", "cusum", "hotelling_t2", "isolation_forest",
             "deep_svdd", "lstm_ae", "tcn", "transformer_ad"]


def time_detector(name: str, X_train: np.ndarray, X_test: np.ndarray,
                  seed: int, repeats: int) -> tuple:
    """Median fit seconds and median score microseconds per test window."""
    fits, scores = [], []
    for _ in range(repeats):
        det = make_detectors([name], seed)[0]
        t0 = time.perf_counter()
        det.fit(X_train)
        fits.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        det.score(X_test)
        scores.append((time.perf_counter() - t0) / len(X_test) * 1e6)
    return float(np.median(fits)), float(np.median(scores))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="invariant", choices=["invariant", "legacy"])
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()

    # Single core, so the numbers mean what the caption says they mean.
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(var, "1")
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass

    pipe = load_pipeline_controlled(RUN, factor=1, mode="none",
                                    feature_mode=args.schema)
    X_train, X_test = pipe["X_train"], pipe["X_test"]
    seed = EXPERIMENT["random_seed"]

    print("=" * 88)
    print(f"Table 25 (tab:compute) -- schema={args.schema}, run={RUN}, "
          f"median of {args.repeats} repeats")
    print(f"{len(X_train)} train / {len(X_test)} test windows, "
          f"{pipe['n_features']} features")
    print("  published caption: 631 train / 506 test windows")
    print("=" * 88)

    rows = []
    for name in DETECTORS:
        try:
            fit_s, inf_us = time_detector(name, X_train, X_test, seed, args.repeats)
        except Exception as e:                       # a detector may be unavailable
            print(f"  {name:<20} FAILED: {e}")
            continue
        det = make_detectors([name], seed)[0]
        rows.append({
            "schema": args.schema, "detector": name, "method": det.name,
            "n_train_windows": len(X_train), "n_test_windows": len(X_test),
            "n_features": pipe["n_features"],
            "train_seconds": round(fit_s, 6),
            "inference_us_per_window": round(inf_us, 3),
            "repeats": args.repeats,
        })
        train_str = "<1 ms" if fit_s < 1e-3 else (f"{fit_s * 1e3:.0f} ms" if fit_s < 1
                                                  else f"{fit_s:.2f} s")
        inf_str = "<0.1" if inf_us < 0.1 else f"{inf_us:.1f}"
        print(f"  {det.name:<24} train {train_str:>10}   inference {inf_str:>7} us/win")

    out = pd.DataFrame(rows)
    path = os.path.join(PATHS["results_tables"], f"compute_cost_IMS_{args.schema}.csv")
    if os.path.exists(path):
        print(f"\nrefusing to overwrite existing {path}")
    else:
        out.to_csv(path, index=False)
        print(f"\nWrote {path}  ({len(out)} rows)")


if __name__ == "__main__":
    main()
