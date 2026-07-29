# PersonalLifeOS

Native macOS app for personal planning: activities, habits, AI project time, kitesurf sessions, tides, and a weekly schedule. Built with **SwiftUI** and **SwiftData**.

## Requirements

- macOS 14.0+
- Xcode 16+ (or newer)

## Run

1. Open `LifeOS.xcodeproj` in Xcode.
2. Select the **LifeOS** scheme and run (⌘R).

No environment variables or secrets are required. The app is offline-first and does not enable App Sandbox (intentional for local personal use; CSV export uses `NSSavePanel`).

## Tests

```bash
xcodebuild test -scheme LifeOS -destination 'platform=macOS'
```

## Data & recovery

SwiftData stores the local database under Application Support (typically `~/Library/Application Support/default.store` and related `-shm`/`-wal` files).

If the store is corrupt and the app warns that it is running in-memory:

1. Quit LifeOS.
2. Delete `default.store*` in `~/Library/Application Support/`.
3. Relaunch — first launch re-seeds tides and sample content from bundled JSON.

Day boundaries (habits, tides, “today”) use **America/Fortaleza** consistently.

## Where things live

| Path | Contents |
|------|----------|
| `LifeOS/` | App source (views, models, UI, bundled JSON in `Resources/`) |
| `LifeOS.xcodeproj/` | Xcode project |
| `tests/` | Unit tests (`LifeOSTests`) |
| `data/` | Raw inputs and reference files (e.g. PDFs) |
| `archive/` | Historical docs kept for reference (Django stack retired) |
| `AGENTS.md` | Folder layout rules for this repo |
