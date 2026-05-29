import React, { useState, useEffect } from 'react'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'

const METRICS_CONFIG = [
  { key: 'new_leads', label: 'New Leads', fmt: 'int' },
  { key: 'total_calls', label: 'Total Calls', fmt: 'int' },
  { key: 'conversations', label: 'Conversations', fmt: 'int' },
  { key: 'demos_booked', label: 'Demos Booked', fmt: 'int' },
  { key: 'demos_showed', label: 'Demos Showed', fmt: 'int' },
  { key: 'offers_made', label: 'Offers Made', fmt: 'int' },
  { key: 'closed_deals', label: 'Closed Deals', fmt: 'int' },
  { key: 'revenue', label: 'Revenue', fmt: 'money' },
  { key: 'cash_collected', label: 'Cash Collected', fmt: 'money' },
]

function fmtMoney(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 0 })
}

export default function Daily() {
  const today = new Date().toISOString().slice(0, 10)
  const [date, setDate] = useState(today)
  const [agents, setAgents] = useState([])
  const [entries, setEntries] = useState({})
  const [saving, setSaving] = useState({})
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const [agentsData, trackerData] = await Promise.all([
      api.getAgents().catch(() => []),
      api.getSalesTracker(date, date).catch(() => ({ entries: [] })),
    ])
    setAgents(agentsData)
    const map = {}
    for (const e of trackerData.entries || []) {
      map[e.agent_id] = e
    }
    setEntries(map)
    setLoading(false)
  }

  useEffect(() => { load() }, [date])

  async function save(agentId, key, value) {
    const existing = entries[agentId] || {}
    const body = {
      agent_id: agentId, date,
      new_leads: existing.new_leads || 0,
      total_calls: existing.total_calls || 0,
      conversations: existing.conversations || 0,
      demos_booked: existing.demos_booked || 0,
      demos_showed: existing.demos_showed || 0,
      offers_made: existing.offers_made || 0,
      closed_deals: existing.closed_deals || 0,
      revenue: existing.revenue || 0,
      cash_collected: existing.cash_collected || 0,
      [key]: parseFloat(value) || 0,
    }
    setSaving(s => ({ ...s, [`${agentId}-${key}`]: true }))
    try {
      await api.upsertEntry(body)
      setEntries(prev => ({ ...prev, [agentId]: { ...prev[agentId], ...body } }))
    } finally {
      setSaving(s => { const n = { ...s }; delete n[`${agentId}-${key}`]; return n })
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>Daily</h1>
          <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>Entrada de datos del día</div>
        </div>
        <input
          type="date"
          value={date}
          onChange={e => setDate(e.target.value)}
          style={{
            background: colors.surface, border: `1px solid ${colors.border}`,
            borderRadius: 8, padding: '8px 14px', color: colors.text,
            fontSize: 14, outline: 'none',
          }}
        />
      </div>

      {loading ? (
        <div style={{ color: colors.muted, textAlign: 'center', padding: 60 }}>Cargando…</div>
      ) : (
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          {agents.map(agent => {
            const e = entries[agent.id] || {}
            return (
              <div key={agent.id} style={{ ...styles.card, flex: 1, minWidth: 280 }}>
                <div style={{ color: colors.text, fontWeight: 600, fontSize: 16, marginBottom: 4 }}>{agent.name}</div>
                <div style={{ color: colors.muted, fontSize: 12, textTransform: 'capitalize', marginBottom: 20 }}>{agent.role}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {METRICS_CONFIG.map(m => (
                    <div key={m.key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <label style={{ color: colors.muted, fontSize: 13 }}>{m.label}</label>
                      <input
                        type="number"
                        defaultValue={e[m.key] || 0}
                        onBlur={ev => save(agent.id, m.key, ev.target.value)}
                        style={{
                          width: 90, background: colors.surface2,
                          border: `1px solid ${saving[`${agent.id}-${m.key}`] ? colors.accent : colors.border}`,
                          borderRadius: 6, padding: '5px 10px',
                          color: colors.text, fontSize: 13, textAlign: 'right', outline: 'none',
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
