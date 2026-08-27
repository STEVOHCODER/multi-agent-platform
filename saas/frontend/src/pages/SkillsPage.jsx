import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { S } from '../styles'

export default function SkillsPage() {
  const [skills, setSkills] = useState([])
  const [cat, setCat] = useState('all')

  useEffect(() => { api.skills.registry().then(setSkills).catch(() => {}) }, [])

  const cats = ['all', ...new Set(skills.map(s => s.category))]
  const filtered = cat === 'all' ? skills : skills.filter(s => s.category === cat)

  return (
    <div style={S.page}>
      <h1 style={S.h1}>Skill Library</h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {cats.map(c => <button key={c} onClick={() => setCat(c)} style={S.btn(cat === c ? '#3b82f6' : '#f3f4f6', cat === c ? '#fff' : '#374151')}>{c}</button>)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
        {filtered.map(s => (
          <div key={s.name} style={S.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div><div style={{ fontWeight: 600 }}>{s.display_name}</div><div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: 4 }}>{s.description}</div></div>
              <span style={S.badge('#f3f4f6', '#374151')}>{s.category}</span>
            </div>
            <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {s.required_permissions.map(p => <span key={p} style={{ ...S.tag, background: '#fef3c7', color: '#92400e' }}>🔒 {p}</span>)}
            </div>
            <div style={{ marginTop: 8, fontSize: '0.8rem', color: '#6b7280' }}>Confidence threshold: {s.confidence_threshold}%</div>
          </div>
        ))}
      </div>
    </div>
  )
}
