import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { LogoMark } from '../components/Logo'

function Register() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const { isAuthenticated, register } = useAuth()
    const navigate = useNavigate()

    if (isAuthenticated) {
        return <Navigate to="/home" replace />
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            await register(username, password)
            navigate('/home')
        } catch (err) {
            setError('Registration failed. Try a different username.')
        }
    }

    return (
        <div className="auth-page">
            <section className="auth-card">
                <div className="auth-brand">
                    <LogoMark />
                    <p className="eyebrow">MahjongSensei</p>
                </div>
                <h2>Create your account</h2>
                <p className="auth-sub">Learn Singapore Mahjong from zero, one decision at a time.</p>
                {error && <p className="error-message">{error}</p>}
                <form className="auth-form" onSubmit={handleSubmit}>
                    <label htmlFor="register-username">Username</label>
                    <input
                        id="register-username"
                        type="text"
                        value={username}
                        autoComplete="username"
                        onChange={(e) => setUsername(e.target.value)}
                    />

                    <label htmlFor="register-password">Password</label>
                    <input
                        id="register-password"
                        type="password"
                        value={password}
                        autoComplete="new-password"
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <button className="primary-button" type="submit">Register</button>
                </form>
                <p className="auth-switch">Already have an account? <Link to="/login">Login</Link></p>
            </section>
        </div>
    )
}

export default Register
