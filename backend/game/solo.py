"""Solo Play engine (Feature 4) — Steps 1-4.

A full 4-player Singapore Mahjong table: one human seat (East by default) plus
three AI opponents. This module implements the core game loop:

  Step 1 - Player + SoloGame skeleton, dealing, flower replacement, dealer seat.
  Step 2 - Draw / discard turn loop, self-draw win detection, washout (wall out).
  Step 3 - AI opponents that draw and discard using the ValuationAlgorithm.
  Step 4 - Bonus tiles drawn mid-game are set aside and replaced; a player who
           draws a 4th matching tile may declare a concealed Kong and redraw.

Claiming Pong/Kong/Chow from other players' discards is Step 5 (not yet here);
turn order currently passes strictly to the next seat after each discard.

The engine is server-authoritative and self-contained (no Django imports), so it
can be unit-tested directly and later driven by an API.
"""

from collections import Counter

from .engine import (
    Deck,
    Hand,
    ValuationAlgorithm,
    WinChecker,
)

# Seats are seated counter-clockwise starting from the dealer (East).
SEAT_WINDS = ("east", "south", "west", "north")
HAND_SIZE = 13

# The last 15 tiles are the "dead wall" / reserve and are not drawn in normal
# play — when only 15 tiles remain the hand ends in a washout draw. (Kong and
# flower replacement tiles are taken from this reserve, so they may still draw
# below 15.)
WALL_RESERVE = 15


class Player:
    def __init__(self, seat_wind, is_human=False, name=None):
        self.seat_wind = seat_wind
        self.is_human = is_human
        self.name = name or seat_wind.capitalize()
        self.hand = Hand([])

    def all_tiles(self):
        """Concealed tiles plus every tile locked in a meld — the full hand used
        for win checking."""
        tiles = list(self.hand.tiles)
        for meld in self.hand.melds:
            tiles.extend(meld.tiles)
        return tiles

    def to_dict(self, reveal=False):
        return {
            "seat_wind": self.seat_wind,
            "name": self.name,
            "is_human": self.is_human,
            "melds": [meld.to_dict() for meld in self.hand.melds],
            "bonus_tiles": [tile.to_dict() for tile in self.hand.bonus_tiles],
            "tile_count": len(self.hand.tiles),
            # Concealed tiles are only revealed for the viewer (or once the game
            # is over) so opponents' hands stay hidden during play.
            "tiles": (
                [tile.to_dict() for tile in self.hand.sorted_tiles()] if reveal else None
            ),
        }


class SoloGame:
    def __init__(self, human_seat="east", round_wind="east"):
        if human_seat not in SEAT_WINDS:
            raise ValueError("human_seat must be one of east/south/west/north.")
        self.players = [
            Player(wind, is_human=(wind == human_seat)) for wind in SEAT_WINDS
        ]
        self.round_wind = round_wind
        self.deck = Deck()
        self.dealer_index = 0  # East deals
        self.current_index = 0
        self.discards = []  # list of (seat_index, Tile)
        self.last_discard = None
        self.last_drawn = None
        self.phase = "draw"  # 'draw' | 'discard' | 'over'
        self.result = None  # None (ongoing) | 'win' | 'washout'
        self.winner_index = None
        self.win_type = None  # 'self_draw' (claim wins come in Step 6)
        self.log = []

    # ----- setup (Step 1) -------------------------------------------------
    def start(self):
        self.deck.shuffle()
        for player in self.players:
            for _ in range(HAND_SIZE):
                self._deal_one(player)
        self.current_index = self.dealer_index
        self.phase = "draw"
        self._log(f"Game started. {self._current().name} is the dealer (East).")
        return self.play_until_human()

    def _deal_one(self, player):
        tile = self.deck.draw()
        while tile.is_bonus:
            player.hand.bonus_tiles.append(tile)
            tile = self.deck.draw()
        player.hand.tiles.append(tile)

    # ----- turn loop (Steps 2-4) -----------------------------------------
    def play_until_human(self):
        """Advance the game (running AI turns) until it is the human's turn to
        discard, or the game ends."""
        while self.result is None:
            player = self._current()

            if self.phase == "draw":
                drawn = self._draw_current()
                if self.result is not None:  # wall ran out -> washout
                    break
                if self._is_winning(player):
                    self._declare_win(self.current_index, "self_draw")
                    break
                self.phase = "discard"

            # phase == 'discard'
            if player.is_human:
                break  # wait for the human's discard

            # AI turn: optionally upgrade to a concealed Kong, then discard.
            if self._maybe_concealed_kong(player):
                if self.result is not None:
                    break
                if self._is_winning(player):
                    self._declare_win(self.current_index, "self_draw")
                    break
            self._do_discard(self._ai_discard_choice(player))

        return self

    def human_discard(self, suit, value):
        """Human action: discard a tile, then let the AI seats play on."""
        if self.result is not None:
            raise ValueError("The game is over.")
        player = self._current()
        if not player.is_human or self.phase != "discard":
            raise ValueError("It is not your turn to discard.")
        tile = next(
            (t for t in player.hand.tiles if t.suit == suit and t.value == value), None
        )
        if tile is None:
            raise ValueError("That tile is not in your hand.")
        self._do_discard(tile)
        return self.play_until_human()

    def human_declare_kong(self, suit, value):
        """Human action: declare a concealed Kong on your turn, then redraw."""
        if self.result is not None:
            raise ValueError("The game is over.")
        player = self._current()
        if not player.is_human or self.phase != "discard":
            raise ValueError("You can only declare a Kong on your turn.")
        if len(self.deck) < 2:
            raise ValueError("Not enough tiles left to Kong.")
        player.hand.declare_kong(suit, value, self.deck)
        self._log(f"{player.name} declared a concealed Kong of {value}.")
        if self._is_winning(player):
            self._declare_win(self.current_index, "self_draw")
        return self

    def _draw_current(self):
        player = self._current()
        tile = self._draw_live_tile(player)
        if tile is None:
            return None
        player.hand.tiles.append(tile)
        self.last_drawn = tile
        return tile

    def _draw_live_tile(self, player):
        """Draw a playable tile for a normal turn, setting aside any bonus tiles
        drawn. Triggers a washout once only the 15-tile reserve remains."""
        # Normal draws stop at the dead-wall reserve.
        if len(self.deck) <= WALL_RESERVE:
            self.phase = "over"
            self.result = "washout"
            self._log(
                f"Only the {WALL_RESERVE}-tile reserve remains — washout draw."
            )
            return None

        tile = self.deck.draw()
        # Flower replacements come from the reserve, so they may dip below it.
        while tile.is_bonus:
            player.hand.bonus_tiles.append(tile)
            self._log(f"{player.name} drew a bonus tile ({tile.label}) and redrew.")
            if len(self.deck) == 0:
                self.phase = "over"
                self.result = "washout"
                self._log("The wall is fully exhausted — washout draw.")
                return None
            tile = self.deck.draw()
        return tile

    def _do_discard(self, tile):
        player = self._current()
        player.hand.tiles.remove(tile)
        self.last_discard = tile
        self.discards.append((self.current_index, tile))
        self._log(f"{player.name} discarded {tile.label}.")
        self.current_index = (self.current_index + 1) % 4
        self.phase = "draw"

    def _maybe_concealed_kong(self, player):
        if len(self.deck) < 2:
            return False
        counts = Counter((t.suit, t.value) for t in player.hand.tiles)
        for (suit, value), count in counts.items():
            if count == 4:
                player.hand.declare_kong(suit, value, self.deck)
                self._log(f"{player.name} declared a concealed Kong of {value}.")
                return True
        return False

    def _ai_discard_choice(self, player):
        recommendation = ValuationAlgorithm().recommend_discard(player.hand)
        target = recommendation["discard"]
        for tile in player.hand.tiles:
            if tile.suit == target["suit"] and tile.value == target["value"]:
                return tile
        return player.hand.tiles[0]

    # ----- win / helpers --------------------------------------------------
    def _is_winning(self, player):
        return WinChecker().check(player.all_tiles())["is_winning"]

    def _declare_win(self, index, win_type):
        self.winner_index = index
        self.win_type = win_type
        self.result = "win"
        self.phase = "over"
        self._log(
            f"{self.players[index].name} wins by {win_type.replace('_', ' ')}!"
        )

    def _current(self):
        return self.players[self.current_index]

    def human_index(self):
        return next(i for i, p in enumerate(self.players) if p.is_human)

    def _log(self, message):
        self.log.append(message)

    # ----- serialization --------------------------------------------------
    def public_state(self):
        """The human's view of the table: own tiles revealed, opponents hidden
        (until the game is over)."""
        game_over = self.result is not None
        return {
            "round_wind": self.round_wind,
            "phase": self.phase,
            "result": self.result,
            "current_seat": self.players[self.current_index].seat_wind,
            "is_human_turn": self._current().is_human and not game_over,
            "wall_count": len(self.deck),
            "live_wall_count": max(0, len(self.deck) - WALL_RESERVE),
            "winner_seat": (
                self.players[self.winner_index].seat_wind
                if self.winner_index is not None
                else None
            ),
            "win_type": self.win_type,
            "last_discard": self.last_discard.to_dict() if self.last_discard else None,
            "discards": [
                {"seat": self.players[i].seat_wind, "tile": t.to_dict()}
                for i, t in self.discards
            ],
            "players": [
                p.to_dict(reveal=p.is_human or game_over) for p in self.players
            ],
            "log": self.log[-15:],
        }
