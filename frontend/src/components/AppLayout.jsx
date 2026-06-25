import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

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
                <div className="brand-block">
                    <p className="eyebrow">MahjongSensei</p>
                    <h1>Learning dashboard</h1>
                </div>

                <nav className="main-nav" aria-label="Main navigation">
                    <NavLink to="/home">Home</NavLink>
                    <NavLink to="/hand-helper">Hand Helper</NavLink>
                    <NavLink to="/profile">Profile</NavLink>
                </nav>

                <div className="session-controls">
                    <span>{user || 'Player'}</span>
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
