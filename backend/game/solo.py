"""Solo Play: a 4 player game with one human (East) and three AI opponents.

Covers dealing, the draw/discard loop, claims, Ron, scoring, and the washout.
No Django imports so it can be tested on its own.
"""

from collections import Counter

from .engine import (
    NUMBERED_SUITS,
    Deck,
    Hand,
    HandEvaluator,
    ScoreCalculator,
    Tile,
    ValuationAlgorithm,
    WinChecker,
)

SEAT_WINDS = ("east", "south", "west", "north")
HAND_SIZE = 13

# Stop normal draws once only this many tiles are left (the dead wall). Kong and
# flower replacements can still be drawn from it.
WALL_RESERVE = 15

# Claim priority: a win beats a Pong/Kong, which beats a Chow.
CLAIM_PRIORITY = {"win": 3, "kong": 2, "pong": 2, "chow": 1}

# How much a locked, completed meld is worth when an AI weighs up a claim. Set
# near a concealed triplet's value so claiming a set the AI already half-holds
# reads as progress, while claims that would break up useful tiles do not.
MELD_STRENGTH = 9


class Player:
    def __init__(self, seat_wind, is_human=False, name=None):
        self.seat_wind = seat_wind
        self.is_human = is_human
        self.name = name or seat_wind.capitalize()
        self.hand = Hand([])

    def all_tiles(self):
        """Concealed tiles plus the tiles in any melds, used for win checking."""
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
    def __init__(self, human_seat="east", round_wind="east", dealer_index=0):
        if human_seat not in SEAT_WINDS:
            raise ValueError("human_seat must be one of east/south/west/north.")
        if dealer_index not in range(4):
            raise ValueError("dealer_index must be 0 to 3.")
        self.players = [
            Player(wind, is_human=(wind == human_seat)) for wind in SEAT_WINDS
        ]
        self.round_wind = round_wind
        self.deck = Deck()
        self.dealer_index = dealer_index  # which seat deals (the banker)
        self.current_index = dealer_index
        self.discards = []  # list of [seat_index, Tile, claim]; claim is None
        # until the tile is claimed, then {"by": index, "as": action}.
        self.last_discard = None
        self.last_drawn = None
        self.phase = "draw"  # 'draw' | 'discard' | 'claim' | 'over'
        self.result = None  # None (ongoing) | 'win' | 'washout'
        self.winner_index = None
        self.win_type = None  # 'self_draw' | 'ron'
        self.winning_tile = None  # the tile that completed the hand
        self.win_result = None  # WinChecker result for the winning hand
        self.win_score = None  # ScoreCalculator result for the winning hand
        self.pending_claim = None  # set while phase == 'claim'
        self.log = []

    def start(self):
        self.deck.shuffle()
        for player in self.players:
            for _ in range(HAND_SIZE):
                self._deal_one(player)
        self.current_index = self.dealer_index
        self.phase = "draw"
        dealer = self.players[self.dealer_index]
        self._log(
            f"Game started. {dealer.name} is the banker for the "
            f"{self.round_wind} round."
        )
        return self.play_until_human()

    def _deal_one(self, player):
        tile = self.deck.draw()
        while tile.is_bonus:
            player.hand.bonus_tiles.append(tile)
            tile = self.deck.draw()
        player.hand.tiles.append(tile)

    def play_until_human(self):
        """Run AI turns until the human must act (discard or claim) or the game
        ends."""
        while self.result is None:
            if self.phase == "claim":
                break  # waiting for the human's claim decision

            if self.phase == "draw":
                self._draw_current()
                if self.result is not None:  # wall ran out -> washout
                    break
                if self._is_valid_win(self._current()):
                    self._declare_win(self.current_index, "self_draw", self.last_drawn)
                    break
                self.phase = "discard"

            # phase == 'discard'
            player = self._current()
            if player.is_human:
                break  # wait for the human's discard

            # AI turn: optionally upgrade to a concealed Kong, then discard.
            if self._maybe_concealed_kong(player):
                if self.result is not None:
                    break
                if self._is_valid_win(player):
                    self._declare_win(self.current_index, "self_draw", None)
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
        """Human action on your turn, then redraw: either declare a concealed
        Kong (four matching tiles in hand) or upgrade an exposed Pong to a Kong
        with the fourth tile you have just drawn."""
        if self.result is not None:
            raise ValueError("The game is over.")
        player = self._current()
        if not player.is_human or self.phase != "discard":
            raise ValueError("You can only declare a Kong on your turn.")
        if len(self.deck) < 2:
            raise ValueError("Not enough tiles left to Kong.")

        concealed = sum(
            1 for t in player.hand.tiles if t.suit == suit and t.value == value
        )
        if concealed >= 4:
            player.hand.declare_kong(suit, value, self.deck)
            self._log(f"{player.name} declared a concealed Kong of {value}.")
        else:
            player.hand.promote_pong_to_kong(suit, value, self.deck)
            self._log(f"{player.name} added the fourth tile to their Pong of {value} for a Kong.")

        if self._is_valid_win(player):
            self._declare_win(self.current_index, "self_draw", None)
        return self

    def human_claim(self, action, low_value=None):
        """Human action: claim the current discard as a Pong/Kong/Chow/Win."""
        if self.result is not None:
            raise ValueError("The game is over.")
        if self.phase != "claim" or not self.pending_claim:
            raise ValueError("There is nothing to claim right now.")

        options = self.pending_claim["options"]
        if not options or action not in options["actions"]:
            raise ValueError("You cannot make that claim.")

        tile = self.pending_claim["tile"]
        discarder = self.pending_claim["discarder"]
        ai_actions = self.pending_claim["ai_actions"]

        # An AI holding a strictly higher priority claim takes precedence.
        best_ai = max(
            (CLAIM_PRIORITY[a] for a in ai_actions.values()), default=0
        )
        if best_ai > CLAIM_PRIORITY[action]:
            self._execute_best_ai(ai_actions, discarder, tile)
            return self.play_until_human()

        self._execute_claim(self.human_index(), action, tile, low_value=low_value)
        return self.play_until_human()

    def human_pass_claim(self):
        """Human action: pass on a claim, letting any waiting AI seat act."""
        if self.result is not None:
            raise ValueError("The game is over.")
        if self.phase != "claim" or not self.pending_claim:
            raise ValueError("There is no claim to pass on.")
        pending = self.pending_claim
        self.pending_claim = None
        self._execute_best_ai(pending["ai_actions"], pending["discarder"], pending["tile"])
        return self.play_until_human()

    def _draw_current(self):
        player = self._current()
        tile = self._draw_live_tile(player)
        if tile is None:
            return None
        player.hand.tiles.append(tile)
        self.last_drawn = tile
        return tile

    def _draw_live_tile(self, player):
        """Draw a normal tile, setting aside any bonus tiles. Returns None and
        ends the game in a washout once only the reserve is left."""
        if len(self.deck) <= WALL_RESERVE:
            self.phase = "over"
            self.result = "washout"
            self._log(f"Only {WALL_RESERVE} tiles left, washout draw.")
            return None

        tile = self.deck.draw()
        # Flower replacements come from the reserve, so they may dip below it.
        while tile.is_bonus:
            player.hand.bonus_tiles.append(tile)
            self._log(f"{player.name} drew a bonus tile ({tile.label}) and redrew.")
            if len(self.deck) == 0:
                self.phase = "over"
                self.result = "washout"
                self._log("Wall fully exhausted, washout draw.")
                return None
            tile = self.deck.draw()
        return tile

    def _do_discard(self, tile):
        player = self._current()
        player.hand.tiles.remove(tile)
        self.last_discard = tile
        self.discards.append([self.current_index, tile, None])
        self._log(f"{player.name} discarded {tile.label}.")
        self._open_claims()

    def _open_claims(self):
        """After a discard, work out who can claim the tile. If the human has a
        claim they could win the contest for, pause for their decision;
        otherwise resolve any AI claim automatically."""
        discarder = self.current_index
        tile = self.last_discard
        human_i = self.human_index()

        human_opts = self._player_claims(human_i, discarder, tile)
        best_human = human_opts["priority"] if human_opts else 0

        # Each AI seat commits to a single action based on a simple heuristic.
        ai_actions = {}
        best_ai = 0
        for index in range(4):
            if index == human_i:
                continue
            opts = self._player_claims(index, discarder, tile)
            if not opts:
                continue
            action = self._ai_will_claim(self.players[index], opts, tile)
            if action is None:
                continue
            ai_actions[index] = action
            best_ai = max(best_ai, CLAIM_PRIORITY[action])

        if best_human == 0 and best_ai == 0:
            self._advance_turn()
            return

        # If an AI outranks anything the human could do, the human never gets a
        # say, so resolve it straight away.
        if best_ai > best_human:
            self._execute_best_ai(ai_actions, discarder, tile)
            return

        self.pending_claim = {
            "discarder": discarder,
            "tile": tile,
            "options": human_opts,
            "ai_actions": ai_actions,
        }
        self.phase = "claim"
        self._log(
            f"You can claim {tile.label} from {self.players[discarder].name}."
        )

    def _player_claims(self, index, discarder, tile):
        """All claim actions player `index` could structurally make on `tile`.
        Returns {actions, priority, chow_runs} or None."""
        if index == discarder:
            return None
        player = self.players[index]
        suit, value = tile.suit, tile.value

        actions = []
        chow_runs = []

        if self._would_win_on(player, tile):
            actions.append("win")

        matches = sum(1 for t in player.hand.tiles if t.suit == suit and t.value == value)
        if matches >= 3 and len(self.deck) > 0:
            actions.append("kong")
        if matches >= 2:
            actions.append("pong")

        # A Chow may only be claimed by the seat immediately after the discarder.
        if index == (discarder + 1) % 4 and suit in NUMBERED_SUITS and isinstance(value, int):
            chow_runs = self._chow_runs(player, suit, value)
            if chow_runs:
                actions.append("chow")

        if not actions:
            return None
        priority = max(CLAIM_PRIORITY[a] for a in actions)
        return {"actions": actions, "priority": priority, "chow_runs": chow_runs}

    def _chow_runs(self, player, suit, value):
        """Lowest values of every three-in-a-row the player can build with the
        discard `value`, using two tiles already in hand."""
        held = Counter(t.value for t in player.hand.tiles if t.suit == suit)
        runs = []
        for low in (value - 2, value - 1, value):
            if low < 1 or low + 2 > 9:
                continue
            needed = [v for v in (low, low + 1, low + 2) if v != value]
            if all(held.get(v, 0) >= 1 for v in needed):
                runs.append(low)
        return runs

    def _ai_will_claim(self, player, opts, tile):
        """Which action an AI seat commits to. It always takes a win. For a
        Pong, Kong or Chow (any suit) it forms the meld only if doing so leaves
        the hand stronger than passing, so it claims tiles that help and leaves
        the rest. The highest-priority helpful claim (kong > pong > chow) wins."""
        actions = opts["actions"]
        if "win" in actions:
            return "win"

        baseline = self._hand_strength(player.hand.tiles, len(player.hand.melds))
        for action in ("kong", "pong", "chow"):
            if action not in actions:
                continue
            strength = self._claim_strength(player, action, tile)
            if strength is not None and strength > baseline:
                return action
        return None

    def _hand_strength(self, tiles, meld_count):
        """A rough score for a hand: the concealed tiles' shape plus a bonus for
        each completed meld already locked away."""
        return HandEvaluator().evaluate_hand(tiles) + MELD_STRENGTH * meld_count

    def _claim_strength(self, player, action, tile):
        """Hand strength if the AI makes this claim (before it discards), or None
        if it cannot form the meld."""
        suit, value = tile.suit, tile.value
        concealed = list(player.hand.tiles)
        used = []

        if action in ("pong", "kong"):
            need = 3 if action == "kong" else 2
            matches = [t for t in concealed if t.suit == suit and t.value == value]
            if len(matches) < need:
                return None
            used = matches[:need]
        elif action == "chow":
            runs = self._chow_runs(player, suit, value)
            if not runs:
                return None
            low = runs[0]
            for needed_value in (v for v in (low, low + 1, low + 2) if v != value):
                match = next(
                    (t for t in concealed if t.suit == suit and t.value == needed_value),
                    None,
                )
                if match is None:
                    return None
                used.append(match)
        else:
            return None

        remaining = list(concealed)
        for used_tile in used:
            remaining.remove(used_tile)
        return self._hand_strength(remaining, len(player.hand.melds) + 1)

    def _execute_best_ai(self, ai_actions, discarder, tile):
        """Run the highest priority AI claim; ties go to the seat nearest after
        the discarder. Falls back to advancing the turn if none want it."""
        if not ai_actions:
            self._advance_turn()
            return
        best = max(CLAIM_PRIORITY[a] for a in ai_actions.values())
        candidates = [i for i, a in ai_actions.items() if CLAIM_PRIORITY[a] == best]
        winner = min(candidates, key=lambda i: (i - discarder) % 4)
        self._execute_claim(winner, ai_actions[winner], tile)

    def _execute_claim(self, index, action, tile, low_value=None):
        suit, value = tile.suit, tile.value
        # The claimed tile stays in the discard pile but is tagged with who took
        # it and how, so the table can show that it was eaten rather than having
        # it silently vanish.
        if self.discards and self.discards[-1][1] is tile:
            self.discards[-1][2] = {"by": index, "as": action}
        self.pending_claim = None
        player = self.players[index]

        if action == "win":
            player.hand.tiles.append(Tile(suit, value))
            self._declare_win(index, "ron", Tile(suit, value))
            return

        if action == "pong":
            player.hand.claim_pong(suit, value)
            self._log(f"{player.name} claimed a Pong of {tile.label}.")
        elif action == "kong":
            player.hand.claim_kong(suit, value, self.deck)
            self._log(f"{player.name} claimed a Kong of {tile.label}.")
            if self._is_valid_win(player):
                self._declare_win(index, "self_draw", None)
                return
        elif action == "chow":
            runs = self._chow_runs(player, suit, value)
            low = low_value if low_value in runs else (runs[0] if runs else None)
            if low is None:
                raise ValueError("You do not hold the tiles needed to claim this Chow.")
            player.hand.claim_chow(suit, low, claimed_value=value)
            self._log(f"{player.name} claimed a Chow using {tile.label}.")
        else:
            raise ValueError("Unknown claim action.")

        # The claimer takes the turn and must now discard.
        self.current_index = index
        self.last_discard = None
        self.phase = "discard"

    def _advance_turn(self):
        self.pending_claim = None
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

    def _is_winning(self, player):
        """Structural win check (ignores the minimum-tai rule)."""
        return WinChecker().check(player.all_tiles())["is_winning"]

    def _is_valid_win(self, player):
        """A win is only valid if the hand is complete and clears the minimum
        tai. This is only ever checked for self-drawn wins, so Pinghu is scored
        with self-draw context. Bonus tiles are scored for the winner's seat."""
        win_result = WinChecker().check(player.all_tiles())
        if not win_result["is_winning"]:
            return False
        score = ScoreCalculator(player.seat_wind, self.round_wind).score(
            win_result, player.hand.bonus_tiles, win_type="self_draw"
        )
        return score["is_valid_win"]

    def _would_win_on(self, player, tile):
        """True if `player` completes a valid winning hand on `tile` (Ron).
        Pinghu is scored with Ron context so its two-sided-wait rule applies."""
        winning_tile = Tile(tile.suit, tile.value)
        combined = player.all_tiles() + [winning_tile]
        win_result = WinChecker().check(combined)
        if not win_result["is_winning"]:
            return False
        score = ScoreCalculator(player.seat_wind, self.round_wind).score(
            win_result,
            player.hand.bonus_tiles,
            win_type="ron",
            winning_tile=winning_tile,
        )
        return score["is_valid_win"]

    def _declare_win(self, index, win_type, winning_tile):
        self.winner_index = index
        self.win_type = win_type
        self.winning_tile = winning_tile
        self.result = "win"
        self.phase = "over"
        self.pending_claim = None

        winner = self.players[index]
        win_result = WinChecker().check(winner.all_tiles())
        score = ScoreCalculator(winner.seat_wind, self.round_wind).score(
            win_result,
            winner.hand.bonus_tiles,
            win_type=win_type,
            winning_tile=winning_tile,
        )
        self.win_result = win_result
        self.win_score = score
        self._log(
            f"{winner.name} wins by {win_type.replace('_', ' ')} "
            f"for {score['total_tai']} tai!"
        )

    def _current(self):
        return self.players[self.current_index]

    def human_index(self):
        return next(i for i, p in enumerate(self.players) if p.is_human)

    def _log(self, message):
        self.log.append(message)

    def _claim_public(self):
        """Claim options to show the human, or None when not their decision."""
        if self.phase != "claim" or not self.pending_claim:
            return None
        pending = self.pending_claim
        options = pending["options"]
        return {
            "tile": pending["tile"].to_dict(),
            "from_seat": self.players[pending["discarder"]].seat_wind,
            "actions": options["actions"],
            "chow_options": options["chow_runs"],
        }

    def _win_public(self):
        """Winning hand plus its tai breakdown, or None if no one has won."""
        if self.result != "win" or self.winner_index is None:
            return None
        winner = self.players[self.winner_index]
        score = self.win_score or {}
        result = self.win_result or {}
        return {
            "winner_seat": winner.seat_wind,
            "winner_name": winner.name,
            "win_type": self.win_type,
            "winning_tile": self.winning_tile.to_dict() if self.winning_tile else None,
            "pattern": result.get("pattern"),
            "pattern_label": result.get("description"),
            "total_tai": score.get("total_tai", 0),
            "hand_tai": score.get("hand_tai", 0),
            "bonus_tai": score.get("bonus_tai", 0),
            "breakdown": score.get("breakdown", []),
            "tiles": [tile.to_dict() for tile in winner.hand.sorted_tiles()],
            "melds": [meld.to_dict() for meld in winner.hand.melds],
            "bonus_tiles": [tile.to_dict() for tile in winner.hand.bonus_tiles],
        }

    def public_state(self):
        """Return the table from the human's side: own tiles shown, opponents
        hidden until the game ends."""
        game_over = self.result is not None
        return {
            "round_wind": self.round_wind,
            "dealer": self.players[self.dealer_index].seat_wind,
            "phase": self.phase,
            "result": self.result,
            "current_seat": self.players[self.current_index].seat_wind,
            "is_human_turn": (
                self._current().is_human and not game_over and self.phase == "discard"
            ),
            "awaiting_claim": self.phase == "claim",
            "claim": self._claim_public(),
            "win": self._win_public(),
            "wall_count": len(self.deck),
            "live_wall_count": max(0, len(self.deck) - WALL_RESERVE),
            "winner_seat": (
                self.players[self.winner_index].seat_wind
                if self.winner_index is not None
                else None
            ),
            "win_type": self.win_type,
            "last_discard": self.last_discard.to_dict() if self.last_discard else None,
            "last_drawn": self.last_drawn.to_dict() if self.last_drawn else None,
            "discards": [
                {
                    "seat": self.players[i].seat_wind,
                    "tile": t.to_dict(),
                    "claimed_by": (
                        self.players[claim["by"]].seat_wind if claim else None
                    ),
                    "claimed_as": claim["as"] if claim else None,
                }
                for i, t, claim in self.discards
            ],
            "players": [
                p.to_dict(reveal=p.is_human or game_over) for p in self.players
            ],
            "log": self.log[-15:],
        }
