# SCADA Lead-Time Benchmark

**Lead-time-centric evaluation of anomaly detectors for bearing prognostics, and a
controlled study of how SCADA-rate logging (aggregation vs decimation) affects warning
time.**

This repository asks a different question than most anomaly-detection benchmarks. Not
*"did the detector flag the failure?"* but *"how many hours of actionable warning did it
give, at an acceptable false-alarm rate?"* — and *"does storing data at a coarse SCADA
logging rate destroy that warning time?"*

> **Headline finding (honest, and opposite to our original hypothesis).** The original claim
> that SCADA averaging *destroys* detection lead time is **refuted on all four datasets**.
> Under a corrected label, an onset-relative metric that defeats the latch-on exploit, and a
> *controlled* sampling sweep, bin aggregation on IMS does not hurt: at the honest unit of
> inference (the **run**, n = 3), the per-run aggregate−decimate difference is the *same
> positive sign across all three runs* for every magnitude-monitoring detector (3σ median
> +18.4 h; IF +12.2 h; EWMA +5.8 h; CUSUM +5.4 h; Hotelling T² +4.6 h). But with only n = 3
> runs this is a **consistent trend, not a significant effect** — the exact sign test floors
> at *p* = 0.25 and nothing survives Holm correction across the detector×dataset family
> (N = 30). On the real **ONGC** turbine (n = 1, a descriptive case study) the difference is
> about a minute or less. On **XJTU-SY (n = 10 run-to-failure bearings)** and **FEMTO/PRONOSTIA (n = 6
> run-to-failure bearings)** the difference is negligible for every detector (median |diff| ≤ 8
> min; nothing survives Holm) — the IMS "averaging *helps*" trend does **not** generalize, but
> neither does "averaging hurts." The defensible cross-dataset conclusion is **non-destruction**:
> coarse SCADA-rate logging does not cost you bearing-fault warning time.
>
> *(An earlier version reported a significant +17.5 h, p = 0.003 on IMS. That p-value rested on
> pooling 3 runs × 5 sampling factors as 15 independent pairs — the factors within a run are
> pseudoreplicates. Collapsing to the run level removes the significance; the direction
> survives as a trend. See `src/stats_rigor.py`.)*

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
| W5/W8 | n = 3, no statistics; conformal/bootstrap built but never wired | **Fixed** | `src/benchmark.py` bootstrap CIs (resampling runs); **run-level** exact sign test + Holm–Bonferroni (`src/stats_rigor.py`) treats the run, not the within-run sampling factor, as the unit of inference; conformal wired (`conformal_if`) with a calibration-curve validation. |
| W5 (baselines) | Too few / dated baselines | **Added** | CUSUM control chart + Deep SVDD + LSTM/TCN/Transformer reconstruction autoencoders (`src/models.py`, `src/deep_baselines.py`), 10 detectors total. Deep sequence models are data-starved at ~100 windows and are reported, not tuned; short runs are marked explicit **N/A**, not dropped. |
| W8 (mechanism) | "Averaging helps" left as a post-hoc guess | **Tested** | `src/robustness.py` injects noise (10/20/30 dB SNR) and compares historian bin-averaging against median / moving-average / Kalman / wavelet denoisers, testing whether the trend is SCADA-averaging specifically or generic smoothing. |
| W6/W7 | FAR on 1–4 windows; window/persistence floored at coarse factors | **Fixed** | FAR over the full pre-onset region; **controlled** feature-level sweep (`--control`) holds window content & persistence constant. |
| W10 | Spectral information discarded | **Added, reported honestly** | `src/spectral_features.py` (defect frequencies, spectral kurtosis, Hilbert envelope). Ablation shows spectral does **not** cleanly help on IMS. |

---

## Datasets

| Dataset | Role | Status |
|---|---|---|
| **IMS** (NASA, 20.48 kHz run-to-failure) | Controlled benchmark; raw waveforms make the sampling sweep valid and enable spectral features | Included (processed parquet) |
| **ONGC Solar Turbine** | Real industrial SCADA: 4 vibration channels, 10-s logging, ~5 days, ending in a real operator shutdown (2023-11-13) | Included (gitignored raw `.xlsx`) |
| **XJTU-SY** (10 run-to-failure bearings, 25.6 kHz) | Cross-condition generalization of the lead-time / sampling claim | Included (`.npy` bundle, conditions 1 & 2); loader auto-caches per-bearing parquet |
| **FEMTO/PRONOSTIA** (6 Learning_set run-to-failure bearings, 25.6 kHz) | Fourth-dataset generalization of the lead-time / sampling claim | Included (local download — see `scripts/download_data.py`); loader auto-caches per-bearing parquet, uses only the run-to-failure Learning_set copies |
| **Paderborn (KAt)** | *Fault classification* (pre-damaged bearings at fixed conditions) — **not run-to-failure**, so it cannot test a lead-time/sampling claim | Present on disk (`archive (5)/`); usable only for a separate healthy-vs-damaged detection study |

---

## Quickstart

```bash
pip install -r requirements.txt          # pinned; CPU-only (torch optional)
python -m pytest                          # 76 tests — metric/onset/conformal/stats/baselines/robustness/FEMTO

# Statistical benchmark (corrected labels, onset-relative metrics, bootstrap CIs)
python -m src.benchmark   --dataset IMS --control   # controlled feature-level sweep (headline), 10 detectors
python -m src.benchmark   --dataset ONGC            # real-turbine SCADA (n=1 case study)
python -m src.benchmark   --dataset XJTU-SY         # 10 run-to-failure bearings
python -m src.benchmark   --dataset FEMTO           # 6 run-to-failure bearings (PRONOSTIA Learning_set)

# Run-level significance (the honest test): exact sign test + Holm across the family
python -m src.stats_rigor --datasets IMS XJTU-SY FEMTO   # emits *_runlevel_test.csv + paired_tests_holm.csv

# Mechanism test: is the IMS trend SCADA-averaging or generic smoothing?
python -m src.robustness  --dataset IMS             # noise sweep + denoiser comparison

# Phase-D analyses
python -m src.calibration --dataset IMS   # conformal FAR <= alpha validation (calibration curve)
python -m src.tradeoff   --dataset IMS    # lead-time vs pre-onset-FAR trade-off (prognostics ROC)
python -m src.ablation   --dataset IMS    # feature-group ablation (time / spectral / envelope)
```

> On Windows set `PYTHONIOENCODING=utf-8` so detector names with σ/λ/T² print correctly.

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
  benchmark.py        statistical harness: long-format, CIs; explicit N/A rows [W2,W5,W7]
  stats_rigor.py      run-level exact sign test + Holm (unit of inference fix) [W1,W2,W3]
  features.py         channel-invariant feature schema + selection       [W4]
  spectral_features.py FFT bands, spectral kurtosis, Hilbert envelope    [W10]
  models.py           detectors + factory (3σ/EWMA/CUSUM/T²/IF/conformal)
  deep_baselines.py   TCN + Transformer reconstruction AEs (short-run N/A guard) [W5]
  robustness.py       noise injection + denoiser comparison (mechanism test) [W8]
  uncertainty.py      ConformalDetector, BootstrapEnsemble, calibration  [W8]
  calibration.py      conformal FAR <= alpha validation over pre-onset   [W8]
  tradeoff.py         lead-time vs pre-onset-FAR trade-off curves         [W6]
  ablation.py         feature-group ablation (invariant schema)          [W10]
  datasets.py         RunBundle contract + IMS/ONGC/XJTU/FEMTO loaders   [W5]
  baselines_extra.py  RMS-trend, spectral-kurtosis, Deep SVDD baselines
tests/                unit tests pinning metric/onset/conformal/stats/baselines/robustness
scripts/download_data.py   guided XJTU-SY / FEMTO downloader (+ checksum hooks)
paper/                methods + results write-up with all tables/figures
```

---

## Honest caveats

- **The "aggregation helps" effect is an IMS-specific *trend*, not significant.** On IMS
  (n = 3) under the controlled sweep the per-run difference is positive and sign-consistent
  for the magnitude-monitoring detectors, but the exact sign test floors at *p* = 0.25 at
  n = 3 and nothing survives Holm correction. It does **not** replicate on XJTU-SY (n = 10),
  FEMTO (n = 6), or ONGC (n = 1 case study), where the difference is negligible (median |diff| ≤ 8
  min on both run-to-failure sets; one detector, Isolation Forest on FEMTO, is all-6-runs negative
  at a nominal sign-test p = 0.031 but does **not** survive Holm). The cross-dataset claim is
  therefore *non-destruction*, not "averaging helps." XJTU and FEMTO bearings are also
  short-lived (XJTU 52–533 min; FEMTO ~1.5–7.5 h), so absolute lead times there are small and
  some abrupt-failure bearings are essentially unwarnable.
- **Deep sequence models are data-starved here.** LSTM/TCN/Transformer autoencoders train on
  ~100 normal windows and are reported for completeness, not tuned to win; on short runs they
  are marked explicit N/A. On IMS they show a small *negative* aggregate−decimate trend,
  consistent with the smoothing mechanism (a reconstruction model gains nothing from a
  smoother input).
- **1st_test onset is late.** Its mean-RMS onset fires ~12 h before failure, so its
  "pre-onset" region already contains degradation. This inflates its pre-onset FAR and
  breaks the conformal exchangeability assumption *on that run only* (2nd/3rd_test are
  well-calibrated). Reported, not hidden.
- **Spectral features did not help on IMS.** They produce longer raw lead times but lower
  validity (more pre-onset false alarms); time-domain `rms`/`kurtosis` carry the signal.
