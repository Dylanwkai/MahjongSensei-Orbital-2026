// Presentational Mahjong tile, matching the tile markup used across the app
// (see Home.jsx / HandHelper.jsx). A tile is { suit, value, code, label }.

const SUIT_CODE = {
    bamboo: 'B',
    circles: 'C',
    characters: 'K',
    honour: 'H',
    flower: 'F',
    animal: 'A',
}

// Build a tile object from a suit + value, deriving code and label the same
// way the Django engine does.
export function makeTile(suit, value) {
    const prefix = SUIT_CODE[suit] || ''
    const numbered = suit === 'bamboo' || suit === 'circles' || suit === 'characters'
    const label = numbered ? `${value} ${suit}` : String(value).replace(/_/g, ' ')
    return { suit, value, code: `${prefix}${value}`, label }
}

function TileCard({ tile, size = 'md' }) {
    return (
        <div className={`tile tile-${tile.suit}${size === 'sm' ? ' tile-sm' : ''}`}>
            <span className="tile-code">{tile.code}</span>
            <span className="tile-label">{tile.label}</span>
        </div>
    )
}

export default TileCard
