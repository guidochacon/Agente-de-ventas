import React, { useState, useEffect } from 'react'
import { colors, styles } from '../theme.js'
import { api } from '../api.js'

function fmtMoney(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 0 })
}

const SETTER_METRICS = [
  { key: 'new_leads', label: 'New Leads #', fmt: 'int' },
  { key: 'demos_booked', label: 'Demos Booked #', fmt: 'int' },
  { key: 'lead_to_demo', label: 'Demo Booking Rate %', fmt: 'pct' },
  { key: 'demos_showed', label: 'Demos Showed #', fmt: 'int' },
  { key: 'show_rate', label: 'Demo Show %', fmt: 'pct' },
]

const CLOSER_METRICS = [
  { key: 'offers_made', label: 'Offers Made #', fmt: 'int' },
  { key: 'closed_deals', label: 'Closed Deals #', fmt: 'int' },
  { key: 'offer_to_close', label: 'Offer to Close %', fmt: 'pct' },
  { key: 'revenue', label: 'Revenue', fmt: 'money' },
  { key: 'cash_collected', label: 'Cash Collected', fmt: 'money' },
]

function pct(num, den) { return den ? Math.round(num / den * 100) : 0 }

function getVal(totals, key) {
  if (key === 'lead_to_demo') return pct(totals.demos_booked, totals.new_leads)
  if (key === 'show_rate') return pct(totals.demos_showed, totals.demos_booked)
  if (key === 'offer_to_close') return pct(totals.closed_deals, totals.offers_made)
  return totals[key] || 0
}

function fmtDisplay(val, fmt) {
  if (fmt === 'money') return fmtMoney(val)
  if (fmt === 'pct') return val + '%'
  return val
}

export default function Projections() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [targets, setTargets] = useState({})

  useEffect(() => {
    // load from localStorage
    const saved = localStorage.getItem('dashboard_targets')
    if (saved) {
      try { setTargets(JSON.parse(saved)) } catch (e) {}
    }

    const from = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10)
    const to = new Date().toISOString().slice(0, 10)
    api.getOverview(from, to)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  function setTarget(key, val) {
    const next = { ...targets, [key]: parseFloat(val) || 0 }
    setTargets(next)
    localStorage.setItem('dashboard_targets', JSON.stringify(next))
  }

  const totals = data?.totals || {}

  function MetricsSection({ title, metrics, color }) {
    return (
      <div style={{ ...styles.card, flex: 1 }}>
        <div style={{ color, fontWeight: 700, fontSize: 15, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
          {title === 'SETTERS' ? '📞' : '💰'} {title}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: '0 16px', alignItems: 'center' }}>
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 600, padding: '0 0 8px' }}>MÉTRICA</div>
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 600, padding: '0 0 8px', textAlign: 'right' }}>ACTUAL</div>
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 600, padding: '0 0 8px' }}>TARGET</div>
          {metrics.map(m => {
            const actual = getVal(totals, m.key)
            const target = targets[m.key] || 0
            const isBelow = target > 0 && actual < target
            const isAbove = target > 0 && actual >= target
            return (
              <React.Fragment key={m.key}>
                <div style={{ color: colors.text, fontSize: 14, padding: '10px 0', borderTop: `1px solid ${colors.border}22` }}>
                  {m.label}
                </div>
                <div style={{
                  textAlign: 'right', padding: '10px 0', borderTop: `1px solid ${colors.border}22`,
                  fontWeight: 600, fontSize: 14,
                  color: isBelow ? colors.red : isAbove ? colors.green : colors.text,
                }}>
                  <span style={{
                    background: (isBelow ? colors.red : isAbove ? colors.green : 'transparent') + '22',
                    padding: '2px 8px', borderRadius: 6,
                  }}>
                    {fmtDisplay(actual, m.fmt)}
                  </span>
                </div>
                <div style={{ padding: '10px 0', borderTop: `1px solid ${colors.border}22` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input
                      type="number"
                      value={targets[m.key] || ''}
                      onChange={e => setTarget(m.key, e.target.value)}
                      placeholder="0"
                      style={{
                        width: 70, background: colors.surface2,
                        border: `1px solid ${colors.border}`,
                        borderRadius: 6, padding: '4px 8px',
                        color: colors.blue, fontSize: 13, textAlign: 'right',
                        outline: 'none', fontWeight: 600,
                      }}
                    />
                    {m.fmt === 'pct' && <span style={{ color: colors.muted, fontSize: 12 }}>%</span>}
                  </div>
                </div>
              </React.Fragment>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ color: colors.text, fontSize: 22, fontWeight: 700, margin: 0 }}>Projections</h1>
        <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>
          Actuales vs targets — MTD. Los targets se guardan en tu browser.
        </div>
      </div>

      {loading ? (
        <div style={{ color: colors.muted, textAlign: 'center', padding: 60 }}>Cargando…</div>
      ) : (
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          <MetricsSection title="SETTERS" metrics={SETTER_METRICS} color={colors.accent} />
          <MetricsSection title="CLOSERS" metrics={CLOSER_METRICS} color={colors.green} />
        </div>
      )}
    </div>
  )
}
