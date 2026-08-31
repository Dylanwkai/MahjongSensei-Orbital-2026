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
    """A Pong, Kong or Chow. claimed=True means it was taken from a discard
    (face up); claimed=False is formed from your own hand (e.g. concealed Kong)."""

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

    def promote_pong_to_kong(self, suit, value, deck=None):
        """Add a fourth tile drawn into hand to an exposed Pong, upgrading it to
        a Kong, then draw a replacement. Returns the replacement tile, or None if
        no deck is given."""
        meld = next(
            (
                m for m in self.melds
                if m.kind == "pong"
                and m.tiles
                and m.tiles[0].suit == suit
                and m.tiles[0].value == value
            ),
            None,
        )
        if meld is None:
            raise ValueError("You do not have an exposed Pong of that tile to upgrade.")

        fourth = next(
            (t for t in self.tiles if t.suit == suit and t.value == value), None
        )
        if fourth is None:
            raise ValueError("You need the fourth matching tile in hand to upgrade the Pong.")

        self.tiles.remove(fourth)
        meld.tiles.append(fourth)
        meld.kind = "kong"

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


# Trainer difficulty: how many complete melds (and a pair) to seed into a dealt
# hand. More seeded groups means the hand starts closer to a win, so an easy
# hand has an obvious discard while a hard hand is mostly loose tiles.
DIFFICULTY_PROFILES = {
    "easy": {"melds": 3, "pair": True},
    "medium": {"melds": 2, "pair": True},
    "hard": {"melds": 1, "pair": False},
}


class HandGenerator:
    def generate_random_hand(self, hand_size=13, difficulty=None):
        """Deal a hand. With no difficulty the tiles are drawn purely at random.
        With a difficulty ('easy'/'medium'/'hard') the hand is seeded with a
        number of complete melds so it starts closer to (or further from) a
        winning shape."""
        if difficulty in DIFFICULTY_PROFILES:
            return self._structured_hand(hand_size, DIFFICULTY_PROFILES[difficulty])
        return self._random_hand(hand_size)

    def _random_hand(self, hand_size):
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

    def _structured_hand(self, hand_size, profile):
        pool = self._fresh_pool()
        keys = []

        for _ in range(profile["melds"]):
            meld = self._draw_meld(pool)
            if meld is None:
                break
            keys.extend(meld)

        if profile.get("pair"):
            pair = self._draw_pair(pool)
            if pair:
                keys.extend(pair)

        # Top up with loose tiles until the hand is full.
        while len(keys) < hand_size:
            keys.append(self._draw_single(pool))

        keys = keys[:hand_size]
        tiles = [Tile(suit, value) for suit, value in keys]
        random.shuffle(tiles)

        hand = Hand(tiles)
        hand.bonus_tiles = []
        return hand

    @staticmethod
    def _fresh_pool():
        pool = Counter()
        for suit in NUMBERED_SUITS:
            for value in range(1, 10):
                pool[(suit, value)] = 4
        for value in HONOUR_VALUES:
            pool[("honour", value)] = 4
        return pool

    def _draw_meld(self, pool):
        """Take a random Pong or Chow out of the pool, respecting tile counts."""
        for kind in random.sample(("pong", "chow"), 2):
            if kind == "pong":
                candidates = [key for key, count in pool.items() if count >= 3]
                if candidates:
                    key = random.choice(candidates)
                    pool[key] -= 3
                    return [key, key, key]
            else:
                runs = []
                for suit in NUMBERED_SUITS:
                    for low in range(1, 8):
                        run = [(suit, low), (suit, low + 1), (suit, low + 2)]
                        if all(pool[key] >= 1 for key in run):
                            runs.append(run)
                if runs:
                    run = random.choice(runs)
                    for key in run:
                        pool[key] -= 1
                    return run
        return None

    @staticmethod
    def _draw_pair(pool):
        candidates = [key for key, count in pool.items() if count >= 2]
        if not candidates:
            return None
        key = random.choice(candidates)
        pool[key] -= 2
        return [key, key]

    @staticmethod
    def _draw_single(pool):
        candidates = [key for key, count in pool.items() if count >= 1]
        key = random.choice(candidates)
        pool[key] -= 1
        return key


class HandEvaluator:
    def evaluate_hand(self, tiles):
        """Rough hand strength: reward complete sets, pairs, and near-sequences,
        penalise isolated tiles."""
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

    def optimal_discards(self, hand):
        """Every distinct discard that ties for the best resulting hand score.
        Several tiles can be equally good, so this returns all of them (not just
        the first one found)."""
        best_score = None
        scored = {}  # (suit, value) -> (Tile, score), deduped across copies

        for tile in hand.sorted_tiles():
            key = (tile.suit, tile.value)
            if key in scored:
                continue
            remaining = hand.tiles.copy()
            remaining.remove(tile)
            score = self.evaluator.evaluate_hand(remaining)
            scored[key] = (tile, score)
            if best_score is None or score > best_score:
                best_score = score

        discards = [
            tile.to_dict() for tile, score in scored.values() if score == best_score
        ]
        return {"discards": discards, "score": best_score}


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
    """Checks for a complete winning hand: standard (four sets + pair), seven
    pairs, or thirteen orphans. Bonus tiles ignored; each Kong adds a tile, so a
    standard hand is 14 to 18 tiles. A standard result also returns pair + melds
    for the scorer."""

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
# must be worth at least MIN_TAI_TO_WIN, and flowers and animals count towards
# that minimum (so a hand can win on bonus tiles alone).
SCORING = {
    "seat_wind": 1,
    "round_wind": 1,
    "dragon": 1,
    "seat_flower": 1,
    "animal": 1,
    "all_pongs": 2,
    "half_flush": 2,        # one suit plus honours
    "full_flush": 4,        # one suit, no honours
    "seven_pairs": 2,
    "thirteen_orphans": 5,
    "pinghu": 4,            # four chows + a pair, no flowers/animals
    "smelly_pinghu": 1,     # the same shape but with at least one flower/animal
}

MIN_TAI_TO_WIN = 1
FLOWERS_COUNT_TOWARD_MIN = True


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

    def score(self, win_result, bonus_tiles=None, win_type=None, winning_tile=None):
        """Score a winning hand. win_type and winning_tile are optional context
        used only by Pinghu (needs a self-draw or a two-sided Ron wait)."""
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

        # Context Pinghu depends on: a valid wait, and whether any bonus tiles
        # are present (which downgrades a Pinghu to a Smelly Pinghu).
        self._pinghu_eligible = self._pinghu_wait_ok(win_result, win_type, winning_tile)
        self._has_bonus = len(bonus_tiles) > 0

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
                else f"A winning hand needs at least {MIN_TAI_TO_WIN} tai."
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

        # Pinghu: four chows plus a pair, provided the winning-tile condition
        # was met. A clean hand scores Pinghu; one with any flower/animal scores
        # the reduced Smelly Pinghu instead.
        if (
            len(melds) == 4
            and all(meld["type"] == "chow" for meld in melds)
            and getattr(self, "_pinghu_eligible", False)
        ):
            if getattr(self, "_has_bonus", False):
                tai += self._add(
                    breakdown, "Smelly Pinghu", self.scoring["smelly_pinghu"]
                )
            else:
                tai += self._add(breakdown, "Pinghu", self.scoring["pinghu"])

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

    def _pinghu_wait_ok(self, win_result, win_type, winning_tile):
        """Whether the winning-tile condition for a Pinghu is satisfied: a
        self-draw always qualifies; a discarded (Ron) tile qualifies only when
        the hand had a two-or-more-sided wait."""
        if win_type == "self_draw":
            return True
        if (
            win_type == "ron"
            and winning_tile is not None
            and win_result.get("pattern") == "standard"
        ):
            counts = self._counts_from_result(win_result)
            return self._count_completing_tiles(counts, winning_tile) >= 2
        return False

    def _count_completing_tiles(self, full_counts, winning_tile):
        """From the 13-tile wait (the full hand minus the winning tile), count
        how many distinct tiles would have completed a standard winning hand."""
        key = (winning_tile.suit, winning_tile.value)
        if full_counts.get(key, 0) <= 0:
            return 0

        wait = dict(full_counts)
        wait[key] -= 1
        if wait[key] == 0:
            del wait[key]

        winners = 0
        for candidate in self._all_tile_keys():
            if wait.get(candidate, 0) >= 4:
                continue
            trial = dict(wait)
            trial[candidate] = trial.get(candidate, 0) + 1
            if WinChecker().decompose_standard(trial) is not None:
                winners += 1
        return winners

    @staticmethod
    def _all_tile_keys():
        keys = [(suit, value) for suit in NUMBERED_SUITS for value in range(1, 10)]
        keys += [("honour", value) for value in HONOUR_VALUES]
        return keys

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

        return tai

    @staticmethod
    def _add(breakdown, label, value):
        if value:
            breakdown.append({"label": label, "tai": value})
        return value
