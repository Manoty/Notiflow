export function StatCard({ label, value, accent }) {
  const accentMap = {
    success: '#22c55e',
    danger:  '#ef4444',
    warning: '#f59e0b',
    info:    '#0ea5e9',
    default: '#1e293b',
  }
  return (
    <div style={{
      background: '#f8fafc', borderRadius: 10,
      padding: '12px 16px', minWidth: 0,
    }}>
      <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase',
        letterSpacing: '0.06em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{
        fontFamily: "'Syne', sans-serif",
        fontSize: 26, fontWeight: 600,
        color: accentMap[accent] || accentMap.default,
        lineHeight: 1,
      }}>
        {value ?? '—'}
      </div>
    </div>
  )
}