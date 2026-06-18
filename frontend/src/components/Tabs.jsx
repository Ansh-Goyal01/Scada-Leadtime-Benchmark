export const TABS = [
  ['overview', 'Overview'],
  ['trends', 'Parameter Trends'],
  ['diagnosis', 'Diagnosis'],
  ['relationships', 'Relationships'],
  ['evaluation', 'Evaluation'],
  ['report', 'Report'],
]

export function Tabs({ active, onChange }) {
  return (
    <div className="tabs-bar">
      {TABS.map(([val, label]) => (
        <button
          key={val}
          className={`tab ${active === val ? 'sel' : ''}`}
          onClick={() => onChange(val)}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
