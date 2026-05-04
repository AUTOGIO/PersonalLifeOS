# Life OS

Personal life and work operating system: a Django web app for planning, tracking, and light automation—oriented around a fixed weekly structure, day-level activities, AI project time, habits, kitesurfing sessions, and Telegram nudges.

**Repository layout:** the runnable application lives under [`lifeos/`](lifeos/).

---

## Documentation

| Document | Audience | Contents |
|----------|----------|----------|
| [docs/README.md](docs/README.md) | Everyone | How the docs are organized (Diátaxis-style map). |
| [docs/architecture.md](docs/architecture.md) | Developers, operators | Components, data flow, scheduling rules, integrations. |
| [docs/runbook.md](docs/runbook.md) | Operators | Install, configure, run, backups, production checklist. |
| [docs/reference.md](docs/reference.md) | Developers | URLs, HTTP API, models overview, management commands. |

For a copy-paste quick start, see **Runbook → [First-time setup](docs/runbook.md#first-time-setup)**.

---

## At a glance

- **Stack:** Django 4.2, SQLite, Django REST Framework, django-htmx, Bootstrap 5, Chart.js, FullCalendar, APScheduler, python-telegram-bot.
- **Locale:** Portuguese (`pt-br`), timezone `America/Fortaleza` (Cabedelo / Paraíba context).
- **Surface area:** Dashboard (home, planner, analytics, activities), Django admin, JSON APIs for charts/calendar, HTMX partials for live edits, optional Telegram bot + scheduler.

---

## Quick start (summary)

```bash
cd lifeos
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # edit SECRET_KEY, hosts, optional Telegram
make migrate
make seed                  # sample AI projects + 30-day activities
make run                   # http://127.0.0.1:8000/dashboard/
```

Telegram bot and scheduled jobs: [docs/runbook.md#telegram-bot-and-scheduler](docs/runbook.md#telegram-bot-and-scheduler).

---

## Principles (for contributors and future you)

1. **Single-user, personal system** — security and multi-tenancy are not product goals; still treat secrets and production hosts seriously ([runbook](docs/runbook.md#security-and-secrets)).
2. **SQLite by design** — zero external database for local use; understand limits before exposing to the internet.
3. **Boring ops** — prefer Makefile + management commands over bespoke tooling.

---

## License

Add a `LICENSE` file in the repository root if you intend to open-source or share this project; until then, default copyright applies.
