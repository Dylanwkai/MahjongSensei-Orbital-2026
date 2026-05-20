import random

class Tile:
    def __init__(self, suit, value, is_bonus = False):
        self.suit = suit #bamboo, characters, circles, special, bonus
        self.value = value #1-9 for bamboo, characters, circles; special is north/south/east/west/white/green/red; 
                            #bonus is chicken/centipede/cat/rat/r1-4/b1-4
        self.is_bonus = is_bonus #True for animal and flowers

    def __repr__(self):
        return self.suit + str(self.value)
    
    def __eq__(self, other):
        if not isinstance(other, Tile):
            return NotImplemented
        return self.suit == other.suit and self.value == other.value
    
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

    #def get_bonus_points(self):
        #return len(self.bonus_tiles)

    def __repr__(self):
        return f'Hand: {self.tiles} | Bonus: {self.bonus_tiles}'
    
class Deck:
    def __init__(self):
        self.tiles = self._build_deck()

    def _build_deck(self):
        tiles = []

        # Numbered suits — 4 copies of each (36 × 3 = 108 tiles)
        for suit in ['bamboo', 'circles', 'characters']:
            for value in range(1, 10):
                for _ in range(4):
                    tiles.append(Tile(suit, value))

        # Honour tiles — 4 copies of each (7 × 4 = 28 tiles)
        for value in ['east', 'west', 'north', 'south', 'red', 'green', 'white']:
            for _ in range(4):
                tiles.append(Tile('honour', value))

        # Flower tiles — 1 copy each (8 tiles, is_bonus=True)
        for value in ['red_1', 'red_2', 'red_3', 'red_4',
                      'blue_1', 'blue_2', 'blue_3', 'blue_4']:
            tiles.append(Tile('flower', value, is_bonus=True))

        # Animal tiles — 1 copy each (4 tiles, is_bonus=True)
        for value in ['cat', 'mouse', 'centipede', 'chicken']:
            tiles.append(Tile('animal', value, is_bonus=True))

        return tiles

    def shuffle(self):
        import random
        random.shuffle(self.tiles)

    def draw(self):
        return self.tiles.pop()

class HandGenerator:
    def generate_random_hand(self):
        deck = Deck()
        deck.shuffle()
        
        tiles = []
        bonus_tiles = []
        
        # Keep drawing until we have 13 valid non-bonus tiles
        while len(tiles) < 13:
            if not deck.tiles:
                raise ValueError("Deck ran out of tiles")
            drawn = deck.draw()
            if drawn.is_bonus:
                bonus_tiles.append(drawn)  # set aside, draw again
            else:
                tiles.append(drawn)
        
        hand = Hand(tiles)
        hand.bonus_tiles = bonus_tiles  # attach any bonus tiles that were drawn
        return hand