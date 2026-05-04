# Runbook

How to install, configure, run, and operate Life OS. For system structure, see [architecture.md](architecture.md).

## Prerequisites

- Python **3.9+** (version used in development is reflected by the project’s `venv`; pin your own in production).
- `pip` and ability to create a virtual environment.
- Optional: Telegram account for bot development.

All commands below assume your shell’s current directory is the **`lifeos`** folder inside your clone of this repository (the directory that contains `manage.py`).

---

## First-time setup

1. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment file**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` at minimum:

   - `SECRET_KEY` — use a long random string; never commit real secrets.
   - `DEBUG` — `False` in any internet-facing deployment.
   - `ALLOWED_HOSTS` — comma-separated hostnames or IPs you serve.

4. **Database**

   ```bash
   make migrate
   ```

5. **Sample data (optional)**

   ```bash
   make seed
   ```

   This runs `seed_schedule`: AI projects plus a 30-day activity seed (see command help for `--clear`).

6. **Admin user (optional)**

   ```bash
   make superuser
   ```

7. **Run the web app**

   ```bash
   make run
   ```

   Open [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/).

---

## Makefile targets

| Target | Effect |
|--------|--------|
| `make run` | `python manage.py runserver` |
| `make migrate` | `makemigrations` + `migrate` |
| `make seed` | `python manage.py seed_schedule` |
| `make bot` | Starts APScheduler and Telegram bot (see below) |
| `make shell` | Django shell |
| `make static` | `collectstatic` |
| `make superuser` | `createsuperuser` |
| `make setup` | `migrate` + `seed` + `superuser` + `static` |

---

## Telegram bot and scheduler

1. Create a bot with [@BotFather](https://t.me/BotFather), obtain `TELEGRAM_BOT_TOKEN`.
2. Obtain your `TELEGRAM_CHAT_ID` (e.g. via [@userinfobot](https://t.me/userinfobot) or your preferred method).
3. Put both in `.env`.

Start **scheduler + bot** (blocking processes; use two terminals or a process manager in production):

```bash
make bot
```

Behavior (see `reminders/tasks.py` and `reminders/bot.py`):

- Scheduled **morning summary** and **evening review** prompts (Fortaleza timezone).
- **Per-minute** job to send “30 minutes before” reminders for today’s planned activities, recorded in `TelegramReminder` to avoid duplicates.
- Interactive commands such as `/today`, `/done`, `/skip`, `/add`, session timers, mood, kite logging.

If token or chat id is missing, the scheduler logs warnings and skips sends.

---

## Tide data import

Tide rows are stored as `TideEvent` records. Import from JSON:

```bash
python manage.py import_tides path/to/tides.json
```

Validate imported data:

```bash
python manage.py validate_tides
```

Sample data may exist under `lifeos/data/tides/` in the repository. JSON shape is documented in the import command implementation.

---

## Weekly schedule seed

To populate repeating **ScheduleBlock** rows (planner v2):

```bash
python manage.py seed_weekly_schedule
```

Use the Django admin or your own workflow to adjust blocks; structural validation goes through `schedule_engine`.

---

## TUI calendar (optional)

```bash
python manage.py tui_calendar
```

Useful for terminal-first inspection of the calendar (see command help for options).

---

## Static files

For production-style serving:

```bash
make static
```

Configure your reverse proxy or `runserver` alternative to serve `STATIC_ROOT` appropriately.

---

## Security and secrets

- **Never commit `.env`** or real `SECRET_KEY` / Telegram tokens.
- With `DEBUG=True`, Django’s error pages leak context; keep debug off outside local machines.
- DRF default permission in settings is `AllowAny` — acceptable for a **local-only** personal dashboard; **tighten** (`IsAuthenticated`, etc.) before exposing to a network.
- Rotate `SECRET_KEY` if it was ever leaked; it invalidates signed sessions.

---

## Backups

- **SQLite file** — copy `db.sqlite3` (or the path in `DB_NAME`) while the app is stopped or use SQLite-safe backup procedures.
- **Uploaded media** — not central to current models; if you add `FileField`s later, back those directories up too.

---

## Production checklist (minimal)

1. `DEBUG=False`, strong `SECRET_KEY`, correct `ALLOWED_HOSTS`.
2. HTTPS termination (reverse proxy) and secure cookies as appropriate.
3. Restrict DRF and admin URLs if the app is not strictly private.
4. Run Gunicorn/Uvicorn (or similar) + process manager instead of `runserver`.
5. Run Telegram bot and scheduler under systemd, supervisord, or PM2—not only `make bot` in an SSH session.

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Migrations fail | Python version, `INSTALLED_APPS`, disk permissions in `lifeos/`. |
| Telegram silent | `.env` values, outbound HTTPS, logs from `reminders` logger. |
| Wrong day/times | `TIME_ZONE` in `settings.py`, server OS timezone, `USE_TZ=True` behavior. |
| HTMX partial empty | CSRF token on forms, URL name matches `dashboard/urls.py`, browser console. |
