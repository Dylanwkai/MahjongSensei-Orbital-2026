import { useCallback, useEffect, useMemo, useState } from 'react'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'
import TileCard from '../components/TileCard'

function MeldRow({ melds }) {
    if (!melds || melds.length === 0) {
        return null
    }
    return (
        <div className="meld-row">
            {melds.map((meld, mi) => (
                <div
                    key={mi}
                    className={`meld-group ${meld.claimed ? 'meld-claimed' : 'meld-concealed'}`}
                >
                    <div className="meld-tiles">
                        {meld.tiles.map((tile, ti) => (
                            <TileCard key={`${tile.code}-${ti}`} tile={tile} size="sm" />
                        ))}
                    </div>
                    <span className="meld-tag">{meld.kind}</span>
                </div>
            ))}
        </div>
    )
}

function Opponent({ player }) {
    return (
        <article className="status-card">
            <p className="eyebrow">{player.seat_wind}</p>
            <strong>{player.name}</strong>
            <span>{player.tile_count} tiles in hand</span>
            <MeldRow melds={player.melds} />
            {player.bonus_tiles.length > 0 && (
                <div className="meld-row" style={{ marginTop: 8 }}>
                    {player.bonus_tiles.map((tile, i) => (
                        <TileCard key={`${tile.code}-${i}`} tile={tile} size="sm" />
                    ))}
                </div>
            )}
        </article>
    )
}

function ClaimPrompt({ claim, onClaim, onPass, disabled }) {
    const suit = claim.tile.suit
    return (
        <section className="tile-picker-panel claim-prompt" style={{ marginTop: 24 }}>
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">Claim available</p>
                    <h3 style={{ textTransform: 'capitalize' }}>{claim.from_seat} discarded {claim.tile.label}</h3>
                </div>
                <div className="meld-row">
                    <TileCard tile={claim.tile} size="sm" />
                </div>
            </div>
            <div className="helper-actions">
                <div className="meld-row" style={{ flexWrap: 'wrap' }}>
                    {claim.actions.includes('win') && (
                        <button className="primary-button" type="button" disabled={disabled} onClick={() => onClaim('win')}>
                            Win
                        </button>
                    )}
                    {claim.actions.includes('kong') && (
                        <button className="secondary-button" type="button" disabled={disabled} onClick={() => onClaim('kong')}>
                            Kong
                        </button>
                    )}
                    {claim.actions.includes('pong') && (
                        <button className="secondary-button" type="button" disabled={disabled} onClick={() => onClaim('pong')}>
                            Pong
                        </button>
                    )}
                    {claim.actions.includes('chow') && (
                        (claim.chow_options && claim.chow_options.length > 0
                            ? claim.chow_options
                            : [undefined]
                        ).map((low, i) => (
                            <button
                                key={`chow-${low ?? i}`}
                                className="secondary-button"
                                type="button"
                                disabled={disabled}
                                onClick={() => onClaim('chow', low)}
                            >
                                {low !== undefined && ['bamboo', 'circles', 'characters'].includes(suit)
                                    ? `Chow ${low}-${low + 1}-${low + 2}`
                                    : 'Chow'}
                            </button>
                        ))
                    )}
                    <button className="secondary-button" type="button" disabled={disabled} onClick={onPass}>
                        Pass
                    </button>
                </div>
            </div>
        </section>
    )
}

function WinSummary({ win }) {
    return (
        <section className="tile-picker-panel win-summary" style={{ marginTop: 24 }}>
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">Round over</p>
                    <h3 style={{ textTransform: 'capitalize' }}>
                        {win.winner_name} wins by {(win.win_type || '').replace('_', ' ')} — {win.total_tai} tai
                    </h3>
                    <p style={{ color: '#666' }}>
                        {win.pattern_label}
                        {win.winning_tile ? ` · winning tile ${win.winning_tile.label}` : ''}
                    </p>
                </div>
            </div>

            <p className="eyebrow" style={{ marginTop: 8 }}>Winning hand</p>
            <MeldRow melds={win.melds} />
            <div className="meld-row" style={{ marginTop: win.melds?.length ? 12 : 0, flexWrap: 'wrap' }}>
                {win.tiles.map((tile, i) => (
                    <TileCard key={`${tile.code}-${i}`} tile={tile} size="sm" />
                ))}
            </div>

            {win.bonus_tiles?.length > 0 && (
                <>
                    <p className="eyebrow" style={{ marginTop: 12 }}>Bonus tiles</p>
                    <div className="meld-row" style={{ flexWrap: 'wrap' }}>
                        {win.bonus_tiles.map((tile, i) => (
                            <TileCard key={`bonus-${tile.code}-${i}`} tile={tile} size="sm" />
                        ))}
                    </div>
                </>
            )}

            <p className="eyebrow" style={{ marginTop: 12 }}>Tai breakdown</p>
            {win.breakdown && win.breakdown.length > 0 ? (
                <table className="tai-breakdown">
                    <tbody>
                        {win.breakdown.map((row, i) => (
                            <tr key={i}>
                                <td>{row.label}</td>
                                <td style={{ textAlign: 'right' }}>{row.tai} tai</td>
                            </tr>
                        ))}
                        <tr className="tai-total">
                            <td><strong>Total</strong></td>
                            <td style={{ textAlign: 'right' }}><strong>{win.total_tai} tai</strong></td>
                        </tr>
                    </tbody>
                </table>
            ) : (
                <p style={{ color: '#666' }}>No scoring elements ({win.total_tai} tai).</p>
            )}
        </section>
    )
}

function SoloPlay() {
    const [state, setState] = useState(null)
    const [error, setError] = useState('')
    const [isBusy, setIsBusy] = useState(false)

    const loadState = useCallback(async () => {
        try {
            const response = await api.get('/api/game/solo/state/')
            setState(response.data)
        } catch (err) {
            if (err.response?.status === 404) {
                setState(null) // no game yet
            } else {
                setError('Could not load the game.')
            }
        }
    }, [])

    useEffect(() => {
        loadState()
    }, [loadState])

    const newGame = async () => {
        setIsBusy(true)
        setError('')
        try {
            const response = await api.post('/api/game/solo/new/')
            setState(response.data)
        } catch (err) {
            setError('Could not start a new game.')
        } finally {
            setIsBusy(false)
        }
    }

    const discard = async (tile) => {
        setIsBusy(true)
        setError('')
        try {
            const response = await api.post('/api/game/solo/discard/', {
                suit: tile.suit,
                value: tile.value,
            })
            setState(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not discard that tile.')
        } finally {
            setIsBusy(false)
        }
    }

    const declareKong = async (tile) => {
        setIsBusy(true)
        setError('')
        try {
            const response = await api.post('/api/game/solo/kong/', {
                suit: tile.suit,
                value: tile.value,
            })
            setState(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not declare a Kong.')
        } finally {
            setIsBusy(false)
        }
    }

    const claim = async (action, lowValue) => {
        setIsBusy(true)
        setError('')
        try {
            const body = { action }
            if (lowValue !== undefined) {
                body.low_value = lowValue
            }
            const response = await api.post('/api/game/solo/claim/', body)
            setState(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not make that claim.')
        } finally {
            setIsBusy(false)
        }
    }

    const passClaim = async () => {
        setIsBusy(true)
        setError('')
        try {
            const response = await api.post('/api/game/solo/pass/')
            setState(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not pass.')
        } finally {
            setIsBusy(false)
        }
    }

    const human = useMemo(
        () => state?.players.find((player) => player.is_human) || null,
        [state],
    )
    const opponents = useMemo(
        () => (state ? state.players.filter((player) => !player.is_human) : []),
        [state],
    )

    // Tiles the human holds four of can be declared as a concealed Kong.
    const kongable = useMemo(() => {
        if (!human?.tiles) {
            return []
        }
        const counts = {}
        for (const tile of human.tiles) {
            const key = `${tile.suit}-${tile.value}`
            counts[key] = counts[key] || { tile, n: 0 }
            counts[key].n += 1
        }
        return Object.values(counts).filter((entry) => entry.n === 4).map((e) => e.tile)
    }, [human])

    const yourTurn = state && state.is_human_turn && !state.result

    return (
        <AppLayout>
            <section className="profile-header">
                <div>
                    <p className="eyebrow">Solo Play</p>
                    <h2>Play a round against the computer</h2>
                    <p>
                        You are East. Draw and discard against three AI opponents who use the
                        same valuation engine. Claim Pong, Kong, Chow or a winning tile off
                        their discards when the prompt appears.
                    </p>
                </div>
                <button className="primary-button" type="button" onClick={newGame} disabled={isBusy}>
                    {state ? 'New game' : 'Start game'}
                </button>
            </section>

            {error && <p className="error-message" style={{ marginTop: 16 }}>{error}</p>}

            {!state ? (
                <div className="empty-state" style={{ marginTop: 24 }}>
                    <p>Start a game to deal the tiles.</p>
                </div>
            ) : (
                <>
                    {state.win && <WinSummary win={state.win} />}

                    {state.awaiting_claim && state.claim && (
                        <ClaimPrompt claim={state.claim} onClaim={claim} onPass={passClaim} disabled={isBusy} />
                    )}

                    <section className="status-grid" aria-label="Game status" style={{ marginTop: 24 }}>
                        <article className="status-card">
                            <p className="eyebrow">Round wind</p>
                            <strong style={{ textTransform: 'capitalize' }}>{state.round_wind}</strong>
                            <span>Wall: {state.live_wall_count} drawable</span>
                        </article>
                        <article className="status-card">
                            <p className="eyebrow">Turn</p>
                            <strong style={{ textTransform: 'capitalize' }}>{state.current_seat}</strong>
                            <span>{state.result ? 'Game over' : (yourTurn ? 'Your move' : 'Opponent moving')}</span>
                        </article>
                        <article className="status-card">
                            <p className="eyebrow">Status</p>
                            <strong style={{ textTransform: 'capitalize' }}>
                                {state.result
                                    ? (state.result === 'win' ? `${state.winner_seat} wins` : 'Washout')
                                    : 'In progress'}
                            </strong>
                            <span>{state.result === 'win' ? (state.win_type || '').replace('_', ' ') : ''}</span>
                        </article>
                    </section>

                    <section style={{ marginTop: 24 }}>
                        <p className="eyebrow">Opponents</p>
                        <div className="solo-opponents">
                            {opponents.map((player) => (
                                <Opponent key={player.seat_wind} player={player} />
                            ))}
                        </div>
                    </section>

                    <section className="tile-picker-panel" style={{ marginTop: 24 }}>
                        <div className="panel-heading">
                            <div>
                                <p className="eyebrow">Latest discards</p>
                                <h3>{state.discards.length} discarded</h3>
                            </div>
                        </div>
                        {state.discards.length > 0 ? (
                            <div className="meld-row">
                                {state.discards.slice(-12).map((entry, i) => (
                                    <TileCard key={`${entry.tile.code}-${i}`} tile={entry.tile} size="sm" />
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <p>No discards yet.</p>
                            </div>
                        )}
                    </section>

                    <section className="tile-picker-panel" style={{ marginTop: 24 }}>
                        <div className="panel-heading">
                            <div>
                                <p className="eyebrow">Your hand (East)</p>
                                <h3>
                                    {state.result
                                        ? 'Game over'
                                        : yourTurn
                                            ? 'Tap a tile to discard'
                                            : 'Waiting…'}
                                </h3>
                            </div>
                        </div>

                        <MeldRow melds={human?.melds} />

                        <div className="picker-grid" style={{ marginTop: human?.melds?.length ? 12 : 0 }}>
                            {(human?.tiles || []).map((tile, i) => (
                                <button
                                    key={`${tile.code}-${i}`}
                                    className={`tile picker-tile tile-${tile.suit}`}
                                    type="button"
                                    onClick={() => discard(tile)}
                                    disabled={!yourTurn || isBusy}
                                >
                                    <span className="tile-code">{tile.code}</span>
                                    <span className="tile-label">{tile.label}</span>
                                </button>
                            ))}
                        </div>

                        {kongable.length > 0 && yourTurn && (
                            <div className="helper-actions">
                                <p className="eyebrow">Declare concealed Kong</p>
                                <div className="meld-row">
                                    {kongable.map((tile, i) => (
                                        <button
                                            key={`kong-${tile.code}-${i}`}
                                            className="secondary-button"
                                            type="button"
                                            onClick={() => declareKong(tile)}
                                            disabled={isBusy}
                                        >
                                            Kong {tile.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {human?.bonus_tiles?.length > 0 && (
                            <div className="bonus-section">
                                <p className="eyebrow">Your bonus tiles ({human.bonus_tiles.length})</p>
                                <div className="meld-row">
                                    {human.bonus_tiles.map((tile, i) => (
                                        <TileCard key={`${tile.code}-${i}`} tile={tile} size="sm" />
                                    ))}
                                </div>
                            </div>
                        )}
                    </section>

                    <section className="tile-picker-panel" style={{ marginTop: 24 }}>
                        <p className="eyebrow">Game log</p>
                        <ul style={{ margin: 0, paddingLeft: 18, color: '#666', lineHeight: 1.7 }}>
                            {state.log.map((line, i) => (
                                <li key={i}>{line}</li>
                            ))}
                        </ul>
                    </section>
                </>
            )}
        </AppLayout>
    )
}

export default SoloPlay
