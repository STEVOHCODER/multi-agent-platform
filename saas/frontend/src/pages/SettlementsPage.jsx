import { useState, useEffect } from 'react'
import * as api from '../api/client'
import { useWs } from '../components/WsProvider'
import { S } from '../styles'

const STATUSES = { REQUESTED: '#fef3c7', UNSETTLED: '#fee2e2', PARTIALLY_SETTLED: '#dbeafe', SETTLED: '#dcfce7', CANCELLED: '#f3f4f6', DISPUTED: '#fce7f3', NEEDS_REVIEW: '#fef3c7' }
const STATUS_COLORS = { REQUESTED: '#92400e', UNSETTLED: '#991b1b', PARTIALLY_SETTLED: '#1e40af', SETTLED: '#166534', CANCELLED: '#374151', DISPUTED: '#9d174d', NEEDS_REVIEW: '#92400e' }
const TRANSITIONS = ['UNSETTLED', 'PARTIALLY_SETTLED', 'SETTLED', 'CANCELLED', 'DISPUTED']

export default function SettlementsPage() {
  const { current } = useWs()
  const [txs, setTxs] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [matchText, setMatchText] = useState('')
  const [matchResult, setMatchResult] = useState(null)
  const [report, setReport] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ amount: '', currency: 'USD', description: '', counterparty: '' })

  useEffect(() => { if (current) loadTxs() }, [current, statusFilter])

  const loadTxs = () => { if (!current) return; api.settlement.transactions(current.id, statusFilter || undefined).then(setTxs).catch(() => {}) }

  const handleTransition = async (txId, newStatus) => {
    if (!current) return
    await api.settlement.transition(current.id, txId, newStatus, `Changed to ${newStatus} from UI`)
    loadTxs()
  }

  const handleMatch = async () => { if (!current || !matchText.trim()) return; const r = await api.settlement.match(current.id, matchText); setMatchResult(r) }
  const handleReport = async () => { if (!current) return; const r = await api.settlement.report(current.id); setReport(r) }

  const handleCreate = async e => {
    e.preventDefault(); if (!current) return
    await api.settlement.create(current.id, { ...form, amount: parseFloat(form.amount) })
    setShowCreate(false); setForm({ amount: '', currency: 'USD', description: '', counterparty: '' }); loadTxs()
  }

  if (!current) return <div style={S.page}><p>Select a workspace first.</p></div>

  return (
    <div style={S.page}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ ...S.h1, marginBottom: 0 }}>Settlements</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handleReport} style={S.btn('#f3f4f6', '#374151')}>Daily Report</button>
          <button onClick={() => setShowCreate(true)} style={S.btn()}>+ New Transaction</button>
        </div>
      </div>

      {/* Status filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <button onClick={() => setStatusFilter('')} style={S.btn(!statusFilter ? '#3b82f6' : '#f3f4f6', !statusFilter ? '#fff' : '#374151')}>All</button>
        {Object.keys(STATUSES).map(st => <button key={st} onClick={() => setStatusFilter(st)} style={S.btn(statusFilter === st ? '#3b82f6' : '#f3f4f6', statusFilter === st ? '#fff' : '#374151')}>{st.replace('_', ' ')}</button>)}
      </div>

      {/* Transaction list */}
      {txs.length === 0 && <div style={{ ...S.card, ...S.empty }}>No transactions</div>}
      {txs.map(tx => (
        <div key={tx.id} style={{ ...S.card, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 600 }}>{tx.description || 'Transaction'}</div>
            <div style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: 2 }}>{tx.counterparty} • {tx.created_at?.slice(0, 10)}</div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <div style={{ textAlign: 'right', marginRight: 12 }}>
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>${tx.amount?.toLocaleString()}</div>
              <span style={S.badge(STATUSES[tx.status], STATUS_COLORS[tx.status])}>{tx.status?.replace('_', ' ')}</span>
            </div>
            {tx.status !== 'SETTLED' && tx.status !== 'CANCELLED' && (
              <select onChange={e => { if (e.target.value) handleTransition(tx.id, e.target.value); e.target.value = '' }} style={{ ...S.select, width: 140, fontSize: '0.8rem' }}>
                <option value="">Move to...</option>
                {TRANSITIONS.filter(t => t !== tx.status).map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
              </select>
            )}
          </div>
        </div>
      ))}

      {/* Message matcher */}
      <div style={{ ...S.card, marginTop: 24 }}>
        <h2 style={S.h2}>Message Matcher</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={matchText} onChange={e => setMatchText(e.target.value)} style={{ ...S.input, flex: 1 }} placeholder="Paste a message to find matching transactions..." onKeyDown={e => e.key === 'Enter' && handleMatch()} />
          <button onClick={handleMatch} style={S.btn()}>Match</button>
        </div>
        {matchResult && (
          <div style={{ marginTop: 12 }}>
            {matchResult.transactions?.length === 0 && <div style={{ padding: 8, color: '#6b7280' }}>No matching transactions found</div>}
            {matchResult.transactions?.map(tx => (
              <div key={tx.id} style={{ padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: 8, marginTop: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>{tx.description} — ${tx.amount}</span>
                <span style={S.badge(STATUSES[tx.status], STATUS_COLORS[tx.status])}>{tx.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Report */}
      {report && (
        <div style={{ ...S.card, marginTop: 16 }}>
          <h2 style={S.h2}>Daily Report — {report.date}</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {Object.entries(report.by_status || {}).map(([st, data]) => (
              <div key={st} style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 8, textAlign: 'center' }}>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{st.replace('_', ' ')}</div>
                <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>${data.total_amount?.toLocaleString()}</div>
                <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{data.count} transactions</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowCreate(false)}>
          <div style={{ background: '#fff', borderRadius: 16, padding: 32, width: 450 }} onClick={e => e.stopPropagation()}>
            <h2 style={S.h2}>New Transaction</h2>
            <form onSubmit={handleCreate}>
              <label style={S.label}>Amount</label>
              <input required type="number" step="0.01" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} style={S.input} placeholder="0.00" />
              <label style={{ ...S.label, marginTop: 12 }}>Description</label>
              <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} style={S.input} placeholder="Invoice #1234" />
              <label style={{ ...S.label, marginTop: 12 }}>Counterparty</label>
              <input value={form.counterparty} onChange={e => setForm({ ...form, counterparty: e.target.value })} style={S.input} placeholder="Customer name" />
              <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => setShowCreate(false)} style={S.btn('#f3f4f6', '#374151')}>Cancel</button>
                <button type="submit" style={S.btn()}>Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
