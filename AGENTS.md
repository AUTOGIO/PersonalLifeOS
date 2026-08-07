# AGENTS.md — PersonalLifeOS layout

Personal macOS app (SwiftUI / SwiftData). Keep the repo simple and predictable.

## Folder rules

| Path | Purpose |
|------|---------|
| `LifeOS/` | Application code (Xcode target; same role as `src/` / `app/`) |
| `LifeOS.xcodeproj/` | Xcode project (toolchain; stays at root) |
| `tests/` | Unit tests (`LifeOSTests`) |
| `data/` | CSV, Excel, exports, PDFs, raw inputs (`data/raw`, `data/processed` if helpful) |
| `archive/` | Obsolete files kept for reference (do not delete casually) |
| `.github/` | CI workflows |
| `docs/` | NotebookLM wiring, standing prompts, architecture brief |

Create `scripts/`, `config/`, or `assets/` only when there is real content for them — do not add empty placeholder folders.

## Root may contain only

`README.md`, `AGENTS.md`, `.gitignore`, `REPOSITORY_AUDIT.md` (optional), and toolchain files (`LifeOS.xcodeproj`, etc.).

## Working rules

- Prefer **move** over copy; prefer **edit** over new files.
- Do not invent new top-level folders without asking.
- Do not redesign features or rewrite the app unless required for a safe move.
- After moves, fix broken paths. Do not commit secrets.
- Obsolete but unsure → `archive/`. Clear duplicates only may be deleted.
- Scope is the local SwiftUI/SwiftData Mac app. Do not revive the retired Django/Telegram stack from `archive/`.
