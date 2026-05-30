import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link, Navigate, useNavigate } from 'react-router-dom'

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
                <p className="eyebrow">MahjongSensei</p>
                <h2>Register</h2>
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
                <p>Already have an account? <Link to="/login">Login</Link></p>
            </section>
        </div>
    )
}

export default Register
