const BASE = ''   // proxied via vite — no host needed in dev

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error || data?.detail || `HTTP ${res.status}`)
  return data
}

export const api = {
  // Notifications
  listNotifications: (params = {}) => {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v))
    )
    return request(`/notifications/?${q}`)
  },

  getNotification: (id) =>
    request(`/notifications/${id}/`),

  sendNotification: (payload) =>
    request('/notifications/send/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  retryNotification: (id, force = false) =>
    request(`/notifications/${id}/retry/`, {
      method: 'POST',
      body: JSON.stringify({ force }),
    }),

  markRead: (id) =>
    request(`/notifications/${id}/read/`, { method: 'PATCH' }),

  // Inbox
  getInbox: (userId, appId, unreadOnly = false) => {
    const q = new URLSearchParams({ user_id: userId, app_id: appId })
    if (unreadOnly) q.set('unread_only', 'true')
    return request(`/notifications/inbox/?${q}`)
  },

  getUnreadCount: (userId, appId) =>
    request(`/notifications/unread-count/?${new URLSearchParams({ user_id: userId, app_id: appId })}`),

  markAllRead: (userId, appId) =>
    request('/notifications/mark-all-read/', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, app_id: appId }),
    }),

  // Queue
  getQueueStats: () =>
    request('/notifications/queue-stats/'),

  // Failed
  getFailed: (appId) => {
    const q = new URLSearchParams(appId ? { app_id: appId } : {})
    return request(`/notifications/failed/?${q}`)
  },
}