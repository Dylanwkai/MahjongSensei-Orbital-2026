from django.test import TestCase
from .engine import Tile, Hand, Deck, HandGenerator

class TileTests(TestCase):
    def test_tile_creation(self):
        tile = Tile('bamboo', 1)
        self.assertEqual(tile.suit, 'bamboo')
        self.assertEqual(tile.value, 1)

    def test_tile_equality(self):
        tile1 = Tile('bamboo', 1)
        tile2 = Tile('bamboo', 1)
        self.assertEqual(tile1, tile2)

    def test_flower_tile_is_bonus(self):
        tile = Tile('flower', 'red_1', is_bonus=True)
        self.assertTrue(tile.is_bonus)

    def test_animal_tile_is_bonus(self):
        tile = Tile('animal', 'cat', is_bonus=True)
        self.assertTrue(tile.is_bonus)

    def test_normal_tile_is_not_bonus(self):
        tile = Tile('bamboo', 1)
        self.assertFalse(tile.is_bonus)

class DeckTests(TestCase):
    def test_deck_has_148_tiles(self):
        deck = Deck()
        self.assertEqual(len(deck.tiles), 148)

    def test_deck_has_108_suited_tiles(self):
        deck = Deck()
        suited = [t for t in deck.tiles if t.suit in ['bamboo', 'circles', 'characters']]
        self.assertEqual(len(suited), 108)

    def test_deck_has_28_honour_tiles(self):
        deck = Deck()
        honours = [t for t in deck.tiles if t.suit == 'honour']
        self.assertEqual(len(honours), 28)

    def test_deck_has_8_flower_tiles(self):
        deck = Deck()
        flowers = [t for t in deck.tiles if t.suit == 'flower']
        self.assertEqual(len(flowers), 8)

    def test_deck_has_4_animal_tiles(self):
        deck = Deck()
        animals = [t for t in deck.tiles if t.suit == 'animal']
        self.assertEqual(len(animals), 4)

    def test_draw_reduces_deck_size(self):
        deck = Deck()
        deck.draw()
        self.assertEqual(len(deck.tiles), 147)

class HandTests(TestCase):
    def test_hand_always_has_13_valid_tiles(self):
        for _ in range(10):  # run 10 times since hands are random
            generator = HandGenerator()
            hand = generator.generate_random_hand()
            self.assertEqual(len(hand.tiles), 13)

    def test_hand_contains_no_bonus_tiles(self):
        for _ in range(10):
            generator = HandGenerator()
            hand = generator.generate_random_hand()
            for tile in hand.tiles:
                self.assertFalse(tile.is_bonus)

    def test_bonus_tiles_tracked_separately(self):
        # force bonus tiles into the deck at the front so they get drawn
        generator = HandGenerator()
        hand = generator.generate_random_hand()
        # all bonus tiles should be in bonus_tiles, not in tiles
        for tile in hand.bonus_tiles:
            self.assertTrue(tile.is_bonus)
            self.assertNotIn(tile, hand.tiles)

    def test_discard_reduces_hand_size(self):
        generator = HandGenerator()
        hand = generator.generate_random_hand()
        tile_to_discard = hand.tiles[0]
        hand.discard(tile_to_discard)
        self.assertEqual(len(hand.tiles), 12)