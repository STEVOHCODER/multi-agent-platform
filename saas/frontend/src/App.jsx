import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth, Protected } from './components/AuthProvider'
import { WsProvider } from './components/WsProvider'
import Layout from './components/Layout'
import { S } from './styles'
import * as api from './api/client'

import DashboardPage from './pages/DashboardPage'
import AgentsPage from './pages/AgentsPage'
import SkillsPage from './pages/SkillsPage'
import ChannelsPage from './pages/ChannelsPage'
import ConversationsPage from './pages/ConversationsPage'
import KnowledgePage from './pages/KnowledgePage'
import SettlementsPage from './pages/SettlementsPage'
import AuditPage from './pages/AuditPage'
import SettingsPage from './pages/SettingsPage'

function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async e => {
    e.preventDefault(); setError('')
    try { await login({ email, password }); navigate('/app') } catch (err) { setError(err.message) }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
      <div style={{ width: 380 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 24, textAlign: 'center' }}>Agent Platform</h1>
        <div style={S.card}>
          <h2 style={{ ...S.h2, textAlign: 'center' }}>Sign In</h2>
          {error && <div style={{ padding: 10, background: '#fee2e2', color: '#991b1b', borderRadius: 8, marginBottom: 12, fontSize: '0.85rem' }}>{error}</div>}
          <form onSubmit={handleSubmit}>
            <label style={S.label}>Email</label>
            <input required type="email" value={email} onChange={e => setEmail(e.target.value)} style={S.input} />
            <label style={{ ...S.label, marginTop: 12 }}>Password</label>
            <input required type="password" value={password} onChange={e => setPassword(e.target.value)} style={S.input} />
            <button type="submit" style={{ ...S.btn(), width: '100%', marginTop: 16 }}>Sign In</button>
          </form>
          <div style={{ textAlign: 'center', marginTop: 16, fontSize: '0.85rem', color: '#6b7280' }}>
            Don't have an account? <Link to="/register" style={{ color: '#3b82f6' }}>Register</Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async e => {
    e.preventDefault(); setError('')
    try { await register({ email, password }); navigate('/app') } catch (err) { setError(err.message) }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
      <div style={{ width: 380 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 24, textAlign: 'center' }}>Agent Platform</h1>
        <div style={S.card}>
          <h2 style={{ ...S.h2, textAlign: 'center' }}>Create Account</h2>
          {error && <div style={{ padding: 10, background: '#fee2e2', color: '#991b1b', borderRadius: 8, marginBottom: 12, fontSize: '0.85rem' }}>{error}</div>}
          <form onSubmit={handleSubmit}>
            <label style={S.label}>Email</label>
            <input required type="email" value={email} onChange={e => setEmail(e.target.value)} style={S.input} />
            <label style={{ ...S.label, marginTop: 12 }}>Password</label>
            <input required type="password" value={password} onChange={e => setPassword(e.target.value)} style={S.input} />
            <button type="submit" style={{ ...S.btn(), width: '100%', marginTop: 16 }}>Create Account</button>
          </form>
          <div style={{ textAlign: 'center', marginTop: 16, fontSize: '0.85rem', color: '#6b7280' }}>
            Already have an account? <Link to="/login" style={{ color: '#3b82f6' }}>Sign In</Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function LandingPage() {
  const { user } = useAuth()
  return (
    <div style={{ minHeight: '100vh', fontFamily: 'system-ui', background: '#0f172a', color: '#fff', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 40px' }}>
        <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>Agent Platform</div>
        <div style={{ display: 'flex', gap: 12 }}>
          {user ? <Link to="/app" style={{ padding: '8px 20px', background: '#3b82f6', color: '#fff', borderRadius: 8, textDecoration: 'none', fontWeight: 600 }}>Dashboard</Link> : (
            <>
              <Link to="/login" style={{ padding: '8px 20px', color: '#94a3b8', textDecoration: 'none' }}>Sign In</Link>
              <Link to="/register" style={{ padding: '8px 20px', background: '#3b82f6', color: '#fff', borderRadius: 8, textDecoration: 'none', fontWeight: 600 }}>Get Started</Link>
            </>
          )}
        </div>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 40px' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 800, marginBottom: 16 }}>Multi-Agent AI Platform</h1>
        <p style={{ fontSize: '1.2rem', color: '#94a3b8', maxWidth: 600, marginBottom: 40 }}>Build, deploy, and manage AI agents that communicate across WhatsApp, Email, and more — with full audit trails, knowledge bases, and settlement tracking.</p>
        <div style={{ display: 'flex', gap: 16 }}>
          <Link to={user ? '/app' : '/register'} style={{ padding: '12px 32px', background: '#3b82f6', color: '#fff', borderRadius: 10, textDecoration: 'none', fontWeight: 700, fontSize: '1.05rem' }}>{user ? 'Go to Dashboard' : 'Start Building'}</Link>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, marginTop: 64, maxWidth: 800 }}>
          {[['🤖', 'Agent Builder', 'Create custom AI agents with templates or build from scratch'], ['⚡', '25+ Skills', 'Reusable skills for email, finance, memory, and more'], ['📡', 'Multi-Channel', 'WhatsApp, Email, and extensible channel support']].map(([icon, title, desc]) => (
            <div key={title} style={{ padding: 24, background: '#1e293b', borderRadius: 12, textAlign: 'left' }}>
              <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>{icon}</div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{title}</div>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/app" element={<Protected><WsProvider><Layout><DashboardPage /></Layout></WsProvider></Protected>} />
          <Route path="/app/agents" element={<Protected><WsProvider><Layout><AgentsPage /></Layout></WsProvider></Protected>} />
          <Route path="/app/skills" element={<Protected><WsProvider><Layout><SkillsPage /></Layout></WsProvider></Protected>} />
          <Route path="/app/channels" element={<Protected><WsProvider><Layout><ChannelsPage /></Layout></WsProvider></Protected>} />
          <Route path="/app/conversations" element={<Protected><WsProvider><Layout><ConversationsPage /></Layout></WsProvider></Protected>} />
          <Route path="/app/knowledge" element={<Protected><WsProvider><Layout><KnowledgePage /></Layout></WsProvider></Protected>} />
          <Route path="/app/settlements" element={<Protected><WsProvider><Layout><SettlementsPage /></Layout></WsProvider></Protected>} />
          <Route path="/app/audit" element={<Protected><WsProvider><Layout><AuditPage /></Layout></WsProvider></Protected>} />
          <Route path="/app/settings" element={<Protected><WsProvider><Layout><SettingsPage /></Layout></WsProvider></Protected>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
