import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

export default function AgentsPage() {
  const { current } = useWs()
  const [agents, setAgents] = useState([])
  const [templates, setTemplates] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', model: 'gpt-4o-mini', system_instructions: '', response_mode: 'off', channels: [] })

  useEffect(() => {
    if (!current) return
    api.agents.list(current.id).then(setAgents).catch(() => {})
    api.agents.templates().then(setTemplates).catch(() => {})
  }, [current])

  const handleTemplate = async tid => { if (!current) return; const a = await api.agents.createFromTemplate(current.id, tid); setAgents(p => [...p, a]) }

  const handleCreate = async e => {
    e.preventDefault(); if (!current) return
    const a = await api.agents.create(current.id, form); setAgents(p => [...p, a]); setShowCreate(false)
    setForm({ name: '', description: '', model: 'gpt-4o-mini', system_instructions: '', response_mode: 'off', channels: [] })
  }

  const handleDelete = async id => { if (!confirm('Delete this agent?')) return; await api.agents.delete(id); setAgents(p => p.filter(a => a.id !== id)) }
  const toggleStatus = async a => { const ns = a.status === 'active' ? 'paused' : 'active'; const u = await api.agents.update(a.id, { status: ns }); setAgents(p => p.map(x => x.id === a.id ? u : x)) }

  if (!current) return <div style={S.page}><p>Select a workspace first.</p></div>

  return (
    <div style={S.page}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ ...S.h1, marginBottom: 0 }}>Agents</h1>
        <button onClick={() => setShowCreate(true)} style={S.btn()}>+ Create Agent</button>
      </div>

      <div style={S.card}>
        <h2 style={S.h2}>Quick Start — Agent Templates</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
          {templates.map(t => (
            <div key={t.id} style={{ padding: 16, border: '1px solid #e5e7eb', borderRadius: 10, cursor: 'pointer' }} onClick={() => handleTemplate(t.id)}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{t.name}</div>
              <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: 8 }}>{t.description}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {t.skills.slice(0, 3).map(s => <span key={s} style={S.tag}>{s}</span>)}
                {t.skills.length > 3 && <span style={S.tag}>+{t.skills.length - 3}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      <h2 style={{ ...S.h2, marginTop: 24 }}>Your Agents</h2>
      {agents.length === 0 && <div style={{ ...S.card, ...S.empty }}>No agents yet. Use a template above or create custom.</div>}
      {agents.map(a => (
        <div key={a.id} style={{ ...S.card, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: '1rem' }}>{a.name}</div>
            <div style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: 2 }}>{a.description || 'No description'}</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
              <span style={S.tag}>{a.model}</span><span style={S.tag}>Response: {a.response_mode}</span>
              {(a.channels || []).map(c => <span key={c} style={S.tag}>{c}</span>)}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => toggleStatus(a)} style={S.btn(a.status === 'active' ? '#dcfce7' : '#fef2f2', a.status === 'active' ? '#16a34a' : '#dc2626')}>{a.status === 'active' ? 'Active' : 'Paused'}</button>
            <button onClick={() => handleDelete(a.id)} style={S.btn('#fef2f2', '#dc2626')}>Delete</button>
          </div>
        </div>
      ))}

      {showCreate && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowCreate(false)}>
          <div style={{ background: '#fff', borderRadius: 16, padding: 32, width: 500, maxHeight: '80vh', overflow: 'auto' }} onClick={e => e.stopPropagation()}>
            <h2 style={S.h2}>Create Custom Agent</h2>
            <form onSubmit={handleCreate}>
              <label style={S.label}>Name</label>
              <input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} style={S.input} placeholder="My Agent" />
              <label style={{ ...S.label, marginTop: 12 }}>Description</label>
              <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} style={S.input} placeholder="What does this agent do?" />
              <label style={{ ...S.label, marginTop: 12 }}>Model</label>
              <select value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} style={S.select}>
                <option value="gpt-4o-mini">GPT-4o Mini</option><option value="gpt-4o">GPT-4o</option>
                <option value="claude-sonnet-4-20250514">Claude Sonnet</option><option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
              </select>
              <label style={{ ...S.label, marginTop: 12 }}>System Instructions</label>
              <textarea value={form.system_instructions} onChange={e => setForm({ ...form, system_instructions: e.target.value })} style={S.textarea} placeholder="You are a helpful assistant..." />
              <label style={{ ...S.label, marginTop: 12 }}>Response Mode</label>
              <select value={form.response_mode} onChange={e => setForm({ ...form, response_mode: e.target.value })} style={S.select}>
                <option value="off">Off (never auto-reply)</option><option value="suggest">Suggest (draft, human approves)</option>
                <option value="auto">Auto (send automatically)</option><option value="auto_escalation">Auto + Escalation</option>
              </select>
              <label style={{ ...S.label, marginTop: 12 }}>Channels</label>
              <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
                {['whatsapp', 'email'].map(ch => (
                  <label key={ch} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                    <input type="checkbox" checked={form.channels.includes(ch)} onChange={e => setForm({ ...form, channels: e.target.checked ? [...form.channels, ch] : form.channels.filter(c => c !== ch) })} />{ch}
                  </label>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => setShowCreate(false)} style={S.btn('#f3f4f6', '#374151')}>Cancel</button>
                <button type="submit" style={S.btn()}>Create Agent</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
