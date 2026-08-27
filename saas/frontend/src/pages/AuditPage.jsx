import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

export default function AuditPage() {
  const { current } = useWs()
  const [logs, setLogs] = useState([])
  const [runs, setRuns] = useState([])
  const [tab, setTab] = useState('logs')

  useEffect(() => { if (current) { api.audit.logs(current.id).then(setLogs).catch(() => {}); api.audit.runs(current.id).then(setRuns).catch(() => {}) } }, [current])

  if (!current) return <div style={S.page}><p>Select a workspace first.</p></div>

  return (
    <div style={S.page}>
      <h1 style={S.h1}>Audit Log</h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button onClick={() => setTab('logs')} style={S.btn(tab === 'logs' ? '#3b82f6' : '#f3f4f6', tab === 'logs' ? '#fff' : '#374151')}>Audit Logs</button>
        <button onClick={() => setTab('runs')} style={S.btn(tab === 'runs' ? '#3b82f6' : '#f3f4f6', tab === 'runs' ? '#fff' : '#374151')}>Agent Runs</button>
      </div>

      {tab === 'logs' && (
        <div style={S.card}>
          {logs.length === 0 && <div style={S.empty}>No audit logs yet</div>}
          {logs.map(l => (
            <div key={l.id} style={{ padding: '10px 0', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={S.badge(l.severity === 'warning' ? '#fef3c7' : l.severity === 'error' ? '#fee2e2' : '#f3f4f6', l.severity === 'warning' ? '#92400e' : l.severity === 'error' ? '#991b1b' : '#374151')}>{l.severity || 'info'}</span>
                  <strong style={{ fontSize: '0.9rem' }}>{l.action}</strong>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: 4 }}>{l.details}</div>
              </div>
              <span style={{ fontSize: '0.8rem', color: '#9ca3af', whiteSpace: 'nowrap' }}>{l.created_at?.slice(0, 19).replace('T', ' ')}</span>
            </div>
          ))}
        </div>
      )}

      {tab === 'runs' && (
        <div style={S.card}>
          {runs.length === 0 && <div style={S.empty}>No agent runs yet</div>}
          {runs.map(r => (
            <div key={r.id} style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>{r.trigger_type}</strong>
                  <span style={{ ...S.tag, marginLeft: 8 }}>Agent: {r.agent_id?.slice(0, 8)}</span>
                </div>
                <span style={S.badge(r.status === 'success' ? '#dcfce7' : '#fee2e2', r.status === 'success' ? '#166534' : '#991b1b')}>{r.status}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: 4 }}>
                {r.tokens_used} tokens • {r.duration_ms}ms • {r.created_at?.slice(0, 19).replace('T', ' ')}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
