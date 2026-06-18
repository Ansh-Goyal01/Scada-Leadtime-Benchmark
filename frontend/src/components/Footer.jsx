// Footer — provenance strip: data coverage, source, version, build stamp.
// __BUILD_DATE__ / __APP_VERSION__ are injected by Vite at build time.

function coverageEnd(series) {
  const t = series?.time
  if (!t || !t.length) return null
  const last = t[t.length - 1]
  if (typeof last === 'number') return `cycle ${Math.round(last)}`
  return String(last).slice(0, 10)
}

export function Footer({ series }) {
  const end = coverageEnd(series)
  const src = series ? (series.isSimulated ? 'simulated fixture' : 'field data') : null
  const ver = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : 'dev'
  const built = typeof __BUILD_DATE__ !== 'undefined' ? __BUILD_DATE__ : ''

  return (
    <div className="app-footer">
      {series ? (
        <>
          <span>{series.dataset} · {src}</span>
          {end ? <><span className="sep">·</span><span>data through {end}</span></> : null}
          <span className="sep">·</span>
        </>
      ) : null}
      <span>console v{ver}</span>
      {built ? <><span className="sep">·</span><span>built {built}</span></> : null}
    </div>
  )
}
