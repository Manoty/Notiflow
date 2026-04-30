import { useState } from 'react'
import { api } from '../api/client'

const INITIAL = {
  user_id: '', app_id: 'tixora',
  channel: 'email', title: '', message: '', max_retries: 3,
}

export function SendModal({ onClose, onSent }) {
  const [form,    setForm]    = useState(INITIAL)
  const [sending, setSending] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSend = async () => {
    if (!form.user_id || !form.title || !form.message) {
      setError('user_id, title, and message are required.')
      return
    }
    setSending(true)
    setError(null)
    try {
      const res = await api.sendNotification(form)
      setResult(res)
      onSent()
    } catch (e) {
      setError(e.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 100,
    }}>
      <div style={{
        background: '#fff', borderRadius: 14,
        padding: '28px 32px', width: 480, maxWidth: '90vw',
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>send notification</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none',
            fontSize: 18, cursor: 'pointer', color: '#94a3b8' }}>✕</button>
        </div>

        {result
          ? (
            <div>
              <div style={{ background: '#dcfce7', borderRadius: 8,
                padding: '12px 16px', marginBottom: 16, fontSize: 13 }}>
                <strong style={{ color: '#166534' }}>Queued successfully</strong>
                <p style={{ color: '#166534', marginTop: 4, fontSize: 12 }}>
                  ID: {result.notification_id}
                </p>
              </div>
              <button onClick={() => { setResult(null); setForm(INITIAL) }}
                style={btnStyle}>send another</button>
            </div>
          )
          : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                ['user_id',  'user_id (email or phone)',  'text'],
                ['title',    'title',                      'text'],
              ].map(([k, ph, type]) => (
                <div key={k}>
                  <label style={labelStyle}>{k}</label>
                  <input style={inputStyle} type={type}
                    placeholder={ph} value={form[k]} onChange={set(k)} />
                </div>
              ))}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={labelStyle}>app</label>
                  <select style={inputStyle} value={form.app_id} onChange={set('app_id')}>
                    <option value="tixora">tixora</option>
                    <option value="scott">scott</option>
                    <option value="default">default</option>
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>channel</label>
                  <select style={inputStyle} value={form.channel} onChange={set('channel')}>
                    <option value="email">email</option>
                    <option value="sms">sms</option>
                    <option value="in_app">in_app</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={labelStyle}>message</label>
                <textarea style={{ ...inputStyle, height: 80, resize: 'vertical' }}
                  placeholder="notification body"
                  value={form.message} onChange={set('message')} />
              </div>

              {error && (
                <p style={{ color: '#ef4444', fontSize: 12 }}>{error}</p>
              )}

              <button onClick={handleSend} disabled={sending} style={btnStyle}>
                {sending ? 'sending...' : 'send notification'}
              </button>
            </div>
          )
        }
      </div>
    </div>
  )
}

const labelStyle = {
  display: 'block', fontSize: 11, color: '#94a3b8',
  textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4,
}
const inputStyle = {
  width: '100%', fontFamily: 'inherit', fontSize: 13,
  padding: '7px 10px', border: '1px solid #e2e8f0',
  borderRadius: 8, background: '#f8fafc', color: '#1e293b',
  boxSizing: 'border-box',
}
const btnStyle = {
  width: '100%', padding: '10px', fontFamily: 'inherit',
  fontSize: 13, fontWeight: 500, border: 'none',
  borderRadius: 8, background: '#1e293b', color: '#fff',
  cursor: 'pointer',
}