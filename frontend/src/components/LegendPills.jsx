// Toggle legend pills. Active = colored pill with glow dot; inactive = dim 40%.
export function LegendPills({ parameters, active, onToggle }) {
  return (
    <div className="legend-wrap">
      {parameters.map((p) => {
        const on = active.includes(p.col)
        return (
          <button
            key={p.col}
            className={`legend-pill ${on ? 'on' : ''}`}
            onClick={() => onToggle(p.col)}
            style={{ borderColor: on ? p.color : 'var(--card-brd)' }}
          >
            <span
              className="pill-dot"
              style={{
                backgroundColor: p.color,
                boxShadow: on ? `0 0 8px ${p.color}` : 'none',
              }}
            />
            <span>{p.label}</span>
          </button>
        )
      })}
    </div>
  )
}
