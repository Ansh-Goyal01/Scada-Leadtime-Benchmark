import { useMemo, useState } from 'react'
import { useConsoleData } from './hooks/useConsoleData.js'
import { Header } from './components/Header.jsx'
import { SystemStatusBar } from './components/SystemStatusBar.jsx'
import { ControlBar } from './components/ControlBar.jsx'
import { Tabs, TABS } from './components/Tabs.jsx'
import { Badge } from './components/Badge.jsx'
import { C } from './theme.js'
import { OverviewTab } from './tabs/OverviewTab.jsx'
import { ParameterTrendsTab } from './tabs/ParameterTrendsTab.jsx'
import { DiagnosisTab } from './tabs/DiagnosisTab.jsx'
import { RelationshipsTab } from './tabs/RelationshipsTab.jsx'
import { EvaluationTab } from './tabs/EvaluationTab.jsx'
import { ReportTab } from './tabs/ReportTab.jsx'
import { Footer } from './components/Footer.jsx'

const TAB_IDS = ['overview', 'trends', 'diagnosis', 'relationships', 'evaluation', 'report']

export default function App() {
  const data = useConsoleData()
  const initialTab = new URLSearchParams(window.location.search).get('tab')
  const [tab, setTab] = useState(
    TAB_IDS.includes(initialTab) ? initialTab : 'overview'
  )
  const {
    datasetNames, units, dataset, setDataset, unit, setUnit,
    percentile, setPercentile, alarm, setAlarm, selectedEvent,
    series, diagnosis, evaluation, evalLoading, loading, error,
  } = data

  const statusPill = useMemo(() => {
    if (selectedEvent) {
      return (
        <Badge color={C.crit} glow className="pulse-crit">ALARM ACTIVE</Badge>
      )
    }
    return <Badge color={C.ok} glow>MONITORING</Badge>
  }, [selectedEvent])

  const headerStatus = series
    ? `${series.unitLabel}  ·  ${series.nSamples.toLocaleString()} samples`
    : loading ? 'loading…' : error ? 'data error' : ''

  const sel = { dataset, unit, percentile, alarm }

  return (
    <div className="app-root">
      <Header statusText={headerStatus} seedTime={selectedEvent?.time} />
      <SystemStatusBar series={series} />

      {series?.isSimulated ? (
        <div className="sim-banner">
          <b>SIMULATED demo data. </b>
          Synthetic stand-in for {dataset}; drop the real file in <code>data/raw/</code> to use field data.
        </div>
      ) : null}

      <div className="body-wrap">
        <ControlBar
          datasetNames={datasetNames} dataset={dataset} onDataset={setDataset}
          units={units} unit={unit} onUnit={setUnit}
          events={series?.events || []} alarm={alarm} onAlarm={setAlarm}
          percentile={percentile} onPercentile={setPercentile}
          statusPill={statusPill}
        />

        <Tabs active={tab} onChange={setTab} />

        <div className="panels">
          {error ? (
            <div className="err-box">Could not load data: {error}</div>
          ) : loading && !series ? (
            <LoadingSkeleton />
          ) : (
            <div className="tab-panel" key={tab}>
              {tab === 'overview' && (
                <OverviewTab series={series} diagnosis={diagnosis} alarm={alarm} onSelectAlarm={setAlarm} />
              )}
              {tab === 'trends' && (
                <ParameterTrendsTab series={series} diagnosis={diagnosis} alarm={alarm} />
              )}
              {tab === 'diagnosis' && <DiagnosisTab diagnosis={diagnosis} />}
              {tab === 'relationships' && (
                <RelationshipsTab series={series} diagnosis={diagnosis} />
              )}
              {tab === 'evaluation' && (
                <EvaluationTab series={series} evaluation={evaluation} evalLoading={evalLoading} />
              )}
              {tab === 'report' && (
                <ReportTab series={series} diagnosis={diagnosis} sel={sel} />
              )}
            </div>
          )}
        </div>
        <Footer series={series} />
      </div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="tab-panel">
      <div className="kpi-row">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="skeleton-card" style={{ flex: 1, marginBottom: 0 }}>
            <div className="skeleton-line" style={{ width: '40%' }} />
            <div className="skeleton-line" style={{ width: '70%', height: 20 }} />
          </div>
        ))}
      </div>
      <div className="skeleton-card">
        <div className="skeleton-line" style={{ width: '30%' }} />
        <div className="skeleton-block" />
      </div>
    </div>
  )
}
