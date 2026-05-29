import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import KPICard from '../components/KPICard.jsx'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'

function fmtMoney(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function daysAgo(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

export default function Overview() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [range, setRange] = useState('30d')

  const rangeMap = {
    '7d': daysAgo(7), '14d': daysAgo(14), '30d': daysAgo(30),
    'qtd': new Date(new Date().getFullYear(), Math.floor(new Date().getMonth() / 3) * 3, 1).toISOString().slice(0, 10),
    'all': '2020-01-01',
  }

  useEffect(() => {
    setLoading(true)
    const from = rangeMap[range]
    const to = new Date().toISOString().slice(0, 10)
    api.getOverview(from, to)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [range])

  const t = data?.totals || {}

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>Dashboard</h1>
          <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>Resumen general del equipo</div>
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
          {/* KPI row */}
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
            <KPICard label="Revenue Total" value={fmtMoney(t.revenue)} />
            <KPICard label="Cash Collected" value={fmtMoney(t.cash_collected)} />
            <KPICard label="Deals Cerrados" value={t.closed_deals || 0} />
            <KPICard label="Demos Realizadas" value={t.demos_showed || 0} />
          </div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 32 }}>
            <KPICard label="Nuevos Leads" value={t.new_leads || 0} />
            <KPICard label="Total Llamadas" value={t.total_calls || 0} />
            <KPICard label="Lead → Demo" value={`${t.lead_to_demo_pct || 0}%`} color={t.lead_to_demo_pct >= 30 ? colors.green : colors.yellow} />
            <KPICard label="Oferta → Cierre" value={`${t.offer_to_close_pct || 0}%`} color={t.offer_to_close_pct >= 30 ? colors.green : colors.red} />
          </div>

          {/* Per-agent table */}
          {data?.per_agent?.length > 0 && (
            <div style={{ ...styles.card }}>
              <div style={{ color: colors.text, fontWeight: 600, fontSize: 15, marginBottom: 16 }}>Rendimiento por Agente</div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                    {['Agente', 'Rol', 'Llamadas', 'Demos', 'Deals', 'Revenue', 'Cierre %'].map(h => (
                      <th key={h} style={{ textAlign: 'left', color: colors.muted, fontWeight: 500, padding: '8px 12px' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.per_agent.map(a => (
                    <tr key={a.agent_id} style={{ borderBottom: `1px solid ${colors.border}` }}>
                      <td style={{ padding: '10px 12px', color: colors.text, fontWeight: 500 }}>{a.name}</td>
                      <td style={{ padding: '10px 12px', color: colors.muted, textTransform: 'capitalize' }}>{a.role}</td>
                      <td style={{ padding: '10px 12px', color: colors.text }}>{a.total_calls}</td>
                      <td style={{ padding: '10px 12px', color: colors.text }}>{a.demos_showed}</td>
                      <td style={{ padding: '10px 12px', color: colors.text }}>{a.closed_deals}</td>
                      <td style={{ padding: '10px 12px', color: colors.green }}>{fmtMoney(a.revenue)}</td>
                      <td style={{ padding: '10px 12px', color: colors.text }}>
                        {_safe_pct(a.closed_deals, a.offers_made)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function _safe_pct(num, den) {
  return den ? Math.round(num / den * 100) : 0
}
