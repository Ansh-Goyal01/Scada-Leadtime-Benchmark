export function Badge({ children, color, glow = false, className = '', style }) {
  return (
    <span
      className={`badge ${glow ? 'glow' : ''} ${className}`}
      style={{ color, borderColor: color, ...style }}
    >
      {children}
    </span>
  )
}
