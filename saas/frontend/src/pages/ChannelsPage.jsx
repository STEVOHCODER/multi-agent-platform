import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

export default function ChannelsPage() {
  const { current } = useWs()
  const [channels, setChannels] = useState([])
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [webhookStatus, setWebhookStatus] = useState(null)

  useEffect(() => {
    if (!current) return
    api.conversations.channels(current.id).then(setChannels).catch(() => {})
    api.conversations.webhookStatus(current.id).then(setWebhookStatus).catch(() => {})
  }, [current])

  const quickConnectWhatsApp = async () => {
    if (!current) return
    setLoading(true); setStatus('')
    try {
      const ch = await api.conversations.quickConnectWhatsApp(current.id)
      setChannels(p => { const idx = p.findIndex(c => c.channel_type === 'whatsapp'); return idx >= 0 ? p.map((c, i) => i === idx ? ch : c) : [...p, ch] })
      setStatus('WhatsApp connected successfully!')
    } catch (e) { setStatus('Error: ' + e.message) }
    setLoading(false)
  }

  const quickConnectEmail = async () => {
    if (!current) return
    setLoading(true); setStatus('')
    try {
      const ch = await api.conversations.quickConnectEmail(current.id)
      setChannels(p => { const idx = p.findIndex(c => c.channel_type === 'email'); return idx >= 0 ? p.map((c, i) => i === idx ? ch : c) : [...p, ch] })
      setStatus('Email connected successfully!')
    } catch (e) { setStatus('Error: ' + e.message) }
    setLoading(false)
  }

  const setupWebhook = async () => {
    if (!current) return
    setLoading(true); setStatus('')
    try {
      const result = await api.conversations.setupWebhook(current.id)
      setStatus(`Webhook configured! URL: ${result.callback_url}`)
      const status = await api.conversations.webhookStatus(current.id)
      setWebhookStatus(status)
    } catch (e) { setStatus('Error: ' + e.message) }
    setLoading(false)
  }

  const webhookUrl = current ? `${window.location.origin}/api/webhooks/whatsapp/${current.id}` : 'Select a workspace first'

  if (!current) return <div style={S.page}><p>Select a workspace first.</p></div>

  return (
    <div style={S.page}>
      <h1 style={S.h1}>Channels</h1>
      {status && <div style={{ padding: 12, background: status.includes('Error') ? '#fee2e2' : '#dcfce7', color: status.includes('Error') ? '#991b1b' : '#166534', borderRadius: 8, marginBottom: 16 }}>{status}</div>}

      {/* Connected channels */}
      <div style={S.card}>
        <h2 style={S.h2}>Connected Channels</h2>
        {channels.length === 0 && <div style={S.empty}>No channels connected yet. Use Quick Connect below.</div>}
        {channels.map(c => (
          <div key={c.id} style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ textTransform: 'capitalize' }}>{c.channel_type}</strong>
              <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                {c.channel_type === 'whatsapp' ? `Phone: ${c.config?.phone_number || c.config?.phone_number_id || 'Connected'}` : `Email: ${c.config?.address || 'Connected'}`}
              </div>
            </div>
            <span style={S.badge('#dcfce7', '#16a34a')}>active</span>
          </div>
        ))}
      </div>

      {/* Quick Connect */}
      <div style={S.card}>
        <h2 style={S.h2}>Quick Connect (Auto-Configure from .env)</h2>
        <p style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: 16 }}>These buttons auto-configure using credentials from your <code>.env</code> file.</p>
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={quickConnectWhatsApp} disabled={loading} style={{ ...S.btn(), opacity: loading ? 0.6 : 1 }}>
            {loading ? 'Connecting...' : 'Connect WhatsApp (Auto)'}
          </button>
          <button onClick={quickConnectEmail} disabled={loading} style={{ ...S.btn('#10b981'), opacity: loading ? 0.6 : 1 }}>
            {loading ? 'Connecting...' : 'Connect Email (Auto)'}
          </button>
        </div>
      </div>

      {/* Auto Webhook Setup */}
      <div style={S.card}>
        <h2 style={S.h2}>Auto Webhook Setup (Meta API)</h2>
        <p style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: 16 }}>
          One-click webhook configuration using Meta Graph API. Requires <code>META_APP_ID</code> and <code>META_APP_SECRET</code> in .env.
        </p>

        {webhookStatus && (
          <div style={{ padding: 12, background: webhookStatus.configured ? '#dcfce7' : '#fef3c7', borderRadius: 8, marginBottom: 16, fontSize: '0.85rem' }}>
            {webhookStatus.configured ? (
              <div>
                <strong style={{ color: '#166534' }}>App Connected</strong> (ID: {webhookStatus.app_id})
                <br />Callback URL: <code>{webhookStatus.callback_url}</code>
                {webhookStatus.subscriptions?.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong>Subscriptions:</strong>
                    {webhookStatus.subscriptions.map((s, i) => (
                      <div key={i} style={{ marginLeft: 12 }}>• {s.object} — {s.callback_url}</div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: '#92400e' }}>{webhookStatus.message}</div>
            )}
          </div>
        )}

        <button onClick={setupWebhook} disabled={loading} style={{ ...S.btn('#8b5cf6'), opacity: loading ? 0.6 : 1 }}>
          {loading ? 'Setting up...' : 'Auto-Setup Webhook via Meta API'}
        </button>
      </div>

      {/* WhatsApp manual setup */}
      <div style={S.card}>
        <h2 style={S.h2}>WhatsApp Webhook Configuration</h2>
        <div style={{ padding: 12, background: '#eff6ff', borderRadius: 8, marginBottom: 16, fontSize: '0.85rem', color: '#1e40af' }}>
          <strong>Webhook URL:</strong> <code style={{ background: '#dbeafe', padding: '2px 6px', borderRadius: 4 }}>{webhookUrl}</code>
          <br /><br />
          <strong>Verify Token:</strong> <code style={{ background: '#dbeafe', padding: '2px 6px', borderRadius: 4 }}>agent_platform_webhook_verify_2024</code>
          <br /><br />
          Set these in Meta Developer Console → WhatsApp → Configuration → Webhook.
        </div>
        <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
          <strong>Your credentials from .env:</strong>
          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
            <li>Phone Number ID: <code>1287317304459774</code></li>
            <li>Phone: <code>+250786508880</code></li>
            <li>Access Token: <code>EAAO6gp7k... (configured)</code></li>
          </ul>
        </div>
      </div>
    </div>
  )
}
