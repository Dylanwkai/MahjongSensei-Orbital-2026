import { useCallback, useEffect, useState } from 'react'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'

function tileKey(tile, index) {
    return `${tile.code}-${index}`
}

function ChallengeTile({ tile, index, isSelected, isDisabled, onClick }) {
    const selectedClass = isSelected ? ' selected-tile' : ''
    return (
        <button
            className={`tile picker-tile tile-${tile.suit}${selectedClass}`}
            type="button"
            onClick={() => onClick(index)}
            disabled={isDisabled}
            aria-pressed={isSelected}
        >
            <span className="tile-code">{tile.code}</span>
            <span className="tile-label">{tile.label}</span>
        </button>
    )
}

function ResultTile({ tile }) {
    if (!tile) {
        return null
    }
    return (
        <div className={`tile tile-${tile.suit}`}>
            <span className="tile-code">{tile.code}</span>
            <span className="tile-label">{tile.label}</span>
        </div>
    )
}

function Trainer() {
    const [tiles, setTiles] = useState([])
    const [moveId, setMoveId] = useState(null)
    const [selectedIndex, setSelectedIndex] = useState(null)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [stats, setStats] = useState({ attempts: 0, correct: 0 })

    const loadChallenge = useCallback(async () => {
        setIsLoading(true)
        setError('')
        setResult(null)
        setSelectedIndex(null)

        try {
            const response = await api.post('/api/game/trainer/new/')
            setTiles(response.data.tiles)
            setMoveId(response.data.move_id)
        } catch (err) {
            setError('Could not load a new hand. Please log in again and retry.')
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        loadChallenge()
    }, [loadChallenge])

    const selectTile = (index) => {
        if (result) {
            return
        }
        setSelectedIndex(index === selectedIndex ? null : index)
    }

    const submitDiscard = async () => {
        if (selectedIndex === null || moveId === null) {
            setError('Pick a tile to discard first.')
            return
        }

        const chosen = tiles[selectedIndex]
        setIsSubmitting(true)
        setError('')

        try {
            const response = await api.post('/api/game/trainer/submit/', {
                move_id: moveId,
                discard: { suit: chosen.suit, value: chosen.value },
            })
            setResult(response.data)
            setStats((prev) => ({
                attempts: prev.attempts + 1,
                correct: prev.correct + (response.data.is_correct ? 1 : 0),
            }))
        } catch (err) {
            setError(err.response?.data?.error || 'Could not score that discard. Please try again.')
        } finally {
            setIsSubmitting(false)
        }
    }

    const accuracy = stats.attempts
        ? Math.round((stats.correct / stats.attempts) * 100)
        : 0

    return (
        <AppLayout>
            <section className="profile-header">
                <div>
                    <p className="eyebrow">Trainer</p>
                    <h2>Spot the best discard</h2>
                    <p>
                        You are dealt a 14-tile hand. Pick the tile you would discard, then
                        the engine scores your choice against the optimal play and explains why.
                    </p>
                </div>
                <div className="hand-count">
                    <strong>{stats.correct}/{stats.attempts}</strong>
                    <span>{accuracy}% optimal</span>
                </div>
            </section>

            <section className="helper-layout">
                <section className="tile-picker-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">Your hand</p>
                            <h3>
                                {isLoading
                                    ? 'Dealing...'
                                    : result
                                        ? 'Result below'
                                        : 'Tap the tile to discard'}
                            </h3>
                        </div>
                        <button
                            className="secondary-button"
                            type="button"
                            onClick={loadChallenge}
                            disabled={isLoading}
                        >
                            {result ? 'Next hand' : 'New hand'}
                        </button>
                    </div>

                    {tiles.length > 0 ? (
                        <div className="picker-grid">
                            {tiles.map((tile, index) => (
                                <ChallengeTile
                                    key={tileKey(tile, index)}
                                    tile={tile}
                                    index={index}
                                    isSelected={selectedIndex === index}
                                    isDisabled={Boolean(result) || isLoading}
                                    onClick={selectTile}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p>{isLoading ? 'Requesting a hand from Django...' : 'No hand yet.'}</p>
                        </div>
                    )}

                    <div className="helper-actions">
                        <button
                            className="primary-button"
                            type="button"
                            onClick={submitDiscard}
                            disabled={selectedIndex === null || Boolean(result) || isSubmitting || isLoading}
                        >
                            {isSubmitting ? 'Scoring...' : 'Submit Discard'}
                        </button>
                        {error && <p className="error-message">{error}</p>}
                    </div>
                </section>

                <section className="helper-result-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">Feedback</p>
                            <h3>{result ? (result.is_correct ? 'Optimal!' : 'Keep practising') : 'Awaiting your discard'}</h3>
                        </div>
                    </div>

                    {result ? (
                        <section className="recommendation-panel" aria-label="Discard feedback">
                            <p className="eyebrow">
                                {result.is_correct ? 'You played the best discard' : 'Best discard was'}
                            </p>
                            <div className="recommendation-content">
                                <ResultTile tile={result.correct_discard} />
                                <div>
                                    <h3>{result.correct_discard?.label}</h3>
                                    <p>{result.feedback}</p>
                                    <span>
                                        Your score: {result.your_score} &middot; Best: {result.best_score}
                                    </span>
                                </div>
                            </div>

                            {!result.is_correct && (
                                <div className="your-pick">
                                    <p className="eyebrow">Your discard</p>
                                    <ResultTile tile={result.your_discard} />
                                </div>
                            )}
                        </section>
                    ) : (
                        <div className="empty-state">
                            <p>Select a tile and submit to see how your decision compares.</p>
                        </div>
                    )}
                </section>
            </section>
        </AppLayout>
    )
}

export default Trainer
