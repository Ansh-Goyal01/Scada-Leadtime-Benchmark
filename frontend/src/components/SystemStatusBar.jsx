import { C } from '../theme.js'

// Fix 6.1 — thin strip of 4 mini-indicators derived from the live data.
// Each: colored dot + mono label. States are computed from the series payload
// (compressor digital flag if present, pressure/temp deviation, alarm count).

function Indicator({ color, label, value }) {
  return (
    <div className="status-ind">
      <span className="dot" style={{ background: color, boxShadow: `0 0 7px ${color}` }} />
      <span>
        {label}: <b>{value}</b>
      </span>
    </div>
  )
}

function lastFinite(arr) {
  if (!arr) return null
  for (let i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return arr[i]
  return null
}

// deviation in sigma of the latest sample vs baseline, for a group of cols
function groupDeviation(series, predicate) {
  if (!series) return 0
  let maxAbs = 0
  for (const p of series.parameters) {
    if (!predicate(p)) continue
    const base = series.baseline[p.col]
    if (!base || !base.std) continue
    const v = lastFinite(series.samples[p.col])
    if (v == null) continue
    const z = Math.abs((v - base.mean) / base.std)
    if (z > maxAbs) maxAbs = z
  }
  return maxAbs
}

export function SystemStatusBar({ series }) {
  // Compressor: prefer a digital "on" flag if present, else infer from motor current.
  let compColor = C.muted
  let compVal = 'UNKNOWN'
  if (series) {
    const comp = series.parameters.find((p) =>
      /compress|motor|caudal|on\b/i.test(p.label) && p.group === 'Digital'
    )
    const current = series.parameters.find((p) => p.group === 'Current')
    if (comp) {
      const v = lastFinite(series.samples[comp.col])
      const on = v != null && v > 0.5
      compColor = on ? C.ok : C.muted
      compVal = on ? 'RUNNING' : 'IDLE'
    } else if (current) {
      const v = lastFinite(series.samples[current.col])
      const base = series.baseline[current.col]
      const on = v != null && base && v > base.mean * 0.3
      compColor = on ? C.ok : C.muted
      compVal = on ? 'RUNNING' : 'IDLE'
    }
  }

  const pDev = groupDeviation(series, (p) => p.group === 'Pressure')
  const pColor = pDev >= 3 ? C.crit : pDev >= 1.5 ? C.warn : C.ok
  const pVal = pDev >= 3 ? 'FAULT' : pDev >= 1.5 ? 'DEVIATING' : 'NOMINAL'

  const tDev = groupDeviation(series, (p) => p.group === 'Temperature')
  const tColor = tDev >= 3 ? C.crit : tDev >= 1.5 ? C.warn : C.ok
  const tVal = tDev >= 3 ? 'CRITICAL' : tDev >= 1.5 ? 'ELEVATED' : 'NOMINAL'

  const nAlarms = series?.events?.length ?? 0
  const aColor = nAlarms > 0 ? C.crit : C.ok
  const aVal = nAlarms > 0 ? `${nAlarms} ACTIVE` : 'NONE'

  return (
    <div className="status-bar">
      <Indicator color={compColor} label="COMPRESSOR" value={compVal} />
      <Indicator color={pColor} label="PRESSURE" value={pVal} />
      <Indicator color={tColor} label="TEMP" value={tVal} />
      <Indicator color={aColor} label="ALARMS" value={aVal} />
    </div>
  )
}
