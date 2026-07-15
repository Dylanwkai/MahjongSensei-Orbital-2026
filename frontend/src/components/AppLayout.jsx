import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Logo from './Logo'

function AppLayout({ children }) {
    const { user, logout } = useAuth()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <div className="app-shell">
            <header className="topbar">
                <NavLink to="/home" style={{ textDecoration: 'none' }}>
                    <Logo />
                </NavLink>

                <nav className="main-nav" aria-label="Main navigation">
                    <NavLink to="/home">Home</NavLink>
                    <NavLink to="/tutorial">Tutorial</NavLink>
                    <NavLink to="/hand-helper">Hand Helper</NavLink>
                    <NavLink to="/trainer">Trainer</NavLink>
                    <NavLink to="/solo">Solo Play</NavLink>
                    <NavLink to="/profile">Profile</NavLink>
                </nav>

                <div className="session-controls">
                    <span className="user-chip">{user || 'Player'}</span>
                    <button className="secondary-button" onClick={handleLogout}>
                        Logout
                    </button>
                </div>
            </header>

            <main className="page-content">
                {children}
            </main>
        </div>
    )
}

export default AppLayout
