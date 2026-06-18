import { useMemo, useState } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, ReferenceLine, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'
import { C, corrColor, PHASE_COLOR } from '../theme.js'

const CELL = 54

function Heatmap({ correlation }) {
  const [hover, setHover] = useState(null)
  if (!correlation || !correlation.matrix?.length) {
    return <div className="empty-note">Select an alarm to compute correlations.</div>
  }
  const { labels, matrix } = correlation
  const n = labels.length
  const short = (s) => (s.length > 16 ? s.slice(0, 15) + '…' : s)

  return (
    <div style={{ overflowX: 'auto' }}>
      <div className="heatmap">
        {/* column labels */}
        <div className="heat-collabels" style={{ marginLeft: 130 }}>
          {labels.map((l, i) => (
            <div key={i} className="heat-collabel" style={{ width: CELL + 2 }}>{short(l)}</div>
          ))}
        </div>
        {matrix.map((row, r) => (
          <div key={r} style={{ display: 'flex', alignItems: 'center' }}>
            <div className="heat-rowlabel" style={{ width: 130 }}>{short(labels[r])}</div>
            <div className="heat-grid" style={{ gridTemplateColumns: `repeat(${n}, ${CELL}px)`, display: 'grid', gap: 2 }}>
              {row.map((v, c) => (
                <div
                  key={c}
                  className="heat-cell"
                  style={{ width: CELL, height: CELL, background: corrColor(v) }}
                  onMouseEnter={() => setHover({ r, c, v })}
                  onMouseLeave={() => setHover(null)}
                  title={`${labels[r]} vs ${labels[c]}: r = ${v == null ? 'n/a' : v.toFixed(2)}`}
                >
                  {v == null ? '·' : v.toFixed(2)}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      {hover ? (
        <div className="rel-note" style={{ marginTop: 10 }}>
          {labels[hover.r]} vs {labels[hover.c]}:{' '}
          <span className="mono" style={{ color: C.text }}>
            r = {hover.v == null ? 'n/a' : hover.v.toFixed(2)}
          </span>
        </div>
      ) : null}
    </div>
  )
}

// least-squares regression endpoints over the scatter points
function regression(points) {
  const pts = points.filter((p) => p.x != null && p.y != null)
  const n = pts.length
  if (n < 2) return null
  let sx = 0, sy = 0, sxx = 0, sxy = 0
  for (const p of pts) { sx += p.x; sy += p.y; sxx += p.x * p.x; sxy += p.x * p.y }
  const denom = n * sxx - sx * sx
  if (Math.abs(denom) < 1e-12) return null
  const slope = (n * sxy - sx * sy) / denom
  const intercept = (sy - slope * sx) / n
  const xs = pts.map((p) => p.x)
  const x0 = Math.min(...xs)
  const x1 = Math.max(...xs)
  return [
    { x: x0, y: intercept + slope * x0 },
    { x: x1, y: intercept + slope * x1 },
  ]
}

function ScatterPlot({ scatter }) {
  const reg = useMemo(() => (scatter ? regression(scatter.points) : null), [scatter])
  if (!scatter || !scatter.points?.length) {
    return <div className="empty-note">Select an alarm to compare its two strongest signals.</div>
  }
  const byPhase = { before: [], at: [], after: [] }
  for (const p of scatter.points) (byPhase[p.phase] || byPhase.at).push(p)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ScatterChart margin={{ top: 12, right: 16, bottom: 36, left: 8 }}>
        <XAxis
          type="number" dataKey="x" name={scatter.xLabel}
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }} stroke={C.cardBrd}
          label={{ value: scatter.xLabel, position: 'bottom', fill: C.muted, fontSize: 11, dy: 4 }}
        />
        <YAxis
          type="number" dataKey="y" name={scatter.yLabel}
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }} stroke={C.cardBrd}
          label={{ value: scatter.yLabel, angle: -90, position: 'insideLeft', fill: C.muted, fontSize: 11 }}
        />
        <ZAxis range={[20, 20]} />
        {reg ? (
          <ReferenceLine
            segment={reg} stroke="#fff" strokeOpacity={0.4} strokeWidth={1} strokeDasharray="5 4"
            ifOverflow="extendDomain"
          />
        ) : null}
        {['before', 'at', 'after'].map((phase) => (
          <Scatter
            key={phase} data={byPhase[phase]} fill={PHASE_COLOR[phase]}
            fillOpacity={0.8} isAnimationActive={false}
          />
        ))}
        <Scatter
          data={[scatter.alarm]} fill={C.crit} shape="diamond" isAnimationActive={false}
        >
          <Cell />
        </Scatter>
        <Tooltip
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{
            background: '#0F1623', border: `1px solid ${C.cardBrd}`, borderRadius: 6,
            fontFamily: 'var(--mono)', fontSize: 11,
          }}
          formatter={(v) => Number(v).toFixed(2)}
        />
      </ScatterChart>
    </ResponsiveContainer>
  )
}

export function RelationshipsTab({ series, diagnosis }) {
  if (!series) return <div className="empty-note">No data.</div>

  return (
    <div className="row-flex">
      <div style={{ flex: 1.3, minWidth: 0 }}>
        <div className="panel-card">
          <div className="card-title">Correlation strength</div>
          <div className="rel-note">
            Deep red = move together (r→+1), deep blue = move opposite (r→−1), near-black = unrelated.
            Computed in a window around the selected alarm.
          </div>
          <Heatmap correlation={diagnosis?.correlation} />
        </div>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="panel-card">
          <div className="card-title">Two strongest signals</div>
          <div className="rel-note">
            before alarm → <span style={{ color: C.blue }}>blue</span> · at alarm →{' '}
            <span style={{ color: C.crit }}>red</span> · after → <span style={{ color: C.ok }}>green</span>
          </div>
          <ScatterPlot scatter={diagnosis?.scatter} />
        </div>
      </div>
    </div>
  )
}
