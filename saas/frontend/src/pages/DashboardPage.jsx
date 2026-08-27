import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import * as api from '../api/client'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

export default function DashboardPage() {
  const { current, createWs } = useWs()
  const [agents, setAgents] = useState([])
  const [txs, setTxs] = useState([])
  const [msgs, setMsgs] = useState([])
  const [name, setName] = useState('')

  useEffect(() => {
    if (!current) return
    api.agents.list(current.id).then(setAgents).catch(() => {})
    api.settlement.unsettled(current.id).then(r => setTxs(r.transactions || [])).catch(() => {})
    api.conversations.messages(current.id).then(setMsgs).catch(() => {})
  }, [current])

  if (!current) return (
    <div style={{ textAlign: 'center', paddingTop: 100, fontFamily: 'system-ui' }}>
      <h2 style={{ marginBottom: 16 }}>Welcome! Create your first workspace</h2>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="My Business" style={{ ...S.input, width: 250 }} onKeyDown={e => e.key === 'Enter' && name.trim() && createWs(name.trim())} />
        <button onClick={() => name.trim() && createWs(name.trim())} style={S.btn()}>Create</button>
      </div>
    </div>
  )

  return (
    <div style={S.page}>
      <h1 style={S.h1}>Dashboard — {current.name}</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <div style={S.stat}><div style={{ fontSize: '0.85rem', color: '#6b7280' }}>Active Agents</div><div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{agents.filter(a => a.status === 'active').length}</div></div>
        <div style={S.stat}><div style={{ fontSize: '0.85rem', color: '#6b7280' }}>Total Agents</div><div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{agents.length}</div></div>
        <div style={S.stat}><div style={{ fontSize: '0.85rem', color: '#6b7280' }}>Unsettled</div><div style={{ fontSize: '1.8rem', fontWeight: 700 }}>${txs.reduce((s, t) => s + (t.amount || 0), 0).toLocaleString()}</div></div>
        <div style={S.stat}><div style={{ fontSize: '0.85rem', color: '#6b7280' }}>Messages</div><div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{msgs.length}</div></div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={S.card}>
          <h2 style={S.h2}>Your Agents</h2>
          {agents.length === 0 && <div style={S.empty}>No agents yet. <Link to="/app/agents">Create one</Link></div>}
          {agents.slice(0, 5).map(a => (
            <div key={a.id} style={{ padding: '10px 0', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div><strong>{a.name}</strong><div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{a.model} • {a.response_mode}</div></div>
              <span style={S.badge(a.status === 'active' ? '#dcfce7' : '#fef2f2', a.status === 'active' ? '#16a34a' : '#dc2626')}>{a.status}</span>
            </div>
          ))}
        </div>
        <div style={S.card}>
          <h2 style={S.h2}>Recent Messages</h2>
          {msgs.length === 0 && <div style={S.empty}>No messages yet</div>}
          {msgs.slice(0, 5).map(m => (
            <div key={m.id} style={{ padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong style={{ fontSize: '0.9rem' }}>{m.sender_name || m.sender_id || 'Unknown'}</strong>
                <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{m.channel}</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: 4 }}>{m.text?.slice(0, 80)}{m.text?.length > 80 ? '...' : ''}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
