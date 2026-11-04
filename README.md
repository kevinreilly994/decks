# Decks — DJ Booking Database

A private, internal booking database for house-music DJs. **Phase 1 (this repo):**
the Django foundation — data model, an admin panel for hand-curating the roster,
internal-only auth, a popularity-score engine, a swappable data-provider seam, and
seeded demo data. The buyer-facing UI (directory, profiles, leaderboard, shortlist)
is Phase 2; live Spotify / Bandsintown / Instagram feeds are Phase 3.

## Stack
- Python 3.12+ · Django 5.2 · PostgreSQL (SQLite by default in dev)
- `django-environ` (config), `Pillow` (headshots), `whitenoise` (static)
- `pytest-django` + `ruff`

## Quickstart (dev, SQLite — no Postgres needed)
```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                  # optional in dev; SQLite is the default
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo            # loads the 12 fictional demo DJs
python manage.py recompute_scores     # computes the popularity leaderboard
python manage.py runserver            # open http://127.0.0.1:8000/admin/
```

## Using Postgres
Set `DATABASE_URL` in `.env`, e.g.
`DATABASE_URL=postgres://decks:decks@localhost:5432/decks`, install
`requirements-prod.txt`, then `migrate`.

## Management commands
- `seed_demo` — idempotently loads the 12 demo DJs (all fictional).
- `recompute_scores` — recomputes `PopularityScore` for every active DJ.

## Project layout
```
config/            project (split settings: base / dev / prod), urls
roster/
  models.py        Genre, DJ, SocialAccount, Management, Show, Release,
                   EngagementSnapshot, PopularityScore
  admin.py         curation admin (inlines, headshot preview, score column)
  scoring.py       popularity-score algorithm (weights in settings)
  providers/       swappable data-provider seam (base, manual, registry, service)
  management/commands/   seed_demo, recompute_scores
  tests/           pytest-django suite
```

## Popularity score
A 0–100 composite. Each component is min-max normalized across the active roster,
then weighted (tune in `config/settings/base.py` -> `DECKS_SCORE_WEIGHTS`):
streaming 35% · social 25% · engagement 20% · booking demand 20%. `delta_7d`
tracks movement since the previous run.

## Data-provider seam
`roster/providers/` defines `DataProvider` (abstract) + `ManualProvider` (Phase 1).
`sync_dj(dj, provider)` maps provider DTOs onto the models and only touches rows
stamped with that provider's name, so hand-entered data is never clobbered. Phase 3
adds `spotify.py` / `bandsintown.py` / `instagram.py` behind the same contract.

## Auth
Internal-only: everything lives behind the Django admin login; no public signup.
Accounts are created by an admin (`createsuperuser`, then add staff users in-app).

## Testing
```bash
pytest              # 13 tests: models, scoring, providers, admin
python manage.py check
```

## Next
- **Phase 2:** buyer UI (directory, profile, leaderboard, shortlist). Decision
  pending: Django templates (re-skin the prototype) vs DRF + React.
- **Phase 3:** live data providers + scheduled refresh.
