import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'

function fmtMoney(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 0 })
}

function daysAgo(n) {
  return new Date(Date.now() - n * 86400000).toISOString().slice(0, 10)
}

export default function TeamPerformance() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [range, setRange] = useState('30d')

  const rangeMap = {
    '7d': daysAgo(7), '14d': daysAgo(14), '30d': daysAgo(30),
    'qtd': new Date(new Date().getFullYear(), Math.floor(new Date().getMonth()/3)*3, 1).toISOString().slice(0,10),
    'all': '2020-01-01',
  }

  useEffect(() => {
    setLoading(true)
    const from = rangeMap[range]
    const to = new Date().toISOString().slice(0, 10)
    api.getTeamPerformance(from, to)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [range])

  const agents = data?.agents || []
  const chartData = agents.map(a => ({ name: a.name.split(' ')[0], revenue: a.revenue, calls: a.total_calls }))

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>Team Performance</h1>
          <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>Rendimiento individual del equipo</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {[['7d','Last 7d'],['14d','Last 14d'],['30d','Last 30d'],['qtd','QTD'],['all','All']].map(([key, label]) => (
            <button key={key} onClick={() => setRange(key)} style={{
              ...styles.btn,
              ...(range === key ? styles.btnPrimary : styles.btnGhost),
              padding: '6px 14px', fontSize: 13,
            }}>{label}</button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ color: colors.muted, textAlign: 'center', padding: 60 }}>Cargando…</div>
      ) : (
        <>
          {/* Chart */}
          {chartData.length > 0 && (
            <div style={{ ...styles.card, marginBottom: 24 }}>
              <div style={{ color: colors.text, fontWeight: 600, marginBottom: 16 }}>Revenue por Agente</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="name" stroke={colors.muted} tick={{ fontSize: 12 }} />
                  <YAxis stroke={colors.muted} tick={{ fontSize: 12 }} tickFormatter={v => '$' + (v/1000).toFixed(0) + 'k'} />
                  <Tooltip
                    contentStyle={{ background: colors.surface2, border: `1px solid ${colors.border}`, borderRadius: 8 }}
                    formatter={(v, n) => [fmtMoney(v), n === 'revenue' ? 'Revenue' : 'Llamadas']}
                  />
                  <Bar dataKey="revenue" fill={colors.accent} radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Agent cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
            {agents.map(agent => (
              <div key={agent.agent_id} style={{ ...styles.card }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                  <div>
                    <div style={{ color: colors.text, fontWeight: 600, fontSize: 15 }}>{agent.name}</div>
                    <div style={{ color: colors.muted, fontSize: 12, textTransform: 'capitalize', marginTop: 2 }}>{agent.role}</div>
                  </div>
                  <div style={{
                    background: colors.accent + '22', color: colors.accent,
                    borderRadius: 20, padding: '3px 10px', fontSize: 12, fontWeight: 600,
                  }}>#{agent.rank}</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {[
                    { label: 'Revenue', value: fmtMoney(agent.revenue), color: colors.green },
                    { label: 'Cash Collected', value: fmtMoney(agent.cash_collected) },
                    { label: 'Llamadas', value: agent.total_calls },
                    { label: 'Deals', value: agent.closed_deals },
                    { label: 'Lead→Demo', value: agent.lead_to_demo_pct + '%' },
                    { label: 'Cierre %', value: agent.offer_to_close_pct + '%' },
                  ].map(({ label, value, color }) => (
                    <div key={label}>
                      <div style={{ color: colors.muted, fontSize: 11 }}>{label}</div>
                      <div style={{ color: color || colors.text, fontWeight: 600, fontSize: 16, marginTop: 2 }}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {agents.length === 0 && (
            <div style={{ ...styles.card, textAlign: 'center', padding: 40, color: colors.muted }}>
              No hay datos en el período seleccionado.
            </div>
          )}
        </>
      )}
    </div>
  )
}
