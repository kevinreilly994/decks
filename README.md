# Decks — DJ Booking Database

[![CI](https://github.com/kevinreilly994/decks/actions/workflows/ci.yml/badge.svg)](https://github.com/kevinreilly994/decks/actions/workflows/ci.yml)

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
pytest              # 28 tests: models, scoring, providers, admin
python manage.py check
```

## Pages (buyer UI)
- `/` — **Roster**: searchable, genre-filterable, sortable card grid.
- `/leaderboard/` — ranked **Popularity Leaderboard** with score bars + 7-day delta.
- `/dj/<slug>/` — **DJ profile**: metrics, score breakdown, upcoming/played shows,
  releases, linked socials, and the management/booking panel.
- `/shortlist/` — session-based **compare** view (add/remove from any card or profile).

All pages require login and share one app shell (left nav rail + search). Styling
lives in `roster/static/roster/css/app.css` (soft beach-green / sunset palette).

## Live data (Phase 3)
Providers live behind the Phase 1 seam in `roster/providers/`:
- **SpotifyProvider** — follower count + top-track releases (Client Credentials).
- **BandsintownProvider** — upcoming events -> shows.

Configure credentials in `.env` (`SPOTIFY_CLIENT_ID/SECRET`, `BANDSINTOWN_APP_ID`)
and set each DJ's `spotify_artist_id` / `bandsintown_artist` in the admin.

```bash
python manage.py sync_roster            # runs configured providers, snapshots, rescoring
python manage.py sync_roster --dry-run  # preview
python manage.py seed_history           # demo: backfill monthly snapshots for trend charts
```

Unconfigured providers are skipped safely, and per-DJ API errors are logged without
aborting the run. Each run writes a dated `EngagementSnapshot`; once two or more
exist, the profile page renders a trend sparkline (Spotify followers + engagement).

### Scheduling
Prefer the OS scheduler (cron / Windows Task Scheduler) calling `manage.py sync_roster`
daily. Or run the bundled blocking scheduler (needs `APScheduler`):
```bash
python manage.py run_scheduler --hours 24 --run-now
```

## Next
- **Phase 2:** done — buyer UI via Django templates (this release).
- **Phase 3:** done — Spotify + Bandsintown providers, `sync_roster`, scheduler,
  and trend charts (this release).
