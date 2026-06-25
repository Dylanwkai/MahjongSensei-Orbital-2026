# Person B task — Interactive Tutorial System (Feature 1)

Paste everything below into your Claude (in the same MahjongSensei repo / folder).

---

You are working in the **MahjongSensei** NUS Orbital repo — a beginner-friendly Singaporean Mahjong web app. Stack: React frontend, Django + Django REST Framework backend, PostgreSQL, SimpleJWT auth.

Two of us are working on the same GitHub repo in parallel right now. My partner is building the **Interactive Trainer** inside the `game` Django app and a new `Trainer.jsx` page. To avoid merge conflicts, **you must only touch the files listed in the "Files you own" section below. Do NOT edit anything in the `game` app, `users` app, `App.jsx`, `AppLayout.jsx`, or `HandHelper.jsx`.**

The routing and navigation for the Tutorial are **already wired** by my partner:
- `frontend/src/App.jsx` already has a protected route `"/tutorial"` rendering `./pages/Tutorial`.
- `frontend/src/components/AppLayout.jsx` already has a nav link to `/tutorial`.
- `frontend/src/pages/Tutorial.jsx` already exists as a **placeholder stub** — replace its contents with the real page.

So you never need to touch shared files. Just fill in the files you own.

## Your feature: Interactive Tutorial System (Feature 1)

A structured, module-based visual tutorial. Users progress through lessons covering tile recognition (bamboo, circles, characters, honours, flowers, animals), meld types (Pong, Kong, Chow), and winning-hand basics. Each module ends with a short quiz. **Completion state is saved to the database per user.**

## Files you own (only edit these)

Backend — the `tutorial` app:
- `backend/tutorial/models.py` — add `TutorialProgress` model
- `backend/tutorial/serializers.py` — NEW file
- `backend/tutorial/views.py` — list modules, fetch progress, mark module complete
- `backend/tutorial/urls.py` — wire your endpoints (currently empty)
- `backend/tutorial/admin.py` — register `TutorialProgress`
- `backend/tutorial/tests.py` — endpoint + model tests
- `backend/tutorial/migrations/` — your generated migration (tutorial app only)

Frontend:
- `frontend/src/pages/Tutorial.jsx` — replace the stub with the real page
- `frontend/src/components/` — you may ADD new component files (e.g. `TileCard.jsx`, `MeldDemo.jsx`, `Quiz.jsx`). Do not edit `AppLayout.jsx`.

## Backend spec

`TutorialProgress` model (in `tutorial` app):
- `user` → ForeignKey to `django.contrib.auth.models.User`, `on_delete=CASCADE`, `related_name="tutorial_progress"`
- `module_id` → CharField (e.g. `"tiles"`, `"melds"`, `"winning-hands"`)
- `completed` → BooleanField, default False
- `completed_at` → DateTimeField, null=True, blank=True
- `quiz_score` → IntegerField, null=True, blank=True
- add `class Meta: unique_together = ("user", "module_id")`

Endpoints (all `permission_classes = [IsAuthenticated]`, mounted under `/api/tutorial/`):
- `GET /api/tutorial/modules/` → returns the list of tutorial modules with the current user's completion status merged in. You can hardcode the module catalog (id, title, description, order) in Python — it doesn't need its own table.
- `GET /api/tutorial/progress/` → returns this user's `TutorialProgress` rows.
- `POST /api/tutorial/complete/` → body `{ "module_id": "tiles", "quiz_score": 4 }`; upserts a `TutorialProgress` row for `(request.user, module_id)` with `completed=True`, `completed_at=now()`, stores `quiz_score`. Return the updated row. Validate that `module_id` is one of the known modules (400 otherwise).

Use `request.user` for the user — never trust a user id from the request body. Follow the existing style in `backend/game/views.py` (APIView subclasses, DRF `Response`).

After writing models, generate the migration. For local testing without PostgreSQL you can run with SQLite:
```bash
cd backend
USE_SQLITE=True python manage.py makemigrations tutorial
USE_SQLITE=True python manage.py test tutorial
```
(The repo's `settings.py` already supports the `USE_SQLITE=True` env var.)

## Frontend spec

Replace `frontend/src/pages/Tutorial.jsx`. Wrap the page in the shared `AppLayout` (import from `../components/AppLayout`) and use the shared API client (`import api from '../api/axios'`) so JWT auth is attached automatically. Reuse the existing CSS classes used elsewhere (`eyebrow`, `primary-button`, `secondary-button`, `tile`, `tile-<suit>`, `panel-heading`, `empty-state`, `status-card`, etc. — see `HandHelper.jsx` and `Home.jsx` for the visual language) so it matches the app.

The page should:
- Fetch modules from `GET /api/tutorial/modules/` on mount and show them as a list/grid with completion ticks.
- Let the user open a module and step through its lessons (tile recognition with visual tile cards, meld demos).
- End each module with a short multiple-choice quiz; on completion, `POST /api/tutorial/complete/` with the score and reflect the saved completion state in the UI.

Tile rendering convention used across the app: a tile has `{ suit, value, code, label }`. Suits are `bamboo` (code prefix `B`), `circles` (`C`), `characters` (`K`), `honour` (`H`). Numbered tiles are values 1–9. Honour values: `east, south, west, north, red, green, white`. Render tiles with `className={`tile tile-${tile.suit}`}` containing a `.tile-code` and `.tile-label` span — copy the `Tile` component pattern from `Home.jsx`.

## Definition of done
- `USE_SQLITE=True python manage.py makemigrations tutorial` produces a migration and `python manage.py test tutorial` passes.
- The frontend builds (`cd frontend && npm run build`) and `/tutorial` renders, lists modules, lets a user complete one, and the completion persists across a page reload (because it's saved server-side).
- You did not modify any file outside the "Files you own" list.

Start by reading `backend/game/views.py`, `backend/users/models.py`, `frontend/src/pages/HandHelper.jsx`, and `frontend/src/pages/Home.jsx` to match the existing conventions, then build.
