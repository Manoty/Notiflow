import { Pill } from './Pill'

export function Header({ queueStats, loading, onRefresh, onSend }) {
  return (
    <header style={{
      display: 'flex', alignItems: 'center',
      borderBottom: '1px solid var(--ln)',
      background: 'var(--bg1)', flexShrink: 0,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '0 20px', height: 44,
        borderRight: '1px solid var(--ln)',
      }}>
        <div style={{
          width: 22, height: 22, borderRadius: 4,
          background: 'var(--acc)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <rect x="1" y="1" width="4" height="4" rx="1" fill="white" opacity=".9"/>
            <rect x="7" y="1" width="4" height="4" rx="1" fill="white" opacity=".6"/>
            <rect x="1" y="7" width="4" height="4" rx="1" fill="white" opacity=".6"/>
            <rect x="7" y="7" width="4" height="4" rx="1" fill="white" opacity=".3"/>
          </svg>
        </div>
        <span style={{
          fontFamily: 'var(--sans)', fontSize: 13,
          fontWeight: 600, letterSpacing: '-0.3px', color: 'var(--t0)',
        }}>
          notiflow
        </span>
      </div>

      {[
        ['live', <><LiveDot /> <span>live</span></>],
        ['queue',   <>queue <b style={{ color: 'var(--t0)', fontWeight: 500 }}>{queueStats.queued ?? '—'}</b></>],
        ['overdue', <>overdue <b style={{ color: 'var(--amb)', fontWeight: 500 }}>{queueStats.overdue ?? '—'}</b></>],
      ].map(([key, content]) => (
        <div key={key} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '0 20px', height: 44, fontSize: 11,
          color: 'var(--t1)', borderRight: '1px solid var(--ln)',
        }}>
          {content}
        </div>
      ))}

      <div style={{
        marginLeft: 'auto', display: 'flex',
        alignItems: 'center', gap: 8, padding: '0 16px',
      }}>
        <Btn onClick={onRefresh} disabled={loading}>
          <span style={loading ? { animation: 'spin .7s linear infinite', display: 'inline-block' } : {}}>
            ↻
          </span>
          {loading ? ' loading' : ' refresh'}
        </Btn>
        <Btn primary onClick={onSend}>+ send</Btn>
      </div>
    </header>
  )
}

function LiveDot() {
  return (
    <span style={{
      width: 6, height: 6, borderRadius: '50%',
      background: 'var(--grn)',
      display: 'inline-block',
      animation: 'blink 2s ease infinite',
      flexShrink: 0,
    }} />
  )
}

function Btn({ children, primary, ...props }) {
  return (
    <button style={{
      fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 500,
      padding: '5px 12px', borderRadius: 4,
      border: `1px solid ${primary ? 'var(--acc)' : 'var(--ln2)'}`,
      background: primary ? 'var(--acc)' : 'var(--bg2)',
      color: primary ? '#fff' : 'var(--t1)',
      cursor: 'pointer', whiteSpace: 'nowrap',
    }} {...props}>
      {children}
    </button>
  )
}