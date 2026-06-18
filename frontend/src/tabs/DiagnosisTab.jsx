import { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, ReferenceLine, Cell, LabelList, ResponsiveContainer,
} from 'recharts'
import { Badge } from '../components/Badge.jsx'
import { InfoDot } from '../components/InfoDot.jsx'
import { C, CONF_COLOR } from '../theme.js'

function ContribChart({ contributions }) {
  // Recharts renders bottom-up; reverse so the strongest sits on top.
  const data = useMemo(
    () => [...contributions].reverse().map((c) => ({
      label: c.label, z: c.z, direction: c.direction, pct: c.pct,
    })),
    [contributions]
  )
  const height = Math.max(220, 42 * data.length)

  const renderLabel = (props) => {
    const { x, y, width, height: h, value, index } = props
    const c = data[index]
    const up = value >= 0
    const color = up ? C.crit : C.blue
    const tx = up ? x + width + 8 : x - 8
    return (
      <text
        x={tx} y={y + h / 2} dy={4} fill={color} fontSize={11} fontWeight={700}
        fontFamily="var(--mono)" textAnchor={up ? 'start' : 'end'}
      >
        {`${value >= 0 ? '+' : ''}${value.toFixed(1)}σ · ${c.pct.toFixed(0)}%`}
      </text>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        layout="vertical" data={data}
        margin={{ top: 8, right: 70, bottom: 24, left: 8 }}
      >
        <defs>
          <linearGradient id="barUp" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#991B1B" />
            <stop offset="100%" stopColor="#EF4444" />
          </linearGradient>
          <linearGradient id="barDown" x1="1" y1="0" x2="0" y2="0">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#1E40AF" />
          </linearGradient>
          <filter id="barGlowUp" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#EF4444" floodOpacity="0.4" />
          </filter>
          <filter id="barGlowDown" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#3B82F6" floodOpacity="0.4" />
          </filter>
        </defs>
        <XAxis
          type="number" domain={['dataMin', 'dataMax']}
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }}
          stroke={C.cardBrd}
          label={{ value: 'deviation from baseline (σ)', position: 'bottom',
            fill: C.muted, fontSize: 11, dy: 6 }}
        />
        <YAxis
          type="category" dataKey="label" width={150}
          tick={{ fontFamily: 'var(--mono)', fontSize: 11, fill: C.text }}
          stroke={C.cardBrd}
        />
        <ReferenceLine x={0} stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
        <Bar dataKey="z" isAnimationActive={false} radius={[2, 2, 2, 2]} barSize={18}>
          {data.map((d, i) => (
            <Cell
              key={i}
              fill={d.z >= 0 ? 'url(#barUp)' : 'url(#barDown)'}
              filter={d.z >= 0 ? 'url(#barGlowUp)' : 'url(#barGlowDown)'}
            />
          ))}
          <LabelList dataKey="z" content={renderLabel} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function SnapshotTable({ contributions }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Parameter</th>
          <th className="r">At alarm</th>
          <th className="r">Baseline</th>
          <th className="r">Deviation</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {contributions.map((c) => {
          const up = c.direction === 'up'
          const flat = c.direction === 'flat'
          const color = flat ? C.muted : up ? C.crit : C.blue
          const arrow = flat ? '—' : up ? '▲' : '▼'
          const hot = c.pct > 15
          const unit = c.unit ? ` ${c.unit}` : ''
          return (
            <tr
              key={c.col}
              style={hot ? { boxShadow: `inset 3px 0 0 ${color}` } : undefined}
            >
              <td>{c.label}</td>
              <td className="r mono" style={{ color: '#fff', fontWeight: 700 }}>
                {c.value.toFixed(2)}{unit}
              </td>
              <td className="r mono" style={{ color: C.muted }}>
                {c.baseline.toFixed(2)}{unit}
              </td>
              <td className="r mono" style={{ color }}>
                {c.z >= 0 ? '+' : ''}{c.z.toFixed(2)}σ
              </td>
              <td style={{ color }}>{arrow} {c.pct.toFixed(0)}%</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function ConfidenceReason({ cd, sig }) {
  const matched = cd.matchedLabels || []
  const ambiguous = cd.ambiguousLabels || []
  if (sig && cd.total > 0) {
    return (
      <span>
        <b>{cd.matched} of {cd.total}</b> signature parameter{cd.total === 1 ? '' : 's'} matched
        {matched.length ? <> ({matched.join(', ')})</> : null}.
        {ambiguous.length
          ? <> {ambiguous.join(', ')} pointed the right way but stayed below the signature
              threshold — hence not higher.</>
          : <> A 3-pattern match reads as high confidence; fewer patterns, lower.</>}
      </span>
    )
  }
  return (
    <span>
      No curated failure signature matched this deviation pattern. Confidence is{' '}
      <b>low</b> by default; the diagnosis falls back to the strongest contributors
      {matched.length ? <> ({matched.join(', ')})</> : null}.
    </span>
  )
}

export function DiagnosisTab({ diagnosis }) {
  if (!diagnosis) {
    return (
      <div className="empty-note">
        Select an alarm (top bar) to see which parameters drove it and the probable cause.
      </div>
    )
  }
  const confColor = CONF_COLOR[diagnosis.confidence] || C.muted
  const sevColor = diagnosis.alarm.severity === 'critical' ? C.crit : C.warn
  const cd = diagnosis.confidenceDetail

  const left = (
    <div className="panel-card">
      <div className="card-title">Root-cause diagnosis</div>
      <div className="diag-cause">{diagnosis.cause}</div>
      <div className="diag-badges">
        {diagnosis.signature ? <Badge color={C.accent} glow>{diagnosis.signature}</Badge> : null}
        <span className="conf-badge-wrap">
          <Badge color={confColor} glow>confidence: {diagnosis.confidence}</Badge>
          {cd && <InfoDot label="confidence explanation"><ConfidenceReason cd={cd} sig={diagnosis.signature} /></InfoDot>}
        </span>
        <Badge color={sevColor} glow>{diagnosis.alarm.severity}</Badge>
      </div>
      <ContribChart contributions={diagnosis.contributions} />
      <div className="diag-explain">{diagnosis.explanation}</div>
      <div className="diag-fix-title">Recommended action</div>
      <div className="diag-fix">{diagnosis.recommendation}</div>
    </div>
  )

  const right = (
    <div className="panel-card">
      <div className="card-title">Snapshot at the selected alarm</div>
      <SnapshotTable contributions={diagnosis.contributions} />
    </div>
  )

  return (
    <div className="row-flex">
      <div style={{ flex: 1.1, minWidth: 0 }}>{left}</div>
      <div style={{ flex: 1, minWidth: 0 }}>{right}</div>
    </div>
  )
}
