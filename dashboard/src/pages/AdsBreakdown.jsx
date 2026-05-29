import React, { useState } from 'react'
import { colors, styles } from '../theme.js'

const INITIAL = [
  { channel: 'Meta Ads', spend: '', leads: '', cpl: '', ctr: '' },
  { channel: 'Google Ads', spend: '', leads: '', cpl: '', ctr: '' },
  { channel: 'LinkedIn Ads', spend: '', leads: '', cpl: '', ctr: '' },
  { channel: 'TikTok Ads', spend: '', leads: '', cpl: '', ctr: '' },
]

export default function AdsBreakdown() {
  const [rows, setRows] = useState(() => {
    try {
      const saved = localStorage.getItem('ads_breakdown')
      return saved ? JSON.parse(saved) : INITIAL
    } catch { return INITIAL }
  })

  function update(idx, key, val) {
    const next = rows.map((r, i) => i === idx ? { ...r, [key]: val } : r)
    setRows(next)
    localStorage.setItem('ads_breakdown', JSON.stringify(next))
  }

  const totalSpend = rows.reduce((s, r) => s + (parseFloat(r.spend) || 0), 0)
  const totalLeads = rows.reduce((s, r) => s + (parseInt(r.leads) || 0), 0)

  function fmtMoney(n) {
    return n ? '$' + Number(n).toLocaleString('es-AR', { minimumFractionDigits: 2 }) : '—'
  }

  const syncSheets = async () => {
    try {
      const r = await fetch('/api/dashboard/sync-sheets', { method: 'POST' })
      const data = await r.json()
      if (data.error) alert('Error: ' + data.error)
      else alert(data.message || 'Sincronizado')
    } catch (e) { alert('Error: ' + e.message) }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>Ads Breakdown</h1>
          <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>
            Desglose de inversión publicitaria — datos editables manualmente
          </div>
        </div>
        <button onClick={syncSheets} style={{ ...styles.btn, ...styles.btnGhost }}>
          ↻ Sync Google Sheets
        </button>
      </div>

      {/* Summary */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Total Adspend', value: fmtMoney(totalSpend) },
          { label: 'Total Leads', value: totalLeads },
          { label: 'CPL Promedio', value: totalLeads ? fmtMoney(totalSpend / totalLeads) : '—' },
        ].map(({ label, value }) => (
          <div key={label} style={{ ...styles.card, flex: 1 }}>
            <div style={{ color: colors.muted, fontSize: 12, fontWeight: 500, textTransform: 'uppercase' }}>{label}</div>
            <div style={{ color: colors.text, fontWeight: 700, fontSize: 26, marginTop: 6 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div style={{ ...styles.card, padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
              {['Canal', 'Adspend ($)', 'Leads #', 'CPL ($)', 'CTR %'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: colors.muted, fontWeight: 500, fontSize: 12 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} style={{ borderBottom: `1px solid ${colors.border}22` }}>
                <td style={{ padding: '8px 16px', color: colors.text, fontWeight: 500 }}>{row.channel}</td>
                {['spend', 'leads', 'cpl', 'ctr'].map(key => (
                  <td key={key} style={{ padding: '8px 16px' }}>
                    <input
                      type="number"
                      value={row[key]}
                      onChange={e => update(idx, key, e.target.value)}
                      placeholder="0"
                      style={{
                        background: colors.surface2, border: `1px solid ${colors.border}`,
                        borderRadius: 6, padding: '5px 10px', color: colors.text,
                        fontSize: 13, outline: 'none', width: 100, textAlign: 'right',
                      }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ color: colors.muted, fontSize: 12, marginTop: 12 }}>
        💡 Los datos se guardan en tu browser. Para importar desde Google Sheets, configurá GOOGLE_SERVICE_ACCOUNT_JSON y GOOGLE_SHEETS_ID en el backend.
      </div>
    </div>
  )
}
