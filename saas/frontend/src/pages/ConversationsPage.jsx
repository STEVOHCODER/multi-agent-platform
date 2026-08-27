import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

export default function ConversationsPage() {
  const { current } = useWs()
  const [contacts, setContacts] = useState([])
  const [messages, setMessages] = useState([])
  const [memory, setMemory] = useState([])
  const [memQuery, setMemQuery] = useState('')
  const [tab, setTab] = useState('messages')
  const [convId, setConvId] = useState('')

  useEffect(() => {
    if (!current) return
    api.conversations.contacts(current.id).then(setContacts).catch(() => {})
    api.conversations.messages(current.id).then(setMessages).catch(() => {})
  }, [current])

  const searchMemory = async () => {
    if (!current || !memQuery.trim()) return
    const res = await api.conversations.memory(current.id, memQuery)
    setMemory(res.memories || res || [])
  }

  if (!current) return <div style={S.page}><p>Select a workspace first.</p></div>

  return (
    <div style={S.page}>
      <h1 style={S.h1}>Conversations</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['messages', 'memory'].map(t => <button key={t} onClick={() => setTab(t)} style={S.btn(tab === t ? '#3b82f6' : '#f3f4f6', tab === t ? '#fff' : '#374151')}>{t}</button>)}
      </div>

      {tab === 'messages' && (
        <div style={S.card}>
          <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
            <select value={convId} onChange={e => setConvId(e.target.value)} style={{ ...S.select, width: 300 }}>
              <option value="">All messages</option>
              {contacts.map(c => <option key={c.id} value={c.id}>{c.name || c.identifier}</option>)}
            </select>
          </div>
          {messages.length === 0 && <div style={S.empty}>No messages yet. Messages appear here when agents process incoming messages.</div>}
          {messages.map(m => (
            <div key={m.id} style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ fontWeight: 600 }}>{m.sender_name || m.sender_id || 'Unknown'}</span>
                  <span style={S.badge('#eff6ff', '#1e40af')}>{m.channel}</span>
                  <span style={S.badge(m.direction === 'inbound' ? '#fef3c7' : '#dcfce7', m.direction === 'inbound' ? '#92400e' : '#166534')}>{m.direction}</span>
                </div>
                <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{m.created_at?.slice(0, 19).replace('T', ' ')}</span>
              </div>
              <div style={{ marginTop: 6, fontSize: '0.9rem', color: '#374151' }}>{m.text}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'memory' && (
        <div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <input value={memQuery} onChange={e => setMemQuery(e.target.value)} style={{ ...S.input, width: 400 }} placeholder="Search memory (e.g. 'customer name', 'last order')" onKeyDown={e => e.key === 'Enter' && searchMemory()} />
            <button onClick={searchMemory} style={S.btn()}>Search</button>
          </div>
          <div style={S.card}>
            {memory.length === 0 && <div style={S.empty}>Search memory to find past conversation context, facts, and preferences.</div>}
            {memory.map(m => (
              <div key={m.id} style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={S.badge(m.memory_type === 'long_term' ? '#dbeafe' : '#f3f4f6', m.memory_type === 'long_term' ? '#1e40af' : '#374151')}>{m.memory_type}</span>
                  <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{m.created_at?.slice(0, 19).replace('T', ' ')}</span>
                </div>
                <div style={{ marginTop: 6, fontSize: '0.9rem' }}>{m.content}</div>
                {m.metadata && Object.keys(m.metadata).length > 0 && <div style={{ marginTop: 4, fontSize: '0.8rem', color: '#6b7280' }}>{JSON.stringify(m.metadata)}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
