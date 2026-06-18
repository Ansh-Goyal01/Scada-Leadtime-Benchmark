// theme.js — single source of truth for design tokens.
//
// NOTE on colors: per the agreed plan, parameter trace colors come from the
// API's registry (console_data.py group palette), NOT a hardcoded table. Each
// parameter object from /api/series carries its own `color`. The tokens below
// are the structural/chrome colors (backgrounds, text, severity, status).

export const C = {
  bg: '#0A0F1A',
  panel: '#0F1623',
  panel2: '#0B111C',
  cardBrd: '#1E2D3D',
  ctrlBar: '#111827',
  ctrl: '#1A2332',
  ctrlBrd: '#2D4A6B',
  text: '#E2E8F0',
  muted: '#64748B',
  place: '#94A3B8',
  accent: '#00D4FF',
  accentSoft: '#67E8F9',
  ok: '#10B981',
  warn: '#F59E0B',
  crit: '#EF4444',
  blue: '#3B82F6',
  grid: '#1E293B',
  baseline: '#334155',
  rowHover: '#1A2535',
  rowSel: '#1E3045',
}

export const FONT = {
  mono: "'JetBrains Mono', ui-monospace, 'Cascadia Code', monospace",
  display: "'Orbitron', 'JetBrains Mono', sans-serif",
  body: "'Inter', 'Segoe UI', system-ui, sans-serif",
}

// Severity / confidence color maps mirror the Python side.
export const SEV_COLOR = { warning: C.warn, critical: C.crit }
export const CONF_COLOR = { high: C.ok, moderate: C.blue, low: C.warn }

// Status pill resolver from a numeric sigma deviation.
export function statusFromSigma(absSigma) {
  if (absSigma >= 3) return { label: 'CRITICAL', color: C.crit }
  if (absSigma >= 1.5) return { label: 'WARNING', color: C.warn }
  return { label: 'NORMAL', color: C.ok }
}

// Heatmap correlation color: deep red (+1) -> near black (0) -> deep blue (-1).
export function corrColor(r) {
  if (r == null || Number.isNaN(r)) return '#0F172A'
  const red = [127, 29, 29] // #7F1D1D
  const mid = [15, 23, 42] // #0F172A
  const blue = [30, 58, 138] // #1E3A8A
  const lerp = (a, b, t) => Math.round(a + (b - a) * t)
  let from, to, t
  if (r >= 0) {
    from = mid
    to = red
    t = Math.min(1, r)
  } else {
    from = mid
    to = blue
    t = Math.min(1, -r)
  }
  const c = [0, 1, 2].map((i) => lerp(from[i], to[i], t))
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`
}

// Phase colors for the scatter plot.
export const PHASE_COLOR = { before: C.blue, at: C.crit, after: C.ok }
