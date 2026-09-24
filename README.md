<div align="center">

# SCADA Lead-Time Benchmark

### A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing Anomaly Detection — and What It Reveals About SCADA-Rate Logging

*How many hours of actionable warning does a detector give — and does coarse SCADA-rate logging destroy it?*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20719076-1682D4.svg)](https://doi.org/10.5281/zenodo.20719076)
[![Tests](https://img.shields.io/badge/tests-181-brightgreen.svg)](tests/)
[![Datasets](https://img.shields.io/badge/datasets-4%20run--to--failure-orange.svg)](#datasets)
[![Reproducible](https://img.shields.io/badge/results-reproducible-success.svg)](#quickstart)

![PyTorch](https://img.shields.io/badge/PyTorch-CPU%20optional-EE4C2C.svg?logo=pytorch&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Isolation%20Forest-F7931E.svg?logo=scikitlearn&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-sign%20test%20%2B%20Holm-8CAAE6.svg?logo=scipy&logoColor=white)
![status](https://img.shields.io/badge/status-under%20review-blueviolet.svg)

</div>

---

This repository asks a different question than most anomaly-detection benchmarks. Not
*"did the detector flag the failure?"* but *"how many hours of actionable warning did it
give, at an acceptable false-alarm rate?"* — and *"does storing data at a coarse SCADA
logging rate destroy that warning time?"*

> **Headline finding (bounded, and opposite to our original hypothesis).** Eleven detectors
> were run on four run-to-failure datasets — XJTU-SY (n = 10), FEMTO/PRONOSTIA (n = 6),
> University of Ferrara (n = 6) and NASA IMS (n = 3). On the three multi-bearing campaigns
> the run-level aggregate−decimate difference in lead time is **equivalent to zero within a
> pre-specified ±1 h margin in all 33 detector × dataset cells**, with every 95% interval
> inside ±0.6 h. Those bearings are short-lived (0.7–8.9 h total life), so the result bounds
> the effect at the scale of **minutes**, not hours; the multi-week runway of industrial
> assets remains untested. On IMS the variance-sensitive charts shift positively (3σ median
> +15.1 h) but inconsistently across the three runs; the exact sign test cannot fall below
> *p* = 0.25 at n = 3, the IMS intervals are too wide to decide for 9 of 11 detectors, and no
> test survives Holm correction across the N = 44 family (0 of 44). The single ONGC
> gas-turbine record (n = 1) is a descriptive case study: the difference there is at most
> about a minute.
>
> *(An earlier version reported a significant +17.5 h, p = 0.003 on IMS. That p-value rested on
> pooling 3 runs × 5 sampling factors as 15 independent pairs — the factors within a run are
> pseudoreplicates. Collapsing to the run level removes the significance; the direction
> survives as a trend. See `src/stats_rigor.py`.)*

The repository accompanies a revised manuscript. Defects found in an earlier version are
documented and fixed below; nothing here is tuned to produce a positive result.

---

## What was wrong, and what changed

| # | Weakness in the earlier version | Status | Fix |
|---|---|---|---|
| W1 | Lead-time metric gameable — a "latch-on" detector scored near-max lead at 0 % FAR | **Fixed** | Data-anchored **degradation onset** (`src/onset.py`) + **pre-onset FAR** over the full normal region; validity gated on a FAR budget. Latch-on now scores invalid (`tests/test_metrics.py`). |
| W3 | `3rd_test` mislabeled — 21.5 % of rows lay *after* the "failure" | **Fixed** | Label corrected `2004-04-08` → `2004-04-18 02:42` (`config.py`), verified against the RMS trajectory. |
| W4 | p ≫ n (445/1465 features vs ~100 samples) | **Fixed** | Channel-count-**invariant** feature schema → fixed 49-dim space, identical across 4-/8-channel runs; train-fit top-k selection guarantees p < n. |
| W5/W8 | n = 3, no statistics; conformal/bootstrap built but never wired | **Fixed** | `src/benchmark.py` bootstrap CIs (resampling runs); **run-level** exact sign test + Holm–Bonferroni (`src/stats_rigor.py`) treats the run, not the within-run sampling factor, as the unit of inference; conformal wired (`conformal_if`) with a calibration-curve validation. |
| W5 (baselines) | Too few / dated baselines | **Added** | CUSUM control chart + Deep SVDD + one-class SVM + LSTM/TCN/Transformer reconstruction autoencoders (`src/models.py`, `src/deep_baselines.py`), eleven detectors in total. Deep sequence models are data-starved (20–335 normal training windows on FEMTO) and are reported, not tuned; short runs are marked explicit **N/A**, not dropped. |
| W8 (mechanism) | "Averaging helps" left as a post-hoc guess | **Tested** | `src/robustness.py` injects noise (10/20/30 dB SNR) and compares historian bin-averaging against median / moving-average / Kalman / wavelet denoisers, testing whether the trend is SCADA-averaging specifically or generic smoothing. |
| W6/W7 | FAR on 1–4 windows; window/persistence floored at coarse factors | **Fixed** | FAR over the full pre-onset region; **controlled** feature-level sweep (`--control`) holds window content & persistence constant. |
| W10 | Spectral information discarded | **Added, reported** | `src/spectral_features.py` (defect frequencies, spectral kurtosis, Hilbert envelope). Ablation shows spectral does **not** cleanly help on IMS. |

---

## Datasets

| Dataset | Role | Status |
|---|---|---|
| **IMS** (NASA, 20.48 kHz run-to-failure) | Controlled benchmark; raw waveforms make the sampling sweep valid and enable spectral features | Included (processed parquet) |
| **ONGC Solar Turbine** | Real industrial SCADA: 4 vibration channels, 10-s logging, ~5 days, ending in a real operator shutdown (2023-11-13) | Included (gitignored raw `.xlsx`) |
| **XJTU-SY** (10 run-to-failure bearings, 25.6 kHz) | Cross-condition generalization of the lead-time / sampling claim | Included (`.npy` bundle, conditions 1 & 2); loader auto-caches per-bearing parquet |
| **FEMTO/PRONOSTIA** (6 Learning_set run-to-failure bearings, 25.6 kHz) | Generalization of the lead-time / sampling claim | Included (local download — see `scripts/download_data.py`); loader auto-caches per-bearing parquet, uses only the run-to-failure Learning_set copies |
| **University of Ferrara** (6 self-aligning double-row ball bearings, 25.6 kHz; Arpa et al., *Data in Brief* 2024) | Independent constant-condition replication | Public (Mendeley); read by `src/loaders/ferrara_loader.py` |
| **Paderborn (KAt)** | *Fault classification* (pre-damaged bearings at fixed conditions) — **not run-to-failure**, so it cannot test a lead-time/sampling claim | Present on disk (`archive (5)/`); usable only for a separate healthy-vs-damaged detection study |

---

## Quickstart

```bash
pip install -r requirements.txt          # pinned; CPU-only (torch optional)
python -m pytest                          # 181 tests, incl. the table-number check below
python paper/verify_tables.py             # re-derives every printed table value from results/tables/

# Statistical benchmark (corrected labels, onset-relative metrics, bootstrap CIs)
python -m src.benchmark   --dataset IMS --control   # controlled feature-level sweep; ten detectors
                                                    # (the one-class SVM: python -m src.d3_ocsvm)
python -m src.benchmark   --dataset ONGC            # real-turbine SCADA (n=1 case study)
python -m src.benchmark   --dataset XJTU-SY         # 10 run-to-failure bearings
python -m src.benchmark   --dataset FEMTO           # 6 run-to-failure bearings (PRONOSTIA Learning_set)
python -m src.benchmark   --dataset Ferrara         # 6 run-to-failure bearings (University of Ferrara)

# Run-level significance (the run is the unit of inference): exact sign test + Holm
python -m src.stats_rigor                          # emits *_runlevel_test.csv + paired_tests_holm.csv
python -m src.d15_equivalence                      # ±1 h equivalence (bootstrap CIs on run-level differences)
python -m src.eq5_validity                         # validity counts under Eq. 5

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

## Diagnostic Console (alarm → root cause → fix)

The benchmark answers *when* an alarm should fire. The **diagnostic console**
answers the question the site engineers actually asked next: *when an alarm fires,
why, and what do we do about it* — without sending someone to the machine.

```bash
pip install dash plotly                    # console deps (in addition to requirements.txt)
python scripts/make_demo_fixtures.py       # synthetic stand-ins so it runs with no downloads
python -m src.diagnostic_console           # open http://127.0.0.1:8050
```

Workflow: pick a detected **alarm** → the multi-parameter timeline pins that moment →
**toggle/overlay** parameters and read their **relationships** (correlation around the
alarm + a scatter of the two strongest signals) → the **root-cause panel** ranks each
parameter's standardized deviation and maps the pattern to a **probable cause and
recommended fix** via an explicit failure-signature library.

Two multivariate machines are supported (the bearing datasets stay vibration-only):

| Machine | Real? | Native parameters | Role |
|---|---|---|---|
| **MetroPT-3** (Metro do Porto APU compressor) | real | pressures, oil temperature, motor current + real failures | headline — closest analog to the ONGC compressor |
| **C-MAPSS** (NASA turbofan) | model-generated | temperatures, pressures, shaft speeds, flows (21 sensors) | the full 8-parameter spread |

Place real data per `python scripts/download_data.py --dataset MetroPT-3` (or `C-MAPSS`);
until then the console clearly labels the view **SIMULATED**. It also illustrates a practical
point made concrete: ONGC's SCADA logs only vibration+RPM, which is *why* diagnosis
needs a site visit — the console demonstrates the multi-parameter diagnosis the site
lacks, and motivates instrumenting those channels.

Code: `src/diagnostic_console.py` (Dash UI) · `src/diagnosis.py` (alarms + root cause) ·
`src/metropt_preprocessing.py`, `src/cmapss_preprocessing.py` (loaders) ·
`src/console_data.py` (shared contract). Tests: `tests/test_diagnostic_console.py`.

---

## Method (one paragraph)

Each run is split temporally into train / calibration / test. A single **degradation
onset** `t_onset` is detected per run from a health indicator (RMS-and-kurtosis trend),
using **only the training baseline** so it is leakage-free; it is the start of the last
sustained above-band excursion before failure. Detectors are fit on normal training data,
scored on test, and thresholded; the first sustained alarm gives the **lead time**
(`t_fail − FAT`). An alarm is **valid** only if its **pre-onset FAR** — the false-alarm
rate over the entire `[start, t_onset)` region — is within budget. The budget is
τ = 10 %; an alarm whose pre-onset region is empty cannot be gated and is excluded from
validity counts. This jointly-reported pair (lead time, pre-onset FAR) is what defeats the
latch-on exploit. No dataset coarsens the raw waveform: on IMS the controlled sweep coarsens
the windowed feature vectors, holding window content and persistence constant; on XJTU-SY,
FEMTO, Ferrara and ONGC it coarsens the per-snapshot feature series (`aggregate` = bin mean
of the summary statistics, `decimate` = every f-th snapshot). This is historian-style storage
of summary statistics, not raw-signal averaging.

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
  d15_equivalence.py  ±1 h equivalence analysis (bootstrap CIs over runs)
  eq5_validity.py     validity counts under Eq. 5 (empty pre-onset region excluded)
tests/                unit tests pinning metric/onset/conformal/stats/baselines/robustness
scripts/download_data.py   guided XJTU-SY / FEMTO downloader (+ checksum hooks)
paper/                manuscript source; verify_tables.py re-derives every printed value
results/tables/       released result files; MANIFEST.md maps each table/figure to its file
```

---

## Caveats

- **The "aggregation helps" effect is an IMS-specific *trend*, not significant.** On IMS
  (n = 3) under the controlled sweep the median difference is positive for the
  magnitude-monitoring detectors, but only CUSUM and Hotelling T² are sign-consistent across
  the three runs; the exact sign test floors at *p* = 0.25 at n = 3 and nothing survives Holm
  correction. It does **not** replicate on XJTU-SY (n = 10), FEMTO (n = 6), Ferrara (n = 6) or
  ONGC (n = 1 case study): run-level medians are within ±9 min on FEMTO and ±1 min on Ferrara,
  and 0 h on XJTU-SY for ten of eleven detectors (−0.10 h for Isolation Forest); the smallest
  raw sign-test p anywhere in the N = 44 family is 0.125 (Transformer-AD on FEMTO), so no cell
  is significant even before Holm correction. The cross-dataset claim is therefore bounded
  equivalence at the scale of minutes, not "averaging helps." These bearings are short-lived
  (XJTU-SY 52–533 min; FEMTO ~1.4–7.8 h; Ferrara 0.7–6.8 h), so absolute lead times there are
  small and some abrupt-failure bearings are essentially unwarnable.
- **Deep sequence models are data-starved here.** LSTM/TCN/Transformer autoencoders train on
  20–335 normal windows on FEMTO (median 88 at the default split) and are reported for
  completeness, not tuned to win; on short runs they are marked explicit N/A. On IMS they show
  a *negative* median aggregate−decimate difference (two of three runs negative),
  consistent with the smoothing mechanism (a reconstruction model gains nothing from a
  smoother input).
- **1st_test onset is late.** Its mean-RMS onset fires ~12 h before failure, so its
  "pre-onset" region already contains degradation. This inflates its pre-onset FAR and
  breaks the conformal exchangeability assumption *on that run only* (2nd_test honors the
  bound through α = 0.10, 3rd_test through α = 0.05). Reported, not hidden.
- **Spectral features did not help on IMS.** They produce longer raw lead times but lower
  validity (more pre-onset false alarms); time-domain `rms`/`kurtosis` carry the signal.

---

## Citation

If you use this benchmark or its results, please cite the archived release
(concept DOI [10.5281/zenodo.20719076](https://doi.org/10.5281/zenodo.20719076), resolves
to the latest version):

```bibtex
@software{goyal_scada_leadtime,
  author    = {Goyal, Ansh},
  title     = {A Latch-On-Resistant, False-Alarm-Gated Lead-Time Metric for Bearing
               Anomaly Detection --- and What It Reveals About SCADA-Rate Logging},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20719076},
  url       = {https://github.com/Ansh-Goyal01/Scada-Leadtime-Benchmark}
}
```

A machine-readable [`CITATION.cff`](CITATION.cff) is provided, so GitHub shows a
**"Cite this repository"** button in the sidebar.

## License

Released under the [MIT License](LICENSE) — free to use, modify, and distribute with
attribution. Dataset terms (IMS, XJTU-SY, FEMTO/PRONOSTIA, University of Ferrara) remain
with their original providers; the ONGC turbine record is proprietary and not redistributed.
