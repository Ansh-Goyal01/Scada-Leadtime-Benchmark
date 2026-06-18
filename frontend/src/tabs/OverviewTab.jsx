import { useMemo } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, ReferenceArea, ReferenceLine, ReferenceDot,
  Tooltip, ResponsiveContainer,
} from 'recharts'
import { Badge } from '../components/Badge.jsx'
import { InfoDot } from '../components/InfoDot.jsx'
import { C, SEV_COLOR } from '../theme.js'
import { toX, xDomain, fmtX, fmtXFull, fmtTimeShort, spanRanges, failureRanges } from '../chartUtils.js'

const KPI_ICONS = {
  machine: ['⚙', C.accent], source: ['⛁', '#A855F7'],
  alarms: ['⚠', C.crit], event: ['◆', C.warn],
}

function Kpi({ label, value, sub, kind }) {
  const [icon, color] = KPI_ICONS[kind]
  return (
    <div className="kpi-card" style={{ borderLeft: `4px solid ${color}` }}>
      <span className="kpi-icon" style={{ color }}>{icon}</span>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value count-up" key={String(value)}>{value}</div>
      <div className="kpi-sub">{sub}</div>
    </div>
  )
}

function HealthChart({ series, selectedX }) {
  const data = useMemo(
    () => series.health.time.map((t, i) => ({ x: toX(t), y: series.health.value[i] })),
    [series]
  )
  const domain = useMemo(() => xDomain(series.health.time), [series])
  const spans = useMemo(() => spanRanges(series), [series])
  const failures = useMemo(() => failureRanges(series), [series])
  const bw = series.baselineWindow
  const baseBand = bw ? { x1: toX(bw.start), x2: toX(bw.end) } : null
  const thr = series.health.threshold

  let selY = null
  if (selectedX != null) {
    let best = null
    let bestD = Infinity
    for (const d of data) {
      if (d.y == null) continue
      const dist = Math.abs(d.x - selectedX)
      if (dist < bestD) { bestD = dist; best = d }
    }
    selY = best?.y ?? null
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ top: 16, right: 18, bottom: 28, left: 8 }}>
        <defs>
          <linearGradient id="healthFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.accent} stopOpacity={0.3} />
            <stop offset="100%" stopColor={C.accent} stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="x" type="number" domain={domain} scale="linear"
          tickFormatter={fmtX(series.timeKind)}
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }}
          stroke={C.cardBrd}
        />
        <YAxis
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }}
          stroke={C.cardBrd} label={{
            value: 'deviation score (σ)', angle: -90, position: 'insideLeft',
            style: { fill: C.muted, fontSize: 11 },
          }}
        />
        {baseBand && (
          <ReferenceArea
            x1={baseBand.x1} x2={baseBand.x2}
            fill="rgba(16,185,129,0.10)" stroke="rgba(16,185,129,0.45)"
            strokeDasharray="2 3" strokeWidth={1}
            label={{ value: 'healthy baseline', position: 'insideTopLeft',
              fill: C.ok, fontSize: 9, fontFamily: 'var(--mono)', dy: 4, dx: 4 }}
          />
        )}
        {spans.map((s, i) => (
          <ReferenceArea
            key={i} x1={s.x1} x2={s.x2}
            fill="rgba(239,68,68,0.12)" stroke="rgba(239,68,68,0.5)"
            strokeDasharray="3 2" strokeWidth={1}
          />
        ))}
        {failures.map((f, i) => (
          <ReferenceLine
            key={`fw${i}`} x={f.x1} stroke={C.crit} strokeWidth={1.4}
            label={{ value: '⚡ failure', position: 'top', fill: C.crit,
              fontSize: 9, fontFamily: 'var(--mono)' }}
          />
        ))}
        <Area
          type="monotone" dataKey="y" stroke={C.accent} strokeWidth={2.2}
          fill="url(#healthFill)" isAnimationActive connectNulls
        />
        <ReferenceLine
          y={thr} stroke={C.crit} strokeWidth={1.6} strokeDasharray="6 4"
          label={{ value: 'threshold', position: 'left', fill: C.crit,
            fontSize: 10, fontFamily: 'var(--mono)' }}
        />
        {selX(selectedX, selY)}
        <Tooltip
          cursor={{ stroke: C.accent, strokeDasharray: '3 3' }}
          contentStyle={{
            background: '#0F1623', border: `1px solid ${C.cardBrd}`, borderRadius: 6,
            fontFamily: 'var(--mono)', fontSize: 12,
          }}
          labelFormatter={(v) => fmtXFull(series.timeKind, v)}
          formatter={(v) => [Number(v).toFixed(2), 'score']}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function selX(x, y) {
  if (x == null || y == null) return null
  return <ReferenceDot x={x} y={y} r={5} fill={C.accent} stroke="#fff" strokeWidth={1.5} />
}

function AlarmTable({ series, alarm, onSelect }) {
  const events = series.events || []
  if (!events.length) {
    return (
      <div className="empty-note">
        No alarms at this sensitivity — lower the percentile to detect earlier.
      </div>
    )
  }
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Time</th><th>Severity</th><th>Driven by</th><th className="r">Score</th>
        </tr>
      </thead>
      <tbody>
        {events.map((e) => {
          const sev = SEV_COLOR[e.severity] || C.muted
          const isSel = e.index === alarm
          return (
            <tr
              key={e.index}
              className={`alarm-row ${isSel ? 'sel' : ''}`}
              style={{ boxShadow: `inset 3px 0 0 ${sev}` }}
              onClick={() => onSelect(e.index)}
            >
              <td className="mono">{e.timeLabel}</td>
              <td><Badge color={sev}>{e.severity}</Badge></td>
              <td>{e.topParamLabel}</td>
              <td className="r">
                <span className="score-badge" style={{ color: sev }}>
                  ◈ {e.score.toFixed(2)}
                </span>
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function fmtLead(lead) {
  // lead.value is hours (datetime) or cycles (cycle data)
  if (lead.unit === 'hours') {
    const days = lead.value / 24
    if (Math.abs(days) >= 1) return `${days.toFixed(1)} days`
    return `${lead.value.toFixed(1)} h`
  }
  return `${Math.round(lead.value)} cycles`
}

function LeadTimeBanner({ lead }) {
  if (!lead) return null
  const late = lead.late
  const color = late ? C.warn : C.ok
  const fstart = fmtTimeShort(lead.failureStart)
  return (
    <div className="lead-banner" style={{ borderColor: color, color }}>
      <span className="lead-icon" style={{ color }}>{late ? '⚠' : '✓'}</span>
      {late ? (
        <span>
          This alarm fired <b>inside/after</b> the reported failure window
          {fstart ? ` (${fstart})` : ''} — no early warning.
        </span>
      ) : (
        <span>
          Detected <b>{fmtLead(lead)}</b> before the reported failure
          {fstart ? ` on ${fstart}` : ''}.
        </span>
      )}
    </div>
  )
}

export function OverviewTab({ series, diagnosis, alarm, onSelectAlarm }) {
  if (!series) return <div className="empty-note">No data.</div>
  const selectedEvent = series.events?.find((e) => e.index === alarm) || null
  const selectedX = selectedEvent ? toX(selectedEvent.time) : null
  const crit = series.events.filter((e) => e.severity === 'critical').length
  const tm = series.health.thresholdMeta
  const lead = diagnosis?.leadTime || null

  return (
    <div>
      <div className="kpi-row">
        <Kpi kind="machine" label="MACHINE" value={series.dataset}
          sub={series.unitLabel.slice(0, 30)} />
        <Kpi kind="source" label="DATA SOURCE" value={series.isSimulated ? 'SIMULATED' : 'REAL'}
          sub={series.isSimulated ? 'synthetic fixture' : 'field data'} />
        <Kpi kind="alarms" label="ACTIVE ALARMS" value={series.events.length}
          sub={`${crit} critical · p${series.percentile}`} />
        <Kpi kind="event" label="SELECTED EVENT"
          value={selectedEvent ? selectedEvent.timeLabel.split(' ')[1] || selectedEvent.timeLabel : 'none'}
          sub={selectedEvent ? `${selectedEvent.severity} · ${selectedEvent.topParamLabel}` : 'select an alarm'} />
      </div>

      {selectedEvent ? <LeadTimeBanner lead={lead} /> : null}

      <div className="panel-card">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          Machine health score &amp; alarms
          {tm && (
            <InfoDot label="threshold explanation">
              <b>Threshold</b> = {tm.percentile}th percentile of the health score over the
              first {Math.round((tm.baselineN / tm.totalN) * 100)}% (healthy) baseline window
              — {tm.baselineN.toLocaleString()} of {tm.totalN.toLocaleString()} samples.
              The green band marks that baseline; red lines mark reported failures.
            </InfoDot>
          )}
        </div>
        <HealthChart series={series} selectedX={selectedX} />
      </div>

      <div className="panel-card" style={{ marginTop: 12 }}>
        <div className="card-title">Detected alarms</div>
        <AlarmTable series={series} alarm={alarm} onSelect={onSelectAlarm} />
      </div>
    </div>
  )
}
