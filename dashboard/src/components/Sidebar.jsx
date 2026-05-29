import React from 'react'
import { NavLink } from 'react-router-dom'
import { colors } from '../theme.js'

const navItems = [
  { to: '/', label: 'Dashboard', exact: true },
  { to: '/daily', label: 'Daily' },
  { to: '/tracker', label: 'Sales Tracker' },
  { to: '/crm', label: 'CRM' },
  { to: '/projections', label: 'Projections' },
  { to: '/team', label: 'Team Performance' },
  { to: '/ads', label: 'Ads Breakdown' },
]

export default function Sidebar() {
  return (
    <aside style={{
      width: 220,
      background: colors.surface,
      borderRight: `1px solid ${colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: '24px 20px 20px', borderBottom: `1px solid ${colors.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: colors.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14, fontWeight: 700, color: '#fff',
          }}>SA</div>
          <div>
            <div style={{ color: colors.text, fontWeight: 600, fontSize: 14 }}>SA Horizon</div>
            <div style={{ color: colors.muted, fontSize: 11 }}>B2B Dashboard</div>
          </div>
        </div>
      </div>

      {/* General */}
      <nav style={{ padding: '16px 12px', flex: 1 }}>
        <div style={{ color: colors.muted, fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', padding: '0 8px 8px', textTransform: 'uppercase' }}>
          General
        </div>
        {navItems.map(({ to, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            style={({ isActive }) => ({
              display: 'block',
              padding: '9px 12px',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: isActive ? 600 : 400,
              color: isActive ? '#fff' : colors.muted,
              background: isActive ? colors.accent : 'transparent',
              textDecoration: 'none',
              marginBottom: 2,
              transition: 'all 0.15s',
            })}
          >
            {label}
          </NavLink>
        ))}

        <div style={{ color: colors.muted, fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', padding: '16px 8px 8px', textTransform: 'uppercase' }}>
          Configuración
        </div>
        <NavLink
          to="/settings"
          style={({ isActive }) => ({
            display: 'block',
            padding: '9px 12px',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: isActive ? 600 : 400,
            color: isActive ? '#fff' : colors.muted,
            background: isActive ? colors.accent : 'transparent',
            textDecoration: 'none',
          })}
        >
          Agentes
        </NavLink>
      </nav>
    </aside>
  )
}
