import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'
import HandDisplay from '../components/HandDisplay'

const FEATURES = [
    {
        to: '/tutorial',
        glyph: '學',
        title: 'Tutorial',
        body: 'Learn the tiles, melds and winning hands with short visual lessons and quizzes.',
        cta: 'Start learning →',
    },
    {
        to: '/hand-helper',
        glyph: '思',
        title: 'Hand Helper',
        body: 'Build any 14-tile hand and see exactly which tile to discard, and why.',
        cta: 'Analyse a hand →',
    },
    {
        to: '/trainer',
        glyph: '練',
        title: 'Trainer',
        body: 'Drill your discard decisions against the engine and track your accuracy.',
        cta: 'Practise now →',
    },
    {
        to: '/solo',
        glyph: '戰',
        title: 'Solo Play',
        body: 'Play a full round against three AI opponents, with claims, kongs and tai scoring.',
        cta: 'Play a game →',
    },
]

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
                        Learn the rules, test your discards, and play full rounds against
                        the computer — every feature is powered by the same Mahjong engine,
                        so the advice you learn from is the same logic you play against.
                    </p>
                </div>
            </section>

            <section className="feature-grid" aria-label="Features">
                {FEATURES.map((feature) => (
                    <Link key={feature.to} to={feature.to} className="feature-card">
                        <span className="feature-glyph" aria-hidden="true">{feature.glyph}</span>
                        <h3>{feature.title}</h3>
                        <p>{feature.body}</p>
                        <span className="feature-cta">{feature.cta}</span>
                    </Link>
                ))}
            </section>

            <section className="status-grid" aria-label="Your record" style={{ marginTop: 24 }}>
                <article className="status-card">
                    <p className="eyebrow">Games played</p>
                    <strong>{profile?.games_played ?? 0}</strong>
                    <span>Solo Play rounds finished</span>
                </article>
                <article className="status-card">
                    <p className="eyebrow">Games won</p>
                    <strong>{profile?.games_won ?? 0}</strong>
                    <span>Wins recorded on your profile</span>
                </article>
                <article className="status-card">
                    <p className="eyebrow">Win rate</p>
                    <strong>{profile?.win_rate ?? 0}%</strong>
                    <span>Updated after every game</span>
                </article>
            </section>

            <section className="demo-layout">
                <section className="demo-copy">
                    <p className="eyebrow">Warm up</p>
                    <h2>Deal a practice hand</h2>
                    <p>
                        Not sure where to start? Deal yourself a random hand and study its
                        shape — then take it to the Hand Helper to see what the engine
                        would keep.
                    </p>
                    <button className="primary-button" onClick={generateHand} disabled={isLoading}>
                        {isLoading ? 'Dealing…' : 'Deal a hand'}
                    </button>
                    {error && <p className="error-message">{error}</p>}
                </section>

                <section className="hand-panel felt-panel" aria-label="Generated Mahjong hand">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">Random hand</p>
                            <h3>{hand ? `${hand.tile_count} playable tiles` : 'No hand dealt yet'}</h3>
                        </div>
                        {hand && hand.bonus_count > 0 && (
                            <span className="bonus-count">{hand.bonus_count} bonus drawn</span>
                        )}
                    </div>

                    {hand ? (
                        <HandDisplay
                            tiles={hand.tiles}
                            melds={hand.melds || []}
                            bonusTiles={hand.bonus_tiles || []}
                        />
                    ) : (
                        <div className="empty-state">
                            <p>Deal a hand to see the tiles land on the felt.</p>
                        </div>
                    )}
                </section>
            </section>
        </AppLayout>
    )
}

export default Home
