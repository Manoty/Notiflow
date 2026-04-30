import { useState } from 'react'
import { Header }   from './components/Header'
import { Metrics }  from './components/Metrics'
import { Toolbar }  from './components/Toolbar'
import { NotificationDetail } from './components/NotificationDetail'
import { SendModal }          from './components/SendModal'
import { Pill }               from './components/Pill'
import { useNotifications, useQueueStats } from './api/useNotifications'
import { fmtTime, canRetry } from './tokens'

const COL = '76px 54px 68px minmax(0,1fr) 130px 64px 48px 20px'

export default function App() {
  const [filters,   setFilters]   = useState({ app_id:'', channel:'', status:'', user_id:'' })
  const [selected,  setSelected]  = useState(null)
  const [showModal, setShowModal] = useState(false)

  const { data, loading, error, refetch } = useNotifications(filters)
  const { stats } = useQueueStats()

  const toggle = n => setSelected(s => s?.id === n.id ? null : n)

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100vh', background: 'var(--bg0)', overflow: 'hidden',
    }}>
      <Header
        queueStats={stats}
        loading={loading}
        onRefresh={refetch}
        onSend={() => setShowModal(true)}
      />

      <Metrics data={data} />

      {error && (
        <div style={{
          fontSize: 11, color: 'var(--red)',
          padding: '7px 16px',
          background: 'rgba(239,68,68,.07)',
          borderBottom: '1px solid rgba(239,68,68,.2)',
          flexShrink: 0,
        }}>
          API error: {error} — showing mock data
        </div>
      )}

      <Toolbar filters={filters} onChange={f => { setFilters(f); setSelected(null); }} />

      {/* Table header */}
      <div style={{
        display: 'grid', gridTemplateColumns: COL, gap: 0,
        padding: '6px 16px', borderBottom: '1px solid var(--ln)',
        background: 'var(--bg0)',
        fontSize: 10, color: 'var(--t2)',
        textTransform: 'uppercase', letterSpacing: '.08em',
        flexShrink: 0,
      }}>
        {['time','app','channel','title','user','status','retry',''].map(h => (
          <span key={h}>{h}</span>
        ))}
      </div>

      {/* Scrollable table body */}
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {data.length === 0 && !loading && (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            height: '100%', color: 'var(--t2)', fontSize: 12,
          }}>
            no notifications match the current filters
          </div>
        )}

        {data.map(n => {
          const isSel  = selected?.id === n.id
          const isFail = n.status === 'failed'
          return (
            <div key={n.id}>
              <div
                onClick={() => toggle(n)}
                style={{
                  display: 'grid', gridTemplateColumns: COL, gap: 0,
                  padding: '0 16px', height: 38, alignItems: 'center',
                  borderBottom: '1px solid var(--ln)',
                  borderLeft: isSel
                    ? '2px solid var(--acc)'
                    : isFail
                      ? '2px solid var(--red)'
                      : '2px solid transparent',
                  paddingLeft: isSel || isFail ? 14 : 16,
                  background: isSel
                    ? 'var(--bg2)'
                    : isFail
                      ? 'rgba(239,68,68,.03)'
                      : 'transparent',
                  cursor: 'pointer',
                  transition: 'background .08s',
                }}
                onMouseEnter={e => { if (!isSel) e.currentTarget.style.background = 'var(--bg2)' }}
                onMouseLeave={e => { if (!isSel) e.currentTarget.style.background = isFail ? 'rgba(239,68,68,.03)' : 'transparent' }}
              >
                <span style={{ fontSize: 10, color: 'var(--t2)' }}>{fmtTime(n.created_at)}</span>
                <Pill type={n.app_id} label={n.app_id} />
                <Pill type={n.channel} label={n.channel} />
                <span style={{ fontSize: 11, color: 'var(--t0)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.title}</span>
                <span style={{ fontSize: 10, color: 'var(--t2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.user_id}</span>
                <Pill type={n.status} label={n.status} />
                <span style={{ fontSize: 10, color: 'var(--t2)' }}>{n.retry_count}/{n.max_retries}</span>
                <span style={{ fontSize: 9, color: 'var(--t3)', textAlign: 'right' }}>{isSel ? '▲' : '▼'}</span>
              </div>

              {isSel && (
                <NotificationDetail
                  notification={n}
                  onClose={() => setSelected(null)}
                  onUpdate={() => { refetch(); setSelected(null) }}
                />
              )}
            </div>
          )
        })}
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