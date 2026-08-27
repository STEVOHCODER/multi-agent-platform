import { useState, useEffect, createContext, useContext } from 'react'
import * as api from '../api/client'

const WsCtx = createContext(null)
export const useWs = () => useContext(WsCtx)

export function WsProvider({ children }) {
  const [workspaces, setWorkspaces] = useState([])
  const [current, setCurrent] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.workspaces.list().then(ws => {
      setWorkspaces(ws)
      const saved = localStorage.getItem('ws_id')
      setCurrent(ws.find(w => w.id === saved) || ws[0] || null)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const switchWs = ws => { setCurrent(ws); localStorage.setItem('ws_id', ws.id) }
  const createWs = async name => {
    const ws = await api.workspaces.create({ name })
    setWorkspaces(p => [...p, ws])
    setCurrent(ws)
    return ws
  }

  return <WsCtx.Provider value={{ workspaces, current, switchWs, createWs, loading }}>{children}</WsCtx.Provider>
}
