import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api/axios'

const AuthContext = createContext()

export function AuthProvider({ children }) {
    const [accessToken, setAccessToken] = useState(() => localStorage.getItem('access_token'))
    const [user, setUser] = useState(() => localStorage.getItem('username'))
    const [profile, setProfile] = useState(null)
    const [isAuthReady, setIsAuthReady] = useState(false)

    const clearSession = useCallback(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('username')
        setAccessToken(null)
        setUser(null)
        setProfile(null)
    }, [])

    const refreshProfile = useCallback(async () => {
        const token = localStorage.getItem('access_token')
        if (!token) {
            clearSession()
            return null
        }

        try {
            const response = await api.get('/api/users/profile/')
            setProfile(response.data)
            setUser(response.data.username)
            localStorage.setItem('username', response.data.username)
            return response.data
        } catch (err) {
            clearSession()
            return null
        }
    }, [clearSession])

    useEffect(() => {
        let isMounted = true

        async function initialiseSession() {
            if (localStorage.getItem('access_token')) {
                await refreshProfile()
            }

            if (isMounted) {
                setIsAuthReady(true)
            }
        }

        initialiseSession()

        return () => {
            isMounted = false
        }
    }, [refreshProfile])

    const login = useCallback(async (username, password) => {
        const response = await api.post('/api/token/', { username, password })
        localStorage.setItem('access_token', response.data.access)
        localStorage.setItem('refresh_token', response.data.refresh)
        localStorage.setItem('username', username)
        setAccessToken(response.data.access)
        setUser(username)
        await refreshProfile()
    }, [refreshProfile])

    const logout = useCallback(() => {
        clearSession()
    }, [clearSession])

    const register = useCallback(async (username, password) => {
        await api.post('/api/users/register/', { username, password })
        await login(username, password)  // auto login after register
    }, [login])

    const value = useMemo(() => ({
        user,
        profile,
        isAuthReady,
        isAuthenticated: Boolean(accessToken),
        login,
        logout,
        register,
        refreshProfile,
    }), [accessToken, isAuthReady, login, logout, profile, refreshProfile, register, user])

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    return useContext(AuthContext)
}
