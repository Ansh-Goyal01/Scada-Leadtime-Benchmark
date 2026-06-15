#!/usr/bin/env python
"""
Guided downloader for the public run-to-failure bearing datasets used in the
generalization experiments (XJTU-SY, FEMTO/PRONOSTIA).

WHY THIS IS GUIDED, NOT FULLY AUTOMATIC
---------------------------------------
These datasets (multi-GB) are hosted on MediaFire / MEGA / Baidu / Mendeley, which
require interactive auth or have anti-bot redirects — a plain `requests.get` is not
reliable. So this script:
  1. Prints the canonical source URLs and the expected on-disk layout.
  2. If you place the downloaded archive(s) in data/raw/_downloads/, it verifies the
     SHA-256 (when known), extracts them into data/raw/<DATASET>/, and reports the
     bearing run folders it found (the run_names you pass to the pipeline).

Usage:
  python scripts/download_data.py --dataset XJTU-SY        # show instructions
  python scripts/download_data.py --dataset XJTU-SY --extract   # verify+extract a placed archive
  python scripts/download_data.py --dataset FEMTO --extract
  python scripts/download_data.py --verify                 # list discovered runs

After extraction, run e.g.:
  python -m src.benchmark --dataset XJTU-SY
"""

import argparse
import hashlib
import os
import sys
import zipfile
import tarfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
DL = os.path.join(RAW, "_downloads")

SOURCES = {
    "XJTU-SY": {
        "papers": "Wang et al., IEEE Trans. Reliability 69(1):401-412, 2020 (DOI 10.1109/TR.2018.2882682)",
        "urls": [
            "https://github.com/WangBiaoXJTU/xjtu-sy-bearing-datasets  (official: MediaFire / MEGA / Baidu links)",
            "https://data.mendeley.com/datasets/mpn45f4gxc/1            (Mendeley mirror, .mat)",
        ],
        "layout": "data/raw/XJTU-SY/<condition>/<BearingX_Y>/<k>.csv  (2 cols H/V, 32768 rows @25.6kHz, 1/min)",
        "archives": ["XJTU-SY_Bearing_Datasets.zip"],
        "sha256": {},   # fill in if you want strict verification
    },
    "FEMTO": {
        "papers": "Nectoux et al., PRONOSTIA, IEEE PHM 2012 Data Challenge",
        "urls": [
            "https://github.com/wkzs111/phm-ieee-2012-data-challenge-dataset",
            "https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/  (PCoE mirror)",
        ],
        "layout": "data/raw/FEMTO/<Learning_set|Full_Test_Set>/<BearingX_Y>/acc_*.csv  (rows: h,m,s,us,h_acc,v_acc; 2560/file @25.6kHz, 1/10s)",
        "archives": ["FEMTOBearingDataSet.zip"],
        "sha256": {},
    },
}


def _sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def show(dataset):
    s = SOURCES[dataset]
    print(f"\n=== {dataset} ===")
    print("Reference:", s["papers"])
    print("Download from one of:")
    for u in s["urls"]:
        print("   -", u)
    print("Expected layout after extraction:")
    print("  ", s["layout"])
    print(f"\nTo extract: place the archive in {DL} and re-run with --extract.")


def extract(dataset):
    s = SOURCES[dataset]
    os.makedirs(DL, exist_ok=True)
    target = os.path.join(RAW, dataset)
    os.makedirs(target, exist_ok=True)
    found = False
    for name in os.listdir(DL):
        path = os.path.join(DL, name)
        if not os.path.isfile(path):
            continue
        want = s["sha256"].get(name)
        if want:
            got = _sha256(path)
            if got != want:
                print(f"!! checksum mismatch for {name}: {got} != {want}; skipping")
                continue
            print(f"checksum OK: {name}")
        try:
            if name.endswith(".zip"):
                with zipfile.ZipFile(path) as z:
                    z.extractall(target)
                found = True
            elif name.endswith((".tar", ".tar.gz", ".tgz")):
                with tarfile.open(path) as t:
                    t.extractall(target)
                found = True
            else:
                continue
            print(f"extracted {name} -> {target}")
        except Exception as e:
            print(f"!! failed to extract {name}: {e}")
    if not found:
        print(f"No archive found in {DL}. Place the dataset archive there first.")
    else:
        verify_one(dataset)


def verify_one(dataset):
    target = os.path.join(RAW, dataset)
    if not os.path.isdir(target):
        print(f"{dataset}: not present at {target}")
        return
    runs = []
    for dp, dn, fn in os.walk(target):
        base = os.path.basename(dp)
        if base.lower().startswith("bearing") and fn:
            runs.append(base)
    runs = sorted(set(runs))
    print(f"{dataset}: {len(runs)} bearing runs discovered: {runs[:8]}{' ...' if len(runs) > 8 else ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=list(SOURCES.keys()))
    ap.add_argument("--extract", action="store_true", help="verify+extract a placed archive")
    ap.add_argument("--verify", action="store_true", help="list discovered runs for all datasets")
    args = ap.parse_args()

    os.makedirs(DL, exist_ok=True)
    if args.verify:
        for d in SOURCES:
            verify_one(d)
        return
    if not args.dataset:
        for d in SOURCES:
            show(d)
        return
    if args.extract:
        extract(args.dataset)
    else:
        show(args.dataset)


if __name__ == "__main__":
    main()
