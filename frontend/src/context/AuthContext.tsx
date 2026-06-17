import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../api/client'

interface User {
  id: number
  email: string
  full_name: string
  created_at: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Restore session on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('wine_token')
    const savedUser = localStorage.getItem('wine_user')
    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
    }
    setIsLoading(false)
  }, [])

  const persistAuth = (token: string, user: User) => {
    localStorage.setItem('wine_token', token)
    localStorage.setItem('wine_user', JSON.stringify(user))
    setToken(token)
    setUser(user)
  }

  const login = async (email: string, password: string) => {
    const { data } = await authApi.login(email, password)
    persistAuth(data.access_token, data.user)
  }

  const register = async (email: string, password: string, fullName: string) => {
    const { data } = await authApi.register(email, password, fullName)
    persistAuth(data.access_token, data.user)
  }

  const logout = () => {
    localStorage.removeItem('wine_token')
    localStorage.removeItem('wine_user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{
      user, token, isLoading,
      login, register, logout,
      isAuthenticated: !!token,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
