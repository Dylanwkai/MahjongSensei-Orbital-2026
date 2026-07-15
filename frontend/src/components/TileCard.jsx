// Mahjong tile rendering for the whole app.
//
// Every tile face is drawn as inline SVG — no image assets — so tiles stay
// crisp at any size and can be themed from CSS. Two things are exported:
//
//   TileFace  — just the face art (corner index + SVG). Use it INSIDE your own
//               <button className="tile ..."> when the tile is interactive.
//   TileCard  — a complete read-only tile (a styled <div> wrapping TileFace).
//
// A tile object is { suit, value, code, label }, matching the Django engine.

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

/* ------------------------------------------------------------------ */
/* palette + shared bits                                               */
/* ------------------------------------------------------------------ */

const INK = '#22304a'      // wind characters, outlines
const RED = '#c02c2c'      // characters suit, red dragon, red flowers
const GREEN = '#1e7a46'    // bamboo, green dragon
const BLUE = '#2b6cb0'     // circles accents, white-dragon frame, blue flowers
const GOLD = '#b98a2f'     // animal art

const CJK_FONT = "'Kaiti SC', 'KaiTi', 'STKaiti', 'Noto Serif SC', serif"

// One dot of the circles suit: a two-tone concentric ring.
function Dot({ x, y, r, color }) {
    return (
        <g>
            <circle cx={x} cy={y} r={r} fill="none" stroke={color} strokeWidth={r * 0.32} />
            <circle cx={x} cy={y} r={r * 0.38} fill={color} />
        </g>
    )
}

// One bamboo stick: a rounded rod with a knot band across the middle.
function Stick({ x, y, h, color }) {
    const w = 7
    return (
        <g>
            <rect x={x - w / 2} y={y - h / 2} width={w} height={h} rx={3} fill={color} />
            <rect x={x - w / 2} y={y - 2} width={w} height={3.4} rx={1.6} fill="#fffdf6" opacity="0.85" />
        </g>
    )
}

/* ------------------------------------------------------------------ */
/* circles (dots) 1-9                                                 */
/* ------------------------------------------------------------------ */

const DOT_LAYOUTS = {
    1: { r: 15, points: [[30, 38]] },
    2: { r: 10.5, points: [[30, 19], [30, 57]] },
    3: { r: 9, points: [[15, 15], [30, 38], [45, 61]] },
    4: { r: 9, points: [[17, 19], [43, 19], [17, 57], [43, 57]] },
    5: { r: 8, points: [[15, 15], [45, 15], [30, 38], [15, 61], [45, 61]] },
    6: { r: 7.5, points: [[17, 14], [43, 14], [17, 38], [43, 38], [17, 62], [43, 62]] },
    7: {
        r: 6.5,
        points: [[13, 11], [30, 15], [47, 19], [17, 44], [43, 44], [17, 64], [43, 64]],
    },
    8: { r: 6.5, points: [[17, 11], [43, 11], [17, 29], [43, 29], [17, 47], [43, 47], [17, 65], [43, 65]] },
    9: { r: 6.5, points: [[14, 13], [30, 13], [46, 13], [14, 38], [30, 38], [46, 38], [14, 63], [30, 63], [46, 63]] },
}

const DOT_COLORS = [GREEN, RED, BLUE]

function CirclesFace({ value }) {
    const layout = DOT_LAYOUTS[value]
    if (!layout) return null
    return (
        <g>
            {layout.points.map(([x, y], i) => (
                <Dot key={i} x={x} y={y} r={layout.r} color={DOT_COLORS[i % 3]} />
            ))}
        </g>
    )
}

/* ------------------------------------------------------------------ */
/* bamboo 1-9 (1 is the traditional bird)                             */
/* ------------------------------------------------------------------ */

const STICK_LAYOUTS = {
    2: { h: 26, points: [[30, 18]], red: [], bottom: [[30, 56]] },
    3: { h: 24, points: [[30, 15], [18, 55], [42, 55]] },
    4: { h: 24, points: [[18, 17], [42, 17], [18, 57], [42, 57]] },
    5: { h: 22, points: [[16, 15], [44, 15], [30, 38], [16, 61], [44, 61]], redIndex: 2 },
    6: { h: 22, points: [[14, 17], [30, 17], [46, 17], [14, 57], [30, 57], [46, 57]] },
    7: { h: 18, points: [[30, 11], [14, 38], [30, 38], [46, 38], [14, 63], [30, 63], [46, 63]], redIndex: 0 },
    // 8 is the traditional Singapore/HK "M over W": two chevron tents of
    // slanted sticks on top (∧∧), mirrored below (∨∨). Each point carries its
    // own tilt angle in degrees (positive = "/", negative = "\").
    8: {
        h: 18,
        points: [
            [13, 21, 18], [24, 21, -18], [36, 21, 18], [47, 21, -18],
            [13, 55, -18], [24, 55, 18], [36, 55, -18], [47, 55, 18],
        ],
    },
    9: { h: 17, points: [[14, 13], [30, 13], [46, 13], [14, 38], [30, 38], [46, 38], [14, 63], [30, 63], [46, 63]], redRow: 1 },
}

// The 1-bamboo is traditionally drawn as a bird. Simple stylised sparrow.
function BambooBird() {
    return (
        <g>
            {/* tail feathers */}
            <path d="M14 58 L26 46 M12 50 L26 44 M18 63 L27 49" stroke={GREEN} strokeWidth="2.6" strokeLinecap="round" fill="none" />
            {/* body */}
            <ellipse cx="33" cy="38" rx="13" ry="10" fill={RED} />
            {/* wing */}
            <path d="M26 38 Q33 30 42 35 Q36 42 27 41 Z" fill="#8f1d1d" />
            {/* head */}
            <circle cx="44" cy="26" r="7" fill={RED} />
            <circle cx="46.5" cy="24.5" r="1.4" fill="#fffdf6" />
            {/* beak */}
            <path d="M50 26 L57 24 L50 29 Z" fill={GOLD} />
            {/* legs */}
            <path d="M31 48 L29 58 M37 48 L37 58" stroke={GOLD} strokeWidth="2.2" strokeLinecap="round" />
        </g>
    )
}

function BambooFace({ value }) {
    if (value === 1) return <BambooBird />
    const layout = STICK_LAYOUTS[value]
    if (!layout) return null
    const points = layout.bottom ? [...layout.points, ...layout.bottom] : layout.points
    return (
        <g>
            {points.map(([x, y, angle], i) => {
                let color = GREEN
                if (layout.redIndex === i) color = RED
                if (layout.redRow !== undefined) {
                    // colour the middle row red on the 9 for the classic look
                    const row = Math.floor(i / 3)
                    if (row === layout.redRow) color = RED
                }
                const stick = <Stick key={i} x={x} y={y} h={layout.h} color={color} />
                return angle ? (
                    <g key={i} transform={`rotate(${angle} ${x} ${y})`}>
                        {stick}
                    </g>
                ) : (
                    stick
                )
            })}
        </g>
    )
}

/* ------------------------------------------------------------------ */
/* characters (wan) 1-9                                               */
/* ------------------------------------------------------------------ */

const CN_NUMERALS = ['一', '二', '三', '四', '五', '六', '七', '八', '九']

function CharactersFace({ value }) {
    return (
        <g fontFamily={CJK_FONT} textAnchor="middle" fontWeight="700">
            <text x="30" y="32" fontSize="26" fill={INK}>{CN_NUMERALS[value - 1]}</text>
            <text x="30" y="66" fontSize="28" fill={RED}>萬</text>
        </g>
    )
}

/* ------------------------------------------------------------------ */
/* honours: winds + dragons                                           */
/* ------------------------------------------------------------------ */

const WIND_CHARS = { east: '東', south: '南', west: '西', north: '北' }

function HonourFace({ value }) {
    if (WIND_CHARS[value]) {
        return (
            <text
                x="30" y="52" fontSize="40" fontWeight="700"
                fontFamily={CJK_FONT} textAnchor="middle" fill={INK}
            >
                {WIND_CHARS[value]}
            </text>
        )
    }
    if (value === 'red') {
        return (
            <text x="30" y="52" fontSize="40" fontWeight="700" fontFamily={CJK_FONT} textAnchor="middle" fill={RED}>
                中
            </text>
        )
    }
    if (value === 'green') {
        return (
            <text x="30" y="52" fontSize="40" fontWeight="700" fontFamily={CJK_FONT} textAnchor="middle" fill={GREEN}>
                發
            </text>
        )
    }
    // White dragon: the traditional empty blue double frame.
    return (
        <g>
            <rect x="13" y="12" width="34" height="52" rx="4" fill="none" stroke={BLUE} strokeWidth="3" />
            <rect x="19" y="18" width="22" height="40" rx="2" fill="none" stroke={BLUE} strokeWidth="1.6" strokeDasharray="4 3" />
        </g>
    )
}

/* ------------------------------------------------------------------ */
/* bonus: flowers + animals                                           */
/* ------------------------------------------------------------------ */

// A five-petal blossom, tinted red or blue to match the flower set.
function FlowerFace({ value }) {
    const [set] = String(value).split('_')
    const color = set === 'red' ? RED : BLUE
    const petals = [0, 72, 144, 216, 288]
    return (
        <g>
            <g transform="translate(30 36)">
                {petals.map((deg) => (
                    <ellipse
                        key={deg}
                        cx="0" cy="-11" rx="6.5" ry="10"
                        fill={color} opacity="0.85"
                        transform={`rotate(${deg})`}
                    />
                ))}
                <circle cx="0" cy="0" r="5" fill={GOLD} />
            </g>
            <path d="M30 50 Q28 60 30 68 M30 56 Q36 54 39 50" stroke={GREEN} strokeWidth="2.4" fill="none" strokeLinecap="round" />
        </g>
    )
}

function CatFace() {
    return (
        <g stroke={INK} strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 20 L21 30 M43 20 L39 30" fill={INK} />
            <path d="M17 20 Q18 28 22 30 M43 20 Q42 28 38 30" />
            <circle cx="30" cy="38" r="14" />
            <circle cx="25" cy="35" r="1.6" fill={INK} stroke="none" />
            <circle cx="35" cy="35" r="1.6" fill={INK} stroke="none" />
            <path d="M28 42 Q30 44 32 42" />
            <path d="M12 38 L21 40 M12 44 L21 44 M48 38 L39 40 M48 44 L39 44" strokeWidth="1.8" />
        </g>
    )
}

function MouseFace() {
    return (
        <g stroke={INK} strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
            <ellipse cx="27" cy="42" rx="14" ry="9.5" />
            <circle cx="43" cy="34" r="6.5" />
            <circle cx="41" cy="26" r="3.5" />
            <circle cx="45" cy="33" r="1.3" fill={INK} stroke="none" />
            <path d="M13 44 Q4 48 8 56 Q10 60 15 58" />
            <path d="M50 35 L55 36" strokeWidth="1.8" />
        </g>
    )
}

function CentipedeFace() {
    const body = [[14, 20], [22, 26], [30, 31], [38, 36], [44, 43], [46, 52], [42, 60]]
    return (
        <g>
            {body.map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r="5" fill={i === 0 ? RED : GOLD} />
            ))}
            <g stroke={INK} strokeWidth="1.6" strokeLinecap="round">
                <path d="M20 20 L24 14 M28 26 L32 20 M36 31 L40 25 M44 37 L49 33" />
                <path d="M18 30 L14 36 M26 36 L22 42 M34 42 L30 48 M38 52 L32 55" />
                <path d="M12 16 L8 10 M16 16 L17 9" />
            </g>
        </g>
    )
}

function ChickenFace() {
    return (
        <g stroke={INK} strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 22 Q20 16 24 15 Q25 11 29 13 Q32 10 33 15" fill={RED} stroke={RED} />
            <circle cx="27" cy="24" r="7" />
            <circle cx="29" cy="22" r="1.3" fill={INK} stroke="none" />
            <path d="M34 24 L40 26 L34 28 Z" fill={GOLD} stroke={GOLD} />
            <path d="M22 30 Q12 38 18 48 Q24 56 34 52 Q42 49 40 40 Q39 34 30 31" />
            <path d="M18 42 Q8 36 10 28 M20 46 Q10 44 8 38" strokeWidth="2" />
            <path d="M26 55 L26 62 M32 53 L33 61" strokeWidth="2" />
        </g>
    )
}

const ANIMAL_FACES = {
    cat: CatFace,
    mouse: MouseFace,
    centipede: CentipedeFace,
    chicken: ChickenFace,
}

/* ------------------------------------------------------------------ */
/* corner index — the beginner-friendly hint                          */
/* ------------------------------------------------------------------ */

const WIND_INDEX = { east: 'E', south: 'S', west: 'W', north: 'N' }
const DRAGON_INDEX = { red: 'R', green: 'G', white: 'W' }
const DRAGON_INDEX_COLOR = { red: RED, green: GREEN, white: BLUE }

function cornerIndex(tile) {
    const { suit, value } = tile
    if (suit === 'bamboo' || suit === 'circles' || suit === 'characters') {
        return { text: String(value), color: '#8a8374' }
    }
    if (suit === 'honour') {
        if (WIND_INDEX[value]) return { text: WIND_INDEX[value], color: '#8a8374' }
        return { text: DRAGON_INDEX[value], color: DRAGON_INDEX_COLOR[value] }
    }
    if (suit === 'flower') {
        const [set, n] = String(value).split('_')
        return { text: n, color: set === 'red' ? RED : BLUE }
    }
    return null // animals carry their name on the face instead
}

/* ------------------------------------------------------------------ */
/* public components                                                  */
/* ------------------------------------------------------------------ */

function faceFor(tile) {
    switch (tile.suit) {
        case 'circles':
            return <CirclesFace value={tile.value} />
        case 'bamboo':
            return <BambooFace value={tile.value} />
        case 'characters':
            return <CharactersFace value={tile.value} />
        case 'honour':
            return <HonourFace value={tile.value} />
        case 'flower':
            return <FlowerFace value={tile.value} />
        case 'animal': {
            const Face = ANIMAL_FACES[tile.value]
            return Face ? (
                <g>
                    <Face />
                    <text x="30" y="72" fontSize="9.5" fontWeight="700" textAnchor="middle" fill="#8a8374">
                        {tile.value}
                    </text>
                </g>
            ) : null
        }
        default:
            return null
    }
}

// The face art alone. Put this inside interactive <button className="tile">s.
export function TileFace({ tile }) {
    const index = cornerIndex(tile)
    return (
        <>
            {index && (
                <span className="tile-index" style={{ color: index.color }} aria-hidden="true">
                    {index.text}
                </span>
            )}
            <svg className="tile-art" viewBox="0 0 60 76" role="img" aria-label={tile.label}>
                {faceFor(tile)}
            </svg>
        </>
    )
}

// A complete read-only tile.
function TileCard({ tile, size = 'md' }) {
    return (
        <div
            className={`tile tile-${tile.suit}${size === 'sm' ? ' tile-sm' : ''}${size === 'lg' ? ' tile-lg' : ''}`}
            title={tile.label}
        >
            <TileFace tile={tile} />
        </div>
    )
}

export default TileCard
