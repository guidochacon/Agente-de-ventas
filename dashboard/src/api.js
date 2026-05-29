const BASE = '/api/dashboard'

async function req(path, opts = {}) {
  const url = path.startsWith('/api') ? path : BASE + path
  const r = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText)
    throw new Error(msg)
  }
  return r.json()
}

export const api = {
  // Agents
  getAgents: () => req('/agents'),
  createAgent: (body) => req('/agents', { method: 'POST', body: JSON.stringify(body) }),

  // Overview
  getOverview: (from, to) => req(`/overview?date_from=${from}&date_to=${to}`),

  // Sales Tracker
  getSalesTracker: (from, to, agentId) => {
    let url = `/sales-tracker?date_from=${from}&date_to=${to}`
    if (agentId) url += `&agent_id=${agentId}`
    return req(url)
  },
  upsertEntry: (body) => req('/sales-tracker', { method: 'POST', body: JSON.stringify(body) }),

  // Team Performance
  getTeamPerformance: (from, to) => req(`/team-performance?date_from=${from}&date_to=${to}`),

  // EOD
  submitEOD: (body) => req('/eod-report', { method: 'POST', body: JSON.stringify(body) }),
  getEODReports: (date, agentId) => {
    let url = `/eod-reports`
    const params = []
    if (date) params.push(`date=${date}`)
    if (agentId) params.push(`agent_id=${agentId}`)
    if (params.length) url += '?' + params.join('&')
    return req(url)
  },

  // Sync
  syncSheets: () => req('/sync-sheets', { method: 'POST' }),
  syncGHL: () => req('/sync-ghl', { method: 'POST' }),

  // Leads (existing endpoint)
  getLeads: (skip = 0, limit = 100) => req(`/api/leads?skip=${skip}&limit=${limit}`),
}
