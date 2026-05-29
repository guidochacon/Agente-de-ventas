export const colors = {
  bg:      '#0d1117',
  surface: '#161b22',
  surface2:'#21262d',
  border:  '#30363d',
  text:    '#e6edf3',
  muted:   '#8b949e',
  accent:  '#7c3aed',
  accentHover: '#6d28d9',
  green:   '#22c55e',
  red:     '#ef4444',
  yellow:  '#f59e0b',
  blue:    '#3b82f6',
}

export const styles = {
  card: {
    background: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: 12,
    padding: '20px 24px',
  },
  label: {
    fontSize: 12,
    fontWeight: 500,
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  value: {
    fontSize: 28,
    fontWeight: 700,
    color: colors.text,
    marginTop: 6,
  },
  btn: {
    padding: '8px 16px',
    borderRadius: 8,
    border: 'none',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500,
    transition: 'background 0.15s',
  },
  btnPrimary: {
    background: colors.accent,
    color: '#fff',
  },
  btnGhost: {
    background: 'transparent',
    color: colors.muted,
    border: `1px solid ${colors.border}`,
  },
}
