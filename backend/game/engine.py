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


class Hand:
    def __init__(self, tiles):
        self.tiles = [t for t in tiles if not t.is_bonus]   # playable tiles
        self.bonus_tiles = [t for t in tiles if t.is_bonus] # set aside

    def discard(self, tile):
        self.tiles.remove(tile)
        return self.tiles

    def add_tile(self, tile):
        if tile.is_bonus:
            self.bonus_tiles.append(tile)  # bonus tiles go to bonus pile
        else:
            self.tiles.append(tile)
        return self.tiles

    def sorted_tiles(self):
        return sorted(self.tiles, key=tile_sort_key)

    def to_dict(self):
        return {
            "tiles": [tile.to_dict() for tile in self.sorted_tiles()],
            "bonus_tiles": [tile.to_dict() for tile in self.bonus_tiles],
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


# Thirteen Orphans needs one of every terminal (1 & 9 in each numbered suit)
# plus all seven honour tiles — 13 distinct tiles, one of them duplicated.
ORPHAN_TILES = frozenset(
    [(suit, value) for suit in NUMBERED_SUITS for value in (1, 9)]
    + [("honour", honour) for honour in HONOUR_VALUES]
)

_SUIT_ORDER = {"characters": 0, "bamboo": 1, "circles": 2, "honour": 3}
_HONOUR_ORDER = {honour: index for index, honour in enumerate(HONOUR_VALUES)}

PATTERN_LABELS = {
    "standard": "Standard hand — four melds and a pair",
    "seven_pairs": "Seven Pairs",
    "thirteen_orphans": "Thirteen Orphans",
}


class WinChecker:
    """Detects whether a 14-tile hand is a complete (winning) hand.

    Recognizes three winning shapes:
      * standard         - four melds (Pong / Chow) plus one pair
      * seven_pairs      - seven distinct pairs
      * thirteen_orphans - one of every terminal and honour, plus a duplicate

    Bonus tiles (flowers / animals) are ignored, and exactly 14 playable tiles
    are required. Kongs are not counted here because a 14-tile hand that uses a
    Kong would need a replacement tile (15 tiles) to be complete.
    """

    def check(self, tiles):
        playable = [tile for tile in tiles if not tile.is_bonus]
        if len(playable) != 14:
            return self._result(False, None)

        counts = Counter((tile.suit, tile.value) for tile in playable)

        if self._is_thirteen_orphans(counts):
            return self._result(True, "thirteen_orphans")
        if self._is_seven_pairs(counts):
            return self._result(True, "seven_pairs")
        if self._is_standard(counts):
            return self._result(True, "standard")
        return self._result(False, None)

    # ----- winning shapes -------------------------------------------------
    def _is_seven_pairs(self, counts):
        return len(counts) == 7 and all(count == 2 for count in counts.values())

    def _is_thirteen_orphans(self, counts):
        if set(counts.keys()) != ORPHAN_TILES:
            return False
        return sorted(counts.values()) == [1] * 12 + [2]

    def _is_standard(self, counts):
        # Try every possible pair (the "eyes"), then check whether the rest
        # decompose into four melds.
        for key, count in counts.items():
            if count >= 2:
                trial = self._subtract(counts, [key, key])
                if self._can_form_melds(trial):
                    return True
        return False

    def _can_form_melds(self, counts):
        if not counts:
            return True

        # Resolve a deterministic "smallest" tile each step.
        key = min(counts.keys(), key=self._tile_order)
        suit, value = key
        count = counts[key]

        # Option 1: use it as a Pong (three identical tiles).
        if count >= 3:
            if self._can_form_melds(self._subtract(counts, [key, key, key])):
                return True

        # Option 2: use it as the start of a Chow (numbered suits only).
        if suit in NUMBERED_SUITS and isinstance(value, int) and value <= 7:
            run = [(suit, value), (suit, value + 1), (suit, value + 2)]
            if all(counts.get(part, 0) >= 1 for part in run):
                if self._can_form_melds(self._subtract(counts, run)):
                    return True

        return False

    # ----- helpers --------------------------------------------------------
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
    def _result(is_winning, pattern):
        return {
            "is_winning": is_winning,
            "pattern": pattern,
            "description": PATTERN_LABELS.get(pattern, "Not a winning hand yet"),
        }
