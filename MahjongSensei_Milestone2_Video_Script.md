# MahjongSensei — Milestone 2 Video Script

**Target length:** ~5 minutes (Orbital MS2 requirement). A tighter 5:00 cut and the optional add-ons are both marked below.
**Goal:** Showcase the working prototype (how to use it) **and** the engineering behind every feature (frontend + backend), plus problems encountered.
**Level of achievement:** Apollo.
**Format:** Screen recording with voiceover. Two columns below — **ON SCREEN** (what to do / show) and **SAY** (narration).

---

## Before you hit record — setup checklist

1. **Start the backend:** `cd backend && python manage.py runserver` → confirm `http://127.0.0.1:8000` is live.
2. **Start the frontend:** `cd frontend && npm start` → `http://localhost:3000`.
3. **Browser:** full-screen, clean tabs, zoom ~110% so tiles read clearly on camera. Hide bookmarks bar.
4. **Test account ready:** know a working username/password. Also have a *fresh* username ready to register live (proves real auth).
5. **Pre-stage hands** so you don't fumble live:
   - Hand Helper: a near-complete 14-tile hand with one obvious junk tile (e.g. a lone honour) so the recommendation is clear.
   - Have the Trainer and Solo Play tabs pre-loaded but not yet started.
6. **Screen recorder:** QuickTime (Mac: File → New Screen Recording) or OBS. Record mic + screen. Do a 10-second test for audio levels.
7. **Optional second window:** your code editor open on the engine files (`engine.py`, `views.py`) for the 2-second "here's the code" cutaways.
8. Close Slack/Mail/notifications. Silence the phone.

> Tip: record the demo and the voiceover in one take if you're comfortable, or record screen silently then narrate over it. Narrating over is more forgiving — you can re-do audio without re-doing clicks.

---

## SEGMENT 1 — Hook & problem (0:00–0:30)

| ON SCREEN | SAY |
|---|---|
| Title card or the login page. Logo / app name visible. | "Mahjong has one of the steepest learning curves of any tile game — tile recognition, hand structure, scoring, and knowing what to discard. And most beginners have no experienced player around to give feedback." |
| (hold) | "This is **MahjongSensei** — an interactive web app that teaches Singaporean Mahjong and trains your decision-making. I'm aiming for the **Apollo** level of achievement. Here's our Milestone 2 prototype." |

---

## SEGMENT 2 — Accounts & architecture (0:30–1:05)

| ON SCREEN | SAY |
|---|---|
| On the **Register** page, create a brand-new account live. Submit. | "Everything sits behind real authentication. I'll register a new account now." |
| It logs you in / land on **Home** dashboard. Point cursor at the nav bar and the "Backend connected" status. | "On the backend that's **Django REST Framework** issuing **JWT tokens** with SimpleJWT. The React frontend stores the access token and an Axios interceptor attaches it as a Bearer token to every API call." |
| Hover the URL / refresh the page once to show you stay logged in. | "Routes like Home, Tutorial and Trainer are protected — React restores the session on refresh by re-fetching the user profile, so a reload doesn't look logged out while the API stays locked down." |
| (Optional 2-sec cutaway to `settings.py` / `axios.js`.) | "Frontend in React, backend in Django talking over a REST API, with a pure-Python Mahjong engine underneath." |

---

## SEGMENT 3 — Tutorial (Feature 1) (1:05–1:45)

| ON SCREEN | SAY |
|---|---|
| Click **Tutorial**. Show the 3 module cards (Tile Recognition, Meld Types, Winning Hands). | "Feature one is the guided **Tutorial**. Three modules take a complete beginner from reading tiles to forming a winning hand." |
| Open **Tile Recognition**. Scroll the lessons — show the rendered tile graphics (suits, honours, flowers, animals). | "Each lesson renders real tiles with a reusable `TileCard` component — the three numbered suits, the honour tiles, and the flower and animal bonus tiles unique to Singapore Mahjong." |
| Open **Meld Types** — show the `MeldDemo` for Pong / Kong / Chow. | "The melds module visually demonstrates Pong, Kong and Chow." |
| Take the end-of-module **Quiz**, answer it, and let it mark the module complete. | "Every module ends in an interactive quiz. On the backend a `TutorialProgress` model saves completion and your quiz score per user — so progress persists across sessions." |

---

## SEGMENT 4 — Hand Helper (Feature 2) (1:45–2:35)

| ON SCREEN | SAY |
|---|---|
| Click **Hand Helper**. Show the visual tile picker. | "Feature two is the **Hand Helper** — the heart of the app's decision support." |
| Build (or load) a 14-tile hand by clicking tiles. Show the count climbing to 14 and the per-tile 'x/4' counter. | "I assemble a fourteen-tile hand with the tile picker. The frontend tracks counts and won't let me exceed four copies of any tile." |
| Click **Recommend Discard**. Show the recommended tile + the reasoning + score. | "I ask for a recommendation, and the app tells me exactly which tile to throw — and *why*." |
| (Optional cutaway to `engine.py` `ValuationAlgorithm` / `HandEvaluator`.) | "Behind this is a custom Python engine. A `HandEvaluator` scores a hand by rewarding complete sets, pairs and near-sequences, and penalising isolated tiles. The `ValuationAlgorithm` then simulates discarding *every* tile and returns the one that leaves the strongest hand. The API validates the input — tile count, valid suits and values, max four copies — before it ever reaches the engine." |

---

## SEGMENT 5 — Interactive Trainer (Feature 3) (2:35–3:20)

| ON SCREEN | SAY |
|---|---|
| Click **Trainer**. A hand is dealt automatically. | "Feature three turns that engine into practice — the **Interactive Trainer**." |
| Pick a tile to discard. Submit. Show the immediate feedback (correct / not optimal + reasoning). | "I'm dealt a hand and asked to choose the best discard. The app scores my choice against the valuation algorithm and gives instant feedback — and a tie with the best discard still counts as correct, because several discards can be equally good." |
| Point at the running accuracy / attempts counter. Optionally request a new hand. | "Every attempt is logged. On the backend, `Session` and `Move` models record each hand, my discard, the optimal discard and whether I got it right, then report running accuracy — the foundation for play-style tracking." |

---

## SEGMENT 6 — Solo Play + scoring (Feature 4) (3:20–4:20)

| ON SCREEN | SAY |
|---|---|
| Click **Solo Play**. Start a new game. | "Feature four is **Solo Play** — a full single-player game against three AI opponents." |
| Show your hand, the three opponents (tile counts hidden), the discard pile. Take a turn: draw, then discard a tile. | "I play as East. I draw and discard; the three computer players take their turns automatically using the same valuation engine. Opponents' hands stay hidden, just like a real table." |
| If a Kong is available, declare it; otherwise mention it. Let a few turns play out. | "The engine handles the full turn loop — dealing, draws, flower replacement, concealed Kongs that draw a replacement tile, self-drawn wins, and the washout draw when the wall runs low." |
| (Optional cutaway to `engine.py` `WinChecker` / `ScoreCalculator`.) | "And it's scored properly. A `WinChecker` recognises three winning shapes — the standard four-melds-and-a-pair, Seven Pairs, and Thirteen Orphans. A `ScoreCalculator` then scores the win in **tai** using Singapore rules: seat and round winds, dragons, flowers by seat, all-pongs, half and full flush — and it reads the hand every possible way to give you the highest legal score." |

---

## SEGMENT 7 — Engineering & testing story (4:20–4:50)

| ON SCREEN | SAY |
|---|---|
| Cut to the terminal. Run `python manage.py test` (or show a prior passing run). | "On software engineering: the Mahjong logic is deliberately separated from the API views, so the same engine powers the Hand Helper, the Trainer and Solo Play. It's backed by about **seventy automated backend tests** across the engine, valuation, win checker, scoring, tutorial and every API endpoint." |
| Show the green test summary, then briefly the GitHub repo (branches / PRs / issues). | "We work with GitHub issues, feature branches and pull-request reviews, and we verify the frontend with a production build." |

---

## SEGMENT 8 — Problems encountered & close (4:50–5:15)

| ON SCREEN | SAY |
|---|---|
| Back on the app — Home or Profile page. | "A few problems we solved this milestone: a Trainer 500 error caused by duplicate play sessions, JWT token-expiry handling on the frontend, and recurring API failures we traced down to unapplied database migrations." |
| Show the Profile page (stats) as a closing shot. | "That's the MahjongSensei prototype: tutorial, hand helper, trainer and solo play — a React front end, a Django REST back end, and a custom Python Mahjong engine tying it together. Next milestone: probability-based recommendations, a richer stats dashboard, and claiming melds in Solo Play. Thanks for watching." |

---

## Timing summary

| Segment | Topic | Target | Running |
|---|---|---|---|
| 1 | Hook & problem | 0:30 | 0:30 |
| 2 | Accounts & architecture | 0:35 | 1:05 |
| 3 | Tutorial | 0:40 | 1:45 |
| 4 | Hand Helper | 0:50 | 2:35 |
| 5 | Trainer | 0:45 | 3:20 |
| 6 | Solo Play + scoring | 1:00 | 4:20 |
| 7 | Engineering & testing | 0:30 | 4:50 |
| 8 | Problems & close | 0:25 | 5:15 |

**If you must hit a hard 5:00:** trim the architecture detail in Segment 2 and the scoring detail in Segment 6 — keep the *demos* intact, shorten the *narration*.

---

## Narration-only script (for one continuous voiceover take)

> Mahjong has one of the steepest learning curves of any tile game — tile recognition, hand structure, scoring, and knowing what to discard — and most beginners have no experienced player around to give feedback. This is MahjongSensei, an interactive web app that teaches Singaporean Mahjong and trains your decision-making. I'm aiming for the Apollo level. Here's our Milestone 2 prototype.
>
> Everything sits behind real authentication — I'll register a new account now. On the backend that's Django REST Framework issuing JWT tokens; the React frontend stores the access token and an Axios interceptor attaches it to every request. Protected routes survive a refresh because React restores the session from the user profile.
>
> Feature one is the guided Tutorial — three modules from reading tiles to forming a winning hand, each lesson rendering real tiles, and each module ending in a quiz whose results we persist per user in the database.
>
> Feature two is the Hand Helper. I build a fourteen-tile hand with the visual picker, and the app recommends exactly which tile to discard and why. Underneath, a Python engine evaluates the hand, simulates every possible discard, and keeps the strongest — with full input validation in the API.
>
> Feature three, the Interactive Trainer, turns that engine into practice: I'm dealt a hand, I pick a discard, and I get instant feedback scored against the optimal play, with every attempt logged and my running accuracy tracked.
>
> Feature four is Solo Play — a full game against three AI opponents. The engine handles dealing, draws, flowers, concealed Kongs, self-drawn wins and washouts, and scores wins in tai using Singapore rules across three winning shapes.
>
> On engineering: the Mahjong logic is separated from the API views and reused everywhere, backed by around seventy automated tests, GitHub issues, feature branches and PR reviews. Problems we solved this milestone included a Trainer session bug, JWT expiry handling, and database-migration mismatches.
>
> That's MahjongSensei — React front end, Django REST back end, custom Python engine. Next up: probability-based recommendations, a richer dashboard, and meld-claiming in Solo Play. Thanks for watching.
