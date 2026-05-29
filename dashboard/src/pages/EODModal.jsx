import React, { useState, useEffect } from 'react'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'

const today = () => new Date().toISOString().slice(0, 10)

export default function EODModal({ role, agents, onClose }) {
  const [agentId, setAgentId] = useState(agents[0]?.id || '')
  const [form, setForm] = useState({
    energy_level: '',
    focus_level: '',
    health_level: '',
    tracker_completed: null,
    post_call_forms: null,
    biggest_win: '',
    biggest_challenge: '',
    tomorrow_plan: '',
    also_tracker: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const filteredAgents = agents.filter(a => a.role === role)

  useEffect(() => {
    if (filteredAgents.length) setAgentId(filteredAgents[0].id)
  }, [role])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  async function submit() {
    if (!agentId) return setError('Seleccioná un agente')
    setLoading(true)
    setError('')
    try {
      await api.submitEOD({
        agent_id: agentId,
        date: today(),
        role,
        energy_level: form.energy_level ? parseInt(form.energy_level) : null,
        focus_level: form.focus_level ? parseInt(form.focus_level) : null,
        health_level: form.health_level ? parseInt(form.health_level) : null,
        tracker_completed: form.tracker_completed === true,
        post_call_forms: form.post_call_forms === true,
        biggest_win: form.biggest_win || null,
        biggest_challenge: form.biggest_challenge || null,
        tomorrow_plan: form.tomorrow_plan || null,
      })
      onClose(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const agentName = filteredAgents.find(a => a.id === agentId)?.name || ''
  const roleLabel = role === 'closer' ? 'Closer' : 'Setter'

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }} onClick={e => e.target === e.currentTarget && onClose(false)}>
      <div style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: 16,
        width: 520,
        maxWidth: '95vw',
        maxHeight: '90vh',
        overflow: 'auto',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: `1px solid ${colors.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}>
          <div>
            <div style={{ color: colors.text, fontWeight: 700, fontSize: 18 }}>
              EOD {roleLabel} — {agentName}
            </div>
            <div style={{ color: colors.muted, fontSize: 13, marginTop: 2 }}>Reporte de Fin de Día</div>
          </div>
          <button onClick={() => onClose(false)} style={{
            background: 'none', border: 'none', color: colors.muted,
            fontSize: 20, cursor: 'pointer', lineHeight: 1,
          }}>✕</button>
        </div>

        <div style={{ padding: '20px 24px' }}>
          {/* Agent selector if multiple */}
          {filteredAgents.length > 1 && (
            <div style={{ marginBottom: 20 }}>
              <label style={{ ...styles.label, display: 'block', marginBottom: 8 }}>Agente</label>
              <select
                value={agentId}
                onChange={e => setAgentId(e.target.value)}
                style={selectStyle}
              >
                {filteredAgents.map(a => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* ESTADO GENERAL */}
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 16 }}>
            Estado General
          </div>

          {[
            { key: 'energy_level', label: 'Nivel de energía' },
            { key: 'focus_level', label: 'Nivel de enfoque' },
            { key: 'health_level', label: 'Nivel de salud hoy (comida, agua, ejercicio, sueño)' },
          ].map(({ key, label }) => (
            <div key={key} style={{ marginBottom: 16 }}>
              <label style={{ ...styles.label, display: 'block', marginBottom: 8 }}>{label}</label>
              <select
                value={form[key]}
                onChange={e => set(key, e.target.value)}
                style={selectStyle}
              >
                <option value="">— elegí —</option>
                {[1,2,3,4,5].map(n => (
                  <option key={n} value={n}>{n} — {['Muy bajo','Bajo','Medio','Alto','Muy alto'][n-1]}</option>
                ))}
              </select>
            </div>
          ))}

          {/* ACTIVIDADES DEL DÍA */}
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', margin: '24px 0 16px' }}>
            Actividades del Día
          </div>

          {[
            { key: 'tracker_completed', label: '¿Completaste el Tracker de Ventas?' },
            { key: 'post_call_forms', label: '¿Formularios Post-Llamadas completados?' },
          ].map(({ key, label }) => (
            <div key={key} style={{ marginBottom: 16 }}>
              <div style={{ color: colors.text, fontSize: 14, marginBottom: 10 }}>{label}</div>
              <div style={{ display: 'flex', gap: 12 }}>
                {[true, false].map(val => (
                  <button
                    key={String(val)}
                    onClick={() => set(key, val)}
                    style={{
                      flex: 1, padding: '12px', borderRadius: 8, cursor: 'pointer',
                      fontSize: 15, fontWeight: 500,
                      border: `2px solid ${form[key] === val ? (val ? colors.green : colors.red) : colors.border}`,
                      background: form[key] === val ? (val ? colors.green + '22' : colors.red + '22') : colors.surface2,
                      color: form[key] === val ? (val ? colors.green : colors.red) : colors.muted,
                      transition: 'all 0.15s',
                    }}
                  >
                    {val ? 'Sí' : 'No'}
                  </button>
                ))}
              </div>
            </div>
          ))}

          {/* Text fields */}
          {[
            { key: 'biggest_win', label: 'Mayor logro del día' },
            { key: 'biggest_challenge', label: 'Mayor desafío del día' },
            { key: 'tomorrow_plan', label: 'Plan para mañana' },
          ].map(({ key, label }) => (
            <div key={key} style={{ marginBottom: 16 }}>
              <label style={{ ...styles.label, display: 'block', marginBottom: 8 }}>{label}</label>
              <textarea
                value={form[key]}
                onChange={e => set(key, e.target.value)}
                rows={2}
                style={{
                  width: '100%', background: colors.surface2,
                  border: `1px solid ${colors.border}`, borderRadius: 8,
                  padding: '10px 12px', color: colors.text, fontSize: 14,
                  resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
                  outline: 'none',
                }}
              />
            </div>
          ))}

          {/* Also complete tracker checkbox */}
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', marginBottom: 24 }}>
            <input
              type="checkbox"
              checked={form.also_tracker}
              onChange={e => set('also_tracker', e.target.checked)}
              style={{ accentColor: colors.accent, width: 16, height: 16 }}
            />
            <span style={{ color: colors.text, fontSize: 14 }}>
              Completar esta misma información en el sales tracker
            </span>
          </label>

          {error && (
            <div style={{ color: colors.red, fontSize: 13, marginBottom: 12 }}>{error}</div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button
              onClick={() => onClose(false)}
              style={{ ...styles.btn, ...styles.btnGhost }}
            >
              Cancelar
            </button>
            <button
              onClick={submit}
              disabled={loading}
              style={{ ...styles.btn, ...styles.btnPrimary, opacity: loading ? 0.7 : 1 }}
            >
              {loading ? 'Enviando…' : 'Enviar EOD'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const selectStyle = {
  width: '100%',
  background: '#0d1117',
  border: '1px solid #30363d',
  borderRadius: 8,
  padding: '10px 14px',
  color: '#e6edf3',
  fontSize: 14,
  appearance: 'none',
  outline: 'none',
  cursor: 'pointer',
}
