// chartUtils.js — shared helpers for turning the API payload into Recharts data.

// Convert an ISO datetime / numeric cycle into a numeric X value (ms epoch or cycle).
export function toX(t) {
  if (typeof t === 'number') return t
  const ms = Date.parse(t)
  return Number.isNaN(ms) ? 0 : ms
}

// Build a numeric X domain [min, max] from the series time array.
export function xDomain(time) {
  if (!time || !time.length) return [0, 1]
  return [toX(time[0]), toX(time[time.length - 1])]
}

// Format an X tick back to a short label depending on time kind.
export function fmtX(timeKind) {
  return (v) => {
    if (timeKind !== 'datetime') return `c${Math.round(v)}`
    const d = new Date(v)
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(
      d.getUTCMinutes()
    )}`
  }
}

// Short label for a failure / onset time value. Cycle datasets (e.g. C-MAPSS)
// return numeric times, datetime datasets return ISO strings — guard both so we
// never call .slice() on a number (which throws and crashes the app).
export function fmtTimeShort(t) {
  if (t == null) return ''
  if (typeof t === 'number') return `cycle ${Math.round(t)}`
  return String(t).slice(0, 10)
}

export function fmtXFull(timeKind, v) {
  if (timeKind !== 'datetime') return `cycle ${Math.round(v)}`
  const d = new Date(v)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(
    d.getUTCHours()
  )}:${pad(d.getUTCMinutes())}`
}

// Per-parameter row data: [{x, y}] dropping nulls-as-gaps (kept as null for line breaks).
export function paramRows(series, col) {
  const { time, samples } = series
  const ys = samples[col] || []
  return time.map((t, i) => ({ x: toX(t), y: ys[i] }))
}

// Min / max of a parameter's finite values (for the 3-tick Y axis).
export function paramExtent(series, col) {
  const ys = series.samples[col] || []
  let lo = Infinity
  let hi = -Infinity
  for (const v of ys) {
    if (v == null) continue
    if (v < lo) lo = v
    if (v > hi) hi = v
  }
  if (!Number.isFinite(lo)) return [0, 1]
  if (lo === hi) return [lo - 1, hi + 1]
  return [lo, hi]
}

// Latest finite value + sigma deviation + percent change vs baseline.
export function latestStats(series, col) {
  const ys = series.samples[col] || []
  const base = series.baseline[col] || { mean: 0, std: 0 }
  let v = null
  for (let i = ys.length - 1; i >= 0; i--) {
    if (ys[i] != null) { v = ys[i]; break }
  }
  if (v == null) return { value: null, sigma: 0, pct: 0, dir: 'flat' }
  const sigma = base.std ? (v - base.mean) / base.std : 0
  const pct = base.mean ? (100 * (v - base.mean)) / Math.abs(base.mean) : 0
  const dir = sigma > 0.5 ? 'up' : sigma < -0.5 ? 'down' : 'flat'
  return { value: v, sigma, pct, dir }
}

// Alarm spans clipped to numeric X for ReferenceArea.
export function spanRanges(series) {
  return (series.alarmSpans || []).map((s) => ({ x1: toX(s.start), x2: toX(s.end) }))
}

export function failureRanges(series) {
  return (series.failureWindows || []).map((s) => ({
    x1: toX(s.start), x2: toX(s.end), point: s.point,
  }))
}
