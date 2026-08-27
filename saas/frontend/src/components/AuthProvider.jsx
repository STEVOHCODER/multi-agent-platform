import { useState, useEffect, createContext, useContext } from 'react'
import * as api from '../api/client'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    const t = localStorage.getItem('token')
    if (t) api.auth.me().then(setUser).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false))
    else setLoading(false)
  }, [])
  const login = async d => { const r = await api.auth.login(d); localStorage.setItem('token', r.access_token); setUser(r.user) }
  const register = async d => { const r = await api.auth.register(d); localStorage.setItem('token', r.access_token); setUser(r.user) }
  const logout = () => { localStorage.removeItem('token'); setUser(null) }
  return <AuthCtx.Provider value={{ user, login, register, logout, loading }}>{children}</AuthCtx.Provider>
}

export function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>Loading...</div>
  return user ? children : <Navigate to="/login" />
}
