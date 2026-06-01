# Life_OS (Native macOS App)

Life_OS is now a **fresh native macOS SwiftUI application** that builds into a `.app` bundle.

## Design target
- Bloomberg Terminal-inspired visual language:
  - Dark background
  - High-contrast typography
  - Amber/cyan/green accent colors
  - Dense panel grid layout with market-style widgets

## Project structure
- `LifeOS.xcodeproj` — Xcode project
- `LifeOS/App` — app entry and root views
- `LifeOS/UI` — reusable UI theme/components
- `LifeOS/Assets.xcassets` — app assets

## Build a native `.app`
1. Open `/tmp/workspace/AUTOGIO/Life_OS/LifeOS.xcodeproj` in Xcode 16+ on macOS.
2. Select scheme **LifeOS** and target **My Mac**.
3. Build (`⌘B`) and Run (`⌘R`).
4. Product output is a native `LifeOS.app` bundle in Xcode DerivedData.

## Archive/export
1. Product → Archive
2. Distribute App → Copy App
3. Export signed/unsigned `.app` as needed.

## System target
- Apple Silicon MacBook Air (M-series)
- macOS 26.6+
