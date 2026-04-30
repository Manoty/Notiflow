export function Toolbar({ filters, onChange }) {
  const set = key => e => onChange({ ...filters, [key]: e.target.value })
  const sel = { fontFamily: 'var(--mono)', fontSize: 11, padding: '4px 8px', borderRadius: 4, border: '1px solid var(--ln2)', background: 'var(--bg0)', color: 'var(--t1)', cursor: 'pointer', appearance: 'none' }
  const lbl = { fontSize: 10, color: 'var(--t2)', textTransform: 'uppercase', letterSpacing: '.07em', marginRight: 4 }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '8px 16px', borderBottom: '1px solid var(--ln)',
      background: 'var(--bg1)', flexShrink: 0, flexWrap: 'wrap',
    }}>
      <span style={lbl}>app</span>
      <select style={sel} value={filters.app_id} onChange={set('app_id')}>
        <option value="">all</option>
        <option value="tixora">tixora</option>
        <option value="scott">scott</option>
      </select>

      <span style={{ ...lbl, marginLeft: 8 }}>ch</span>
      <select style={sel} value={filters.channel} onChange={set('channel')}>
        <option value="">all</option>
        <option value="email">email</option>
        <option value="sms">sms</option>
        <option value="in_app">in_app</option>
      </select>

      <span style={{ ...lbl, marginLeft: 8 }}>status</span>
      <select style={sel} value={filters.status} onChange={set('status')}>
        <option value="">all</option>
        <option value="sent">sent</option>
        <option value="pending">pending</option>
        <option value="failed">failed</option>
        <option value="read">read</option>
      </select>

      <div style={{ flex: 1 }} />

      <input
        style={{ ...sel, width: 148 }}
        placeholder="filter user_id…"
        value={filters.user_id}
        onChange={set('user_id')}
      />
    </div>
  )
}