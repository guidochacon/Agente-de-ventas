import React from 'react'
import { colors, styles } from '../theme.js'

export default function KPICard({ label, value, sub, color }) {
  return (
    <div style={{ ...styles.card, flex: 1, minWidth: 160 }}>
      <div style={styles.label}>{label}</div>
      <div style={{ ...styles.value, color: color || colors.text }}>{value}</div>
      {sub && <div style={{ color: colors.muted, fontSize: 12, marginTop: 4 }}>{sub}</div>}
    </div>
  )
}
