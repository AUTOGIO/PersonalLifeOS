# PersonalLifeOS — Engineering Brief

Distilled for NotebookLM and Cursor. Facts only from repo docs / audit summary. No invented metrics.

## Constraints

- Scope is the **local** SwiftUI / SwiftData macOS app only.
- Do **not** revive the retired Django / Telegram stack in `archive/`.
- Do not invent empty top-level folders (`scripts/`, `config/`, `assets/`) without real content — see `AGENTS.md`.
- Root may contain only: `README.md`, `AGENTS.md`, `.gitignore`, optional `REPOSITORY_AUDIT.md`, toolchain (`LifeOS.xcodeproj`), plus approved trees (`LifeOS/`, `tests/`, `data/`, `archive/`, `.github/`, `docs/` when content exists).
- No committed secrets; app needs no env vars for normal run.
- Day boundaries (habits, tides, “today”) use **America/Fortaleza**.

## Current architecture / decisions

- Single-window SwiftUI app: `LifeOSApp` → `RootView` → sidebar modules (Dashboard, Weekly Schedule, Activities, AI Projects, Habits, Kite Sessions, Tides, Analytics).
- Persistence: SwiftData `ModelContainer` / on-disk store; entity state via `@Query`.
- Thin `MainViewModel` (navigation + quote); CRUD through `ModelContext`.
- Saves go through `PersistenceAlerts.save(_:)` (do/catch + UI alert). Seed failures surface via `SeedLoader` warnings → `PersistenceAlerts.seedWarning`.
- On-disk store open failure falls back to in-memory + recovery alert (data lost on quit until store reset).
- First-launch seed from bundled `tides.json` / `daily_plans.json` plus sample data (`SeedLoader`).
- Daily Plan can be edited from the Dashboard.
- Offline-first; no network clients in current Swift code; CSV export via `NSSavePanel`.
- Run: open `LifeOS.xcodeproj`, scheme **LifeOS**, ⌘R. macOS 14+.

## Conventions

- Prefer **move** over copy; **edit** over new files.
- App code under `LifeOS/` (views, models, UI, `Resources/`).
- Obsolete but unsure → `archive/`. Clear duplicates only may be deleted.
- Conflict order for agents: `AGENTS.md` / skills → Cursor architecture brief → NotebookLM synthesis.

## Exclusions

- Do not upload tests, `archive/`, raw `data/`, or the full `REPOSITORY_AUDIT.md` as routine NotebookLM fontes (lean Tier-1 only).
- Prefer one copy of each fonte in NotebookLM (avoid duplicate Standing Prompts).
- Do not treat NotebookLM as source of live/changing metrics.
- App Sandbox / notarized distribution not required for personal local use.

## Known gaps / priorities

- Prefer expanding reliability and tests before analytics/cloud/bot ideas.
- Check `tests/` before assuming coverage for a path you change.
- Tide calendar refresh beyond the bundled year — open.
- App Sandbox / distribution intent — undecided.

## Open questions

- Whether tide data will be refreshed beyond the bundled calendar year.
- Whether App Sandbox / distribution is ever intended.

## Citations

- `AGENTS.md`, `README.md`, `LifeOS/Persistence/PersistenceAlerts.swift`, `REPOSITORY_AUDIT.md` remediation notes (not uploaded in full).
