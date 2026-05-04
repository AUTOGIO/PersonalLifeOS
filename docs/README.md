# Life OS — documentation

This folder follows ideas from [Diátaxis](https://diataxis.fr/): separate **tutorial**, **how-to**, **explanation**, and **reference** so readers can pick the right lens.

## Map

| Type | Document | Use when |
|------|----------|----------|
| **Tutorial** (learning-oriented) | [runbook.md](runbook.md) — [First-time setup](runbook.md#first-time-setup) | You are installing and running Life OS for the first time. |
| **How-to** (problem-oriented) | [runbook.md](runbook.md) — Telegram, tides, static files, production | You need to accomplish a specific task (reminders, import data, deploy). |
| **Explanation** (understanding-oriented) | [architecture.md](architecture.md) | You want the mental model: apps, flows, schedule engine, external services. |
| **Reference** (information-oriented) | [reference.md](reference.md) | You need exact URLs, env vars, models, or commands without narrative. |

## Repository entry points

- **Project overview and links:** [../README.md](../README.md)
- **Legacy quick reference inside the app tree:** [../lifeos/README.md](../lifeos/README.md) (points here for full detail)

## Conventions

- Paths in runbook and reference are given from the **`lifeos/`** directory (where `manage.py` lives) unless stated otherwise.
- Dates in examples follow the machine locale; the app’s canonical timezone is `America/Fortaleza`.
