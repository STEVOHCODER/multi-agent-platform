import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthProvider'
import { useWs } from './WsProvider'

const NAV = [
  ['Dashboard', '/app'],
  ['Agents', '/app/agents'],
  ['Skills', '/app/skills'],
  ['Channels', '/app/channels'],
  ['Conversations', '/app/conversations'],
  ['Knowledge', '/app/knowledge'],
  ['Settlements', '/app/settlements'],
  ['Audit', '/app/audit'],
  ['Settings', '/app/settings'],
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const { current, workspaces, switchWs, createWs } = useWs()
  const [showWs, setShowWs] = useState(false)
  const [newName, setNewName] = useState('')
  const location = useLocation()
  const path = location.pathname

  const handleCreateWs = async () => {
    if (!newName.trim()) return
    await createWs(newName.trim())
    setNewName('')
    setShowWs(false)
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ width: 240, background: '#0f172a', color: '#94a3b8', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '20px 20px 12px', fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>Agent Platform</div>
        <div style={{ padding: '0 16px 16px' }}>
          <div onClick={() => setShowWs(!showWs)} style={{ padding: '8px 12px', background: '#1e293b', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{current?.name || 'No Workspace'}</span><span>▾</span>
          </div>
          {showWs && (
            <div style={{ marginTop: 4, background: '#1e293b', borderRadius: 8, overflow: 'hidden' }}>
              {workspaces.map(w => (
                <div key={w.id} onClick={() => { switchWs(w); setShowWs(false) }} style={{ padding: '8px 12px', cursor: 'pointer', fontSize: '0.85rem', background: w.id === current?.id ? '#334155' : 'transparent' }}>{w.name}</div>
              ))}
              <div style={{ padding: '8px 12px', borderTop: '1px solid #334155' }}>
                <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="New workspace..." onKeyDown={e => e.key === 'Enter' && handleCreateWs()} style={{ width: '100%', padding: '6px 8px', background: '#0f172a', border: '1px solid #475569', borderRadius: 6, color: '#fff', fontSize: '0.85rem', boxSizing: 'border-box' }} />
              </div>
            </div>
          )}
        </div>
        <div style={{ flex: 1 }}>
          {NAV.map(([label, href]) => (
            <Link key={href} to={href} style={{ display: 'block', padding: '10px 20px', textDecoration: 'none', color: path === href || path.startsWith(href + '/') ? '#fff' : '#94a3b8', background: path === href || path.startsWith(href + '/') ? '#1e293b' : 'transparent', borderLeft: path === href ? '3px solid #3b82f6' : '3px solid transparent', fontSize: '0.9rem' }}>{label}</Link>
          ))}
        </div>
        <div style={{ padding: '12px 20px', borderTop: '1px solid #1e293b' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 4 }}>{user?.email}</div>
          <div onClick={logout} style={{ fontSize: '0.85rem', color: '#ef4444', cursor: 'pointer' }}>Logout</div>
        </div>
      </div>
      <div style={{ flex: 1, background: '#f8fafc', minHeight: '100vh', overflow: 'auto' }}>{children}</div>
    </div>
  )
}
