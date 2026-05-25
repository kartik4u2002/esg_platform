import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { login as loginApi } from '../api/endpoints'
import { setAccessToken, clearAuthData } from '../api/client'

interface User {
  id: number
  username: string
  email: string
  role: string
  organization: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('esg_user')
    return stored ? JSON.parse(stored) : null
  })
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  // Restore access token from refresh on mount
  useEffect(() => {
    const refreshTokenStr = localStorage.getItem('esg_refresh_token')
    if (refreshTokenStr && !user) {
      // If we have a refresh token but no user, try to restore
      // The interceptor will handle token refresh on first API call
    }
  }, [user])

  const isAuthenticated = !!user

  const login = useCallback(
    async (email: string, password: string) => {
      setIsLoading(true)
      try {
        const response = await loginApi(email, password)
        const { access, refresh } = response.data

        setAccessToken(access)
        localStorage.setItem('esg_refresh_token', refresh)

        // Decode user info from JWT access token
        const payload = JSON.parse(atob(access.split('.')[1]))
        const userData: User = {
          id: payload.user_id || payload.sub || 0,
          username: payload.username || email.split('@')[0],
          email: payload.email || email,
          role: payload.role || 'analyst',
          organization: payload.organization || 'ESG Corp',
        }

        setUser(userData)
        localStorage.setItem('esg_user', JSON.stringify(userData))
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  const logout = useCallback(() => {
    clearAuthData()
    setUser(null)
    navigate('/login')
  }, [navigate])

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default useAuth
