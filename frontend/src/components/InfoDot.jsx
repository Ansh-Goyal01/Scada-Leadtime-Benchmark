// InfoDot — a small "ⓘ" affordance with a hover/focus popover. Pure CSS-positioned,
// no portal; the popover is keyboard-focusable for accessibility.
export function InfoDot({ children, label = 'more info' }) {
  return (
    <span className="info-dot" tabIndex={0} role="button" aria-label={label}>
      <span className="info-glyph">i</span>
      <span className="info-pop" role="tooltip">{children}</span>
    </span>
  )
}
