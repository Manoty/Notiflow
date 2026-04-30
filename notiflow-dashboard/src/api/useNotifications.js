import { useState, useEffect, useCallback } from 'react'
import { api } from './client'

export function useNotifications(filters = {}) {
  const [data,    setData]    = useState([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)
  const [count,   setCount]   = useState(0)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.listNotifications(filters)
      // DRF returns { count, results } or plain array
      if (res.results) {
        setData(res.results)
        setCount(res.count)
      } else {
        setData(res)
        setCount(res.length)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(filters)])

  useEffect(() => { fetch() }, [fetch])

  return { data, count, loading, error, refetch: fetch }
}

export function useQueueStats() {
  const [stats,   setStats]   = useState({ queued: 0, overdue: 0 })
  const [loading, setLoading] = useState(false)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.getQueueStats()
      setStats(res)
    } catch { }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    fetch()
    // Poll queue stats every 10 seconds
    const interval = setInterval(fetch, 10000)
    return () => clearInterval(interval)
  }, [fetch])

  return { stats, loading, refetch: fetch }
}