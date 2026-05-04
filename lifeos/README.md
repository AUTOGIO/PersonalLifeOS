# Life OS — application package

This directory contains the Django project (`manage.py`, `lifeos/` settings package, `dashboard/`, `reminders/`).

**Canonical documentation** (architecture, runbook, API and model reference) lives in the repository root:

- [../README.md](../README.md) — overview and documentation index  
- [../docs/README.md](../docs/README.md) — how documentation is organized  
- [../docs/runbook.md](../docs/runbook.md) — install, Telegram, operations  
- [../docs/architecture.md](../docs/architecture.md) — system design  
- [../docs/reference.md](../docs/reference.md) — URLs, env vars, models  

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
