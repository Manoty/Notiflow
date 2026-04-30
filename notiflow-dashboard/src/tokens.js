export const pill = (type, text) => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '2px 7px',
  borderRadius: 99,
  fontSize: 10,
  fontWeight: 500,
  whiteSpace: 'nowrap',
  ...PILL_STYLES[type],
})

const PILL_STYLES = {
  sent:    { background: 'rgba(34,197,94,.12)',  color: 'var(--grn)' },
  pending: { background: 'rgba(245,158,11,.12)', color: 'var(--amb)' },
  failed:  { background: 'rgba(239,68,68,.12)',  color: 'var(--red)' },
  read:    { background: 'var(--bg3)',            color: 'var(--t2)'  },
  email:   { background: 'rgba(59,130,246,.12)', color: 'var(--blu)' },
  sms:     { background: 'rgba(124,106,247,.14)',color: 'var(--acc)' },
  in_app:  { background: 'var(--bg3)',            color: 'var(--t2)'  },
  tixora:  { background: 'rgba(34,197,94,.10)',  color: 'var(--grn)' },
  scott:   { background: 'rgba(59,130,246,.10)', color: 'var(--blu)' },
}

export const fmtTime = iso => {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString([], {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

export const fmtDate = iso => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    + ' ' + fmtTime(iso)
}

export const timeAgo = iso => {
  if (!iso) return ''
  const s = Math.round((Date.now() - new Date(iso)) / 1000)
  if (s < 60)   return `${s}s ago`
  if (s < 3600) return `${Math.round(s / 60)}m ago`
  return `${Math.round(s / 3600)}h ago`
}

export const canRetry = n =>
  n.status === 'failed' && n.retry_count < n.max_retries