import TileCard from './TileCard'

// Renders a labelled row of tiles illustrating a meld (Pong / Kong / Chow) or
// any small worked example. `tiles` is an array of { suit, value, code, label }.
function MeldDemo({ name, tiles, description }) {
    return (
        <article className="status-card meld-demo">
            {name && <p className="eyebrow">{name}</p>}
            <div
                className="meld-tile-row"
                style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', margin: '0.5rem 0' }}
            >
                {tiles.map((tile, index) => (
                    <TileCard key={`${tile.code}-${index}`} tile={tile} />
                ))}
            </div>
            {description && <span>{description}</span>}
        </article>
    )
}

export default MeldDemo
