# Life OS — application package (HISTORICAL)

> **Historical only — Django / Telegram stack is retired.**  
> The live product is the native macOS app in `LifeOS/`. See the root [README.md](../README.md) to run the app. Do not follow the `venv` / `make` / bot instructions below as current procedure.

This archive note describes the former Django project (`manage.py`, `lifeos/` settings package, `dashboard/`, `reminders/`). Linked `docs/*` paths below no longer exist on `main`.

---

## Quick commands (from this directory)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make migrate && make seed && make run
```

Dashboard: [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)

Telegram: configure `.env`, then `make bot`.

---

The sections below are a **compact duplicate** of the runbook for offline skimming only.

### Telegram commands (bot)

| Command | Description |
|---------|-------------|
| `/today` | Today’s schedule |
| `/done [activity_name]` | Mark done |
| `/skip [activity_name]` | Mark skipped |
| `/add [HH:MM] [activity]` | Add activity today |
| `/start_session [project]` | Start AI session timer |
| `/stop` | Stop active session |
| `/mood [1-10]` | Log mood |
| `/kite` | Log kite session |

### Timezone

`LANGUAGE_CODE = pt-br`, `TIME_ZONE = America/Fortaleza` in `lifeos/settings.py`.

### Makefile

`make run`, `make migrate`, `make seed`, `make bot`, `make shell`, `make static`, `make superuser`, `make setup`.
