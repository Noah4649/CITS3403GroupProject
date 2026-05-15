# FitTrack

A social fitness-tracking web app built with Flask. Log workouts and meals, track calories burned against an editable daily goal, compete with friends on the leaderboard, and earn achievements as you go.

Built for **CITS3403 — Agile Web Development** at UWA.

---

## Features

- **Authentication** — signup, login, password reset via email
- **Dashboard** — at-a-glance view of recent activity, calorie progress, and goals
- **Workouts** — start a workout, log exercises with sets/reps/weight, finish to save it, browse history
- **Calories** — daily meal log, calories-burned tracking, editable daily calorie burn goal, weekly chart
- **Friends & feed** — search users, send/accept requests, share workouts and posts, comment on activity
- **Leaderboard** — overall ranking plus per-metric boards (calories, workouts, training time, bench / squat / deadlift), with **Friends vs Global** toggle and side-by-side comparison
- **Profile & settings** — editable bio, weight, height, goals; change password
- **Achievements** — earned automatically based on workout count and calories burned (First Workout, Calorie Crusher, Consistency King, Century Club, etc.)

---

## Tech stack

- **Backend:** Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-Migrate (Alembic), Flask-Mail
- **Database:** SQLite by default (configurable via `DATABASE_URL`)
- **Frontend:** Jinja2 templates, Bootstrap 5, vanilla JS, Chart.js for charts
- **Tests:** pytest and Selenium WebDriver

---

## Quick start

### 1. Clone and set up a virtual environment

```bash
git clone <repo-url>
cd CITS3403GroupProject-1
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
SECRET_KEY=change-me-in-prod
DATABASE_URL=sqlite:///fitness.db

# Optional — only needed for password-reset emails
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your@email.com
```

### 3. Create the database

This step is **required before the first run** — it creates the SQLite file and all tables:

```bash
python create_db.py
```

### 4. (Optional) Load demo data

```bash
python seed.py
```

Loads a handful of demo users with workouts, meals, goals, and friendships so you can poke around without signing up.

### 5. Run the app

```bash
python run.py
```

Visit <http://127.0.0.1:5000>. Debug mode is on by default — code changes hot-reload.

---

## Running tests

```bash
python -m pytest -q
```

Tests live in [`tests/`](tests/) and cover authentication, models, route behavior, and browser flows.

Selenium tests run against a live local Flask server and use an isolated test database:

```bash
python -m pytest tests/test_selenium.py -q
```

Selenium uses Chrome in headless mode by default. Install Chrome before running browser tests. To watch the browser, run with `SELENIUM_HEADLESS=0`.

---

## Project structure

```
.
├── app/
│   ├── __init__.py           # Flask app factory + extension wiring
│   ├── models.py             # SQLAlchemy models (User, Workout, Meal, Goal, …)
│   ├── routes.py             # All routes / blueprints / API endpoints
│   ├── achievements.py       # Achievement-evaluation logic
│   ├── templates/            # Jinja2 templates (one per page)
│   └── static/               # CSS, JS, images
├── migrations/               # Alembic migration history
├── tests/                    # pytest suite
├── instance/                 # SQLite DB lives here (git-ignored)
├── seed.py                   # Demo data loader
├── create_db.py              # Creates the SQLite file + all tables
├── run.py                    # Entry point
└── requirements.txt
```

---

## Database migrations

When a model changes, generate a migration with Flask-Migrate (Alembic):

```bash
flask --app run db migrate -m "describe the change"
flask --app run db upgrade
```

Migration files land in `migrations/versions/` and should be committed.

> First-time setup uses `create_db.py` (above) rather than `db upgrade` — they're equivalent for a fresh DB.

---

## Demo accounts

After running `python seed.py`, log in with any seeded user. See `seed.py` for the full list and passwords.

---

## Contributing

This is a group coursework repo, but the basic workflow is:

1. Branch from `main`: `git checkout -b feature/my-thing`
2. Make changes; keep commits focused
3. Open a PR against `main` with a short summary and test plan
4. Resolve review comments, then merge

Pre-PR checklist:

- [ ] `pytest` passes
- [ ] No leftover debug prints or commented-out code
- [ ] DB schema changes have a migration committed under `migrations/versions/`
- [ ] Templates render without Jinja errors (manually click through the affected pages)

---

## License

For coursework / educational use.
