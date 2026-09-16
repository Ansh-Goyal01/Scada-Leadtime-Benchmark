"""
Table 25 (`tab:compute`) -- the detectors the published table omits, plus the deep-model
parameter counts register item 3.3 (G5) needs.

WHY THIS EXISTS. `src/compute_cost_ims.py` times nine detectors. Two of the eleven
evaluated detectors are missing from it and from the published Table 25:

  * `one_class_svm` -- added by decision D-5 (report OC-SVM);
  * `rms_trend`     -- **already missing before OC-SVM**. Table 25 (tex:1013-1021) has
    nine rows, but tex:970 claims monitoring "is therefore not compute-bound for any of
    the ten evaluated detectors". That sentence already overreaches its own table by one
    detector. Timing rms_trend here retires that gap at the same time.

With both added the table covers all eleven evaluated detectors and tex:970 can be
restated as "eleven" truthfully.

PROTOCOL. `time_detector` is imported from `src.compute_cost_ims` rather than
reimplemented, so the protocol is identical by construction: largest IMS run
(3rd_test), single CPU core, `fit(X_train)` for train and `score(X_test)` for
inference, median of five repeats, microseconds per test window.

NOTE ON ABSOLUTES. Per progress-file section 5E.7, the machine here is not the machine
that produced the published absolutes -- report RATIOS, not absolute seconds. The
existing nine remain in compute_cost_IMS_<schema>.csv, measured on this same machine,
so a same-machine ratio can be formed directly.

Outputs (NEW; the existing compute_cost_IMS_*.csv are never touched):
    results/tables/compute_cost_IMS_extra_<schema>.csv
    results/tables/deep_model_params.csv

Usage
-----
    python -m src.d3_compute_cost_extra
    python -m src.d3_compute_cost_extra --schema legacy
    python -m src.d3_compute_cost_extra --repeats 1        # quick check
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

from src.benchmark import make_detectors
from src.compute_cost_ims import RUN, time_detector
from src.config import EXPERIMENT, PATHS
from src.sampling import load_pipeline_controlled

try:                                       # N-13: cp1252 console cannot print sigma
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# The two detectors absent from the published Table 25.
MISSING = ["one_class_svm", "rms_trend"]

# Deep models whose parameter counts register item 3.3 (G5) needs.
DEEP = ["lstm_ae", "tcn", "transformer_ad"]


def _pin_single_core():
    """Same single-core pinning compute_cost_ims applies, so timings are comparable."""
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(var, "1")
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass


def count_params(detector):
    """
    Total and trainable parameter counts for a fitted deep detector.

    The torch module is built inside fit(), so the detector must already be fitted.
    Rather than assume an attribute name, walk the instance for anything that is an
    nn.Module -- the three deep detectors do not share a common attribute.
    """
    try:
        import torch.nn as nn
    except ImportError:
        return None, None
    modules = [v for v in vars(detector).values() if isinstance(v, nn.Module)]
    if not modules:
        return None, None
    total = sum(p.numel() for m in modules for p in m.parameters())
    trainable = sum(p.numel() for m in modules for p in m.parameters() if p.requires_grad)
    return int(total), int(trainable)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="invariant", choices=["invariant", "legacy"])
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--skip-params", action="store_true",
                    help="skip the deep-model parameter counts (they require a fit)")
    args = ap.parse_args()

    _pin_single_core()

    pipe = load_pipeline_controlled(RUN, factor=1, mode="none", feature_mode=args.schema)
    X_train, X_test = pipe["X_train"], pipe["X_test"]
    seed = EXPERIMENT["random_seed"]

    print("=" * 88)
    print("Table 25 additions -- schema=%s, run=%s, median of %d repeats"
          % (args.schema, RUN, args.repeats))
    print("%d train / %d test windows, %d features"
          % (len(X_train), len(X_test), pipe["n_features"]))
    print("=" * 88)

    rows = []
    for name in MISSING:
        try:
            fit_s, inf_us = time_detector(name, X_train, X_test, seed, args.repeats)
        except Exception as e:
            print("  %-20s FAILED: %s" % (name, e))
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
        train_str = "<1 ms" if fit_s < 1e-3 else ("%.0f ms" % (fit_s * 1e3) if fit_s < 1
                                                  else "%.2f s" % fit_s)
        inf_str = "<0.1" if inf_us < 0.1 else "%.1f" % inf_us
        print("  %-24s train %10s   inference %7s us/win" % (det.name, train_str, inf_str))

    if rows:
        out = pd.DataFrame(rows)
        p = os.path.join(PATHS["results_tables"],
                         "compute_cost_IMS_extra_%s.csv" % args.schema)
        if os.path.exists(p):
            print("\nrefusing to overwrite existing %s" % p)
        else:
            out.to_csv(p, index=False)
            print("\nWrote %s  (%d rows)" % (p, len(out)))

    if args.skip_params:
        return

    print("\n" + "=" * 88)
    print("Deep-model parameter counts (register item 3.3 / G5)")
    print("=" * 88)
    prows = []
    for name in DEEP:
        try:
            det = make_detectors([name], seed)[0]
            det.fit(X_train)
            total, trainable = count_params(det)
        except Exception as e:
            print("  %-20s FAILED: %s" % (name, e))
            continue
        prows.append({
            "detector": name, "method": det.name,
            "n_features": pipe["n_features"],
            "seq_len": getattr(det, "seq_len", None),
            "hidden_size": getattr(det, "hidden_size", None),
            "num_layers": getattr(det, "num_layers", None),
            "total_params": total, "trainable_params": trainable,
            "schema": args.schema,
        })
        print("  %-24s total %-10s trainable %-10s (seq_len=%s)"
              % (det.name, total, trainable, getattr(det, "seq_len", "?")))

    if prows:
        pf = pd.DataFrame(prows)
        p = os.path.join(PATHS["results_tables"], "deep_model_params.csv")
        if os.path.exists(p):
            print("\nrefusing to overwrite existing %s" % p)
        else:
            pf.to_csv(p, index=False)
            print("\nWrote %s  (%d rows)" % (p, len(pf)))


if __name__ == "__main__":
    main()
