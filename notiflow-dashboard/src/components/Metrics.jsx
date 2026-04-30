export function Metrics({ data }) {
  const total   = data.length
  const sent    = data.filter(n => n.status === 'sent' || n.status === 'read').length
  const failed  = data.filter(n => n.status === 'failed').length
  const pending = data.filter(n => n.status === 'pending').length
  const retryable = data.filter(n => n.status === 'failed' && n.retry_count < n.max_retries).length
  const sr = total ? Math.round(sent / total * 100) : 0

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(4,1fr)',
      gap: 1, background: 'var(--ln)',
      borderBottom: '1px solid var(--ln)', flexShrink: 0,
    }}>
      {[
        { label: 'total',     value: total,   sub: 'notifications shown',   accent: null    },
        { label: 'delivered', value: sent,    sub: `${sr}% success rate`,   accent: 'grn'   },
        { label: 'failed',    value: failed,  sub: `${retryable} retryable`, accent: 'red'  },
        { label: 'pending',   value: pending, sub: 'in queue',               accent: 'amb'   },
      ].map(({ label, value, sub, accent }) => (
        <div key={label} style={{ background: 'var(--bg1)', padding: '14px 20px' }}>
          <div style={{
            fontSize: 10, color: 'var(--t2)',
            textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6,
          }}>
            {label}
          </div>
          <div style={{
            fontFamily: 'var(--sans)', fontSize: 24,
            fontWeight: 700, lineHeight: 1,
            color: accent ? `var(--${accent})` : 'var(--t0)',
          }}>
            {value}
          </div>
          <div style={{ fontSize: 10, color: 'var(--t2)', marginTop: 4 }}>{sub}</div>
        </div>
      ))}
    </div>
  )
}