import random
from collections import Counter
from dataclasses import dataclass


NUMBERED_SUITS = ("bamboo", "circles", "characters")
HONOUR_VALUES = ("east", "south", "west", "north", "red", "green", "white")
FLOWER_VALUES = (
    "red_1",
    "red_2",
    "red_3",
    "red_4",
    "blue_1",
    "blue_2",
    "blue_3",
    "blue_4",
)
ANIMAL_VALUES = ("cat", "mouse", "centipede", "chicken")

SUIT_CODE = {
    "bamboo": "B",
    "circles": "C",
    "characters": "K",
    "honour": "H",
    "flower": "F",
    "animal": "A",
}

# Winds and dragons are both stored under the "honour" suit; split them so the
# scorer can tell them apart.
WINDS = ("east", "south", "west", "north")
DRAGONS = ("red", "green", "white")

# Each seat owns the flower with its number.
SEAT_NUMBER = {"east": 1, "south": 2, "west": 3, "north": 4}
SEAT_WIND_BY_NUMBER = {number: wind for wind, number in SEAT_NUMBER.items()}


@dataclass(frozen=True)
class Tile:
    suit: str
    value: int | str
    is_bonus: bool = False

    @property
    def code(self):
        return f"{SUIT_CODE[self.suit]}{self.value}"

    @property
    def label(self):
        if self.suit in NUMBERED_SUITS:
            return f"{self.value} {self.suit}"
        return str(self.value).replace("_", " ")

    def to_dict(self):
        return {
            "suit": self.suit,
            "value": self.value,
            "code": self.code,
            "label": self.label,
            "is_bonus": self.is_bonus,
        }

    def __repr__(self):
        return self.code


class Meld:
    """A Pong, Kong or Chow.

    claimed=True means the meld was made by taking another player's discard, so
    it is shown face up and its tiles are fixed. claimed=False is a meld formed
    from your own hand (like a concealed Kong), which stays hidden.
    """

    def __init__(self, kind, tiles, claimed=False):
        self.kind = kind          # pong, kong or chow
        self.tiles = list(tiles)
        self.claimed = claimed

    @property
    def is_concealed(self):
        return not self.claimed

    def to_dict(self):
        return {
            "kind": self.kind,
            "claimed": self.claimed,
            "concealed": not self.claimed,
            "tiles": [tile.to_dict() for tile in self.tiles],
        }

    def __repr__(self):
        state = "claimed" if self.claimed else "concealed"
        return f"Meld({self.kind}, {state}, {self.tiles})"


class Hand:
    def __init__(self, tiles):
        self.tiles = [t for t in tiles if not t.is_bonus]   # concealed tiles
        self.bonus_tiles = [t for t in tiles if t.is_bonus] # flowers/animals
        self.declared_kongs = []
        self.melds = []

    def discard(self, tile):
        self.tiles.remove(tile)
        return self.tiles

    def claim_pong(self, suit, value):
        """Claim a discard to make a Pong using two matching tiles in hand."""
        used = self._take_matching(suit, value, 2, "Pong")
        meld = Meld("pong", used + [Tile(suit, value)], claimed=True)
        self.melds.append(meld)
        return meld

    def claim_kong(self, suit, value, deck=None):
        """Claim a discard to make a Kong using three matching tiles in hand,
        then draw a replacement."""
        used = self._take_matching(suit, value, 3, "Kong")
        meld = Meld("kong", used + [Tile(suit, value)], claimed=True)
        self.melds.append(meld)
        if deck is not None:
            self._draw_replacement(deck)
        return meld

    def claim_chow(self, suit, low_value, claimed_value=None):
        """Claim a discard to make a Chow using two tiles in hand. low_value is
        the run's lowest tile and claimed_value is the discarded tile."""
        if suit not in NUMBERED_SUITS or not isinstance(low_value, int) or low_value > 7:
            raise ValueError("A Chow is three consecutive numbers in a numbered suit.")

        run = [low_value, low_value + 1, low_value + 2]
        if claimed_value is None:
            claimed_value = low_value
        if claimed_value not in run:
            raise ValueError("The claimed tile must be part of the Chow run.")

        used = []
        for value in run:
            if value == claimed_value:
                continue
            match = next(
                (t for t in self.tiles if t.suit == suit and t.value == value), None
            )
            if match is None:
                raise ValueError("You do not hold the tiles needed to claim this Chow.")
            used.append(match)

        for tile in used:
            self.tiles.remove(tile)

        ordered = sorted(used + [Tile(suit, claimed_value)], key=lambda t: t.value)
        meld = Meld("chow", ordered, claimed=True)
        self.melds.append(meld)
        return meld

    def _take_matching(self, suit, value, needed, label):
        matching = [t for t in self.tiles if t.suit == suit and t.value == value]
        if len(matching) < needed:
            raise ValueError(
                f"Need {needed} matching concealed tiles to claim a {label}."
            )
        used = matching[:needed]
        for tile in used:
            self.tiles.remove(tile)
        return used

    def _draw_replacement(self, deck):
        replacement = deck.draw_replacement()
        while replacement.is_bonus:
            self.bonus_tiles.append(replacement)
            replacement = deck.draw_replacement()
        self.tiles.append(replacement)
        return replacement

    def declare_kong(self, suit, value, deck=None):
        """Set four matching tiles aside as a concealed Kong and draw a
        replacement. Returns the replacement tile, or None if no deck is given."""
        matching = [t for t in self.tiles if t.suit == suit and t.value == value]
        if len(matching) < 4:
            raise ValueError("Need four matching tiles to declare a Kong.")

        kong_tiles = matching[:4]
        for tile in kong_tiles:
            self.tiles.remove(tile)
        self.declared_kongs.append(kong_tiles)
        self.melds.append(Meld("kong", kong_tiles, claimed=False))

        if deck is None:
            return None

        return self._draw_replacement(deck)

    def add_tile(self, tile):
        if tile.is_bonus:
            self.bonus_tiles.append(tile)
        else:
            self.tiles.append(tile)
        return self.tiles

    def sorted_tiles(self):
        return sorted(self.tiles, key=tile_sort_key)

    def to_dict(self):
        return {
            "tiles": [tile.to_dict() for tile in self.sorted_tiles()],
            "bonus_tiles": [tile.to_dict() for tile in self.bonus_tiles],
            "melds": [meld.to_dict() for meld in self.melds],
            "tile_count": len(self.tiles),
            "bonus_count": len(self.bonus_tiles),
        }

    def __repr__(self):
        return f'Hand: {self.tiles} | Bonus: {self.bonus_tiles}'
    

class Deck:
    def __init__(self):
        self.tiles = self._build_deck()

    def _build_deck(self):
        tiles = []

        # Numbered suits: 4 copies of 1-9 in each suit.
        for suit in NUMBERED_SUITS:
            for value in range(1, 10):
                for _ in range(4):
                    tiles.append(Tile(suit, value))

        # Honour tiles: 4 copies each.
        for value in HONOUR_VALUES:
            for _ in range(4):
                tiles.append(Tile('honour', value))

        # Flower and animal tiles are Singapore Mahjong bonus tiles.
        for value in FLOWER_VALUES:
            tiles.append(Tile('flower', value, is_bonus=True))

        for value in ANIMAL_VALUES:
            tiles.append(Tile('animal', value, is_bonus=True))

        return tiles

    def shuffle(self):
        random.shuffle(self.tiles)

    def draw(self):
        if not self.tiles:
            raise ValueError("Deck ran out of tiles")
        return self.tiles.pop()

    def draw_replacement(self):
        """Draw a replacement tile after a Kong or a bonus tile."""
        return self.draw()

    def __len__(self):
        return len(self.tiles)


def tile_sort_key(tile):
    suit_order = {
        "characters": 0,
        "bamboo": 1,
        "circles": 2,
        "honour": 3,
        "flower": 4,
        "animal": 5,
    }
    value = tile.value if isinstance(tile.value, int) else str(tile.value)
    return (suit_order[tile.suit], value)


class HandGenerator:
    def generate_random_hand(self, hand_size=13):
        deck = Deck()
        deck.shuffle()
        
        tiles = []
        bonus_tiles = []
        
        # Bonus tiles are replaced immediately, so the playable hand stays full.
        while len(tiles) < hand_size:
            drawn = deck.draw()
            if drawn.is_bonus:
                bonus_tiles.append(drawn)
            else:
                tiles.append(drawn)
        
        hand = Hand(tiles)
        hand.bonus_tiles = bonus_tiles
        return hand


class HandEvaluator:
    def evaluate_hand(self, tiles):
        """
        Return a rough hand strength score.

        This is a first-pass evaluator for discard recommendations. It rewards
        complete sets, pairs, and useful near-sequences, while subtracting for
        isolated tiles.
        """
        playable_tiles = [tile for tile in tiles if not tile.is_bonus]
        counts = Counter((tile.suit, tile.value) for tile in playable_tiles)

        return (
            self._score_groups(counts)
            + self._score_numbered_sequences(playable_tiles)
            - self._score_isolated_tiles(playable_tiles)
        )

    def _score_groups(self, counts):
        score = 0

        for count in counts.values():
            if count >= 3:
                score += 9
            elif count == 2:
                score += 4

        return score

    def _score_numbered_sequences(self, tiles):
        score = 0

        for suit in NUMBERED_SUITS:
            values = {tile.value for tile in tiles if tile.suit == suit}

            for value in range(1, 8):
                if {value, value + 1, value + 2}.issubset(values):
                    score += 8

            for value in range(1, 9):
                if {value, value + 1}.issubset(values):
                    score += 3

            for value in range(1, 8):
                if {value, value + 2}.issubset(values):
                    score += 2

        return score

    def _score_isolated_tiles(self, tiles):
        penalty = 0
        counts = Counter((tile.suit, tile.value) for tile in tiles)

        for tile in tiles:
            if counts[(tile.suit, tile.value)] > 1:
                continue

            if self._has_numbered_neighbour(tile, tiles):
                continue

            penalty += 2

        return penalty

    def _has_numbered_neighbour(self, tile, tiles):
        if tile.suit not in NUMBERED_SUITS:
            return False

        nearby_values = {
            other.value
            for other in tiles
            if other.suit == tile.suit and other != tile
        }

        return any(abs(tile.value - value) <= 2 for value in nearby_values)


class ValuationAlgorithm:
    def __init__(self, evaluator=None):
        self.evaluator = evaluator or HandEvaluator()

    def recommend_discard(self, hand):
        best_discard = None
        best_score = None

        for tile in hand.sorted_tiles():
            remaining_tiles = hand.tiles.copy()
            remaining_tiles.remove(tile)
            score = self.evaluator.evaluate_hand(remaining_tiles)

            if best_score is None or score > best_score:
                best_score = score
                best_discard = tile

        return {
            "discard": best_discard.to_dict(),
            "score": best_score,
            "reasoning": (
                f"Discarding {best_discard.label} keeps the strongest remaining "
                "combination of sets, pairs, and near-sequences."
            ),
        }


# Thirteen Orphans: one of every terminal (1 and 9 in each suit) and every
# honour tile, with one of them pair.
ORPHAN_TILES = frozenset(
    [(suit, value) for suit in NUMBERED_SUITS for value in (1, 9)]
    + [("honour", honour) for honour in HONOUR_VALUES]
)

_SUIT_ORDER = {"characters": 0, "bamboo": 1, "circles": 2, "honour": 3}
_HONOUR_ORDER = {honour: index for index, honour in enumerate(HONOUR_VALUES)}

PATTERN_LABELS = {
    "standard": "Standard hand: four melds and a pair",
    "seven_pairs": "Seven Pairs",
    "thirteen_orphans": "Thirteen Orphans",
}


class WinChecker:
    """Checks whether a hand is a complete winning hand.

    Handles three shapes: standard (four sets plus a pair), seven pairs, and
    thirteen orphans. Bonus tiles are ignored. A hand is normally 14 tiles, but
    each Kong adds one, so a standard hand can be 14 to 18 tiles. For a standard
    win the result also includes the pair and melds so the scorer can use them.
    """

    def check(self, tiles):
        playable = [tile for tile in tiles if not tile.is_bonus]
        count = len(playable)
        counts = Counter((tile.suit, tile.value) for tile in playable)

        # Seven pairs and thirteen orphans are 14 tiles only.
        if count == 14:
            if self._is_thirteen_orphans(counts):
                return self._result(True, "thirteen_orphans")
            if self._is_seven_pairs(counts):
                return self._result(True, "seven_pairs")

        # Standard hand: four sets and a pair, plus one tile per Kong.
        if 14 <= count <= 18:
            decomposition = self.decompose_standard(counts)
            if decomposition is not None:
                return self._result(
                    True,
                    "standard",
                    pair=decomposition["pair"],
                    melds=decomposition["melds"],
                )

        return self._result(False, None)

    def _is_seven_pairs(self, counts):
        return len(counts) == 7 and all(count == 2 for count in counts.values())

    def _is_thirteen_orphans(self, counts):
        if set(counts.keys()) != ORPHAN_TILES:
            return False
        return sorted(counts.values()) == [1] * 12 + [2]

    def decompose_standard(self, counts):
        """Return the first valid {pair, melds} split, or None. Each meld is
        {"type": pong/kong/chow, "tile": (suit, value)}; a chow's tile is its
        lowest."""
        for key, count in counts.items():
            if count >= 2:
                trial = self._subtract(counts, [key, key])
                melds = self._decompose_melds(trial, 4)
                if melds is not None:
                    return {"pair": key, "melds": melds}
        return None

    def _decompose_melds(self, counts, need):
        # Done when we've formed exactly need number of melds and used every tile.
        if need == 0:
            return [] if not counts else None
        if not counts:
            return None

        key = min(counts.keys(), key=self._tile_order)
        suit, value = key
        count = counts[key]

        # Option 1: Kong (four identical tiles).
        if count >= 4:
            rest = self._decompose_melds(self._subtract(counts, [key] * 4), need - 1)
            if rest is not None:
                return [{"type": "kong", "tile": key}] + rest

        # Option 2: Pong (three identical tiles).
        if count >= 3:
            rest = self._decompose_melds(self._subtract(counts, [key] * 3), need - 1)
            if rest is not None:
                return [{"type": "pong", "tile": key}] + rest

        # Option 3: Chow (run of three, numbered suits only).
        if suit in NUMBERED_SUITS and isinstance(value, int) and value <= 7:
            run = [(suit, value), (suit, value + 1), (suit, value + 2)]
            if all(counts.get(part, 0) >= 1 for part in run):
                rest = self._decompose_melds(self._subtract(counts, run), need - 1)
                if rest is not None:
                    return [{"type": "chow", "tile": key}] + rest

        return None

    def iter_standard(self, counts):
        """Yield every valid {pair, melds} split. A hand can be read more than
        one way, so the scorer uses this to find the best scoring reading."""
        for key, count in counts.items():
            if count >= 2:
                trial = self._subtract(counts, [key, key])
                for melds in self._iter_melds(trial, 4):
                    yield {"pair": key, "melds": melds}

    def _iter_melds(self, counts, need):
        if need == 0:
            if not counts:
                yield []
            return
        if not counts:
            return

        key = min(counts.keys(), key=self._tile_order)
        suit, value = key
        count = counts[key]

        if count >= 4:
            for rest in self._iter_melds(self._subtract(counts, [key] * 4), need - 1):
                yield [{"type": "kong", "tile": key}] + rest
        if count >= 3:
            for rest in self._iter_melds(self._subtract(counts, [key] * 3), need - 1):
                yield [{"type": "pong", "tile": key}] + rest
        if suit in NUMBERED_SUITS and isinstance(value, int) and value <= 7:
            run = [(suit, value), (suit, value + 1), (suit, value + 2)]
            if all(counts.get(part, 0) >= 1 for part in run):
                for rest in self._iter_melds(self._subtract(counts, run), need - 1):
                    yield [{"type": "chow", "tile": key}] + rest

    @staticmethod
    def _subtract(counts, keys):
        reduced = dict(counts)
        for key in keys:
            reduced[key] -= 1
            if reduced[key] == 0:
                del reduced[key]
        return reduced

    @staticmethod
    def _tile_order(key):
        suit, value = key
        if isinstance(value, int):
            return (_SUIT_ORDER.get(suit, 9), value)
        return (_SUIT_ORDER.get(suit, 9), 100 + _HONOUR_ORDER.get(value, 0))

    @staticmethod
    def _result(is_winning, pattern, pair=None, melds=None):
        return {
            "is_winning": is_winning,
            "pattern": pattern,
            "description": PATTERN_LABELS.get(pattern, "Not a winning hand yet"),
            "pair": pair,
            "melds": melds,
        }


# Tai (point) values. Edit these to match a different house rule set. A hand
# must be worth at least MIN_TAI_TO_WIN, and by default flowers do not count
# towards that minimum.
SCORING = {
    "seat_wind": 1,
    "round_wind": 1,
    "dragon": 1,
    "seat_flower": 1,
    "animal": 1,
    "no_flower": 1,         # no flowers and no animals at all
    "all_pongs": 2,
    "half_flush": 2,        # one suit plus honours
    "full_flush": 4,        # one suit, no honours
    "seven_pairs": 2,
    "thirteen_orphans": 4,
}

MIN_TAI_TO_WIN = 1
FLOWERS_COUNT_TOWARD_MIN = False


def parse_flower(value):
    """'red_3' -> ('red', 3), or (None, None) if not a flower."""
    try:
        color, number = value.split("_")
        return color, int(number)
    except (ValueError, AttributeError):
        return None, None


class ScoreCalculator:
    """Scores a winning hand in tai. seat_wind is the player's seat (and decides
    their flowers); round_wind is the prevailing wind."""

    def __init__(self, seat_wind="east", round_wind="east", scoring=None):
        self.seat_wind = seat_wind
        self.round_wind = round_wind
        self.scoring = scoring or SCORING

    def score(self, win_result, bonus_tiles=None):
        bonus_tiles = bonus_tiles or []

        if not win_result.get("is_winning"):
            return {
                "is_valid_win": False,
                "hand_tai": 0,
                "bonus_tai": 0,
                "total_tai": 0,
                "breakdown": [],
                "reason": "Hand is not a complete winning hand.",
            }

        breakdown = []
        pattern = win_result.get("pattern")
        hand_tai = 0

        if pattern == "seven_pairs":
            hand_tai += self._add(breakdown, "Seven Pairs", self.scoring["seven_pairs"])
        elif pattern == "thirteen_orphans":
            hand_tai += self._add(
                breakdown, "Thirteen Orphans", self.scoring["thirteen_orphans"]
            )
        elif pattern == "standard":
            hand_tai += self._score_standard(win_result, breakdown)

        bonus_tai = self._score_bonus(bonus_tiles, breakdown)

        qualifying = (hand_tai + bonus_tai) if FLOWERS_COUNT_TOWARD_MIN else hand_tai
        is_valid = qualifying >= MIN_TAI_TO_WIN

        return {
            "is_valid_win": is_valid,
            "hand_tai": hand_tai,
            "bonus_tai": bonus_tai,
            "total_tai": hand_tai + bonus_tai,
            "breakdown": breakdown,
            "reason": (
                ""
                if is_valid
                else f"A winning hand needs at least {MIN_TAI_TO_WIN} tai "
                "(flowers excluded)."
            ),
        }

    def _score_standard(self, win_result, breakdown):
        # Score every way the hand can be read and keep the best.
        counts = self._counts_from_result(win_result)
        best_tai = None
        best_breakdown = []

        for decomposition in WinChecker().iter_standard(counts):
            trial_breakdown = []
            tai = self._score_decomposition(decomposition, trial_breakdown)
            if best_tai is None or tai > best_tai:
                best_tai = tai
                best_breakdown = trial_breakdown

        if best_tai is None:  # fall back to the supplied decomposition
            return self._score_decomposition(win_result, breakdown)

        breakdown.extend(best_breakdown)
        return best_tai

    def _score_decomposition(self, decomposition, breakdown):
        melds = decomposition.get("melds") or []
        tai = 0

        # Wind and dragon pongs/kongs.
        for meld in melds:
            if meld["type"] not in ("pong", "kong"):
                continue
            suit, value = meld["tile"]
            if suit != "honour":
                continue
            if value in DRAGONS:
                tai += self._add(
                    breakdown, f"Dragon {meld['type']}: {value}", self.scoring["dragon"]
                )
            if value == self.seat_wind:
                tai += self._add(
                    breakdown,
                    f"Seat wind {meld['type']}: {value}",
                    self.scoring["seat_wind"],
                )
            if value == self.round_wind:
                tai += self._add(
                    breakdown,
                    f"Round wind {meld['type']}: {value}",
                    self.scoring["round_wind"],
                )

        # All Pongs (no chow among the four sets).
        if melds and all(meld["type"] in ("pong", "kong") for meld in melds):
            tai += self._add(breakdown, "All Pongs", self.scoring["all_pongs"])

        # Flush, based on the suits present across pair + melds.
        tai += self._score_flush(decomposition, breakdown)
        return tai

    @staticmethod
    def _counts_from_result(win_result):
        counts = {}

        def add(key, number):
            counts[key] = counts.get(key, 0) + number

        add(win_result["pair"], 2)
        for meld in win_result["melds"]:
            suit, value = meld["tile"]
            if meld["type"] == "kong":
                add((suit, value), 4)
            elif meld["type"] == "pong":
                add((suit, value), 3)
            else:  # chow
                add((suit, value), 1)
                add((suit, value + 1), 1)
                add((suit, value + 2), 1)
        return counts

    def _score_flush(self, decomposition, breakdown):
        keys = [decomposition["pair"]] + [meld["tile"] for meld in decomposition["melds"]]
        suits = {suit for suit, _ in keys if suit != "honour"}
        has_honour = any(suit == "honour" for suit, _ in keys)

        if len(suits) == 1 and not has_honour:
            return self._add(breakdown, "Full Flush", self.scoring["full_flush"])
        if len(suits) == 1 and has_honour:
            return self._add(breakdown, "Half Flush", self.scoring["half_flush"])
        return 0

    def _score_bonus(self, bonus_tiles, breakdown):
        seat_number = SEAT_NUMBER.get(self.seat_wind)
        flowers = [tile for tile in bonus_tiles if tile.suit == "flower"]
        animals = [tile for tile in bonus_tiles if tile.suit == "animal"]
        tai = 0

        for tile in flowers:
            _color, number = parse_flower(tile.value)
            if number == seat_number:
                tai += self._add(
                    breakdown, f"Seat flower: {tile.value}", self.scoring["seat_flower"]
                )

        for tile in animals:
            tai += self._add(breakdown, f"Animal: {tile.value}", self.scoring["animal"])

        if not flowers and not animals:
            tai += self._add(breakdown, "No flowers", self.scoring["no_flower"])

        return tai

    @staticmethod
    def _add(breakdown, label, value):
        if value:
            breakdown.append({"label": label, "tai": value})
        return value
