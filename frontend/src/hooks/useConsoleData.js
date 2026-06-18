import { useEffect, useRef, useState, useCallback } from 'react'
import { fetchDatasets, fetchSeries, fetchDiagnosis, fetchEvaluation } from '../api.js'

// Centralized data layer: holds dataset/unit/percentile/alarm selection and the
// series + diagnosis payloads, refetching when selection changes.
export function useConsoleData() {
  const [datasets, setDatasets] = useState([])
  const [dataset, setDataset] = useState('MetroPT-3')
  const [unit, setUnit] = useState('APU')
  const [percentile, setPercentile] = useState(99)
  const [alarm, setAlarm] = useState(null)

  const [series, setSeries] = useState(null)
  const [diagnosis, setDiagnosis] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [evalLoading, setEvalLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reqId = useRef(0)
  const diagReqId = useRef(0)
  const evalReqId = useRef(0)

  // dataset list once
  useEffect(() => {
    fetchDatasets()
      .then((d) => setDatasets(d.datasets || []))
      .catch((e) => setError(e.message))
  }, [])

  // when dataset changes, reset unit to its first option
  useEffect(() => {
    const ds = datasets.find((d) => d.dataset === dataset)
    if (ds && ds.units?.length) {
      setUnit((u) => (ds.units.some((o) => o.value === u) ? u : ds.units[0].value))
    }
  }, [dataset, datasets])

  // clear the selected alarm whenever the dataset changes — an alarm index from
  // one machine is meaningless on another, and the series effect re-selects.
  useEffect(() => {
    setAlarm(null)
  }, [dataset])

  // True only when the current (dataset, unit) pair is mutually consistent with
  // the loaded dataset list. During a dataset switch there is a render where the
  // new dataset is still paired with the PREVIOUS dataset's unit; fetching that
  // pair 500s on the backend (e.g. XJTU-SY + "1st_test"). We must not fetch until
  // the unit-reset effect above has corrected the unit.
  const dsEntry = datasets.find((d) => d.dataset === dataset)
  const pairReady = !dsEntry || (dsEntry.units || []).some((o) => String(o.value) === String(unit))

  // fetch series when selection changes
  useEffect(() => {
    if (!pairReady) {
      setLoading(true)
      return
    }
    const id = ++reqId.current
    setLoading(true)
    setError(null)
    fetchSeries({ dataset, unit, percentile })
      .then((s) => {
        if (id !== reqId.current) return
        setSeries(s)
        // auto-select the first alarm if none chosen / stale
        setAlarm((a) => {
          const exists = s.events?.some((e) => e.index === a)
          return exists ? a : s.events?.[0]?.index ?? null
        })
        setLoading(false)
      })
      .catch((e) => {
        if (id !== reqId.current) return
        setError(e.message)
        setLoading(false)
      })
  }, [dataset, unit, percentile, pairReady])

  // fetch diagnosis when alarm (or selection) changes
  useEffect(() => {
    if (alarm == null || !pairReady) {
      setDiagnosis(null)
      return
    }
    const id = ++diagReqId.current
    fetchDiagnosis({ dataset, unit, percentile, alarm })
      .then((d) => {
        if (id !== diagReqId.current) return
        setDiagnosis(d.hasAlarm ? d : null)
      })
      .catch(() => {
        if (id !== diagReqId.current) return
        setDiagnosis(null)
      })
  }, [alarm, dataset, unit, percentile, pairReady])

  // evaluation sweep — refetch on dataset/unit/percentile change
  useEffect(() => {
    if (!pairReady) {
      setEvalLoading(true)
      return
    }
    const id = ++evalReqId.current
    setEvalLoading(true)
    fetchEvaluation({ dataset, unit, percentile })
      .then((e) => {
        if (id !== evalReqId.current) return
        setEvaluation(e)
        setEvalLoading(false)
      })
      .catch(() => {
        if (id !== evalReqId.current) return
        setEvaluation(null)
        setEvalLoading(false)
      })
  }, [dataset, unit, percentile, pairReady])

  const units = datasets.find((d) => d.dataset === dataset)?.units || []
  const datasetNames = datasets.map((d) => d.dataset)
  const selectedEvent = series?.events?.find((e) => e.index === alarm) || null

  const reset = useCallback(() => setAlarm(null), [])

  return {
    datasetNames, units,
    dataset, setDataset,
    unit, setUnit,
    percentile, setPercentile,
    alarm, setAlarm, selectedEvent,
    series, diagnosis, evaluation, evalLoading, loading, error, reset,
  }
}
