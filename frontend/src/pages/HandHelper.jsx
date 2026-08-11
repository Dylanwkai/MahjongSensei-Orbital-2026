import { useEffect, useMemo, useState } from 'react'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'
import TileCard, { TileFace } from '../components/TileCard'

const NUMBERED_SUITS = [
    { suit: 'bamboo', label: 'Bamboo', code: 'B' },
    { suit: 'circles', label: 'Circles', code: 'C' },
    { suit: 'characters', label: 'Characters', code: 'K' },
]

const HONOUR_TILES = [
    { suit: 'honour', value: 'east', code: 'Heast', label: 'east' },
    { suit: 'honour', value: 'south', code: 'Hsouth', label: 'south' },
    { suit: 'honour', value: 'west', code: 'Hwest', label: 'west' },
    { suit: 'honour', value: 'north', code: 'Hnorth', label: 'north' },
    { suit: 'honour', value: 'red', code: 'Hred', label: 'red' },
    { suit: 'honour', value: 'green', code: 'Hgreen', label: 'green' },
    { suit: 'honour', value: 'white', code: 'Hwhite', label: 'white' },
]

function buildTileOption(suit, value, codePrefix) {
    return {
        suit,
        value,
        code: `${codePrefix}${value}`,
        label: `${value} ${suit}`,
    }
}

function getTileKey(tile) {
    return `${tile.suit}-${tile.value}`
}

function TileButton({ tile, count, onClick, disabled }) {
    return (
        <button
            className={`tile picker-tile tile-${tile.suit}`}
            type="button"
            onClick={() => onClick(tile)}
            disabled={disabled}
            title={tile.label}
        >
            <TileFace tile={tile} />
            {count > 0 && <span className="tile-count">{count}/4</span>}
        </button>
    )
}

function SelectedTile({ tile, onRemove }) {
    return (
        <button
            className={`tile tile-${tile.suit}`}
            type="button"
            onClick={onRemove}
            aria-label={`Remove ${tile.label}`}
            title={`Remove ${tile.label}`}
        >
            <TileFace tile={tile} />
        </button>
    )
}

function HandHelper() {
    const [selectedTiles, setSelectedTiles] = useState([])
    const [recommendation, setRecommendation] = useState(null)
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [winResult, setWinResult] = useState(null)

    const tileCounts = useMemo(() => {
        return selectedTiles.reduce((counts, tile) => {
            const key = getTileKey(tile)
            counts[key] = (counts[key] || 0) + 1
            return counts
        }, {})
    }, [selectedTiles])

    const addTile = (tile) => {
        const count = tileCounts[getTileKey(tile)] || 0

        if (selectedTiles.length >= 14 || count >= 4) {
            return
        }

        setSelectedTiles([...selectedTiles, tile])
        setRecommendation(null)
        setError('')
    }

    const removeTile = (indexToRemove) => {
        setSelectedTiles(selectedTiles.filter((_, index) => index !== indexToRemove))
        setRecommendation(null)
        setError('')
    }

    const clearHand = () => {
        setSelectedTiles([])
        setRecommendation(null)
        setError('')
    }

    const recommendDiscard = async () => {
        if (selectedTiles.length !== 14) {
            setError('Choose exactly 14 tiles before asking for a recommendation.')
            return
        }

        setIsLoading(true)
        setError('')
        setRecommendation(null)

        try {
            const response = await api.post('/api/game/recommend-discard/', {
                tiles: selectedTiles.map(({ suit, value }) => ({ suit, value })),
            })
            setRecommendation(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not recommend a discard. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    // Whenever a full 14-tile hand is selected, automatically ask the backend
    // whether it is already a complete winning hand. Below 14 tiles there is
    // nothing to check, so the banner is cleared.
    useEffect(() => {
        if (selectedTiles.length !== 14) {
            setWinResult(null)
            return
        }

        let cancelled = false
        const checkWin = async () => {
            try {
                const response = await api.post('/api/game/check-win/', {
                    tiles: selectedTiles.map(({ suit, value }) => ({ suit, value })),
                })
                if (!cancelled) {
                    setWinResult(response.data)
                }
            } catch (err) {
                if (!cancelled) {
                    setWinResult(null)
                }
            }
        }

        checkWin()
        return () => {
            cancelled = true
        }
    }, [selectedTiles])

    return (
        <AppLayout>
            <section className="profile-header">
                <div>
                    <p className="eyebrow">Hand Helper</p>
                    <h2>Find a recommended discard</h2>
                    <p>
                        Build a 14-tile hand, then ask the backend evaluator which discard
                        leaves the strongest remaining structure.
                    </p>
                </div>
                <div className="hand-count">
                    <strong>{selectedTiles.length}/14</strong>
                    <span>tiles selected</span>
                </div>
            </section>

            <section className="helper-layout">
                <section className="tile-picker-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">Tile picker</p>
                            <h3>Select your hand</h3>
                        </div>
                    </div>

                    {NUMBERED_SUITS.map(({ suit, label, code }) => (
                        <div className="picker-group" key={suit}>
                            <p className="eyebrow">{label}</p>
                            <div className="picker-grid">
                                {Array.from({ length: 9 }, (_, index) => {
                                    const tile = buildTileOption(suit, index + 1, code)
                                    const count = tileCounts[getTileKey(tile)] || 0

                                    return (
                                        <TileButton
                                            key={tile.code}
                                            tile={tile}
                                            count={count}
                                            onClick={addTile}
                                            disabled={selectedTiles.length >= 14 || count >= 4}
                                        />
                                    )
                                })}
                            </div>
                        </div>
                    ))}

                    <div className="picker-group">
                        <p className="eyebrow">Honours</p>
                        <div className="picker-grid honour-picker-grid">
                            {HONOUR_TILES.map((tile) => {
                                const count = tileCounts[getTileKey(tile)] || 0

                                return (
                                    <TileButton
                                        key={tile.code}
                                        tile={tile}
                                        count={count}
                                        onClick={addTile}
                                        disabled={selectedTiles.length >= 14 || count >= 4}
                                    />
                                )
                            })}
                        </div>
                    </div>
                </section>

                <section className="helper-result-panel felt-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">Current hand</p>
                            <h3>{selectedTiles.length === 14 ? 'Ready to evaluate' : 'Keep selecting tiles'}</h3>
                        </div>
                        <button className="secondary-button" type="button" onClick={clearHand}>
                            Clear
                        </button>
                    </div>

                    {selectedTiles.length > 0 ? (
                        <div className="selected-grid">
                            {selectedTiles.map((tile, index) => (
                                <SelectedTile
                                    key={`${tile.code}-${index}`}
                                    tile={tile}
                                    onRemove={() => removeTile(index)}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p>Select tiles from the picker to build your hand.</p>
                        </div>
                    )}

                    {winResult?.is_winning && (
                        <section className="win-banner" aria-label="Winning hand">
                            <p className="eyebrow">Winning hand!</p>
                            <h3>{winResult.description}</h3>
                            <p>
                                This hand is already complete - no discard needed. You can
                                still ask for a recommendation below to explore alternatives.
                            </p>
                        </section>
                    )}

                    <div className="helper-actions">
                        <button
                            className="primary-button"
                            type="button"
                            onClick={recommendDiscard}
                            disabled={selectedTiles.length !== 14 || isLoading}
                        >
                            {isLoading ? 'Evaluating...' : 'Recommend Discard'}
                        </button>
                        {error && <p className="error-message">{error}</p>}
                    </div>

                    {recommendation && (
                        <section className="recommendation-panel" aria-label="Discard recommendation">
                            <p className="eyebrow">Recommended discard</p>
                            <div className="recommendation-content">
                                <TileCard tile={recommendation.discard} size="lg" />
                                <div>
                                    <h3>{recommendation.discard.label}</h3>
                                    <p>{recommendation.reasoning}</p>
                                    <span>Score: {recommendation.score}</span>
                                </div>
                            </div>
                        </section>
                    )}
                </section>
            </section>
        </AppLayout>
    )
}

export default HandHelper
