import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link, Navigate, useNavigate } from 'react-router-dom'

function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const { isAuthenticated, login } = useAuth()
    const navigate = useNavigate()

    if (isAuthenticated) {
        return <Navigate to="/home" replace />
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            await login(username, password)
            navigate('/home')
        } catch (err) {
            setError('Invalid username or password.')
        }
    }

    return (
        <div className="auth-page">
            <section className="auth-card">
                <p className="eyebrow">MahjongSensei</p>
                <h2>Login</h2>
                {error && <p className="error-message">{error}</p>}
                <form className="auth-form" onSubmit={handleSubmit}>
                    <label htmlFor="login-username">Username</label>
                    <input
                        id="login-username"
                        type="text"
                        value={username}
                        autoComplete="username"
                        onChange={(e) => setUsername(e.target.value)}
                    />

                    <label htmlFor="login-password">Password</label>
                    <input
                        id="login-password"
                        type="password"
                        value={password}
                        autoComplete="current-password"
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <button className="primary-button" type="submit">Login</button>
                </form>
                <p>No account? <Link to="/register">Register</Link></p>
            </section>
        </div>
    )
}

export default Login
