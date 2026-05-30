import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'

function Tile({ tile }) {
    return (
        <li className={`tile tile-${tile.suit}`}>
            <span className="tile-code">{tile.code}</span>
            <span className="tile-label">{tile.label}</span>
        </li>
    )
}

function Home() {
    const { user, profile } = useAuth()
    const [hand, setHand] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')

    const generateHand = async () => {
        setIsLoading(true)
        setError('')

        try {
            const response = await api.get('/api/game/random-hand/')
            setHand(response.data)
        } catch (err) {
            setError('Could not generate a hand. Please log in again and retry.')
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <AppLayout>
            <section className="dashboard-hero">
                <div>
                    <p className="eyebrow">Welcome back, {user || 'player'}</p>
                    <h2>Build Mahjong understanding one decision at a time.</h2>
                    <p>
                        This base app now has authentication, protected routes, a profile-backed
                        session, and a backend-powered Mahjong hand generator. The next features
                        can plug into this structure instead of starting from scratch.
                    </p>
                </div>
                <div className="hero-status">
                    <span className="status-dot" aria-hidden="true" />
                    Backend connected
                </div>
            </section>

            <section className="status-grid" aria-label="Project status">
                <article className="status-card">
                    <p className="eyebrow">Current user</p>
                    <strong>{profile?.username || user || 'Player'}</strong>
                    <span>JWT session active</span>
                </article>
                <article className="status-card">
                    <p className="eyebrow">Games played</p>
                    <strong>{profile?.games_played ?? 0}</strong>
                    <span>Ready for dashboard tracking</span>
                </article>
                <article className="status-card">
                    <p className="eyebrow">Milestone 1</p>
                    <strong>Proof ready</strong>
                    <span>React + Django + Python engine</span>
                </article>
            </section>

            <section className="demo-layout">
                <section className="demo-copy">
                    <p className="eyebrow">Technical proof</p>
                    <h2>Generate a Mahjong hand from Django</h2>
                    <p>
                        This page proves the React frontend can call the Django API,
                        pass authentication, run Python Mahjong logic, and render the
                        result in the browser.
                    </p>
                    <button className="primary-button" onClick={generateHand} disabled={isLoading}>
                        {isLoading ? 'Generating...' : 'Generate Hand'}
                    </button>
                    {error && <p className="error-message">{error}</p>}
                </section>

                <section className="hand-panel" aria-label="Generated Mahjong hand">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">Random hand</p>
                            <h3>{hand ? `${hand.tile_count} playable tiles` : 'No hand generated yet'}</h3>
                        </div>
                        {hand && hand.bonus_count > 0 && (
                            <span className="bonus-count">{hand.bonus_count} bonus drawn</span>
                        )}
                    </div>

                    {hand ? (
                        <>
                            <ul className="tile-grid">
                                {hand.tiles.map((tile, index) => (
                                    <Tile key={`${tile.code}-${index}`} tile={tile} />
                                ))}
                            </ul>

                            {hand.bonus_tiles.length > 0 && (
                                <div className="bonus-section">
                                    <p className="eyebrow">Bonus tiles</p>
                                    <ul className="bonus-list">
                                        {hand.bonus_tiles.map((tile, index) => (
                                            <Tile key={`${tile.code}-${index}`} tile={tile} />
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="empty-state">
                            <p>Click generate to request a hand from Django.</p>
                        </div>
                    )}
                </section>
            </section>

            <section className="roadmap-section">
                <div className="section-heading">
                    <p className="eyebrow">Feature base</p>
                    <h2>What this unlocks next</h2>
                </div>
                <div className="feature-grid">
                    <article className="feature-card">
                        <h3>Rules Guide</h3>
                        <p>Use the same layout and profile session to store tutorial progress.</p>
                    </article>
                    <article className="feature-card">
                        <h3>Hand Helper</h3>
                        <p>Reuse tile serialization and API patterns for user-submitted hands.</p>
                    </article>
                    <article className="feature-card">
                        <h3>Trainer</h3>
                        <p>Reuse generated hands, then add best-discard logic and feedback.</p>
                    </article>
                    <article className="feature-card">
                        <h3>SoloPlay</h3>
                        <p>Build later on the engine once validation and valuation are stable.</p>
                    </article>
                </div>
            </section>
        </AppLayout>
    )
}

export default Home
