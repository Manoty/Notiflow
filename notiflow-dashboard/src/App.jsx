import { useState } from 'react'
import { StatCard }             from './components/StatCard'
import { ChannelBadge, StatusBadge } from './components/Badge'
import { NotificationDetail }   from './components/NotificationDetail'
import { SendModal }            from './components/SendModal'
import { useNotifications, useQueueStats } from './api/useNotifications'
import { fmtTime }              from './utils'

export default function App() {
  const [filters, setFilters] = useState({
    app_id: '', channel: '', status: '', user_id: '',
  })
  const [selected,   setSelected]   = useState(null)
  const [showModal,  setShowModal]  = useState(false)

  const { data, count, loading, error, refetch } = useNotifications(filters)
  const { stats } = useQueueStats()

  const set = (k) => (e) => {
    setFilters(f => ({ ...f, [k]: e.target.value }))
    setSelected(null)
  }

  const allSent    = data.filter(n => n.status === 'sent' || n.status === 'read').length
  const allFailed  = data.filter(n => n.status === 'failed').length
  const allPending = data.filter(n => n.status === 'pending').length

  return (
    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 13,
      color: '#1e293b', minHeight: '100vh', background: '#fff' }}>

      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@500;600&display=swap" rel="stylesheet" />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', padding: '14px 24px',
        borderBottom: '1px solid #f1f5f9' }}>
        <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 20,
          fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%',
            background: '#22c55e', display: 'inline-block',
            animation: 'pulse 2s infinite' }} />
          Notiflow
          <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}`}</style>
        </div>
        <button
          onClick={() => setShowModal(true)}
          style={{ fontFamily: 'inherit', fontSize: 12, padding: '6px 16px',
            border: '1px solid #e2e8f0', borderRadius: 8,
            background: '#1e293b', color: '#fff', cursor: 'pointer' }}>
          + send notification
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 12, padding: '16px 24px', borderBottom: '1px solid #f1f5f9' }}>
        <StatCard label="total shown"  value={count}      />
        <StatCard label="delivered"    value={allSent}    accent="success" />
        <StatCard label="failed"       value={allFailed}  accent="danger"  />
        <StatCard label="queued"       value={stats.queued} accent="warning" />
      </div>

      {error && (
        <div style={{ background: '#fee2e2', color: '#b91c1c',
          fontSize: 12, padding: '8px 24px', borderBottom: '1px solid #fca5a5' }}>
          API error: {error}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 24px', borderBottom: '1px solid #f1f5f9', flexWrap: 'wrap' }}>

        {[
          ['app',     'app_id',  [['','all'],['tixora','tixora'],['scott','scott']]],
          ['channel', 'channel', [['','all'],['email','email'],['sms','sms'],['in_app','in_app']]],
          ['status',  'status',  [['','all'],['sent','sent'],['pending','pending'],['failed','failed'],['read','read']]],
        ].map(([label, key, opts]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>{label}</span>
            <select value={filters[key]} onChange={set(key)}
              style={{ fontFamily: 'inherit', fontSize: 12, padding: '4px 8px',
                border: '1px solid #e2e8f0', borderRadius: 6,
                background: '#f8fafc', color: '#1e293b', cursor: 'pointer' }}>
              {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
        ))}

        <input
          placeholder="search user_id..."
          value={filters.user_id}
          onChange={set('user_id')}
          style={{ fontFamily: 'inherit', fontSize: 12, padding: '4px 10px',
            border: '1px solid #e2e8f0', borderRadius: 6,
            background: '#f8fafc', color: '#1e293b', width: 160 }}
        />

        <button onClick={refetch} disabled={loading}
          style={{ marginLeft: 'auto', fontFamily: 'inherit', fontSize: 12,
            padding: '5px 14px', border: '1px solid #e2e8f0', borderRadius: 6,
            background: 'transparent', color: '#1e293b', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ display: 'inline-block',
            animation: loading ? 'spin 0.8s linear infinite' : 'none' }}>↻</span>
          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          {loading ? 'loading...' : 'refresh'}
        </button>
      </div>

      {/* Table header */}
      <div style={{ ...rowStyle, background: '#f8fafc', cursor: 'default',
        fontSize: 10, color: '#94a3b8', textTransform: 'uppercase',
        letterSpacing: '0.07em', paddingTop: 6, paddingBottom: 6 }}>
        <span>time</span>
        <span>app</span>
        <span>channel</span>
        <span>title</span>
        <span>user</span>
        <span>status</span>
        <span>retries</span>
      </div>

      {/* Rows */}
      <div style={{ overflowY: 'auto', maxHeight: '50vh' }}>
        {data.length === 0 && !loading && (
          <div style={{ textAlign: 'center', padding: '40px 24px',
            color: '#94a3b8', fontSize: 12 }}>
            no notifications match the current filters
          </div>
        )}

        {data.map(n => (
          <div key={n.id}>
            <div
              onClick={() => setSelected(selected?.id === n.id ? null : n)}
              style={{
                ...rowStyle,
                cursor: 'pointer', fontSize: 12,
                background: selected?.id === n.id ? '#eff6ff' : '#fff',
                borderBottom: '1px solid #f8fafc',
              }}
              onMouseEnter={e => { if (selected?.id !== n.id) e.currentTarget.style.background = '#f8fafc' }}
              onMouseLeave={e => { if (selected?.id !== n.id) e.currentTarget.style.background = '#fff' }}
            >
              <span style={{ color: '#94a3b8', whiteSpace: 'nowrap' }}>{fmtTime(n.created_at)}</span>
              <span style={{ color: '#64748b' }}>{n.app_id}</span>
              <ChannelBadge channel={n.channel} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis',
                whiteSpace: 'nowrap', color: '#1e293b' }}>
                {n.title}
              </span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis',
                whiteSpace: 'nowrap', color: '#64748b', fontSize: 11 }}>
                {n.user_id}
              </span>
              <StatusBadge status={n.status} />
              <span style={{ color: '#94a3b8', fontSize: 11 }}>
                {n.retry_count}/{n.max_retries}
              </span>
            </div>

            {selected?.id === n.id && (
              <NotificationDetail
                notification={n}
                onUpdate={() => { refetch(); setSelected(null) }}
              />
            )}
          </div>
        ))}
      </div>

      {showModal && (
        <SendModal
          onClose={() => setShowModal(false)}
          onSent={() => { setShowModal(false); refetch() }}
        />
      )}
    </div>
  )
}

const rowStyle = {
  display: 'grid',
  gridTemplateColumns: '80px 64px 80px 1fr 160px 80px 60px',
  alignItems: 'center',
  gap: 10,
  padding: '8px 24px',
  borderBottom: '1px solid #f1f5f9',
}