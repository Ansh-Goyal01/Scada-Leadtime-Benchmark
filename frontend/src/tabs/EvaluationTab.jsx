import { useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
  ResponsiveContainer, Legend,
} from 'recharts'
import { C } from '../theme.js'
import { fmtTimeShort } from '../chartUtils.js'

function pct(x) {
  return x == null ? '—' : `${(x * 100).toFixed(0)}%`
}

function fmtLead(value, unit) {
  if (value == null) return '—'
  if (unit === 'hours') {
    const d = value / 24
    return Math.abs(d) >= 1 ? `${d.toFixed(1)} d` : `${value.toFixed(0)} h`
  }
  return `${Math.round(value)} cyc`
}

function MetricTile({ label, value, sub, color }) {
  return (
    <div className="metric-tile">
      <div className="mt-label">{label}</div>
      <div className="mt-value" style={color ? { color } : undefined}>{value}</div>
      {sub ? <div className="mt-sub">{sub}</div> : null}
    </div>
  )
}

// ── Paper-faithful FAR-gated lead-time view (IMS / ONGC / XJTU / FEMTO) ──────────
// Mirrors the paper's ungameable metric: an alarm is a VALID early warning only if
// it fires after the degradation onset AND keeps the pre-onset false-alarm rate
// within budget. A latch-on detector floods the pre-onset window and is invalid.
function PaperEvaluation({ paper }) {
  const p = paper
  const valid = p.validAlarm
  const farKnown = p.farPreonsetPct != null
  const leadNorm = p.leadNorm != null ? `${(p.leadNorm * 100).toFixed(0)}%` : '—'

  // Raw lead in hours is misleading for synthetic-clock datasets; lead_norm
  // (fraction of the degradation window) is the clock-invariant figure.
  const note = p.lead?.clockNote

  return (
    <div>
      <div className="metric-row">
        <MetricTile
          label="Valid early warning"
          value={valid ? 'YES' : 'NO'}
          color={valid ? C.ok : C.crit}
          sub={valid ? 'FAR-gated, onset-anchored' : 'failed the false-alarm gate'}
        />
        <MetricTile
          label="Normalized lead"
          value={leadNorm}
          sub="fraction of degradation window (clock-invariant)"
        />
        <MetricTile
          label="Pre-onset FAR"
          value={farKnown ? `${p.farPreonsetPct.toFixed(1)}%` : 'n/a'}
          color={farKnown && p.farPreonsetPct > 10 ? C.crit : C.text}
          sub={farKnown ? `budget ${(p.farBudget * 100).toFixed(0)}%` : 'no pre-onset window'}
        />
        <MetricTile
          label="Lead time"
          value={p.leadTimeHours != null ? fmtLead(p.leadTimeHours, 'hours') : '—'}
          sub={note ? 'raw clock — see note' : 'onset → first alarm'}
        />
      </div>

      <div className="panel-card" style={{ marginTop: 12 }}>
        <div className="card-title">How this alarm scored</div>
        <table className="eval-matrix">
          <tbody>
            <tr><th>Detector</th><td>{p.detector}</td></tr>
            <tr><th>Degradation onset</th><td>{p.tOnset || '— (none detected)'}</td></tr>
            <tr><th>Failure / shutdown</th><td>{p.tFail}</td></tr>
            <tr>
              <th>Pre-onset false-alarm rate</th>
              <td style={{ color: !farKnown ? C.muted : p.farPreonsetPct > 10 ? C.crit : C.ok }}>
                {farKnown ? `${p.farPreonsetPct.toFixed(1)}% (budget ${(p.farBudget * 100).toFixed(0)}%)`
                  : 'no normal period before onset to measure against'}
              </td>
            </tr>
            <tr>
              <th>Verdict</th>
              <td style={{ color: valid ? C.ok : C.crit, fontWeight: 700 }}>
                {valid ? 'VALID early warning' : 'INVALID — alarm not credited'}
              </td>
            </tr>
          </tbody>
        </table>
        <div className="eval-caption">
          This is the paper's <b>ungameable</b> metric. An alarm counts only if it fires
          after the data-anchored degradation onset and the pre-onset false-alarm rate
          stays within budget — so a detector that simply latches “on” is scored invalid.
          {note ? <><br /><b>Clock note:</b> {note}</> : null}
          {!farKnown ? (
            <><br /><b>Weaker evidence:</b> onset lands near this run’s start, leaving no
            pre-onset window — this run passes on lead time alone, not a measured FAR.</>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function ConfusionMatrix({ det }) {
  return (
    <table className="eval-matrix">
      <thead>
        <tr><th></th><th>Caught</th><th>Missed</th></tr>
      </thead>
      <tbody>
        <tr>
          <th>Failures</th>
          <td style={{ background: 'rgba(16,185,129,0.10)' }}>
            <span className="mx-num" style={{ color: C.ok }}>{det.detectedFailures}</span>
            <span className="mx-tag">true positive</span>
          </td>
          <td style={{ background: det.missedFailures ? 'rgba(239,68,68,0.10)' : 'transparent' }}>
            <span className="mx-num" style={{ color: det.missedFailures ? C.crit : C.muted }}>
              {det.missedFailures}
            </span>
            <span className="mx-tag">false negative</span>
          </td>
        </tr>
        <tr>
          <th>Alarms</th>
          <td>
            <span className="mx-num" style={{ color: C.ok }}>{det.tp}</span>
            <span className="mx-tag">near a failure</span>
          </td>
          <td style={{ background: 'rgba(245,158,11,0.08)' }}>
            <span className="mx-num" style={{ color: C.warn }}>{det.fp}</span>
            <span className="mx-tag">false alarm</span>
          </td>
        </tr>
      </tbody>
    </table>
  )
}

function SweepChart({ sweep, currentPercentile }) {
  const data = useMemo(
    () => sweep.map((s) => ({
      p: s.percentile,
      alarms: s.nAlarms,
      recall: s.recall != null ? s.recall * 100 : null,
      precision: s.precision != null ? s.precision * 100 : null,
    })),
    [sweep]
  )
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 12, right: 16, bottom: 24, left: 8 }}>
        <CartesianGrid stroke={C.grid} strokeDasharray="2 4" />
        <XAxis
          dataKey="p" type="number" domain={['dataMin', 'dataMax']}
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }}
          stroke={C.cardBrd}
          label={{ value: 'alarm percentile', position: 'bottom', fill: C.muted, fontSize: 11, dy: 6 }}
        />
        <YAxis
          yAxisId="left" stroke={C.cardBrd}
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }}
          label={{ value: 'alarms', angle: -90, position: 'insideLeft', style: { fill: C.muted, fontSize: 11 } }}
        />
        <YAxis
          yAxisId="right" orientation="right" domain={[0, 100]} stroke={C.cardBrd}
          tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: C.muted }}
          label={{ value: '%', angle: 90, position: 'insideRight', style: { fill: C.muted, fontSize: 11 } }}
        />
        <ReferenceLine
          yAxisId="left" x={currentPercentile} stroke={C.accent} strokeDasharray="4 3"
          label={{ value: 'current', position: 'top', fill: C.accent, fontSize: 10, fontFamily: 'var(--mono)' }}
        />
        <Line yAxisId="left" type="monotone" dataKey="alarms" stroke={C.warn} strokeWidth={2}
          dot={{ r: 3 }} name="alarms" isAnimationActive={false} />
        <Line yAxisId="right" type="monotone" dataKey="recall" stroke={C.ok} strokeWidth={2}
          dot={{ r: 3 }} name="recall %" isAnimationActive={false} connectNulls />
        <Line yAxisId="right" type="monotone" dataKey="precision" stroke={C.blue} strokeWidth={2}
          dot={{ r: 3 }} name="precision %" isAnimationActive={false} connectNulls />
        <Legend wrapperStyle={{ fontFamily: 'var(--mono)', fontSize: 11 }} />
        <Tooltip
          contentStyle={{ background: '#0F1623', border: `1px solid ${C.cardBrd}`, borderRadius: 6,
            fontFamily: 'var(--mono)', fontSize: 12 }}
          labelFormatter={(v) => `percentile ${v}`}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function EvaluationTab({ series, evaluation, evalLoading }) {
  if (!series) return <div className="empty-note">No data.</div>

  const det = series.detection

  // Paper datasets (IMS/ONGC/XJTU/FEMTO) report the FAR-gated lead-time metric.
  if (det && det.metric === 'far_gated_lead_time') {
    if (!det.paper || !det.paper.hasGroundTruth) {
      return (
        <div className="panel-card">
          <div className="card-title">Detection quality</div>
          <div className="empty-note">
            No degradation onset could be detected for this run, so the FAR-gated
            lead-time metric is undefined.
          </div>
        </div>
      )
    }
    return <PaperEvaluation paper={det.paper} />
  }

  if (!det || !det.hasGroundTruth) {
    return (
      <div className="panel-card">
        <div className="card-title">Detection quality</div>
        <div className="empty-note">
          This dataset has no labeled ground-truth failures, so precision / recall
          cannot be computed. Detection metrics are available for datasets with
          reported failure windows (e.g. MetroPT-3).
        </div>
      </div>
    )
  }

  const leadUnitWord = det.leadUnit === 'hours' ? 'hours' : 'cycles'
  const horizonText = `${det.horizon} ${det.horizonUnit}`

  return (
    <div>
      <div className="metric-row">
        <MetricTile label="Recall" value={pct(det.recall)}
          sub={`${det.detectedFailures}/${det.nFailures} failures caught`} />
        <MetricTile label="Precision" value={pct(det.precision)}
          sub={`${det.tp}/${det.nAlarms} alarms near a failure`} />
        <MetricTile label="F1" value={det.f1 != null ? det.f1.toFixed(2) : '—'} sub="harmonic mean" />
        <MetricTile label="Median lead" value={fmtLead(det.medianLead, det.leadUnit)}
          sub={`early warning (${leadUnitWord})`} />
      </div>

      <div className="eval-grid">
        <div className="panel-card" style={{ flex: '0 0 auto' }}>
          <div className="card-title">Detection-quality matrix</div>
          <ConfusionMatrix det={det} />
          <div className="eval-caption">
            Horizon: an alarm credits a failure if it fires within <b>{horizonText}</b> before it.
            {' '}TN is undefined for episodic alarms (no discrete “non-events”), so only
            TP / FP / FN are shown.
          </div>
        </div>

        <div className="panel-card" style={{ flex: 1, minWidth: 320 }}>
          <div className="card-title">Per-failure lead time</div>
          <ul className="lead-list">
            {det.leadTimes.map((r, i) => (
              <li key={i}>
                <span style={{ color: r.detected ? C.text : C.crit }}>
                  {fmtTimeShort(r.failureStart) || `failure ${i + 1}`}
                </span>
                <span style={{ color: r.detected ? C.ok : C.crit, fontWeight: 700 }}>
                  {r.detected ? `+${fmtLead(r.lead, r.leadUnit)} early` : 'MISSED'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="panel-card" style={{ marginTop: 12 }}>
        <div className="card-title">Sensitivity sweep — detection vs. alarm percentile</div>
        {evalLoading && !evaluation ? (
          <div className="skeleton-block" />
        ) : evaluation?.sweep?.length ? (
          <>
            <SweepChart sweep={evaluation.sweep} currentPercentile={evaluation.currentPercentile} />
            <div className="eval-caption">
              Lower percentile → more alarms (earlier, noisier); higher → fewer, more
              specific. The cyan line marks the current sensitivity (p{series.percentile}).
            </div>
          </>
        ) : (
          <div className="empty-note">Sweep unavailable.</div>
        )}
      </div>
    </div>
  )
}
