import { channelColor, statusColor } from '../utils'

const CHANNEL_BG = {
  email:  '#e0f2fe', sms: '#f3e8ff', in_app: '#f1f5f9',
}
const STATUS_BG = {
  sent: '#dcfce7', pending: '#fef9c3', failed: '#fee2e2', read: '#f1f5f9',
}

export function ChannelBadge({ channel }) {
  return (
    <span style={{
      background: CHANNEL_BG[channel] || '#f1f5f9',
      color: channelColor[channel] || '#64748b',
      borderRadius: 99, fontSize: 11, fontWeight: 500,
      padding: '2px 8px', whiteSpace: 'nowrap',
    }}>
      {channel}
    </span>
  )
}

export function StatusBadge({ status }) {
  return (
    <span style={{
      background: STATUS_BG[status] || '#f1f5f9',
      color: statusColor[status] || '#64748b',
      borderRadius: 99, fontSize: 11, fontWeight: 500,
      padding: '2px 8px', whiteSpace: 'nowrap',
    }}>
      {status}
    </span>
  )
}