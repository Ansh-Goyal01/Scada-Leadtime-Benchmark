import { Badge } from './Badge.jsx'
import { statusFromSigma } from '../theme.js'

// Status pill resolved from absolute sigma deviation: NORMAL / WARNING / CRITICAL.
export function StatusPill({ absSigma, className, style }) {
  const { label, color } = statusFromSigma(absSigma)
  return (
    <Badge color={color} glow className={className} style={style}>
      {label}
    </Badge>
  )
}
