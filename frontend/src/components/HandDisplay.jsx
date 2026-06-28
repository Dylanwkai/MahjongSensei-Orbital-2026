import TileCard from './TileCard'

// Shows a hand: exposed melds, the concealed tiles, and a bonus row for
// flowers/animals. Pass children to render the concealed tiles yourself (for an
// interactive picker); otherwise they render read-only.

function MeldGroup({ meld }) {
    const stateClass = meld.claimed ? 'meld-claimed' : 'meld-concealed'
    return (
        <div className={`meld-group ${stateClass}`}>
            <div className="meld-tiles">
                {meld.tiles.map((tile, index) => (
                    <TileCard key={`${tile.code}-${index}`} tile={tile} size="sm" />
                ))}
            </div>
            <span className="meld-tag">
                {meld.kind}{meld.claimed ? ' · claimed' : ' · concealed'}
            </span>
        </div>
    )
}

function HandDisplay({ tiles = [], melds = [], bonusTiles = [], children }) {
    return (
        <div className="hand-display">
            {melds.length > 0 && (
                <div className="hand-section">
                    <p className="eyebrow">Exposed melds</p>
                    <div className="meld-row">
                        {melds.map((meld, index) => (
                            <MeldGroup key={index} meld={meld} />
                        ))}
                    </div>
                </div>
            )}

            {children ? (
                children
            ) : (
                <div className="tile-grid">
                    {tiles.map((tile, index) => (
                        <TileCard key={`${tile.code}-${index}`} tile={tile} />
                    ))}
                </div>
            )}

            {bonusTiles.length > 0 && (
                <div className="bonus-section">
                    <p className="eyebrow">Bonus tiles ({bonusTiles.length})</p>
                    <div className="meld-row">
                        {bonusTiles.map((tile, index) => (
                            <TileCard key={`${tile.code}-${index}`} tile={tile} size="sm" />
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default HandDisplay
