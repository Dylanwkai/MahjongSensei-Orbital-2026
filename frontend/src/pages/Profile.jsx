import { useState } from 'react'
import AppLayout from '../components/AppLayout'
import { useAuth } from '../context/AuthContext'

function formatDate(value) {
    if (!value) {
        return 'Not available'
    }

    return new Intl.DateTimeFormat('en-SG', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
    }).format(new Date(value))
}

function Profile() {
    const { profile, refreshProfile } = useAuth()
    const [isRefreshing, setIsRefreshing] = useState(false)

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await refreshProfile()
        setIsRefreshing(false)
    }

    return (
        <AppLayout>
            <section className="profile-header">
                <div>
                    <p className="eyebrow">Player profile</p>
                    <h2>{profile?.username || 'MahjongSensei player'}</h2>
                    <p>
                        Your play record, updated automatically after every Solo Play game.
                        Finish a round to see your games played, wins and win rate change.
                    </p>
                </div>
                <button className="primary-button" onClick={handleRefresh} disabled={isRefreshing}>
                    {isRefreshing ? 'Refreshing...' : 'Refresh Profile'}
                </button>
            </section>

            <section className="profile-grid" aria-label="Profile details">
                <article className="profile-card">
                    <p className="eyebrow">Username</p>
                    <strong>{profile?.username || 'Loading...'}</strong>
                </article>
                <article className="profile-card">
                    <p className="eyebrow">User ID</p>
                    <strong>{profile?.user_id ?? 'Loading...'}</strong>
                </article>
                <article className="profile-card">
                    <p className="eyebrow">Joined</p>
                    <strong>{formatDate(profile?.created_at)}</strong>
                </article>
                <article className="profile-card">
                    <p className="eyebrow">Session</p>
                    <strong>Authenticated</strong>
                </article>
            </section>

            <section className="stats-panel">
                <div className="section-heading">
                    <p className="eyebrow">Solo Play record</p>
                    <h2>Your game history</h2>
                </div>
                <div className="stats-grid">
                    <article>
                        <span>Games played</span>
                        <strong>{profile?.games_played ?? 0}</strong>
                    </article>
                    <article>
                        <span>Games won</span>
                        <strong>{profile?.games_won ?? 0}</strong>
                    </article>
                    <article>
                        <span>Win rate</span>
                        <strong>{profile?.win_rate ?? 0}%</strong>
                    </article>
                </div>
            </section>
        </AppLayout>
    )
}

export default Profile
