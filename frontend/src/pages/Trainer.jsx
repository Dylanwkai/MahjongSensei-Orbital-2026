import { useCallback, useEffect, useState } from 'react'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'
import TileCard, { TileFace } from '../components/TileCard'

function tileKey(tile, index) {
    return `${tile.code}-${index}`
}

function formatTime(value) {
    if (!value) {
        return ''
    }
    return new Intl.DateTimeFormat('en-SG', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
    }).format(new Date(value))
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
            title={tile.label}
        >
            <TileFace tile={tile} />
        </button>
    )
}

function ResultTile({ tile }) {
    if (!tile) {
        return null
    }
    return <TileCard tile={tile} />
}

function HistoryEntry({ attempt }) {
    return (
        <article className="history-entry">
            <div className="history-entry-head">
                <span className={`history-badge ${attempt.is_correct ? 'history-ok' : 'history-miss'}`}>
                    {attempt.is_correct ? 'Optimal' : 'Missed'}
                </span>
                {attempt.difficulty && (
                    <span className="history-diff">{attempt.difficulty}</span>
                )}
                <span className="history-time">{formatTime(attempt.created_at)}</span>
            </div>

            {attempt.hand?.length > 0 && (
                <div className="meld-row history-hand">
                    {attempt.hand.map((tile, index) => (
                        <TileCard key={`${tile.code}-${index}`} tile={tile} size="sm" />
                    ))}
                </div>
            )}

            <div className="history-entry-foot">
                <div className="history-pick">
                    <span className="eyebrow">Your discard</span>
                    {attempt.your_discard ? <TileCard tile={attempt.your_discard} size="sm" /> : <span>-</span>}
                </div>
                <div className="history-pick">
                    <span className="eyebrow">
                        {(attempt.optimal_discards?.length || 0) > 1 ? 'Optimal discards' : 'Best discard'}
                    </span>
                    {(() => {
                        const optimal = attempt.optimal_discards
                            || (attempt.correct_discard ? [attempt.correct_discard] : [])
                        if (optimal.length === 0) {
                            return <span>-</span>
                        }
                        return (
                            <div className="meld-row" style={{ flexWrap: 'wrap' }}>
                                {optimal.map((tile, index) => (
                                    <TileCard key={`${tile.code}-${index}`} tile={tile} size="sm" />
                                ))}
                            </div>
                        )
                    })()}
                </div>
                <div className="history-pick history-scores">
                    <span className="eyebrow">Score</span>
                    <strong>{attempt.your_score} / {attempt.best_score}</strong>
                </div>
            </div>
        </article>
    )
}

function Trainer() {
    const [tiles, setTiles] = useState([])
    const [bonusTiles, setBonusTiles] = useState([])
    const [moveId, setMoveId] = useState(null)
    const [selectedIndex, setSelectedIndex] = useState(null)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [difficulty, setDifficulty] = useState('medium')
    const [history, setHistory] = useState({
        total_attempts: 0,
        correct: 0,
        accuracy: 0,
        attempts: [],
    })

    const loadHistory = useCallback(async () => {
        try {
            const response = await api.get('/api/game/trainer/history/')
            setHistory(response.data)
        } catch (err) {
            // A missing history is not fatal; the log just stays empty.
        }
    }, [])

    const loadChallenge = useCallback(async (level) => {
        setIsLoading(true)
        setError('')
        setResult(null)
        setSelectedIndex(null)

        try {
            const response = await api.post('/api/game/trainer/new/', {
                difficulty: level || difficulty,
            })
            setTiles(response.data.tiles)
            setBonusTiles(response.data.bonus_tiles || [])
            setMoveId(response.data.move_id)
        } catch (err) {
            setError('Could not load a new hand. Please log in again and retry.')
        } finally {
            setIsLoading(false)
        }
    }, [difficulty])

    const changeDifficulty = (level) => {
        if (level === difficulty || isLoading) {
            return
        }
        setDifficulty(level)
        loadChallenge(level)
    }

    useEffect(() => {
        loadChallenge('medium')
        loadHistory()
        // Only deal once on mount; difficulty changes deal their own hand.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

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
            loadHistory()  // refresh the persisted log and accuracy
        } catch (err) {
            setError(err.response?.data?.error || 'Could not score that discard. Please try again.')
        } finally {
            setIsSubmitting(false)
        }
    }

    const accuracy = Math.round(history.accuracy || 0)

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
                    <strong>{history.correct}/{history.total_attempts}</strong>
                    <span>{accuracy}% optimal</span>
                </div>
            </section>

            <section className="helper-layout">
                <section className="tile-picker-panel felt-panel">
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
                            onClick={() => loadChallenge()}
                            disabled={isLoading}
                        >
                            {result ? 'Next hand' : 'New hand'}
                        </button>
                    </div>

                    <div className="difficulty-toggle" role="group" aria-label="Difficulty">
                        {['easy', 'medium', 'hard'].map((level) => (
                            <button
                                key={level}
                                type="button"
                                className={`difficulty-option${difficulty === level ? ' difficulty-active' : ''}`}
                                onClick={() => changeDifficulty(level)}
                                disabled={isLoading}
                                aria-pressed={difficulty === level}
                            >
                                {level.charAt(0).toUpperCase() + level.slice(1)}
                            </button>
                        ))}
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

                    {bonusTiles.length > 0 && (
                        <div className="bonus-section">
                            <p className="eyebrow">Bonus tiles drawn ({bonusTiles.length})</p>
                            <div className="meld-row">
                                {bonusTiles.map((tile, index) => (
                                    <TileCard key={`${tile.code}-${index}`} tile={tile} size="sm" />
                                ))}
                            </div>
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
                            {(() => {
                                const optimal = result.optimal_discards
                                    || (result.correct_discard ? [result.correct_discard] : [])
                                const many = optimal.length > 1
                                return (
                                    <>
                                        <p className="eyebrow">
                                            {result.is_correct
                                                ? (many ? 'You played an optimal discard' : 'You played the best discard')
                                                : (many ? `Optimal discards (${optimal.length})` : 'Best discard was')}
                                        </p>
                                        <div className="meld-row" style={{ flexWrap: 'wrap' }}>
                                            {optimal.map((tile, index) => (
                                                <ResultTile key={`${tile.code}-${index}`} tile={tile} />
                                            ))}
                                        </div>
                                        <p style={{ marginTop: 12 }}>{result.feedback}</p>
                                        <span>
                                            Your score: {result.your_score} &middot; Best: {result.best_score}
                                        </span>
                                    </>
                                )
                            })()}

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

            <section className="tile-picker-panel" style={{ marginTop: 24 }}>
                <div className="panel-heading">
                    <div>
                        <p className="eyebrow">Hand history</p>
                        <h3>
                            {history.total_attempts > 0
                                ? `${history.total_attempts} attempts · ${accuracy}% optimal`
                                : 'Your past attempts'}
                        </h3>
                    </div>
                </div>

                {history.attempts.length > 0 ? (
                    <div className="history-list">
                        {history.attempts.map((attempt) => (
                            <HistoryEntry key={attempt.move_id} attempt={attempt} />
                        ))}
                    </div>
                ) : (
                    <div className="empty-state">
                        <p>No attempts logged yet. Submit a discard to start your history.</p>
                    </div>
                )}
            </section>
        </AppLayout>
    )
}

export default Trainer
