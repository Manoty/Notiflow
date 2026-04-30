export const fmtDate = (iso) => {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('en-KE', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).format(new Date(iso))
}

export const fmtTime = (iso) => {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('en-KE', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).format(new Date(iso))
}

export const channelColor = {
  email:  '#0ea5e9',
  sms:    '#a855f7',
  in_app: '#64748b',
}

export const statusColor = {
  sent:    '#22c55e',
  pending: '#f59e0b',
  failed:  '#ef4444',
  read:    '#94a3b8',
}

export const canRetry = (n) =>
  n.status === 'failed' && n.retry_count < n.max_retries