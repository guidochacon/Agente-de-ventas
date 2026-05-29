import React, { useState, useEffect } from 'react'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'

const STATUS_COLORS = {
  new: colors.blue,
  contacted: colors.yellow,
  qualified: colors.accent,
  converted: colors.green,
}

export default function CRM() {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    api.getLeads()
      .then(data => setLeads(Array.isArray(data) ? data : data.leads || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  async function syncGHL() {
    setSyncing(true)
    try {
      const r = await api.syncGHL()
      alert(`GHL sincronizado: ${r.created} creados, ${r.updated} actualizados`)
      const data = await api.getLeads()
      setLeads(Array.isArray(data) ? data : data.leads || [])
    } catch (e) {
      alert('Error: ' + e.message)
    } finally {
      setSyncing(false)
    }
  }

  const filtered = leads.filter(l =>
    !search || [l.name, l.email, l.phone].some(v => v?.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>CRM</h1>
          <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>{leads.length} leads en total</div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar por nombre, email..."
            style={{
              background: colors.surface, border: `1px solid ${colors.border}`,
              borderRadius: 8, padding: '8px 14px', color: colors.text,
              fontSize: 14, outline: 'none', width: 240,
            }}
          />
          <button onClick={syncGHL} disabled={syncing} style={{ ...styles.btn, ...styles.btnGhost }}>
            {syncing ? 'Sincronizando…' : '↻ Sync GHL'}
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ color: colors.muted, textAlign: 'center', padding: 60 }}>Cargando…</div>
      ) : (
        <div style={{ ...styles.card, padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                {['Nombre', 'Email', 'Teléfono', 'Estado', 'Fuente', 'Fecha'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: colors.muted, fontWeight: 500, fontSize: 12 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(lead => (
                <tr key={lead.id} style={{ borderBottom: `1px solid ${colors.border}22` }}>
                  <td style={{ padding: '10px 16px', color: colors.text, fontWeight: 500 }}>{lead.name || '—'}</td>
                  <td style={{ padding: '10px 16px', color: colors.muted }}>{lead.email || '—'}</td>
                  <td style={{ padding: '10px 16px', color: colors.muted }}>{lead.phone || '—'}</td>
                  <td style={{ padding: '10px 16px' }}>
                    <span style={{
                      background: (STATUS_COLORS[lead.status] || colors.muted) + '22',
                      color: STATUS_COLORS[lead.status] || colors.muted,
                      padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 500,
                      textTransform: 'capitalize',
                    }}>{lead.status}</span>
                  </td>
                  <td style={{ padding: '10px 16px', color: colors.muted, fontSize: 12 }}>{lead.utm_source || lead.source_page || '—'}</td>
                  <td style={{ padding: '10px 16px', color: colors.muted, fontSize: 12 }}>
                    {lead.created_at ? new Date(lead.created_at).toLocaleDateString('es-AR') : '—'}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: 40, textAlign: 'center', color: colors.muted }}>
                    {search ? 'Sin resultados para la búsqueda' : 'No hay leads aún'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
