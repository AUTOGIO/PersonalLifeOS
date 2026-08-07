# NotebookLM ↔ this repo

Dedicated notebook: [PersonalLifeOS](https://notebook.google.com/notebook/9d3b30f4-c728-4c3d-af37-c80cf79614cb/preview)

ID: `9d3b30f4-c728-4c3d-af37-c80cf79614cb`

Canonical truth: `AGENTS.md`, `README.md`, `docs/architecture-brief-source.md`

Cursor brief: `.cursor/rules/architecture-brief.mdc` (local; `.cursor/` is gitignored — keep `docs/architecture-brief-source.md` as the committed copy)

General wiring guide: [`docs/cursor-notebooklm-wiring-guide.md`](cursor-notebooklm-wiring-guide.md)

## Sync when these change

| Path | Why |
|------|-----|
| `AGENTS.md` | Folder layout / agent policy |
| `README.md` | Run/recovery/product summary |
| `docs/notebooklm-standing-prompts.md` | NotebookLM operating contract |
| `docs/architecture-brief-source.md` | Durable constraints for Cursor + notebook |

**Skip:** tests, `archive/`, `data/`, full `REPOSITORY_AUDIT.md`, secrets.

## Refresh the Cursor brief

After material changes: update `docs/architecture-brief-source.md` → mirror into `.cursor/rules/architecture-brief.mdc` → re-upload changed fontes in NotebookLM (prefer browser upload; MCP `add_source` can fail on Portuguese UI / preview URLs).

## Seed note

Initial fontes were uploaded manually in the NotebookLM UI. Prefer the owner URL (`notebooklm.google.com/notebook/<id>`, no `/preview`) when editing sources.

## Fonte hygiene

Keep **one** of each: Standing Prompts, `AGENTS.md`, `README.md`, Engineering Brief. Remove duplicate Standing Prompts (and empty/`---` stubs) in the Fontes panel so citations stay clean.

After updating `docs/architecture-brief-source.md` or `AGENTS.md` in Git, re-upload that file in NotebookLM (replace the old fonte).
