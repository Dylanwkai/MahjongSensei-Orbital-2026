import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

function Home() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <div>
            <h2>Welcome, {user}!</h2>
            <p>You are logged in.</p>
            <button onClick={handleLogout}>Logout</button>
        </div>
    )
}

export default Home