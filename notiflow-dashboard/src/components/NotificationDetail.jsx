import { useState } from 'react'
import { StatusBadge, ChannelBadge } from './Badge'
import { fmtDate, fmtTime, canRetry } from '../utils'
import { api } from '../api/client'

export function NotificationDetail({ notification: n, onUpdate }) {
  const [retrying, setRetrying] = useState(false)

  const handleRetry = async () => {
    setRetrying(true)
    try {
      await api.retryNotification(n.id)
      onUpdate()
    } catch (e) {
      alert(`Retry failed: ${e.message}`)
    } finally {
      setRetrying(false)
    }
  }

  return (
    <div style={{
      borderTop: '1px solid #f1f5f9',
      background: '#f8fafc',
      padding: '20px 24px',
      animation: 'slideIn 0.15s ease',
    }}>
      <style>{`@keyframes slideIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }`}</style>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

        {/* Left — metadata */}
        <div>
          <p style={sectionTitle}>details</p>

          {[
            ['id',        <code style={{ fontSize: 10 }}>{n.id}</code>],
            ['user',      n.user_id],
            ['app',       n.app_id],
            ['channel',   <ChannelBadge channel={n.channel} />],
            ['status',    <StatusBadge  status={n.status}  />],
            ['retries',   `${n.retry_count} / ${n.max_retries}`],
            ['created',   fmtDate(n.created_at)],
            ['updated',   fmtDate(n.updated_at)],
          ].map(([k, v]) => (
            <div key={k} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 10, color: '#94a3b8', marginBottom: 2 }}>{k}</div>
              <div style={{ fontSize: 13, color: '#1e293b' }}>{v}</div>
            </div>
          ))}

          {canRetry(n) && (
            <button
              onClick={handleRetry}
              disabled={retrying}
              style={{
                marginTop: 12, fontFamily: 'inherit',
                fontSize: 12, padding: '5px 12px',
                border: '1px solid #fca5a5', borderRadius: 8,
                background: 'transparent', color: '#ef4444',
                cursor: 'pointer',
              }}
            >
              {retrying ? 'retrying...' : '↻ retry now'}
            </button>
          )}
        </div>

        {/* Right — message + logs */}
        <div>
          <p style={sectionTitle}>message</p>
          <pre style={{
            background: '#fff', border: '1px solid #f1f5f9',
            borderRadius: 8, padding: '10px 12px',
            fontSize: 12, lineHeight: 1.6,
            color: '#475569', whiteSpace: 'pre-wrap',
            wordBreak: 'break-word', marginBottom: 16,
          }}>
            {n.message}
          </pre>

          <p style={sectionTitle}>
            delivery log ({n.logs?.length ?? 0} attempt{n.logs?.length !== 1 ? 's' : ''})
          </p>

          {!n.logs?.length
            ? <p style={{ fontSize: 12, color: '#94a3b8' }}>no attempts yet — queued</p>
            : n.logs.map(log => (
              <div key={log.id} style={{
                display: 'flex', gap: 10, alignItems: 'flex-start',
                padding: '6px 0', borderBottom: '1px solid #f1f5f9',
                fontSize: 12,
              }}>
                <span style={{
                  minWidth: 24, fontWeight: 600,
                  color: '#94a3b8', fontSize: 11,
                }}>
                  #{log.attempt_number}
                </span>
                <span style={{
                  minWidth: 54, fontSize: 11, fontWeight: 500,
                  color: log.status === 'success' ? '#22c55e' : '#ef4444',
                }}>
                  {log.status}
                </span>
                <span style={{ flex: 1, color: '#475569', lineHeight: 1.4 }}>
                  {log.response_data || log.error_message || '—'}
                </span>
                <span style={{ fontSize: 11, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                  {fmtTime(log.attempted_at)}
                </span>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  )
}

const sectionTitle = {
  fontSize: 10, textTransform: 'uppercase',
  letterSpacing: '0.07em', color: '#94a3b8',
  marginBottom: 10,
}