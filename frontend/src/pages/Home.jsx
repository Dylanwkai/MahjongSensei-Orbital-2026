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
            <section className="home-hero">
                <span className="home-hero-glyph" aria-hidden="true">師</span>
                <div className="home-hero-content">
                    <p className="eyebrow">Welcome back, {user || 'player'}</p>
                    <h1 className="home-hero-title">
                        Build Mahjong understanding, one decision at a time.
                    </h1>
                    <p className="home-hero-sub">
                        Learn the rules, sharpen your discards, and play full rounds against
                        the computer — every feature runs on the same Mahjong engine.
                    </p>
                    <div className="home-stats" aria-label="Your record">
                        <div className="home-stat">
                            <strong>{profile?.games_played ?? 0}</strong>
                            <span>Played</span>
                        </div>
                        <div className="home-stat">
                            <strong>{profile?.games_won ?? 0}</strong>
                            <span>Won</span>
                        </div>
                        <div className="home-stat">
                            <strong>{profile?.win_rate ?? 0}%</strong>
                            <span>Win rate</span>
                        </div>
                    </div>
                </div>
            </section>

            <div className="home-section-head">
                <h2>Explore</h2>
                <p>New here? Work through them in order.</p>
            </div>

            <nav className="feature-flow" aria-label="Features">
                {FEATURES.map((feature, index) => (
                    <Link key={feature.to} to={feature.to} className="feature-item">
                        <span className="feature-num">{String(index + 1).padStart(2, '0')}</span>
                        <span className="feature-glyph" aria-hidden="true">{feature.glyph}</span>
                        <span className="feature-body">
                            <h3>{feature.title}</h3>
                            <p>{feature.body}</p>
                        </span>
                        <span className="feature-arrow" aria-hidden="true">→</span>
                    </Link>
                ))}
            </nav>

            <section className="demo-layout">
                <div className="demo-copy">
                    <p className="eyebrow">Warm up</p>
                    <h2>Deal a practice hand</h2>
                    <p>
                        Not sure where to start? Deal yourself a random hand and study its
                        shape — then take it to the Hand Helper to see what the engine would keep.
                    </p>
                    <button className="primary-button" onClick={generateHand} disabled={isLoading}>
                        {isLoading ? 'Dealing…' : 'Deal a hand'}
                    </button>
                    {error && <p className="error-message">{error}</p>}
                </div>

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
