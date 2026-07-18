# AGENTS.md — PersonalLifeOS layout

Personal macOS app (SwiftUI / SwiftData). Keep the repo simple and predictable.

## Folder rules

| Path | Purpose |
|------|---------|
| `LifeOS/` | Application code (Xcode target; same role as `src/` / `app/`) |
| `LifeOS.xcodeproj/` | Xcode project (toolchain; stays at root) |
| `scripts/` | Runnable helpers (`.sh`, `.zsh`, `.command`) |
| `config/` | Non-secret settings |
| `data/` | CSV, Excel, exports, PDFs, raw inputs (`data/raw`, `data/processed` if helpful) |
| `assets/` | Loose images, icons, logos (not Xcode `Assets.xcassets`) |
| `docs/` | Markdown guides, design notes |
| `docs/prompts/` | AI prompt files |
| `tests/` | Tests only |
| `archive/` | Obsolete files kept for reference (do not delete casually) |

## Root may contain only

`README.md`, `AGENTS.md`, `.gitignore`, and toolchain files (`LifeOS.xcodeproj`, etc.).

## Working rules

- Prefer **move** over copy; prefer **edit** over new files.
- Do not invent new top-level folders without asking.
- Do not redesign features or rewrite the app unless required for a safe move.
- After moves, fix broken paths. Do not commit secrets.
- Obsolete but unsure → `archive/`. Clear duplicates only may be deleted.
