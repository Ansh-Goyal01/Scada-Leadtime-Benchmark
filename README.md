# SCADA Lead-Time Benchmark

**Lead-time-centric evaluation of anomaly detectors for bearing prognostics, and a
controlled study of how SCADA-rate logging (aggregation vs decimation) affects warning
time.**

This repository asks a different question than most anomaly-detection benchmarks. Not
*"did the detector flag the failure?"* but *"how many hours of actionable warning did it
give, at an acceptable false-alarm rate?"* — and *"does storing data at a coarse SCADA
logging rate destroy that warning time?"*

> **Headline finding (honest, and opposite to our original hypothesis).** Under a corrected
> label, an ungameable onset-relative metric, and a *controlled* sampling sweep, bin
> **aggregation does not destroy lead time on IMS — it significantly *extends* it** for
> several detectors (3σ: +17.5 h median, *p* = 0.003; EWMA: +2.5 h, *p* = 0.006; Hotelling
> T²: +0.8 h, *p* = 0.05; Isolation Forest: n.s.). On real ONGC turbine SCADA data the
> aggregate-vs-decimate difference is sub-minute and not significant (*p* ≥ 0.125, n = 5).
> Averaging stabilizes the health signal more than it smears the transient. With n = 3 IMS
> runs this is a motivating result, not a closed case — hence the XJTU-SY / FEMTO loaders
> for generalization.

This is a revision of an earlier version that a reviewer scored 3/10. The defects were
real and are documented and fixed below; nothing here is tuned to produce a positive
result.

---

## What was wrong, and what changed

| # | Reviewer weakness | Status | Fix |
|---|---|---|---|
| W1 | Lead-time metric gameable — a "latch-on" detector scored near-max lead at 0 % FAR | **Fixed** | Data-anchored **degradation onset** (`src/onset.py`) + **pre-onset FAR** over the full normal region; validity gated on a FAR budget. Latch-on now scores invalid (`tests/test_metrics.py`). |
| W3 | `3rd_test` mislabeled — 21.5 % of rows lay *after* the "failure" | **Fixed** | Label corrected `2004-04-08` → `2004-04-18 02:42` (`config.py`), verified against the RMS trajectory. |
| W4 | p ≫ n (445/1465 features vs ~100 samples) | **Fixed** | Channel-count-**invariant** feature schema → fixed 49-dim space, identical across 4-/8-channel runs; train-fit top-k selection guarantees p < n. |
| W5/W8 | n = 3, no statistics; conformal/bootstrap built but never wired | **Fixed** | `src/benchmark.py` bootstrap CIs (resampling runs) + Wilcoxon paired test; conformal wired (`conformal_if`) with a calibration-curve validation. |
| W6/W7 | FAR on 1–4 windows; window/persistence floored at coarse factors | **Fixed** | FAR over the full pre-onset region; **controlled** feature-level sweep (`--control`) holds window content & persistence constant. |
| W10 | Spectral information discarded | **Added, reported honestly** | `src/spectral_features.py` (defect frequencies, spectral kurtosis, Hilbert envelope). Ablation shows spectral does **not** cleanly help on IMS. |

---

## Datasets

| Dataset | Role | Status |
|---|---|---|
| **IMS** (NASA, 20.48 kHz run-to-failure) | Controlled benchmark; raw waveforms make the sampling sweep valid and enable spectral features | Included (processed parquet) |
| **ONGC Solar Turbine** | Real industrial SCADA: 4 vibration channels, 10-s logging, ~5 days, ending in a real operator shutdown (2023-11-13) | Included (gitignored raw `.xlsx`) |
| **XJTU-SY**, **FEMTO/PRONOSTIA** | Cross-condition generalization | Loaders implemented; data is a multi-GB local download — see `scripts/download_data.py` |

---

## Quickstart

```bash
pip install -r requirements.txt          # pinned; CPU-only (torch optional)
python -m pytest                         # 32 tests — metric/onset/conformal contracts

# Statistical benchmark (corrected labels, onset-relative metrics, bootstrap CIs, paired test)
python -m src.benchmark --dataset IMS               # standard sweep
python -m src.benchmark --dataset IMS --control     # W7 controlled feature-level sweep (headline)
python -m src.benchmark --dataset ONGC              # real-turbine SCADA

# Phase-D analyses
python -m src.calibration --dataset IMS   # conformal FAR <= alpha validation (calibration curve)
python -m src.tradeoff   --dataset IMS    # lead-time vs pre-onset-FAR trade-off (prognostics ROC)
python -m src.ablation   --dataset IMS    # feature-group ablation (time / spectral / envelope)
```

> On Windows set `PYTHONIOENCODING=utf-8` so the σ / T² glyphs in log output render.

Outputs land in `results/tables/` (long-format CSVs + aggregates) and `results/figures/`.

---

## Method (one paragraph)

Each run is split temporally into train / calibration / test. A single **degradation
onset** `t_onset` is detected per run from a health indicator (RMS-and-kurtosis trend),
using **only the training baseline** so it is leakage-free; it is the start of the last
sustained above-band excursion before failure. Detectors are fit on normal training data,
scored on test, and thresholded; the first sustained alarm gives the **lead time**
(`t_fail − FAT`). An alarm is **valid** only if its **pre-onset FAR** — the false-alarm
rate over the entire `[start, t_onset)` region — is within budget. This jointly-reported
pair (lead time, pre-onset FAR) is what defeats the latch-on exploit. The SCADA constraint
is simulated by coarsening the grid before feature extraction (`aggregate` = bin mean,
`decimate` = every k-th sample); the controlled sweep instead resamples at the feature
level so window content and persistence stay constant.

---

## Repository map

```
src/
  onset.py            degradation-onset detection (leakage-free)         [W1]
  lead_time.py        FAT / lead-time / pre-onset-FAR / evaluation       [W1,W6]
  benchmark.py        statistical harness: long-format, CIs, paired test [W2,W5,W7]
  features.py         channel-invariant feature schema + selection       [W4]
  spectral_features.py FFT bands, spectral kurtosis, Hilbert envelope    [W10]
  models.py           detectors + factory (incl. conformal_if)
  uncertainty.py      ConformalDetector, BootstrapEnsemble, calibration  [W8]
  calibration.py      conformal FAR <= alpha validation over pre-onset   [W8]
  tradeoff.py         lead-time vs pre-onset-FAR trade-off curves         [W6]
  ablation.py         feature-group ablation (invariant schema)          [W10]
  datasets.py         RunBundle contract + IMS/ONGC/XJTU/FEMTO loaders   [W5]
  baselines_extra.py  RMS-trend, spectral-kurtosis, Deep SVDD baselines
tests/                unit tests pinning the metric/onset/conformal contracts
scripts/download_data.py   guided XJTU-SY / FEMTO downloader (+ checksum hooks)
paper/                methods + results write-up with all tables/figures
```

---

## Honest caveats

- **n = 3 IMS runs.** The reversed aggregation finding is significant under a paired test
  but rests on three runs; treat it as motivating until XJTU-SY/FEMTO are run.
- **1st_test onset is late.** Its mean-RMS onset fires ~12 h before failure, so its
  "pre-onset" region already contains degradation. This inflates its pre-onset FAR and
  breaks the conformal exchangeability assumption *on that run only* (2nd/3rd_test are
  well-calibrated). Reported, not hidden.
- **Spectral features did not help on IMS.** They produce longer raw lead times but lower
  validity (more pre-onset false alarms); time-domain `rms`/`kurtosis` carry the signal.
