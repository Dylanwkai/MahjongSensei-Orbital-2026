import random
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
