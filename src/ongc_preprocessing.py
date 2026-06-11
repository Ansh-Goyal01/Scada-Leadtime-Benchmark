# src/ongc_preprocessing.py
"""
ONGC Solar Turbine Data Loader and Preprocessor.

Handles:
- Multi-format timestamp parsing (robust to format variations)
- Column renaming with friendly engineering labels
- Merging Before/After shutdown files
- Baseline statistics computation (mean, UCL, LCL)
- Anomaly scoring via Isolation Forest
- Failure evolution window extraction
- DRI (Deterioration Rate Index) computation
"""

import numpy as np
import pandas as pd
import logging
from typing import Optional, Tuple, Dict, List

logger = logging.getLogger(__name__)

# ── Friendly channel labels ───────────────────────────────────────────────────
CHANNEL_META = {
    "LPC_DE_X_Vib":  {
        "label":  "Drive End — X Axis Vibration",
        "short":  "DE-X Vib",
        "unit":   "mm/s",
        "color":  "#3b82f6",
        "type":   "vibration",
    },
    "LPC_DE_Y_Vib":  {
        "label":  "Drive End — Y Axis Vibration",
        "short":  "DE-Y Vib",
        "unit":   "mm/s",
        "color":  "#ef4444",
        "type":   "vibration",
    },
    "LPC_NDE_X_Vib": {
        "label":  "Non-Drive End — X Axis Vibration",
        "short":  "NDE-X Vib",
        "unit":   "mm/s",
        "color":  "#22c55e",
        "type":   "vibration",
    },
    "LPC_NDE_Y_Vib": {
        "label":  "Non-Drive End — Y Axis Vibration",
        "short":  "NDE-Y Vib",
        "unit":   "mm/s",
        "color":  "#f59e0b",
        "type":   "vibration",
    },
    "Ncp": {
        "label":  "Compressor Speed",
        "short":  "Speed (RPM)",
        "unit":   "RPM",
        "color":  "#a855f7",
        "type":   "speed",
    },
}

# ── ISO 10816-3 vibration thresholds for industrial turbomachinery ────────────
# Class III/IV machines (large turbines/compressors on flexible mounts)
ISO_THRESHOLDS = {
    "good":    2.3,    # below this = good condition (green)
    "alert":   7.1,    # ISO alert threshold (yellow)
    "alarm":   11.2,   # ISO alarm threshold (orange)
    "danger":  18.0,   # ISO danger/trip threshold (red)
}

# ONGC typically uses 7.1 mm/s as advisory and 11.2 mm/s as trip for compressors
ONGC_ADVISORY = 7.1
ONGC_TRIP     = 11.2


# ─────────────────────────────────────────────────────────────────────────────
# Timestamp parser — handles any reasonable format
# ─────────────────────────────────────────────────────────────────────────────

def _parse_timestamp(s) -> pd.Timestamp:
    """
    Robustly parse a timestamp string from ONGC historian exports.
    Handles: '08-11-2023# 11:24:30', '2023-11-08 11:24:30', etc.
    """
    if isinstance(s, pd.Timestamp):
        return s
    if pd.isna(s):
        return pd.NaT

    s = str(s).strip().replace('# ', ' ').replace('#', ' ')

    formats = [
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%d-%b-%Y %H:%M:%S',
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            pass

    try:
        return pd.to_datetime(s)
    except Exception:
        logger.warning(f"Could not parse timestamp: {s!r}")
        return pd.NaT


# ─────────────────────────────────────────────────────────────────────────────
# File loader
# ─────────────────────────────────────────────────────────────────────────────

def load_ongc_file(path: str) -> pd.DataFrame:
    """
    Load a single ONGC Excel file.
    Returns a clean DataFrame with:
      - 'timestamp' as DatetimeIndex
      - Original column names preserved (empty columns dropped)
    """
    df = pd.read_excel(path)

    # Drop entirely empty columns
    df = df.dropna(axis=1, how='all')

    # Rename first column to 'timestamp'
    df = df.rename(columns={df.columns[0]: 'timestamp'})

    # Parse timestamps
    df['timestamp'] = df['timestamp'].apply(_parse_timestamp)
    df = df.dropna(subset=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Drop rows where ALL sensor columns are NaN
    sensor_cols = [c for c in df.columns if c != 'timestamp']
    df = df.dropna(subset=sensor_cols, how='all')

    logger.info(
        f"Loaded {path}: {len(df)} rows, "
        f"{df['timestamp'].min()} → {df['timestamp'].max()}"
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Merge Before + After into one continuous timeline
# ─────────────────────────────────────────────────────────────────────────────

def merge_before_after(before_path: str,
                       after_path: str) -> Tuple[pd.DataFrame, pd.Timestamp]:
    """
    Load and merge Before_Shutdown and After_Shutdown files.
    Adds a 'phase' column: 'operating' or 'post_shutdown'.
    Returns (merged_df, shutdown_timestamp).
    """
    df_b = load_ongc_file(before_path)
    df_a = load_ongc_file(after_path)

    # Shutdown = last timestamp of before file
    shutdown_time = df_b['timestamp'].max()

    df_b['phase'] = 'operating'
    df_a['phase'] = 'post_shutdown'

    # Align columns — after file may be missing some
    for col in df_b.columns:
        if col not in df_a.columns:
            df_a[col] = np.nan

    df_merged = pd.concat([df_b, df_a], ignore_index=True)
    df_merged = df_merged.sort_values('timestamp').reset_index(drop=True)
    df_merged = df_merged.set_index('timestamp')

    logger.info(
        f"Merged: {len(df_merged)} rows total | "
        f"Shutdown: {shutdown_time}"
    )
    return df_merged, shutdown_time


# ─────────────────────────────────────────────────────────────────────────────
# Baseline statistics
# ─────────────────────────────────────────────────────────────────────────────

def compute_baseline_stats(df: pd.DataFrame,
                            baseline_days: float = 2.0) -> Dict:
    """
    Compute mean, std, UCL (3σ), LCL (3σ) from the first N days of operation.
    Only uses the 'operating' phase rows.

    Returns a dict keyed by column name:
    {
      'LPC_DE_X_Vib': {
          'mean': ..., 'std': ..., 'ucl_3s': ..., 'lcl_3s': ...,
          'iso_alert': 7.1, 'iso_alarm': 11.2, 'iso_danger': 18.0
      }, ...
    }
    """
    operating = df[df['phase'] == 'operating'].copy() if 'phase' in df.columns else df.copy()
    operating = operating.select_dtypes(include=[np.number])

    start_time = operating.index.min()
    baseline_end = start_time + pd.Timedelta(days=baseline_days)
    baseline = operating[operating.index <= baseline_end]

    if len(baseline) < 10:
        logger.warning("Baseline period too short — using first 30% of data")
        n = max(10, int(len(operating) * 0.30))
        baseline = operating.iloc[:n]

    stats = {}
    for col in operating.columns:
        if col == 'phase':
            continue
        s = baseline[col].dropna()
        if len(s) < 5:
            continue
        mu    = float(s.mean())
        sigma = float(s.std()) + 1e-12
        meta  = CHANNEL_META.get(col, {})
        ch_type = meta.get('type', 'unknown')

        stats[col] = {
            'mean':    mu,
            'std':     sigma,
            'ucl_3s':  mu + 3 * sigma,
            'lcl_3s':  max(0.0, mu - 3 * sigma),
            'ucl_2s':  mu + 2 * sigma,
            'lcl_2s':  max(0.0, mu - 2 * sigma),
        }

        # Add ISO thresholds only for vibration channels
        if ch_type == 'vibration':
            stats[col].update({
                'iso_alert':  ISO_THRESHOLDS['alert'],
                'iso_alarm':  ISO_THRESHOLDS['alarm'],
                'iso_danger': ISO_THRESHOLDS['danger'],
            })

    logger.info(
        f"Baseline stats computed from {len(baseline)} rows "
        f"({baseline.index.min()} → {baseline.index.max()})"
    )
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly scoring — Isolation Forest
# ─────────────────────────────────────────────────────────────────────────────

def compute_anomaly_scores(df: pd.DataFrame,
                            baseline_stats: Dict,
                            train_frac: float = 0.40) -> pd.Series:
    """
    Train Isolation Forest on the first train_frac of operating data.
    Score the full dataset.
    Returns a Series of anomaly scores indexed by timestamp.
    Higher score = more anomalous.
    """
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import RobustScaler

    operating = df[df['phase'] == 'operating'].copy() if 'phase' in df.columns else df.copy()
    vib_cols  = [c for c in operating.columns
                 if c in CHANNEL_META and CHANNEL_META[c]['type'] == 'vibration']

    if not vib_cols:
        vib_cols = [c for c in operating.select_dtypes(include=[np.number]).columns
                    if c != 'phase']

    X_full = operating[vib_cols].fillna(method='ffill').fillna(method='bfill').values

    n_train = max(50, int(len(X_full) * train_frac))
    X_train = X_full[:n_train]

    scaler  = RobustScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_full_s  = scaler.transform(X_full)

    model = IsolationForest(
        n_estimators=200,
        contamination='auto',
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_s)

    raw_scores = -model.decision_function(X_full_s)

    # Normalize to [0, 1]
    lo, hi = raw_scores.min(), raw_scores.max()
    if hi - lo > 1e-10:
        scores_norm = (raw_scores - lo) / (hi - lo)
    else:
        scores_norm = np.zeros_like(raw_scores)

    score_series = pd.Series(scores_norm, index=operating.index, name='anomaly_score')

    # Also compute 3σ violation score (fraction of channels exceeding UCL)
    ucl_violations = pd.Series(0.0, index=operating.index)
    for col in vib_cols:
        if col in baseline_stats:
            ucl = baseline_stats[col]['ucl_3s']
            ucl_violations += (operating[col] > ucl).astype(float)
    ucl_violations = ucl_violations / max(len(vib_cols), 1)

    logger.info(
        f"Anomaly scoring complete | "
        f"Train: {n_train} rows | "
        f"Max score: {scores_norm.max():.4f}"
    )

    return score_series, ucl_violations, model, scaler, vib_cols


def find_first_alarm(score_series: pd.Series,
                     threshold_percentile: float = 95.0,
                     persistence: int = 5) -> Optional[pd.Timestamp]:
    """
    Find first sustained alarm from anomaly score series.
    persistence: number of consecutive windows above threshold.
    """
    threshold = float(np.percentile(score_series.values, threshold_percentile))
    above     = (score_series > threshold).values
    n         = len(above)

    for i in range(n - persistence + 1):
        if np.all(above[i:i + persistence]):
            return score_series.index[i]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Failure evolution analysis
# ─────────────────────────────────────────────────────────────────────────────

def compute_failure_evolution(df: pd.DataFrame,
                               baseline_stats: Dict,
                               shutdown_time: pd.Timestamp,
                               windows_hours: List[float] = None) -> pd.DataFrame:
    """
    Compute parameter deviation (in σ units) at each pre-failure time window.

    Returns a DataFrame:
      rows = channels
      columns = time windows (e.g. 'T-24h', 'T-12h', ..., 'Shutdown')
      values = deviation from baseline mean in σ units
    """
    if windows_hours is None:
        windows_hours = [24, 12, 6, 3, 1, 0]

    operating = df[df['phase'] == 'operating'] if 'phase' in df.columns else df
    vib_cols  = [c for c in operating.columns
                 if c in CHANNEL_META and CHANNEL_META[c]['type'] != 'speed']

    if not vib_cols:
        vib_cols = [c for c in operating.select_dtypes(include=[np.number]).columns]

    results = {}
    for h in windows_hours:
        t_window = shutdown_time - pd.Timedelta(hours=h)

        # Get readings within ±5 minutes of the window time
        window_data = operating[
            (operating.index >= t_window - pd.Timedelta(minutes=5)) &
            (operating.index <= t_window + pd.Timedelta(minutes=5))
        ]

        if len(window_data) == 0:
            # Fall back to nearest available reading
            idx = operating.index.get_indexer([t_window], method='nearest')[0]
            window_data = operating.iloc[[idx]]

        col_label = f"T-{h}h" if h > 0 else "Shutdown"
        results[col_label] = {}

        for col in vib_cols:
            if col not in baseline_stats:
                continue
            mu    = baseline_stats[col]['mean']
            sigma = baseline_stats[col]['std']
            val   = float(window_data[col].mean())
            deviation = (val - mu) / sigma
            results[col_label][col] = deviation

    evolution_df = pd.DataFrame(results)  # rows=channels, cols=time windows
    return evolution_df


def compute_dri(df: pd.DataFrame,
                baseline_stats: Dict,
                window_hours: int = 1) -> pd.Series:
    """
    Deterioration Rate Index — rolling mean of normalized deviation across all
    vibration channels. Shows acceleration of deterioration over time.

    DRI(t) = mean over all vib channels of (x(t) - mu) / sigma
    """
    operating = df[df['phase'] == 'operating'] if 'phase' in df.columns else df
    vib_cols  = [c for c in operating.columns
                 if c in CHANNEL_META and CHANNEL_META[c].get('type') == 'vibration'
                 and c in baseline_stats]

    if not vib_cols:
        return pd.Series(dtype=float)

    z_scores = pd.DataFrame(index=operating.index)
    for col in vib_cols:
        mu    = baseline_stats[col]['mean']
        sigma = baseline_stats[col]['std']
        z_scores[col] = (operating[col] - mu) / sigma

    dri = z_scores.mean(axis=1)
    window_pts = max(1, window_hours * 360)  # 10-sec sampling → 360 per hour
    dri_smooth = dri.rolling(window=window_pts, min_periods=1).mean()
    dri_smooth.name = 'DRI'
    return dri_smooth


def classify_fault_propagation(df: pd.DataFrame,
                                baseline_stats: Dict) -> List[Dict]:
    """
    Identify which channel first crossed its UCL — determines fault propagation sequence.
    Returns list of dicts sorted by first_exceedance_time.
    """
    operating = df[df['phase'] == 'operating'] if 'phase' in df.columns else df
    vib_cols  = [c for c in operating.columns
                 if c in CHANNEL_META and CHANNEL_META[c].get('type') == 'vibration'
                 and c in baseline_stats]

    results = []
    for col in vib_cols:
        ucl = baseline_stats[col]['ucl_3s']
        exceeded = operating[operating[col] > ucl]
        if len(exceeded) > 0:
            first_time = exceeded.index[0]
            meta = CHANNEL_META.get(col, {})
            results.append({
                'channel':    col,
                'label':      meta.get('label', col),
                'first_exceedance': first_time,
                'peak_value': float(operating[col].max()),
                'ucl':        ucl,
            })

    results.sort(key=lambda x: x['first_exceedance'])
    return results


def classify_behavior(series: pd.Series,
                       baseline_mean: float,
                       baseline_std: float) -> str:
    """
    Classify the anomaly behavior pattern of a channel.
    Returns: 'Gradual Drift' | 'Sudden Spike' | 'Oscillatory' | 'Sustained High' | 'Normal'
    """
    if len(series) < 10:
        return 'Insufficient Data'

    vals = series.dropna().values
    if len(vals) < 10:
        return 'Insufficient Data'

    z = (vals - baseline_mean) / (baseline_std + 1e-12)
    max_z      = float(np.max(np.abs(z)))
    mean_z     = float(np.mean(z[-len(z)//4:]))  # last quarter mean z-score
    slope      = float(np.polyfit(np.arange(len(z)), z, 1)[0])  # linear trend slope
    oscillation = float(np.std(np.diff(vals)))    # variation in differences

    if max_z < 1.5:
        return 'Normal'
    if slope > 0.0005 and mean_z > 1.0:
        return 'Gradual Drift'
    if oscillation > baseline_std * 0.5 and max_z > 3:
        return 'Oscillatory'
    if max_z > 5 and mean_z < 2:
        return 'Sudden Spike'
    if mean_z > 2:
        return 'Sustained High'
    return 'Anomalous'


def generate_nl_explanation(channel_contribs: List[Dict],
                             fault_sequence: List[Dict],
                             shutdown_time: pd.Timestamp,
                             first_alarm: Optional[pd.Timestamp]) -> str:
    """
    Generate a rule-based natural language explanation for the alert.
    """
    if not channel_contribs:
        return "Insufficient data to generate explanation."

    top = channel_contribs[:2]
    top_str = " and ".join(
        f"{c['label']} ({c['behavior']}, contributing {c['shap_pct']:.0f}%)"
        for c in top
    )

    lead_str = ""
    if first_alarm and shutdown_time:
        lead_hours = (shutdown_time - first_alarm).total_seconds() / 3600
        lead_str = f" The system raised an alert {lead_hours:.1f} hours before shutdown."

    seq_str = ""
    if len(fault_sequence) >= 2:
        seq_str = (
            f" Fault propagation sequence: {fault_sequence[0]['label']} "
            f"exceeded control limits first, followed by {fault_sequence[1]['label']}."
        )

    behavior_map = {
        'Gradual Drift':   'showing a progressive increasing trend',
        'Sudden Spike':    'exhibiting sudden high-amplitude spikes',
        'Oscillatory':     'displaying oscillatory behavior',
        'Sustained High':  'sustaining elevated levels above normal operating range',
        'Normal':          'within normal range',
    }

    detail_parts = []
    for c in channel_contribs[:3]:
        beh_desc = behavior_map.get(c['behavior'], 'showing abnormal behavior')
        detail_parts.append(
            f"{c['label']} was {beh_desc} "
            f"(peak: {c['peak_value']:.1f} {c['unit']}, "
            f"baseline: {c['baseline_mean']:.1f} {c['unit']})"
        )
    detail_str = ". ".join(detail_parts) + "." if detail_parts else ""

    explanation = (
        f"⚠️ Emergency shutdown triggered due to {top_str}.{lead_str}"
        f"{seq_str} {detail_str} "
        f"Recommend immediate inspection of Drive End bearing assembly and lubrication system."
    )
    return explanation


# ─────────────────────────────────────────────────────────────────────────────
# Full preprocessing pipeline — single call
# ─────────────────────────────────────────────────────────────────────────────

def run_ongc_pipeline(before_path: str, after_path: str) -> Dict:
    """
    Complete preprocessing pipeline for ONGC dashboard.

    Returns a dict containing everything the dashboard needs:
      df, shutdown_time, baseline_stats, score_series,
      ucl_violations, first_alarm, evolution_df, dri,
      fault_sequence, channel_meta
    """
    # 1. Load and merge
    df, shutdown_time = merge_before_after(before_path, after_path)

    # 2. Baseline stats
    baseline_stats = compute_baseline_stats(df, baseline_days=2.0)

    # 3. Anomaly scoring
    score_series, ucl_violations, if_model, scaler, vib_cols = compute_anomaly_scores(
        df, baseline_stats, train_frac=0.40
    )

    # 4. First alarm
    first_alarm = find_first_alarm(score_series, threshold_percentile=95.0, persistence=5)

    # 5. Failure evolution
    evolution_df = compute_failure_evolution(df, baseline_stats, shutdown_time)

    # 6. DRI
    dri = compute_dri(df, baseline_stats)

    # 7. Fault propagation sequence
    fault_sequence = classify_fault_propagation(df, baseline_stats)

    # 8. Channel contributions with behavior classification
    operating = df[df['phase'] == 'operating'] if 'phase' in df.columns else df
    channel_contribs = []
    total_deviation = 0.0

    for col in vib_cols:
        if col not in baseline_stats:
            continue
        stats  = baseline_stats[col]
        series = operating[col].dropna()
        beh    = classify_behavior(series, stats['mean'], stats['std'])
        dev    = max(0.0, float(series.max()) - stats['mean'])
        total_deviation += dev
        meta   = CHANNEL_META.get(col, {})
        channel_contribs.append({
            'channel':       col,
            'label':         meta.get('label', col),
            'short':         meta.get('short', col),
            'unit':          meta.get('unit', ''),
            'behavior':      beh,
            'peak_value':    float(series.max()),
            'baseline_mean': stats['mean'],
            'baseline_std':  stats['std'],
            'deviation_abs': dev,
            'shap_pct':      0.0,  # filled below
        })

    for c in channel_contribs:
        c['shap_pct'] = (c['deviation_abs'] / total_deviation * 100) if total_deviation > 0 else 0.0

    channel_contribs.sort(key=lambda x: x['deviation_abs'], reverse=True)

    # 9. Natural language explanation
    nl_explanation = generate_nl_explanation(
        channel_contribs, fault_sequence, shutdown_time, first_alarm
    )

    lead_time_hours = 0.0
    if first_alarm and shutdown_time:
        lead_time_hours = (shutdown_time - first_alarm).total_seconds() / 3600

    logger.info(
        f"Pipeline complete | "
        f"First alarm: {first_alarm} | "
        f"Lead time: {lead_time_hours:.1f}h | "
        f"Shutdown: {shutdown_time}"
    )

    return {
        'df':                df,
        'shutdown_time':     shutdown_time,
        'baseline_stats':    baseline_stats,
        'score_series':      score_series,
        'ucl_violations':    ucl_violations,
        'first_alarm':       first_alarm,
        'lead_time_hours':   lead_time_hours,
        'evolution_df':      evolution_df,
        'dri':               dri,
        'fault_sequence':    fault_sequence,
        'channel_contribs':  channel_contribs,
        'nl_explanation':    nl_explanation,
        'vib_cols':          vib_cols,
        'channel_meta':      CHANNEL_META,
        'baseline_stats':    baseline_stats,
        'iso_thresholds':    ISO_THRESHOLDS,
        'if_model':          if_model,
        'scaler':            scaler,
    }