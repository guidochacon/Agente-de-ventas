import React, { useState, useEffect } from 'react'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'

export default function Settings() {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ name: '', email: '', role: 'closer' })
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    const data = await api.getAgents().catch(() => [])
    setAgents(data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function create(e) {
    e.preventDefault()
    if (!form.name || !form.email) return setError('Nombre y email son requeridos')
    setCreating(true)
    setError('')
    try {
      await api.createAgent(form)
      setForm({ name: '', email: '', role: 'closer' })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>Agentes</h1>
        <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>Gestión del equipo comercial</div>
      </div>

      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        {/* Form */}
        <div style={{ ...styles.card, width: 320 }}>
          <div style={{ color: colors.text, fontWeight: 600, marginBottom: 16 }}>Nuevo Agente</div>
          <form onSubmit={create} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { key: 'name', label: 'Nombre completo', type: 'text' },
              { key: 'email', label: 'Email', type: 'email' },
            ].map(({ key, label, type }) => (
              <div key={key}>
                <label style={{ color: colors.muted, fontSize: 12, display: 'block', marginBottom: 6 }}>{label}</label>
                <input
                  type={type}
                  value={form[key]}
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  style={{
                    width: '100%', background: colors.surface2,
                    border: `1px solid ${colors.border}`, borderRadius: 8,
                    padding: '9px 12px', color: colors.text, fontSize: 14,
                    outline: 'none', boxSizing: 'border-box',
                  }}
                />
              </div>
            ))}
            <div>
              <label style={{ color: colors.muted, fontSize: 12, display: 'block', marginBottom: 6 }}>Rol</label>
              <select
                value={form.role}
                onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
                style={{
                  width: '100%', background: colors.surface2,
                  border: `1px solid ${colors.border}`, borderRadius: 8,
                  padding: '9px 12px', color: colors.text, fontSize: 14, outline: 'none',
                }}
              >
                <option value="closer">Closer</option>
                <option value="setter">Setter</option>
                <option value="agent">Agente</option>
              </select>
            </div>
            {error && <div style={{ color: colors.red, fontSize: 13 }}>{error}</div>}
            <button
              type="submit"
              disabled={creating}
              style={{ ...styles.btn, ...styles.btnPrimary, opacity: creating ? 0.7 : 1 }}
            >
              {creating ? 'Creando…' : 'Crear Agente'}
            </button>
          </form>
        </div>

        {/* List */}
        <div style={{ flex: 1, minWidth: 300 }}>
          <div style={{ ...styles.card, padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  {['Nombre', 'Email', 'Rol', 'Estado'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: colors.muted, fontWeight: 500, fontSize: 12 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={4} style={{ padding: 40, textAlign: 'center', color: colors.muted }}>Cargando…</td></tr>
                ) : agents.length === 0 ? (
                  <tr><td colSpan={4} style={{ padding: 40, textAlign: 'center', color: colors.muted }}>No hay agentes</td></tr>
                ) : agents.map(a => (
                  <tr key={a.id} style={{ borderBottom: `1px solid ${colors.border}22` }}>
                    <td style={{ padding: '10px 16px', color: colors.text, fontWeight: 500 }}>{a.name}</td>
                    <td style={{ padding: '10px 16px', color: colors.muted }}>{a.email}</td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        background: colors.accent + '22', color: colors.accent,
                        padding: '3px 10px', borderRadius: 20, fontSize: 12, textTransform: 'capitalize',
                      }}>{a.role}</span>
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        background: (a.is_active ? colors.green : colors.red) + '22',
                        color: a.is_active ? colors.green : colors.red,
                        padding: '3px 10px', borderRadius: 20, fontSize: 12,
                      }}>{a.is_active ? 'Activo' : 'Inactivo'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
