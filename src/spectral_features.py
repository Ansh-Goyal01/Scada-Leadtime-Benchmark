# src/spectral_features.py
"""
Vibration spectral / envelope / defect-frequency features for bearing prognostics.

Addresses reviewer weakness W10 (spectral information discarded): the time-domain
loader in ``preprocessing.load_ims_run`` reduces each 1-second snapshot to a handful
of statistical scalars (rms, kurtosis, ...). This module computes the complementary
*frequency-domain* per-snapshot scalars: broadband FFT band energies, spectral
kurtosis (an impulsiveness / fault-band locator), and Hilbert-envelope-spectrum
amplitudes at the kinematic bearing defect frequencies (BPFO / BPFI / BSF / FTF).

Design notes
------------
* Pure functions, numpy + scipy only (scipy.signal, scipy.fft, scipy.stats).
* No global state; safe to call from notebooks, loaders, and scripts.
* ``compute_spectral_for_run`` mirrors the file-reading + timestamp-parsing logic of
  ``preprocessing.load_ims_run`` so its datetime index matches and the two DataFrames
  can be joined column-wise (``df_stats.join(df_spectral)``).

The classic outer-race-fault model motivates the pipeline: a localized defect produces
a periodic impulse train (at the defect frequency) that *amplitude-modulates* a
high-frequency structural resonance. The raw spectrum shows the resonance, not the
defect rate; demodulating with the Hilbert envelope and FFT-ing the envelope recovers
a peak at the defect frequency and its harmonics. Spectral kurtosis points to the
resonance band to band-pass before demodulation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import signal as scipy_signal
from scipy import fft as scipy_fft
from scipy import stats as scipy_stats


# ---------------------------------------------------------------------------
# Bearing geometry & kinematic defect frequencies
# ---------------------------------------------------------------------------

@dataclass
class BearingGeometry:
    """Physical geometry of a rolling-element bearing.

    Attributes
    ----------
    n_balls : int
        Number of rolling elements (N).
    ball_diameter_mm : float
        Rolling-element diameter (d), millimetres.
    pitch_diameter_mm : float
        Pitch / cage diameter (D), millimetres.
    contact_angle_deg : float
        Contact angle (theta), degrees. 0 for radial-only deep-groove bearings.
    """
    n_balls: int
    ball_diameter_mm: float
    pitch_diameter_mm: float
    contact_angle_deg: float = 0.0


def defect_frequencies(geom: BearingGeometry, shaft_speed_hz: float) -> dict:
    """Kinematic bearing defect frequencies in Hz.

    Standard rolling-bearing formulas (fr = shaft rotation rate)::

        ratio = (d / D) * cos(theta)
        FTF  = (fr / 2) * (1 - ratio)                    # cage / fundamental train
        BPFO = (N / 2) * fr * (1 - ratio)                # ball-pass outer race
        BPFI = (N / 2) * fr * (1 + ratio)                # ball-pass inner race
        BSF  = (D / (2*d)) * fr * (1 - ratio**2)         # ball-spin

    Returns
    -------
    dict
        {'BPFO', 'BPFI', 'BSF', 'FTF'} -> frequency in Hz.
    """
    fr = float(shaft_speed_hz)
    N = float(geom.n_balls)
    d = float(geom.ball_diameter_mm)
    D = float(geom.pitch_diameter_mm)
    theta = np.deg2rad(geom.contact_angle_deg)
    ratio = (d / D) * np.cos(theta)

    ftf = (fr / 2.0) * (1.0 - ratio)
    bpfo = (N / 2.0) * fr * (1.0 - ratio)
    bpfi = (N / 2.0) * fr * (1.0 + ratio)
    bsf = (D / (2.0 * d)) * fr * (1.0 - ratio ** 2)

    return {"BPFO": float(bpfo), "BPFI": float(bpfi),
            "BSF": float(bsf), "FTF": float(ftf)}


# ---------------------------------------------------------------------------
# Broadband FFT band energies
# ---------------------------------------------------------------------------

def band_energies(x: np.ndarray, fs: float, bands: dict) -> dict:
    """Power (mean |X|^2 per bin) inside each frequency band.

    Parameters
    ----------
    x : 1-D array
        Real signal.
    fs : float
        Sampling rate, Hz.
    bands : dict
        {name: (f_lo, f_hi)} band edges in Hz.

    Returns
    -------
    dict
        {name: power} where power is the mean one-sided power spectral
        contribution within [f_lo, f_hi). Returns 0.0 for empty bands.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n == 0:
        return {name: 0.0 for name in bands}

    x = x - x.mean()
    X = scipy_fft.rfft(x)
    freqs = scipy_fft.rfftfreq(n, d=1.0 / fs)
    # One-sided power spectrum, normalized so it is independent of n.
    power = (np.abs(X) ** 2) / (n ** 2)

    out = {}
    for name, (f_lo, f_hi) in bands.items():
        mask = (freqs >= f_lo) & (freqs < f_hi)
        out[name] = float(power[mask].mean()) if mask.any() else 0.0
    return out


# ---------------------------------------------------------------------------
# Spectral kurtosis
# ---------------------------------------------------------------------------

def spectral_kurtosis(x: np.ndarray, fs: float, nperseg: int = 256) -> tuple:
    """Spectral kurtosis via STFT: impulsiveness of each frequency bin over time.

    For each frequency bin we collect its magnitude across all STFT time frames
    and take the kurtosis of that distribution. A high value flags a band that is
    intermittently energetic (impulsive) — characteristic of a bearing fault
    resonance — and is the canonical band selector for envelope analysis.

    Parameters
    ----------
    x : 1-D array
    fs : float
    nperseg : int
        STFT window length.

    Returns
    -------
    (sk_max, f_at_max) : tuple of float
        Maximum spectral kurtosis across frequency and the frequency (Hz) at
        which it occurs. Returns (0.0, 0.0) if the signal is too short.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size < nperseg:
        nperseg = max(8, x.size // 4)
        if x.size < 8:
            return 0.0, 0.0

    f, _, Z = scipy_signal.stft(x, fs=fs, nperseg=nperseg,
                                noverlap=nperseg // 2, boundary=None,
                                padded=False)
    mag = np.abs(Z)                                  # (n_freq, n_frames)
    if mag.shape[1] < 4:
        return 0.0, 0.0

    # Fisher kurtosis (excess) across time, per frequency bin.
    sk = scipy_stats.kurtosis(mag, axis=1, fisher=True, bias=False,
                              nan_policy="omit")
    sk = np.nan_to_num(sk, nan=0.0, posinf=0.0, neginf=0.0)
    idx = int(np.argmax(sk))
    return float(sk[idx]), float(f[idx])


# ---------------------------------------------------------------------------
# Envelope spectrum
# ---------------------------------------------------------------------------

def _bandpass(x: np.ndarray, fs: float, f_lo: float, f_hi: float) -> np.ndarray:
    """Zero-phase Butterworth band-pass; clamps band edges to a valid range."""
    nyq = fs / 2.0
    f_lo = max(1.0, float(f_lo))
    f_hi = min(nyq * 0.999, float(f_hi))
    if f_hi <= f_lo:
        return x
    sos = scipy_signal.butter(4, [f_lo / nyq, f_hi / nyq],
                              btype="band", output="sos")
    return scipy_signal.sosfiltfilt(sos, x)


def envelope_spectrum(x: np.ndarray, fs: float, band: Optional[tuple] = None):
    """Hilbert-envelope spectrum, optionally band-limited first.

    Demodulates the signal: optionally band-pass to a resonance band, take the
    analytic-signal magnitude (Hilbert envelope), remove its DC, and FFT.

    Parameters
    ----------
    x : 1-D array
    fs : float
    band : (f_lo, f_hi) or None
        If given, band-pass x before enveloping (use the SK-selected band).

    Returns
    -------
    (freqs, amp) : ndarray, ndarray
        One-sided envelope-spectrum frequencies (Hz) and magnitudes
        (normalized by signal length).
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n == 0:
        return np.array([0.0]), np.array([0.0])

    x = x - x.mean()
    if band is not None:
        x = _bandpass(x, fs, band[0], band[1])

    env = np.abs(scipy_signal.hilbert(x))
    env = env - env.mean()                            # drop DC of the envelope
    Env = scipy_fft.rfft(env)
    freqs = scipy_fft.rfftfreq(n, d=1.0 / fs)
    amp = np.abs(Env) / n
    return freqs, amp


def _peak_amp_at(freqs: np.ndarray, amp: np.ndarray,
                 target_hz: float, tol_hz: float) -> float:
    """Max envelope amplitude within +/- tol_hz of a target frequency."""
    if target_hz <= 0:
        return 0.0
    mask = (freqs >= target_hz - tol_hz) & (freqs <= target_hz + tol_hz)
    if not mask.any():
        return 0.0
    return float(amp[mask].max())


def defect_band_amplitudes(x: np.ndarray, fs: float, geom: BearingGeometry,
                           shaft_speed_hz: float, n_harmonics: int = 3,
                           tol_hz: float = 3.0) -> dict:
    """Envelope-spectrum amplitude summed over each defect frequency + harmonics.

    These are the headline fault features. For each defect frequency f_d we sum
    the peak envelope amplitude found near f_d, 2*f_d, ..., n_harmonics*f_d
    (each within +/- tol_hz), giving a single robust scalar per fault mode.

    Returns
    -------
    dict
        {'env_BPFO', 'env_BPFI', 'env_BSF', 'env_FTF'} -> summed amplitude.
    """
    freqs, amp = envelope_spectrum(x, fs, band=None)
    dfreq = defect_frequencies(geom, shaft_speed_hz)

    out = {}
    for name, f_d in dfreq.items():
        total = 0.0
        for h in range(1, n_harmonics + 1):
            total += _peak_amp_at(freqs, amp, f_d * h, tol_hz)
        out[f"env_{name}"] = float(total)
    return out


# ---------------------------------------------------------------------------
# Per-snapshot top-level feature extraction
# ---------------------------------------------------------------------------

# Broadband bands as fractions of Nyquist (fs/2), so they adapt to any fs.
_BROADBAND_FRACTIONS = {
    "band_lo": (0.00, 0.10),    # near-DC / shaft orders
    "band_mid": (0.10, 0.40),   # mid-frequency structural content
    "band_hi": (0.40, 0.95),    # high-frequency resonance region
}


def snapshot_spectral_features(x: np.ndarray, fs: float,
                               geom: Optional[BearingGeometry],
                               shaft_speed_hz: Optional[float],
                               channel_name: str) -> dict:
    """All spectral scalars for one channel's 1-D snapshot, as a flat dict.

    Keys are suffixed with ``channel_name`` (e.g. 'sk_max_ch0', 'env_BPFO_ch0').
    If ``geom`` or ``shaft_speed_hz`` is None, defect-frequency (envelope) features
    are skipped but spectral kurtosis and broadband band energies are still emitted.
    """
    x = np.asarray(x, dtype=np.float64)
    suffix = channel_name
    out = {}

    # Spectral kurtosis (impulsiveness locator).
    sk_max, sk_f = spectral_kurtosis(x, fs)
    out[f"sk_max_{suffix}"] = sk_max
    out[f"sk_f_{suffix}"] = sk_f

    # Broadband FFT band energies (fractions of Nyquist -> absolute Hz).
    nyq = fs / 2.0
    bands = {name: (lo * nyq, hi * nyq)
             for name, (lo, hi) in _BROADBAND_FRACTIONS.items()}
    for name, val in band_energies(x, fs, bands).items():
        out[f"{name}_{suffix}"] = val

    # Defect-frequency envelope features (the headline fault indicators).
    if geom is not None and shaft_speed_hz is not None:
        env = defect_band_amplitudes(x, fs, geom, shaft_speed_hz)
        for name, val in env.items():
            out[f"{name}_{suffix}"] = val

    return out


# ---------------------------------------------------------------------------
# Run-level driver (mirrors preprocessing.load_ims_run file/timestamp logic)
# ---------------------------------------------------------------------------

def _parse_timestamp(stem: str, i: int) -> pd.Timestamp:
    """Parse an IMS snapshot filename into a Timestamp (mirror of load_ims_run)."""
    try:
        parts = stem.split(".")
        return pd.Timestamp(
            year=int(parts[0]), month=int(parts[1]), day=int(parts[2]),
            hour=int(parts[3]), minute=int(parts[4]),
            second=int(parts[5]) if len(parts) > 5 else 0,
        )
    except Exception:
        try:
            return pd.Timestamp(float(stem), unit="s")
        except Exception:
            return pd.Timestamp("2003-10-22") + pd.Timedelta(minutes=i)


def compute_spectral_for_run(run_dir: str, geom: Optional[BearingGeometry],
                             shaft_speed_hz: Optional[float],
                             n_channels: int = 8, fs: float = 20480.0,
                             max_files: Optional[int] = None,
                             verbose: bool = True) -> pd.DataFrame:
    """Compute per-snapshot spectral features for an entire IMS run.

    Iterates the raw snapshot files in ``run_dir`` (same ordering, file-reading,
    and timestamp parsing as ``preprocessing.load_ims_run``), computes
    ``snapshot_spectral_features`` per channel, and returns a datetime-indexed
    DataFrame whose index matches ``load_ims_run`` so the two can be joined.

    Parameters
    ----------
    run_dir : str
        Folder of raw IMS snapshot files.
    geom, shaft_speed_hz : optional
        Bearing geometry & shaft rate; pass None to skip defect-freq features.
    n_channels : int
        Max channels to read per file (clamped to the file's actual width).
    fs : float
        Sampling rate, Hz (IMS = 20480).
    max_files : int or None
        If set, process only the first ``max_files`` files (fast testing).

    Returns
    -------
    pandas.DataFrame
        Datetime-indexed, one row per snapshot, spectral columns per channel.
    """
    run_dir = Path(run_dir)
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    files = sorted([f for f in run_dir.iterdir() if f.is_file()])
    if len(files) == 0:
        raise ValueError(f"No files found in {run_dir}")
    if max_files is not None:
        files = files[:max_files]

    if verbose:
        print(f"[spectral] Processing {len(files)} snapshot files from {run_dir.name} ...")

    records = []
    for i, filepath in enumerate(files):
        try:
            raw = np.loadtxt(filepath)
        except Exception:
            try:
                raw = np.loadtxt(filepath, delimiter="\t")
            except Exception:
                continue

        if raw.ndim == 1:
            raw = raw.reshape(-1, 1)

        actual_channels = min(raw.shape[1], n_channels)
        ts = _parse_timestamp(filepath.stem, i)

        row = {"timestamp": ts}
        for ch in range(actual_channels):
            x = raw[:, ch].astype(np.float64)
            row.update(snapshot_spectral_features(
                x, fs, geom, shaft_speed_hz, channel_name=f"ch{ch}"))
        records.append(row)

        if verbose and (i + 1) % 100 == 0:
            print(f"[spectral]   {i+1}/{len(files)} files ...")

    df = pd.DataFrame(records).set_index("timestamp").sort_index()
    if verbose:
        print(f"[spectral] Done: {df.shape[0]} snapshots x {df.shape[1]} features.")
    return df
