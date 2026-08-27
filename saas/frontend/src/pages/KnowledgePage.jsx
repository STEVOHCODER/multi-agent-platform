import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

export default function KnowledgePage() {
  const { current } = useWs()
  const [sources, setSources] = useState([])
  const [cat, setCat] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ title: '', content: '', category: 'general', tags: '' })

  useEffect(() => { if (current) loadSources() }, [current, cat])

  const loadSources = () => { if (!current) return; api.knowledge.list(current.id, cat || undefined).then(setSources).catch(() => {}) }

  const handleCreate = async e => {
    e.preventDefault(); if (!current) return
    await api.knowledge.create(current.id, { ...form, tags: form.tags.split(',').map(t => t.trim()).filter(Boolean) })
    setShowCreate(false); setForm({ title: '', content: '', category: 'general', tags: '' }); loadSources()
  }

  const handleDelete = async id => { if (!confirm('Delete?')) return; await api.knowledge.delete(current.id, id); loadSources() }

  if (!current) return <div style={S.page}><p>Select a workspace first.</p></div>

  return (
    <div style={S.page}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ ...S.h1, marginBottom: 0 }}>Knowledge Base</h1>
        <button onClick={() => setShowCreate(true)} style={S.btn()}>+ Add Source</button>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['', 'faq', 'product', 'policy', 'process', 'general'].map(c => <button key={c} onClick={() => setCat(c)} style={S.btn(cat === c ? '#3b82f6' : '#f3f4f6', cat === c ? '#fff' : '#374151')}>{c || 'All'}</button>)}
      </div>

      {sources.length === 0 && <div style={{ ...S.card, ...S.empty }}>No knowledge sources yet. Add your first source to give agents context.</div>}
      {sources.map(s => (
        <div key={s.id} style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <div style={{ fontWeight: 600 }}>{s.title}</div>
              <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: 4 }}>{s.content?.slice(0, 200)}{s.content?.length > 200 ? '...' : ''}</div>
              <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                <span style={S.badge('#f3f4f6', '#374151')}>{s.category}</span>
                {(s.tags || []).map(t => <span key={t} style={S.tag}>{t}</span>)}
              </div>
            </div>
            <button onClick={() => handleDelete(s.id)} style={S.btn('#fef2f2', '#dc2626')}>Delete</button>
          </div>
        </div>
      ))}

      {showCreate && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowCreate(false)}>
          <div style={{ background: '#fff', borderRadius: 16, padding: 32, width: 500 }} onClick={e => e.stopPropagation()}>
            <h2 style={S.h2}>Add Knowledge Source</h2>
            <form onSubmit={handleCreate}>
              <label style={S.label}>Title</label>
              <input required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} style={S.input} placeholder="e.g. Return Policy" />
              <label style={{ ...S.label, marginTop: 12 }}>Content</label>
              <textarea required value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} style={{ ...S.textarea, minHeight: 120 }} placeholder="The full text of this knowledge source..." />
              <label style={{ ...S.label, marginTop: 12 }}>Category</label>
              <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} style={S.select}>
                <option value="faq">FAQ</option><option value="product">Product</option><option value="policy">Policy</option><option value="process">Process</option><option value="general">General</option>
              </select>
              <label style={{ ...S.label, marginTop: 12 }}>Tags (comma-separated)</label>
              <input value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} style={S.input} placeholder="return, refund, exchange" />
              <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => setShowCreate(false)} style={S.btn('#f3f4f6', '#374151')}>Cancel</button>
                <button type="submit" style={S.btn()}>Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
