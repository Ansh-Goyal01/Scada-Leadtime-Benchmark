import { useState } from 'react'
import { reportPdfUrl } from '../api.js'
import { C } from '../theme.js'

const SEV_BG = { warning: ['#FEF3C7', '#92400E'], critical: ['#FEE2E2', '#991B1B'] }
const CONF_BG = {
  high: ['#D1FAE5', '#065F46'], moderate: ['#DBEAFE', '#1E40AF'], low: ['#FEF3C7', '#92400E'],
}

function Logo() {
  return (
    <svg width="120" height="40" viewBox="0 0 120 40" fill="none" aria-label="logo">
      <rect x="1" y="1" width="38" height="38" rx="7" fill="#0A0F1A" />
      <path d="M11 27 L17 15 L23 23 L29 11" stroke="#00D4FF" strokeWidth="2.4"
        fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="29" cy="11" r="2.6" fill="#00D4FF" />
      <text x="48" y="18" fontFamily="'Orbitron',monospace" fontSize="12" fontWeight="800" fill="#0A0F1A">SCADA</text>
      <text x="48" y="32" fontFamily="'JetBrains Mono',monospace" fontSize="8" fill="#64748B">DIAGNOSTIC</text>
    </svg>
  )
}

function ToolBtn({ children, onClick, href, filled, disabled }) {
  const cls = `tool-btn ${filled ? 'filled' : ''}`
  if (href) {
    return (
      <a className={cls} href={disabled ? undefined : href} download
         style={disabled ? { opacity: 0.4, pointerEvents: 'none' } : undefined}>
        {children}
      </a>
    )
  }
  return (
    <button className={cls} onClick={onClick} disabled={disabled}>{children}</button>
  )
}

export function ReportTab({ series, diagnosis, sel }) {
  const [copied, setCopied] = useState(false)

  if (!diagnosis) {
    return (
      <div className="empty-note">
        Select an alarm (top bar) to generate the diagnostic report.
      </div>
    )
  }

  const a = diagnosis.alarm
  const sevColors = SEV_BG[a.severity] || SEV_BG.warning
  const confColors = CONF_BG[diagnosis.confidence] || CONF_BG.low
  const genTime = a.timeLabel
  const pdfHref = reportPdfUrl(sel)

  const summaryText = [
    `SCADA Diagnostic Report — ${diagnosis.unitLabel}`,
    `Alarm: ${a.timeLabel} (${a.severity})`,
    `Probable cause: ${diagnosis.cause}`,
    `Fault class: ${diagnosis.signature || 'generic / unrecognized'}`,
    `Confidence: ${diagnosis.confidence}`,
    `Recommended action: ${diagnosis.recommendation}`,
  ].join('\n')

  const copySummary = async () => {
    try {
      await navigator.clipboard.writeText(summaryText)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      /* clipboard may be blocked; ignore */
    }
  }

  const top = diagnosis.contributions.slice(0, 6)

  return (
    <div className="panel-card">
      <div className="report-toolbar">
        <ToolBtn href={pdfHref} filled>↓ DOWNLOAD PDF</ToolBtn>
        <ToolBtn onClick={() => window.print()}>🖶 PRINT</ToolBtn>
        <ToolBtn onClick={copySummary}>⧉ {copied ? 'COPIED' : 'COPY SUMMARY'}</ToolBtn>
        <ToolBtn onClick={copySummary}>🔗 SHARE LINK</ToolBtn>
      </div>

      <div className="report-stage">
        <div className="report-page">
          <div className="rp-header">
            <div>
              <div className="rp-title">SCADA DIAGNOSTIC CONSOLE</div>
              <div className="rp-sub">Maintenance Report — {diagnosis.unitLabel}</div>
              <div className="rp-meta">
                {series?.dataset || 'MetroPT-3'} · Generated: {genTime}
                {diagnosis.isSimulated ? ' · SIMULATED DATA' : ''}
              </div>
            </div>
            <Logo />
          </div>

          <hr className="rp-rule" />

          <div className="rp-section">Alarm Summary</div>
          <table className="rp-table">
            <thead>
              <tr><th>Time</th><th>Parameter</th><th>Score</th><th>Severity</th></tr>
            </thead>
            <tbody>
              <tr>
                <td className="mono">{a.timeLabel}</td>
                <td>{a.topParamLabel}</td>
                <td className="mono">{a.score.toFixed(2)}</td>
                <td>
                  <span className="rp-badge"
                    style={{ background: sevColors[0], color: sevColors[1] }}>
                    {a.severity.toUpperCase()}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>

          <div className="rp-section">Root Cause Diagnosis</div>
          <div className="rp-cause">“{diagnosis.cause}”</div>
          <div className="rp-kv">
            Fault class: <b>{(diagnosis.signature || 'generic / unrecognized').toUpperCase()}</b>
          </div>
          <div className="rp-kv" style={{ marginTop: 6 }}>
            Confidence:{' '}
            <span className="rp-badge" style={{ background: confColors[0], color: confColors[1] }}>
              {diagnosis.confidence.toUpperCase()}
            </span>
            {'  ·  '}
            Severity:{' '}
            <span className="rp-badge" style={{ background: sevColors[0], color: sevColors[1] }}>
              {a.severity.toUpperCase()}
            </span>
          </div>

          <div className="rp-section">Parameter Snapshot (at alarm)</div>
          <table className="rp-table">
            <thead>
              <tr><th>Parameter</th><th>Value</th><th>Deviation</th></tr>
            </thead>
            <tbody>
              {top.map((c) => (
                <tr key={c.col}>
                  <td>{c.label}</td>
                  <td className="mono">{c.value.toFixed(2)}{c.unit ? ` ${c.unit}` : ''}</td>
                  <td className="mono" style={{ color: c.direction === 'up' ? '#991B1B' : c.direction === 'down' ? '#1E40AF' : '#6B7280' }}>
                    {c.z >= 0 ? '+' : ''}{c.z.toFixed(2)}σ · {c.pct.toFixed(0)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="rp-section">Recommended Action</div>
          <div className="rp-action">{diagnosis.recommendation}</div>

          <hr className="rp-rule" style={{ marginTop: 28 }} />
          <div className="rp-footer">
            Powered by SCADA Diagnostic Console · MetroPT-3 Dataset
          </div>
        </div>
      </div>
    </div>
  )
}
