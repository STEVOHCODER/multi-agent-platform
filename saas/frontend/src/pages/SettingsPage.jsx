import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { useAuth } from '../components/AuthProvider'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

export default function SettingsPage() {
  const { user } = useAuth()
  const { current, workspaces } = useWs()
  const [billing, setBilling] = useState(null)
  const [plans, setPlans] = useState([])

  useEffect(() => {
    api.billing.plans().then(setPlans).catch(() => {})
    api.billing.subscription().then(setBilling).catch(() => {})
  }, [])

  return (
    <div style={S.page}>
      <h1 style={S.h1}>Settings</h1>

      {/* Account */}
      <div style={S.card}>
        <h2 style={S.h2}>Account</h2>
        <div style={{ fontSize: '0.9rem' }}><strong>Email:</strong> {user?.email}</div>
        <div style={{ fontSize: '0.9rem', marginTop: 4 }}><strong>Workspaces:</strong> {workspaces.length}</div>
      </div>

      {/* Subscription */}
      <div style={S.card}>
        <h2 style={S.h2}>Subscription</h2>
        {billing ? (
          <div>
            <div style={{ fontSize: '0.9rem' }}><strong>Plan:</strong> {billing.plan}</div>
            <div style={{ fontSize: '0.9rem', marginTop: 4 }}><strong>Status:</strong> {billing.status}</div>
            {billing.status === 'active' && (
              <button onClick={() => api.billing.portal().then(r => window.location.href = r.url)} style={{ ...S.btn('#f3f4f6', '#374151'), marginTop: 12 }}>Manage Billing</button>
            )}
          </div>
        ) : (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 8 }}>
              {plans.filter(p => p.name !== 'free').map(p => (
                <div key={p.name} style={{ padding: 16, border: '1px solid #e5e7eb', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontWeight: 600, textTransform: 'capitalize', marginBottom: 4 }}>{p.name}</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>${p.price}<span style={{ fontSize: '0.8rem', color: '#6b7280' }}>/mo</span></div>
                  <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: 4 }}>{p.messages_per_month} messages/mo</div>
                  <button onClick={() => api.billing.checkout(p.name).then(r => window.location.href = r.url)} style={{ ...S.btn(), marginTop: 12, width: '100%' }}>Upgrade</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* AI Provider config */}
      <div style={S.card}>
        <h2 style={S.h2}>AI Provider</h2>
        <p style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: 12 }}>Configure via environment variables in your <code>.env</code> file:</p>
        <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', background: '#f3f4f6', padding: 12, borderRadius: 8 }}>
          <div>AI_PROVIDER=openai|anthropic|google</div>
          <div>OPENAI_API_KEY=sk-...</div>
          <div>ANTHROPIC_API_KEY=sk-ant-...</div>
          <div>GOOGLE_AI_API_KEY=...</div>
        </div>
      </div>
    </div>
  )
}
