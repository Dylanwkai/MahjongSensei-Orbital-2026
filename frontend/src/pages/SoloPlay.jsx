import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'
import TileCard, { TileFace, makeTile } from '../components/TileCard'
import { useAuth } from '../context/AuthContext'

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

// Each seat scores 1 tai for a Pong of its own wind, and for the flower/season
// carrying its number (East=1, South=2, West=3, North=4).
const SEAT_TAI_NUMBER = { east: 1, south: 2, west: 3, north: 4 }

// A small hint showing the wind and flower that score tai for a given seat.
function TaiTargets({ seatWind }) {
    const n = SEAT_TAI_NUMBER[seatWind]
    if (!n) {
        return null
    }
    const windTile = makeTile('honour', seatWind)
    const flowerTile = makeTile('flower', `red_${n}`)
    const label = `${cap(seatWind)} scores a Pong of the ${cap(seatWind)} wind, and flower/season ${n}`
    return (
        <div className="tai-targets" title={label}>
            <span className="tai-targets-label">Tai</span>
            <TileCard tile={windTile} size="sm" />
            <TileCard tile={flowerTile} size="sm" />
        </div>
    )
}

// While claims are still animating, a claimer's open meld should not appear
// until its discard has been shown as eaten. Given how many of a player's
// claimed melds should be visible, drop the most recent claimed melds beyond
// that count (concealed melds are always kept).
function visibleMelds(melds, claimsToShow) {
    if (!melds || melds.length === 0) {
        return melds
    }
    const totalClaimed = melds.filter((m) => m.claimed).length
    let hide = totalClaimed - Math.max(0, claimsToShow || 0)
    if (hide <= 0) {
        return melds
    }
    const result = []
    for (let i = melds.length - 1; i >= 0; i--) {
        if (hide > 0 && melds[i].claimed) {
            hide -= 1
            continue
        }
        result.unshift(melds[i])
    }
    return result
}

// A single face-down tile (the back). Used for hidden opponent hands and the
// wall is drawn separately as thin slivers.
function TileBack() {
    return <div className="tile-back" aria-hidden="true" />
}

function HandBacks({ count }) {
    return (
        <div className="hand-backs">
            {Array.from({ length: Math.max(0, count) }).map((_, i) => (
                <TileBack key={i} />
            ))}
        </div>
    )
}

// One AI seat: name + tile count, their face-up melds and bonus tiles, and their
// concealed hand shown as tile backs.
function SeatPanel({ player, active, banker, claimsToShow, winner }) {
    if (!player) {
        return null
    }
    return (
        <article className={`seat-panel${active ? ' seat-active' : ''}${banker ? ' seat-banker' : ''}${winner ? ' seat-winner' : ''}`}>
            <div className="seat-head">
                <strong>{player.name}</strong>
                <span className="seat-wind">{player.wind}</span>
                {winner && <span className="winner-chip">Winner</span>}
                {banker && <span className="banker-chip">Banker</span>}
                <span className="seat-count">{player.tile_count} tiles</span>
            </div>
            <TaiTargets seatWind={player.wind} />
            <MeldRow melds={visibleMelds(player.melds, claimsToShow)} />
            {player.bonus_tiles?.length > 0 && (
                <div className="seat-bonus">
                    {player.bonus_tiles.map((tile, i) => (
                        <TileCard key={`${tile.code}-${i}`} tile={tile} size="sm" />
                    ))}
                </div>
            )}
            <HandBacks count={player.tile_count} />
        </article>
    )
}

// The wall: a strip of slivers with the drawable (live) tiles on one end and the
// dead wall (Kong / flower / animal replacements) on the other.
function WallBar({ live, dead }) {
    const liveShown = Math.min(live, 40)
    return (
        <div className="wall-bar">
            <div className="wall-labels">
                <span>Draw ▸ {live} drawable</span>
                <span>{dead} dead wall</span>
            </div>
            <div className="wall-strip" aria-hidden="true">
                {Array.from({ length: liveShown }).map((_, i) => (
                    <span key={`l${i}`} className="wall-sliver" />
                ))}
                <span className="wall-divider" />
                {Array.from({ length: dead }).map((_, i) => (
                    <span key={`d${i}`} className="wall-sliver wall-dead" />
                ))}
            </div>
        </div>
    )
}

function ClaimPrompt({ claim, onClaim, onPass, disabled }) {
    const suit = claim.tile.suit
    return (
        <section className="tile-picker-panel claim-prompt" style={{ marginTop: 24 }}>
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">Claim available</p>
                    <h3>{claim.from_name || cap(claim.from_seat)} discarded {claim.tile.label}</h3>
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
                        {win.winner_name} wins by {(win.win_type || '').replace('_', ' ')} - {win.total_tai} tai
                    </h3>
                    <p style={{ color: '#666' }}>
                        {win.pattern_label}
                        {win.winning_tile ? ` · winning tile ${win.winning_tile.label}` : ''}
                    </p>
                </div>
            </div>

            <p className="eyebrow" style={{ marginTop: 12 }}>Winning tile</p>
            <div className="win-source">
                {win.winning_tile && <TileCard tile={win.winning_tile} size="sm" />}
                <span className="win-source-text">
                    {win.win_type === 'ron'
                        ? win.from_seat
                            ? <>Thrown by <strong style={{ textTransform: 'capitalize' }}>{win.from_name || cap(win.from_seat)}</strong>{win.from_seat === 'east' ? ' (you)' : ''}</>
                            : 'Won on a discard'
                        : 'Self-drawn — no one threw it'}
                </span>
            </div>

            <p className="eyebrow" style={{ marginTop: 12 }}>Winning hand</p>
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

const REVEAL_DELAY = 1000  // ms between each revealed AI discard
const EAT_DELAY = 800      // ms a discard sits on the table before it is eaten

// Indices of the discards that have been claimed by a seat, for marking them
// eaten on the table.
function claimedIndices(discards) {
    const set = new Set()
    ;(discards || []).forEach((d, i) => {
        if (d.claimed_as) {
            set.add(i)
        }
    })
    return set
}

// Wind and banker tracker. hand 1-4 within a round maps to the banker seat
// (east, south, west, north); after four hands the round wind advances. The
// tracker is persisted in localStorage so it survives a page reload.
const SEAT_WINDS = ['east', 'south', 'west', 'north']
const TRACKER_KEY = 'mahjong_solo_tracker'
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1)

function loadTracker() {
    try {
        const t = JSON.parse(localStorage.getItem(TRACKER_KEY))
        if (t && Number.isInteger(t.round) && Number.isInteger(t.hand)
            && t.round >= 0 && t.round < 4 && t.hand >= 1 && t.hand <= 4) {
            return t
        }
    } catch (e) { /* fall through to default */ }
    return { round: 0, hand: 1 }
}

// The banker keeps the deal after a win or a washout; otherwise the deal passes
// to the next seat, and the round wind advances after the fourth hand.
function advanceTracker(tracker, finishedState) {
    if (!finishedState || !finishedState.result) {
        return tracker
    }
    const bankerSeat = SEAT_WINDS[tracker.hand - 1]
    const bankerWon = finishedState.result === 'win'
        && finishedState.winner_seat === bankerSeat
    if (bankerWon || finishedState.result === 'washout') {
        return tracker
    }
    let hand = tracker.hand + 1
    let round = tracker.round
    if (hand > 4) {
        hand = 1
        round = (round + 1) % 4
    }
    return { round, hand }
}

function SoloPlay() {
    const { refreshProfile } = useAuth()
    const [state, setState] = useState(null)
    const [error, setError] = useState('')
    const [isBusy, setIsBusy] = useState(false)
    const [hint, setHint] = useState(null)
    // True when the human's most recent action ends in a fresh draw, so the
    // newly drawn tile should be held back during the reveal then highlighted.
    const [drawnActive, setDrawnActive] = useState(false)

    // Wind and banker tracker, persisted in localStorage across reloads.
    const [tracker, setTracker] = useState(loadTracker)
    const setTrackerPersist = useCallback((next) => {
        setTracker(next)
        try {
            localStorage.setItem(TRACKER_KEY, JSON.stringify(next))
        } catch (e) { /* storage unavailable, keep in memory only */ }
    }, [])

    // How many discards are currently revealed. When a move produces several AI
    // discards at once, we reveal them one at a time (see commitState).
    const [revealCount, setRevealCount] = useState(0)
    const revealCountRef = useRef(0)
    const revealTimer = useRef(null)

    // Indices of revealed discards whose "eaten" badge is currently shown. A
    // claimed tile is first shown as a plain discard, then a beat later marked
    // eaten, so the claim is easy to follow.
    const [eatenShown, setEatenShown] = useState(() => new Set())

    const setReveal = useCallback((n) => {
        revealCountRef.current = n
        setRevealCount(n)
    }, [])

    const clearRevealTimer = useCallback(() => {
        if (revealTimer.current) {
            clearTimeout(revealTimer.current)
            revealTimer.current = null
        }
    }, [])

    // Store the new game state. When animate is true and the discard pile grew,
    // reveal the new discards one by one with a short delay between each so the
    // AI seats appear to play in turn rather than all at once.
    const commitState = useCallback((data, animate) => {
        setHint(null)  // any hint is stale once the table changes
        setState((prev) => {
            if (data?.result && (!prev || !prev.result)) {
                refreshProfile()
            }
            return data
        })

        clearRevealTimer()
        const discards = data?.discards || []
        const total = discards.length

        if (!animate || total <= revealCountRef.current) {
            setReveal(total)
            setEatenShown(claimedIndices(discards))  // all eaten marks at once
            return
        }

        // Step through the new discards one at a time. When a tile was claimed,
        // show it as a plain discard first, pause, then mark it eaten before
        // moving on, so the claim is easy to follow.
        const step = (i) => {
            if (i >= total) {
                revealTimer.current = null
                return
            }
            setReveal(i + 1)
            if (discards[i]?.claimed_as) {
                revealTimer.current = setTimeout(() => {
                    setEatenShown((prev) => new Set(prev).add(i))
                    revealTimer.current = setTimeout(() => step(i + 1), REVEAL_DELAY)
                }, EAT_DELAY)
            } else {
                revealTimer.current = setTimeout(() => step(i + 1), REVEAL_DELAY)
            }
        }
        step(revealCountRef.current)
    }, [refreshProfile, clearRevealTimer, setReveal])

    useEffect(() => clearRevealTimer, [clearRevealTimer])

    const loadState = useCallback(async () => {
        try {
            const response = await api.get('/api/game/solo/state/')
            commitState(response.data, false)
            // Sync the tracker to the game actually on the server, so the badge
            // is right after a reload even if localStorage was cleared.
            const data = response.data
            const round = SEAT_WINDS.indexOf(data.round_wind)
            const hand = SEAT_WINDS.indexOf(data.dealer) + 1
            if (round >= 0 && hand >= 1) {
                setTrackerPersist({ round, hand })
            }
        } catch (err) {
            if (err.response?.status === 404) {
                setState(null) // no game yet
            } else {
                setError('Could not load the game.')
            }
        }
    }, [commitState, setTrackerPersist])

    useEffect(() => {
        loadState()
    }, [loadState])

    const startGameAt = async (next) => {
        setIsBusy(true)
        setError('')
        setDrawnActive(false)
        setTrackerPersist(next)
        try {
            const response = await api.post('/api/game/solo/new/', {
                round_wind: SEAT_WINDS[next.round],
                dealer: next.hand - 1,
            })
            // Start from an empty table, then animate the banker and any AI
            // seats before us playing their opening discards and claims. (When
            // we are the banker there are no opening discards, so nothing shows.)
            setReveal(0)
            setEatenShown(new Set())
            commitState(response.data, true)
        } catch (err) {
            setError('Could not start a new game.')
        } finally {
            setIsBusy(false)
        }
    }

    // New game: advance the banker/wind from the game currently on the table
    // (the banker keeps the deal on a win or washout), then deal the next hand.
    const newGame = () => startGameAt(advanceTracker(tracker, state))

    // Reset: back to the start of the East round, East as banker.
    const resetGame = () => startGameAt({ round: 0, hand: 1 })

    const discard = async (tile) => {
        setIsBusy(true)
        setError('')
        setDrawnActive(true)  // we will draw again once the AI seats finish
        try {
            const response = await api.post('/api/game/solo/discard/', {
                suit: tile.suit,
                value: tile.value,
            })
            commitState(response.data, true)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not discard that tile.')
        } finally {
            setIsBusy(false)
        }
    }

    const declareKong = async (tile) => {
        setIsBusy(true)
        setError('')
        setDrawnActive(false)
        try {
            const response = await api.post('/api/game/solo/kong/', {
                suit: tile.suit,
                value: tile.value,
            })
            commitState(response.data, false)
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
            setDrawnActive(false)  // a claim takes a discard, no fresh draw
            commitState(response.data, true)
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
            setDrawnActive(true)  // passing returns play to us and we draw
            commitState(response.data, true)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not pass.')
        } finally {
            setIsBusy(false)
        }
    }

    const requestHint = async () => {
        setError('')
        try {
            const response = await api.get('/api/game/solo/hint/')
            setHint(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Could not get a hint.')
        }
    }

    const human = useMemo(
        () => state?.players.find((player) => player.is_human) || null,
        [state],
    )
    // Look up a seat by its wind, for placing players around the table.
    const seatOf = useCallback(
        (wind) => state?.players.find((player) => player.seat_wind === wind) || null,
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

    // Exposed Pongs the human can upgrade to a Kong because they hold (just
    // drew) the fourth matching tile.
    const promotableKongs = useMemo(() => {
        if (!human?.melds || !human?.tiles) {
            return []
        }
        const held = new Set(human.tiles.map((t) => `${t.suit}-${t.value}`))
        return human.melds
            .filter((meld) => meld.kind === 'pong' && meld.claimed && meld.tiles?.length)
            .map((meld) => meld.tiles[0])
            .filter((tile) => held.has(`${tile.suit}-${tile.value}`))
    }, [human])

    // Tiles the hint suggests discarding, for highlighting in the hand.
    const hintKeys = useMemo(() => {
        const list = hint?.optimal_discards || (hint?.discard ? [hint.discard] : [])
        return new Set(list.map((tile) => `${tile.suit}-${tile.value}`))
    }, [hint])

    // While AI discards are still being revealed one by one, hold back the
    // player's controls, the claim prompt and the win summary.
    const revealing = Boolean(state && revealCount < state.discards.length)
    const revealedDiscards = state
        ? state.discards.slice(0, revealCount).map((d, i) => ({ ...d, index: i }))
        : []

    // How many of each seat's claimed melds may be shown so far: one per discard
    // that seat has claimed and that has been revealed as eaten. This keeps a
    // claimer's open meld hidden until its discard visibly leaves the table.
    const claimsShownBySeat = {}
    for (const d of revealedDiscards) {
        if (d.claimed_by && eatenShown.has(d.index)) {
            claimsShownBySeat[d.claimed_by] = (claimsShownBySeat[d.claimed_by] || 0) + 1
        }
    }
    const yourTurn = state && state.is_human_turn && !state.result && !revealing
    const locked = isBusy || revealing

    // Once the reveal finishes, mark the winning seat on the board.
    const gameOver = Boolean(state && state.result && !revealing)
    const wonBy = (wind) => gameOver && state.result === 'win' && state.winner_seat === wind

    // The tile just drawn onto the human's turn. It is hidden until the AI
    // discards have all been revealed, then shown with a highlight.
    const drawnKey = (
        drawnActive && state && state.is_human_turn && !state.result && state.last_drawn
            ? `${state.last_drawn.suit}-${state.last_drawn.value}`
            : null
    )

    // The hand tiles to render. The freshly drawn tile is pulled out of its
    // sorted position: hidden entirely while the AI discards are still being
    // revealed, then shown on its own at the right end of the hand (and
    // highlighted) until the player discards, at which point it settles back
    // into the sorted hand on their next draw.
    const handTiles = useMemo(() => {
        const tiles = human?.tiles || []
        if (!drawnKey) {
            return tiles.map((tile) => ({ tile, isDrawn: false }))
        }

        let drawn = null
        const rest = []
        for (const tile of tiles) {
            if (!drawn && `${tile.suit}-${tile.value}` === drawnKey) {
                drawn = tile
                continue
            }
            rest.push({ tile, isDrawn: false })
        }

        // While revealing, keep the drawn tile hidden; otherwise append it on
        // the right.
        if (drawn && !revealing) {
            rest.push({ tile: drawn, isDrawn: true })
        }
        return rest
    }, [human, drawnKey, revealing])

    // Discards laid in front of each seat, around the centre of the table. A
    // tile another seat has claimed is dimmed and tagged with who ate it.
    const renderSeatDiscards = (wind) => {
        const items = revealedDiscards.filter((entry) => entry.seat === wind)
        if (items.length === 0) {
            return null
        }
        return (
            <div className="discard-tiles">
                {items.map((entry, i) => {
                    const eaten = entry.claimed_as && eatenShown.has(entry.index)
                    return (
                        <div
                            key={`${wind}-${entry.tile.code}-${i}`}
                            className={`discard-item${eaten ? ' discard-eaten' : ''}`}
                        >
                            <TileCard tile={entry.tile} size="sm" />
                            {eaten && (
                                <span className="eaten-badge">
                                    {cap(entry.claimed_as)} · {cap(entry.claimed_by)}
                                </span>
                            )}
                        </div>
                    )
                })}
            </div>
        )
    }

    return (
        <AppLayout>
            <section className="profile-header solo-header">
                <div>
                    <p className="eyebrow">Solo Play</p>
                    <h2>Play a round against the computer</h2>
                </div>
                <div className="solo-header-actions">
                    <div className="wind-tracker" title="Prevailing wind and banker">
                        <span className="wind-tracker-main">{cap(SEAT_WINDS[tracker.round])} {tracker.hand}</span>
                        <span className="wind-tracker-sub">
                            Banker: {cap(SEAT_WINDS[tracker.hand - 1])}
                            {SEAT_WINDS[tracker.hand - 1] === 'east' ? ' (you)' : ''}
                        </span>
                    </div>
                    <div className="solo-header-buttons">
                        <button className="primary-button" type="button" onClick={newGame} disabled={isBusy}>
                            {state ? 'New game' : 'Start game'}
                        </button>
                        <button className="secondary-button" type="button" onClick={resetGame} disabled={isBusy}>
                            Reset
                        </button>
                    </div>
                </div>
            </section>

            {error && <p className="error-message" style={{ marginTop: 16 }}>{error}</p>}

            {!state ? (
                <div className="empty-state" style={{ marginTop: 24 }}>
                    <p>Start a game to deal the tiles.</p>
                </div>
            ) : (
                <>
                    {state.win && !revealing && <WinSummary win={state.win} />}

                    <div className="solo-status">
                        <span>Round wind: <strong style={{ textTransform: 'capitalize' }}>{state.round_wind}</strong></span>
                        <span>Turn: <strong>{state.current_name}</strong></span>
                        <span>
                            {state.result
                                ? (state.result === 'win' ? `${state.winner_name} wins` : 'Washout draw')
                                : revealing
                                    ? 'Opponents playing…'
                                    : yourTurn
                                        ? 'Your move'
                                        : 'Opponent moving'}
                        </span>
                    </div>

                    <div className="solo-table">
                        <div className="seat-slot seat-top">
                            <SeatPanel
                                player={seatOf('west')}
                                active={!state.result && state.current_seat === 'west'}
                                banker={state.dealer === 'west'}
                                claimsToShow={claimsShownBySeat.west}
                                winner={wonBy('west')}
                            />
                        </div>

                        <div className="seat-slot seat-left">
                            <SeatPanel
                                player={seatOf('north')}
                                active={!state.result && state.current_seat === 'north'}
                                banker={state.dealer === 'north'}
                                claimsToShow={claimsShownBySeat.north}
                                winner={wonBy('north')}
                            />
                        </div>

                        <div className="table-center">
                            <WallBar
                                live={state.live_wall_count}
                                dead={Math.max(0, state.wall_count - state.live_wall_count)}
                            />
                            <div className="discard-board">
                                <div className="dboard-cell d-top">{renderSeatDiscards('west')}</div>
                                <div className="dboard-cell d-left">{renderSeatDiscards('north')}</div>
                                <div className="dboard-mid">
                                    <span className="center-status">
                                        {revealedDiscards.length} discards
                                        {revealing ? ' · playing…' : ''}
                                    </span>
                                </div>
                                <div className="dboard-cell d-right">{renderSeatDiscards('south')}</div>
                                <div className="dboard-cell d-bottom">{renderSeatDiscards('east')}</div>

                                {gameOver && (
                                    <div className={`win-overlay${state.result === 'washout' ? ' win-overlay-draw' : ''}`}>
                                        {state.result === 'win' ? (
                                            <>
                                                <span className="win-overlay-icon">🏆</span>
                                                <span className="win-overlay-title">
                                                    {wonBy('east') ? 'You win!' : `${state.winner_name || cap(state.winner_seat)} wins`}
                                                </span>
                                                {state.win && (
                                                    <span className="win-overlay-sub">
                                                        {(state.win.win_type || '').replace('_', ' ')} · {state.win.total_tai} tai
                                                    </span>
                                                )}
                                            </>
                                        ) : (
                                            <>
                                                <span className="win-overlay-icon">🀄</span>
                                                <span className="win-overlay-title">Washout</span>
                                                <span className="win-overlay-sub">No winner this hand</span>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="seat-slot seat-right">
                            <SeatPanel
                                player={seatOf('south')}
                                active={!state.result && state.current_seat === 'south'}
                                banker={state.dealer === 'south'}
                                claimsToShow={claimsShownBySeat.south}
                                winner={wonBy('south')}
                            />
                        </div>

                        <div className="seat-slot seat-bottom">
                            {state.awaiting_claim && state.claim && !revealing && (
                                <ClaimPrompt
                                    claim={state.claim}
                                    onClaim={claim}
                                    onPass={passClaim}
                                    disabled={isBusy}
                                />
                            )}

                            <section className={`seat-panel seat-human${state.dealer === 'east' ? ' seat-banker' : ''}${wonBy('east') ? ' seat-winner' : ''}`}>
                                <div className="panel-heading">
                                    <div>
                                        <p className="eyebrow">
                                            You{human ? ` · ${cap(human.wind)} · ${human.tile_count} tiles` : ''}
                                            {wonBy('east') && <span className="winner-chip">Winner</span>}
                                            {state.dealer === 'east' && <span className="banker-chip">Banker</span>}
                                        </p>
                                        <h3>
                                            {state.result
                                                ? 'Game over'
                                                : yourTurn
                                                    ? 'Tap a tile to discard'
                                                    : 'Waiting…'}
                                        </h3>
                                    </div>
                                    {yourTurn && (
                                        <button
                                            className="secondary-button"
                                            type="button"
                                            onClick={requestHint}
                                            disabled={locked}
                                        >
                                            Hint
                                        </button>
                                    )}
                                </div>

                                <TaiTargets seatWind={human?.wind} />

                                {hint && (
                                    <div className="hint-banner">
                                        <span className="eyebrow">Suggested discard</span>
                                        <div className="meld-row" style={{ flexWrap: 'wrap' }}>
                                            {(hint.optimal_discards || [hint.discard]).map((tile, i) => (
                                                <TileCard key={`hint-${tile.code}-${i}`} tile={tile} size="sm" />
                                            ))}
                                        </div>
                                        {(hint.optimal_discards?.length || 1) > 1 && (
                                            <p style={{ margin: 0, color: '#666', fontSize: '0.85rem' }}>
                                                Any of these is an equally strong discard.
                                            </p>
                                        )}
                                    </div>
                                )}

                                <MeldRow melds={visibleMelds(human?.melds, claimsShownBySeat.east)} />

                                <div className="picker-grid" style={{ marginTop: human?.melds?.length ? 12 : 0 }}>
                                    {handTiles.map(({ tile, isDrawn }, i) => {
                                        const isHinted = yourTurn && hintKeys.has(`${tile.suit}-${tile.value}`)
                                        return (
                                            <button
                                                key={`${tile.code}-${i}`}
                                                className={`tile picker-tile tile-${tile.suit}${isHinted ? ' hint-tile' : ''}${isDrawn ? ' drawn-tile' : ''}`}
                                                type="button"
                                                onClick={() => discard(tile)}
                                                disabled={!yourTurn || locked}
                                                title={isDrawn ? `${tile.label} (just drawn)` : tile.label}
                                            >
                                                <TileFace tile={tile} />
                                            </button>
                                        )
                                    })}
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
                                                    disabled={locked}
                                                >
                                                    Kong {tile.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {promotableKongs.length > 0 && yourTurn && (
                                    <div className="helper-actions">
                                        <p className="eyebrow">Upgrade Pong to Kong</p>
                                        <div className="meld-row">
                                            {promotableKongs.map((tile, i) => (
                                                <button
                                                    key={`promo-${tile.code}-${i}`}
                                                    className="secondary-button"
                                                    type="button"
                                                    onClick={() => declareKong(tile)}
                                                    disabled={locked}
                                                >
                                                    Kong {tile.label} (add to Pong)
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
                        </div>
                    </div>

                    <section className="tile-picker-panel solo-log">
                        <p className="eyebrow">Game log</p>
                        {revealing ? (
                            <p style={{ margin: 0, color: '#888' }}>Opponents are playing…</p>
                        ) : (
                            <ul className="game-log">
                                {state.log.map((line, i) => (
                                    <li key={i}>{line}</li>
                                ))}
                            </ul>
                        )}
                    </section>
                </>
            )}
        </AppLayout>
    )
}

export default SoloPlay
