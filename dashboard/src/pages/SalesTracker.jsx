import React, { useState, useEffect, useRef } from 'react'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'
import EODModal from './EODModal.jsx'

const METRICS = [
  { key: 'new_leads',       label: 'New Leads',             fmt: 'int' },
  { key: 'total_calls',     label: 'Total Calls',           fmt: 'int' },
  { key: 'conversations',   label: 'Conversations',         fmt: 'int' },
  { key: 'demos_booked',    label: 'Demos Booked',          fmt: 'int' },
  { key: 'lead_to_demo',    label: 'Lead to Demo %',        fmt: 'pct', computed: true },
  { key: 'demos_showed',    label: 'Demos Showed',          fmt: 'int' },
  { key: 'show_rate',       label: 'Show %',                fmt: 'pct', computed: true },
  { key: 'offers_made',     label: 'Offers Made',           fmt: 'int' },
  { key: 'offer_to_close',  label: 'Offer to Close %',      fmt: 'pct', computed: true },
  { key: 'closed_deals',    label: 'Closed Deals',          fmt: 'int' },
  { key: 'revenue',         label: 'Revenue',               fmt: 'money' },
  { key: 'cash_collected',  label: 'Cash Collected',        fmt: 'money' },
]

function fmtMoney(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 0 })
}
function pct(num, den) {
  return den ? Math.round(num / den * 100) : 0
}
function fmtVal(metric, entry) {
  if (!entry) return '—'
  if (metric.computed) {
    if (metric.key === 'lead_to_demo') return pct(entry.demos_booked, entry.new_leads) + '%'
    if (metric.key === 'show_rate') return pct(entry.demos_showed, entry.demos_booked) + '%'
    if (metric.key === 'offer_to_close') return pct(entry.closed_deals, entry.offers_made) + '%'
  }
  if (metric.fmt === 'money') return fmtMoney(entry[metric.key])
  return entry[metric.key] ?? 0
}

function getWeekDates(offset = 0) {
  const today = new Date()
  const monday = new Date(today)
  monday.setDate(today.getDate() - today.getDay() + 1 + offset * 7)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return d.toISOString().slice(0, 10)
  })
}

function rangeLabel(days) {
  const to = new Date().toISOString().slice(0, 10)
  const from = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10)
  return { from, to }
}

export default function SalesTracker() {
  const [agents, setAgents] = useState([])
  const [entries, setEntries] = useState([])
  const [range, setRange] = useState('7d')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState({})
  const [eodModal, setEodModal] = useState(null) // 'closer' | 'setter' | null
  const [editCell, setEditCell] = useState(null) // { agentId, date, key }
  const [editVal, setEditVal] = useState('')
  const debounceRef = useRef({})

  const rangeMap = {
    '7d': rangeLabel(7),
    '14d': rangeLabel(14),
    '30d': rangeLabel(30),
    'qtd': { from: new Date(new Date().getFullYear(), Math.floor(new Date().getMonth()/3)*3, 1).toISOString().slice(0,10), to: new Date().toISOString().slice(0,10) },
    'all': { from: '2020-01-01', to: new Date().toISOString().slice(0,10) },
  }

  async function load() {
    setLoading(true)
    const { from, to } = rangeMap[range]
    const [agentsData, trackerData] = await Promise.all([
      api.getAgents().catch(() => []),
      api.getSalesTracker(from, to).catch(() => ({ entries: [] })),
    ])
    setAgents(agentsData)
    setEntries(trackerData.entries || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [range])

  // Build date columns
  const { from, to } = rangeMap[range]
  const dates = []
  let cur = new Date(from)
  const end = new Date(to)
  while (cur <= end) {
    dates.push(cur.toISOString().slice(0, 10))
    cur.setDate(cur.getDate() + 1)
  }

  // Map entries by agent+date
  const entryMap = {}
  entries.forEach(e => {
    if (!entryMap[e.agent_id]) entryMap[e.agent_id] = {}
    entryMap[e.agent_id][e.date] = e
  })

  async function saveCell(agentId, date, key, value) {
    const existing = entryMap[agentId]?.[date] || {}
    const body = {
      agent_id: agentId,
      date,
      new_leads: existing.new_leads || 0,
      total_calls: existing.total_calls || 0,
      conversations: existing.conversations || 0,
      demos_booked: existing.demos_booked || 0,
      demos_showed: existing.demos_showed || 0,
      offers_made: existing.offers_made || 0,
      closed_deals: existing.closed_deals || 0,
      revenue: existing.revenue || 0,
      cash_collected: existing.cash_collected || 0,
      notes: existing.notes || null,
      [key]: parseFloat(value) || 0,
    }
    setSaving(s => ({ ...s, [`${agentId}-${date}-${key}`]: true }))
    try {
      await api.upsertEntry(body)
      await load()
    } finally {
      setSaving(s => { const n = { ...s }; delete n[`${agentId}-${date}-${key}`]; return n })
    }
  }

  function startEdit(agentId, date, key, currentVal) {
    if (METRICS.find(m => m.key === key)?.computed) return
    setEditCell({ agentId, date, key })
    setEditVal(String(currentVal ?? ''))
  }

  function commitEdit() {
    if (!editCell) return
    const { agentId, date, key } = editCell
    saveCell(agentId, date, key, editVal)
    setEditCell(null)
  }

  const fmtDate = (d) => {
    const dt = new Date(d + 'T00:00:00')
    return dt.toLocaleDateString('es-AR', { weekday: 'short', day: 'numeric', month: 'short' })
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>Sales Tracker</h1>
          <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>Tracker semanal de ventas del equipo</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {[['7d','Last 7d'],['14d','Last 14d'],['30d','Last 30d'],['qtd','QTD'],['all','All']].map(([key, label]) => (
            <button key={key} onClick={() => setRange(key)} style={{
              ...styles.btn,
              ...(range === key ? styles.btnPrimary : styles.btnGhost),
              padding: '6px 14px', fontSize: 13,
            }}>{label}</button>
          ))}
          <div style={{ width: 1, height: 28, background: colors.border, margin: '0 4px' }} />
          <button onClick={() => setEodModal('closer')} style={{
            ...styles.btn, background: colors.accent, color: '#fff', padding: '7px 16px',
          }}>EOD Closer</button>
          <button onClick={() => setEodModal('setter')} style={{
            ...styles.btn, background: colors.green, color: '#fff', padding: '7px 16px',
          }}>EOD Setter</button>
        </div>
      </div>

      {loading ? (
        <div style={{ color: colors.muted, textAlign: 'center', padding: 60 }}>Cargando…</div>
      ) : agents.length === 0 ? (
        <div style={{ ...styles.card, textAlign: 'center', padding: 40, color: colors.muted }}>
          No hay agentes configurados. Agregá agentes en la sección de Configuración.
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{
            width: '100%', borderCollapse: 'collapse', fontSize: 13,
            background: colors.surface, border: `1px solid ${colors.border}`,
            borderRadius: 12, overflow: 'hidden',
          }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                <th style={{ ...thStyle, width: 180 }}>Métrica</th>
                {dates.map(d => (
                  <th key={d} style={{ ...thStyle, minWidth: 110, textAlign: 'center' }}>
                    {fmtDate(d)}
                  </th>
                ))}
                <th style={{ ...thStyle, textAlign: 'center' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {agents.map(agent => {
                const agentEntries = entryMap[agent.id] || {}
                return (
                  <React.Fragment key={agent.id}>
                    {/* Agent header row */}
                    <tr style={{ background: colors.surface2 }}>
                      <td colSpan={dates.length + 2} style={{
                        padding: '8px 16px',
                        color: colors.accent, fontWeight: 600, fontSize: 13,
                        borderBottom: `1px solid ${colors.border}`,
                      }}>
                        {agent.name}
                        <span style={{ color: colors.muted, fontWeight: 400, marginLeft: 8, fontSize: 12 }}>
                          ({agent.role})
                        </span>
                      </td>
                    </tr>
                    {METRICS.map(metric => {
                      const totals = dates.reduce((acc, d) => {
                        const e = agentEntries[d]
                        if (!e || metric.computed) return acc
                        acc[metric.key] = (acc[metric.key] || 0) + (e[metric.key] || 0)
                        return acc
                      }, {})

                      return (
                        <tr key={metric.key} style={{ borderBottom: `1px solid ${colors.border}22` }}>
                          <td style={{ padding: '8px 16px', color: colors.muted, fontWeight: 500 }}>
                            {metric.label}
                          </td>
                          {dates.map(d => {
                            const e = agentEntries[d]
                            const isEditing = editCell?.agentId === agent.id && editCell?.date === d && editCell?.key === metric.key
                            const isSaving = saving[`${agent.id}-${d}-${metric.key}`]
                            const displayVal = fmtVal(metric, e)

                            return (
                              <td key={d} style={{ padding: '6px 8px', textAlign: 'center' }}>
                                {isEditing ? (
                                  <input
                                    type="number"
                                    value={editVal}
                                    autoFocus
                                    onChange={ev => setEditVal(ev.target.value)}
                                    onBlur={commitEdit}
                                    onKeyDown={ev => { if (ev.key === 'Enter') commitEdit(); if (ev.key === 'Escape') setEditCell(null) }}
                                    style={{
                                      width: 70, background: colors.surface2,
                                      border: `1px solid ${colors.accent}`,
                                      borderRadius: 6, padding: '4px 8px',
                                      color: colors.text, fontSize: 13, textAlign: 'center',
                                      outline: 'none',
                                    }}
                                  />
                                ) : (
                                  <span
                                    onClick={() => !metric.computed && startEdit(agent.id, d, metric.key, e?.[metric.key])}
                                    style={{
                                      display: 'inline-block',
                                      padding: '4px 8px', borderRadius: 6,
                                      cursor: metric.computed ? 'default' : 'pointer',
                                      color: displayVal === '—' ? colors.border : (metric.fmt === 'money' ? colors.green : colors.text),
                                      background: isSaving ? colors.accent + '33' : 'transparent',
                                      minWidth: 50,
                                      transition: 'background 0.1s',
                                    }}
                                    onMouseEnter={e => { if (!metric.computed) e.target.style.background = colors.surface2 }}
                                    onMouseLeave={e => { e.target.style.background = 'transparent' }}
                                  >
                                    {displayVal}
                                  </span>
                                )}
                              </td>
                            )
                          })}
                          {/* Total column */}
                          <td style={{ padding: '8px 12px', textAlign: 'center', color: metric.fmt === 'money' ? colors.green : colors.text, fontWeight: 600 }}>
                            {metric.computed ? '—' : (metric.fmt === 'money' ? fmtMoney(totals[metric.key] || 0) : (totals[metric.key] || 0))}
                          </td>
                        </tr>
                      )
                    })}
                  </React.Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* EOD Modal */}
      {eodModal && (
        <EODModal
          role={eodModal}
          agents={agents}
          onClose={(submitted) => {
            setEodModal(null)
            if (submitted) load()
          }}
        />
      )}
    </div>
  )
}

const thStyle = {
  padding: '12px 16px',
  textAlign: 'left',
  color: '#8b949e',
  fontWeight: 500,
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
}
