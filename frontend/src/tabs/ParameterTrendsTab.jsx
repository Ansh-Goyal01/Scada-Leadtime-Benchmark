import { useMemo, useState } from 'react'
import {
  LineChart, Line, Area, AreaChart, XAxis, YAxis, ReferenceArea, ReferenceLine,
  ReferenceDot, Tooltip, ResponsiveContainer,
} from 'recharts'
import { LegendPills } from '../components/LegendPills.jsx'
import { StatusPill } from '../components/StatusPill.jsx'
import { C } from '../theme.js'
import {
  paramRows, paramExtent, latestStats, xDomain, spanRanges, failureRanges,
  toX, fmtX, fmtXFull,
} from '../chartUtils.js'

const ROW_H = 80

function DevBadge({ sigma, pct }) {
  const up = sigma >= 0
  const color = Math.abs(sigma) < 0.5 ? C.muted : up ? C.crit : C.blue
  const arrow = Math.abs(sigma) < 0.5 ? '—' : up ? '▲' : '▼'
  return (
    <span style={{ color, fontFamily: 'var(--mono)', fontWeight: 700 }}>
      {arrow}
      {Math.abs(sigma).toFixed(1)}σ&nbsp;&nbsp;
      {pct >= 0 ? '+' : ''}
      {pct.toFixed(0)}%
    </span>
  )
}

function MiniTooltip({ active, payload, timeKind, label }) {
  if (!active || !payload?.length) return null
  const v = payload[0]?.value
  if (v == null) return null
  return (
    <div
      style={{
        background: '#0F1623', border: `1px solid ${C.cardBrd || '#1E2D3D'}`,
        borderRadius: 6, padding: '6px 9px', fontFamily: 'var(--mono)', fontSize: 11,
        color: C.text,
      }}
    >
      <div style={{ color: C.muted }}>{fmtXFull(timeKind, label)}</div>
      <div style={{ color: '#fff', fontWeight: 700 }}>{Number(v).toFixed(2)}</div>
    </div>
  )
}

function SmallMultipleRow({ series, param, isLast, hovered, onHover, selAlarmX, contrib }) {
  const data = useMemo(() => paramRows(series, param.col), [series, param.col])
  const [lo, hi] = useMemo(() => paramExtent(series, param.col), [series, param.col])
  const spans = useMemo(() => spanRanges(series), [series])
  const fwins = useMemo(() => failureRanges(series), [series])
  const domain = useMemo(() => xDomain(series.time), [series.time])
  const isHover = hovered === param.col
  const yTicks = [lo, 0 >= lo && 0 <= hi ? 0 : (lo + hi) / 2, hi]
  const unit = param.unit ? ` ${param.unit}` : ''

  // Anchor the marker + status to the SELECTED alarm so this row agrees with the
  // Diagnosis tab. With no alarm selected, fall back to the latest reading.
  const alarmX = selAlarmX
  let alarmY = null
  if (alarmX != null) {
    let best = null
    let bestD = Infinity
    for (const d of data) {
      if (d.y == null) continue
      const dist = Math.abs(d.x - alarmX)
      if (dist < bestD) { bestD = dist; best = d }
    }
    alarmY = best?.y ?? null
  }

  // Status/deviation: prefer the backend's exact at-alarm contribution (matches
  // Diagnosis); else compute from the nearest at-alarm sample; else latest value.
  const stats = useMemo(() => {
    const base = series.baseline[param.col] || { mean: 0, std: 0 }
    const atAlarm = contrib ? contrib.value : (alarmX != null ? alarmY : null)
    if (atAlarm == null) return latestStats(series, param.col)
    const sigma = contrib ? contrib.z : (base.std ? (atAlarm - base.mean) / base.std : 0)
    const pct = base.mean ? (100 * (atAlarm - base.mean)) / Math.abs(base.mean) : 0
    return { value: atAlarm, sigma, pct, dir: sigma > 0.5 ? 'up' : sigma < -0.5 ? 'down' : 'flat' }
  }, [series, param.col, contrib, alarmX, alarmY])

  return (
    <div
      className="sm-row"
      onMouseEnter={() => onHover(param.col)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="sm-left">
        <div className="sm-name">
          <span className="pill-dot" style={{ background: param.color, width: 9, height: 9 }} />
          {param.label}
        </div>
        <div className="sm-val">
          {stats.value == null ? '—' : stats.value.toFixed(2)}
          <span style={{ color: C.muted, fontWeight: 400, fontSize: 12 }}>{unit}</span>
        </div>
        <div className="sm-meta">
          <DevBadge sigma={stats.sigma} pct={stats.pct} />
        </div>
      </div>
      <div className="sm-right">
        <div className="sm-status">
          <StatusPill absSigma={Math.abs(stats.sigma)} />
        </div>
        <ResponsiveContainer width="100%" height={ROW_H}>
          <LineChart data={data} margin={{ top: 10, right: 14, bottom: isLast ? 16 : 4, left: 0 }}>
            <defs>
              <linearGradient id={`fill-${param.col}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={param.color} stopOpacity={0.18} />
                <stop offset="100%" stopColor={param.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="x" type="number" domain={domain} scale="linear"
              hide={!isLast}
              tickFormatter={fmtX(series.timeKind)}
              tick={{ fontFamily: 'var(--mono)', fontSize: 9, fill: C.muted }}
              stroke={C.cardBrd || '#1E2D3D'}
            />
            <YAxis
              domain={[lo, hi]} ticks={yTicks}
              tickFormatter={(v) => (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(1))}
              tick={{ fontFamily: 'var(--mono)', fontSize: 8, fill: C.muted }}
              width={46} stroke={C.cardBrd || '#1E2D3D'}
            />
            {fwins.map((f, i) =>
              f.point ? null : (
                <ReferenceArea
                  key={`f${i}`} x1={f.x1} x2={f.x2} fill="rgba(239,68,68,0.18)" stroke="none"
                />
              )
            )}
            {spans.map((s, i) => (
              <ReferenceArea
                key={`s${i}`} x1={s.x1} x2={s.x2}
                fill="rgba(239,68,68,0.12)" stroke="rgba(239,68,68,0.4)" strokeDasharray="2 2"
              />
            ))}
            {0 >= lo && 0 <= hi ? (
              <ReferenceLine y={0} stroke={C.baseline} strokeDasharray="4 3" />
            ) : null}
            <Area
              type="monotone" dataKey="y" stroke="none"
              fill={`url(#fill-${param.col})`} isAnimationActive={false} connectNulls
            />
            <Line
              type="monotone" dataKey="y" stroke={param.color}
              strokeWidth={isHover ? 3 : 2} dot={false} isAnimationActive={false}
              connectNulls activeDot={{ r: 3, fill: param.color }}
            />
            {alarmX != null && alarmY != null ? (
              <ReferenceDot
                x={alarmX} y={alarmY} r={4} fill={C.crit}
                stroke="#fff" strokeWidth={1} shape="diamond"
              />
            ) : null}
            <Tooltip
              content={<MiniTooltip timeKind={series.timeKind} />}
              cursor={{ stroke: C.accent, strokeWidth: 1, strokeDasharray: '3 3' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function OverviewStrip({ series, active }) {
  const domain = useMemo(() => xDomain(series.time), [series.time])
  // Normalize each active param to its baseline sigma so they share one scale.
  const data = useMemo(() => {
    const { time, samples, baseline } = series
    return time.map((t, i) => {
      const row = { x: toX(t) }
      for (const col of active) {
        const base = baseline[col] || { mean: 0, std: 0 }
        const v = samples[col]?.[i]
        row[col] = v == null || !base.std ? null : (v - base.mean) / base.std
      }
      return row
    })
  }, [series, active])
  const paramByCol = Object.fromEntries(series.parameters.map((p) => [p.col, p]))

  return (
    <div className="overview-strip">
      <div className="strip-label">ALL CHANNELS OVERVIEW</div>
      <ResponsiveContainer width="100%" height={60}>
        <LineChart data={data} margin={{ top: 4, right: 14, bottom: 0, left: 0 }}>
          <XAxis dataKey="x" type="number" domain={domain} hide />
          <YAxis hide domain={['auto', 'auto']} />
          {active.map((col) => (
            <Line
              key={col} type="monotone" dataKey={col} stroke={paramByCol[col]?.color}
              strokeWidth={1} dot={false} isAnimationActive={false} connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ParameterTrendsTab({ series, diagnosis, alarm }) {
  const defaultActive = useMemo(
    () => (series?.healthParams?.length ? series.healthParams.slice(0, 6)
      : series?.parameters.slice(0, 6).map((p) => p.col)) || [],
    [series]
  )
  const [active, setActive] = useState(defaultActive)
  const [hovered, setHovered] = useState(null)

  // keep active in sync if dataset changes (param cols differ)
  const activeValid = useMemo(
    () => active.filter((c) => series?.parameters.some((p) => p.col === c)),
    [active, series]
  )
  const effActive = activeValid.length ? activeValid : defaultActive

  // Anchor status/deviation to the selected alarm (consistent with Diagnosis).
  const selectedEvent = series?.events?.find((e) => e.index === alarm) || null
  const selAlarmX = selectedEvent ? toX(selectedEvent.time) : null
  const contribByCol = useMemo(
    () => Object.fromEntries((diagnosis?.contributions || []).map((c) => [c.col, c])),
    [diagnosis]
  )

  if (!series) return <div className="empty-note">No data.</div>

  const toggle = (col) =>
    setActive((prev) => {
      const base = prev.length ? prev : defaultActive
      return base.includes(col) ? base.filter((c) => c !== col) : [...base, col]
    })

  const activeParams = series.parameters.filter((p) => effActive.includes(p.col))

  return (
    <div className="panel-card">
      <div className="card-title">Parameter trends — small multiples</div>
      <div className="rel-note" style={{ marginBottom: 8 }}>
        {selectedEvent
          ? <>Status &amp; deviation measured <b>at the selected alarm</b> ({selectedEvent.timeLabel}) — consistent with the Diagnosis tab.</>
          : <>No alarm selected — showing each parameter's <b>latest reading</b>. Select an alarm to anchor the snapshot.</>}
      </div>

      <OverviewStrip series={series} active={effActive} />

      <div className="sm-list">
        {activeParams.length === 0 ? (
          <div className="empty-note">Toggle one or more parameters below to plot them.</div>
        ) : (
          activeParams.map((p, i) => (
            <SmallMultipleRow
              key={p.col} series={series} param={p}
              isLast={i === activeParams.length - 1}
              hovered={hovered} onHover={setHovered}
              selAlarmX={selAlarmX} contrib={contribByCol[p.col]}
            />
          ))
        )}
      </div>

      <LegendPills parameters={series.parameters} active={effActive} onToggle={toggle} />
    </div>
  )
}
