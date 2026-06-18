import { Badge } from './Badge.jsx'
import { C } from '../theme.js'

function Field({ label, width, children }) {
  return (
    <div className="ctrl-field" style={{ width }}>
      <label className="ctrl-label">{label}</label>
      {children}
    </div>
  )
}

export function ControlBar({
  datasetNames, dataset, onDataset,
  units, unit, onUnit,
  events, alarm, onAlarm,
  percentile, onPercentile,
  statusPill,
}) {
  return (
    <div className="control-bar">
      <Field label="DATASET" width="180px">
        <select className="ddark" value={dataset} onChange={(e) => onDataset(e.target.value)}>
          {datasetNames.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </Field>

      <Field label="MACHINE / UNIT" width="230px">
        <select className="ddark" value={unit} onChange={(e) => onUnit(e.target.value)}>
          {units.map((u) => (
            <option key={u.value} value={u.value}>{u.label}</option>
          ))}
        </select>
      </Field>

      <Field label="ALARM (CLICK TO DIAGNOSE)" width="360px">
        <select
          className={`ddark ${alarm == null ? 'placeholder' : ''}`}
          value={alarm == null ? '' : String(alarm)}
          onChange={(e) => onAlarm(e.target.value === '' ? null : Number(e.target.value))}
        >
          <option value="" style={{ color: C.place }}>No alarm selected</option>
          {events.map((e) => (
            <option key={e.index} value={e.index}>
              {(e.severity === 'critical' ? '● ' : '○ ') +
                `${e.timeLabel} — ${e.severity} — ${e.topParamLabel}`}
            </option>
          ))}
        </select>
      </Field>

      <Field label="SENSITIVITY (PERCENTILE)" width="240px">
        <div className="slider-field">
          <div className="slider-val">p{Number(percentile).toFixed(1)}</div>
          <input
            className="slider" type="range" min={90} max={99.5} step={0.5}
            value={percentile} onChange={(e) => onPercentile(Number(e.target.value))}
          />
          <div className="slider-marks"><span>90</span><span>95</span><span>99</span></div>
        </div>
      </Field>

      <div style={{ marginLeft: 'auto', alignSelf: 'center' }}>{statusPill}</div>
    </div>
  )
}
