// api.js — fetch wrappers for the Flask JSON API (proxied at /api in dev).

const qs = (params) =>
  Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&')

async function getJSON(url) {
  const res = await fetch(url)
  if (!res.ok) {
    let detail = ''
    try {
      detail = (await res.json()).error || ''
    } catch {
      /* ignore */
    }
    throw new Error(detail || `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const fetchDatasets = () => getJSON('/api/datasets')

export const fetchSeries = ({ dataset, unit, percentile }) =>
  getJSON(`/api/series?${qs({ dataset, unit, percentile })}`)

export const fetchDiagnosis = ({ dataset, unit, percentile, alarm }) =>
  getJSON(`/api/diagnosis?${qs({ dataset, unit, percentile, alarm })}`)

export const fetchEvaluation = ({ dataset, unit, percentile }) =>
  getJSON(`/api/evaluation?${qs({ dataset, unit, percentile })}`)

export const reportPdfUrl = ({ dataset, unit, percentile, alarm }) =>
  `/api/report.pdf?${qs({ dataset, unit, percentile, alarm })}`
