import { useEffect, useState } from 'react'

// Live clock (Fix 6.2). Starts from the selected event's wall-clock time when the
// data is historical (MetroPT timestamps are from 2020), otherwise real "now",
// and ticks every second.
function useLiveClock(seedISO) {
  const [now, setNow] = useState(() => (seedISO ? new Date(seedISO) : new Date()))
  useEffect(() => {
    if (seedISO) setNow(new Date(seedISO))
  }, [seedISO])
  useEffect(() => {
    const id = setInterval(() => setNow((t) => new Date(t.getTime() + 1000)), 1000)
    return () => clearInterval(id)
  }, [])
  const pad = (n) => String(n).padStart(2, '0')
  return (
    `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ` +
    `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())} UTC`
  )
}

export function Header({ statusText, seedTime }) {
  const clock = useLiveClock(seedTime)
  return (
    <div className="app-header">
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <span
          style={{
            color: 'var(--accent)', fontSize: 20, marginRight: 10,
            textShadow: '0 0 12px var(--accent)',
          }}
        >
          ◆
        </span>
        <span className="app-title">SCADA DIAGNOSTIC CONSOLE</span>
      </div>
      <div className="header-right">
        <span className="live-clock mono">{clock}</span>
        <div className="live-wrap">
          <span className="live-dot" />
          <span className="live-text">LIVE</span>
        </div>
        {statusText ? <span className="meta-pill">{statusText}</span> : null}
      </div>
    </div>
  )
}
