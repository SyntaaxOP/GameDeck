# Changelog

All notable changes are recorded here. This project follows [Semantic Versioning](https://semver.org/).

## [0.8.4] - 2026-08-12

### Fixed

- Build the GameDeck desktop executable with the Windows GUI subsystem so launching it never opens a console window.
- Open the author profile through a native desktop command instead of relying on WebView link navigation.
- Run the Tauri frontend build hook from its actual frontend working directory.

## [0.8.3] - 2026-08-12

### Changed

- Replace cramped game-card actions with a balanced two-column Play, Details, Edit, and Delete layout.
- Remove archive controls from the game library in favor of explicit permanent deletion.
- Add a “Made by Syn” link to the author’s GitHub profile in the application footer.

### Fixed

- Exclude every GameDeck backend build and PyInstaller error window from automatic game discovery.

## [0.8.2] - 2026-08-12

### Added

- Permanent library deletion with explicit history safeguards.
- Rotating playtime FAQ insights and automatic or manual time-zone control.
- Rich Windows hardware inventory with named CPU, GPU, motherboard, and total per-volume storage.

### Fixed

- Report notification permission and delivery results in the desktop UI.
- Package the local backend without a visible command window.

## [0.8.1] - 2026-08-12

### Fixed

- Reject screenshot viewers, capture utilities, Windows Store apps, AppData tools, and unrelated foreground programs from launcher-independent game discovery.
- Count overlapping games once in global analytics while retaining full per-game playtime.
- Verify detection-review routes in the packaged backend contract and remove false-app sessions when an automatic detection is ignored.
- Stop running GameDeck desktop and backend processes before Windows upgrades or uninstalls so NSIS can replace locked application files.
- Run the frontend build from its explicit workspace directory during desktop packaging.

## [0.8.0] - 2026-08-11

### Added

- Singleton local PC hardware profile with manual CPU, GPU, memory, motherboard, storage, and notes.
- One-time read-only OS, processor, memory, and storage inventory snapshot with no background telemetry.

## [0.7.0] - 2026-08-11

### Added

- Tauri 2 Windows shell with a tightly scoped FastAPI sidecar lifecycle and per-user local data.
- PyInstaller sidecar script and reproducible NSIS packaging workflow.
- Desktop-aware API routing, loopback CORS policy, and restrictive webview content-security policy.

## [0.6.0] - 2026-08-11

### Added

- Preview-before-commit Steam owned-library import using Valve's official Web API.
- Backend-only Steam API key configuration, duplicate app-ID protection, offline-safe failure handling, and explicit placeholder executables.

## [0.5.0] - 2026-08-11

### Added

- Local game-night scheduling with optional library game, status, duration, notes, and attendee responses.
- User-triggered, copyable Discord announcement generation without bot tokens or network transmission.

## [0.4.0] - 2026-08-11

### Added

- Offline FiveM companion for manual server favorites, addresses, connect codes, notes, Discord links, last-joined history, and tracked playtime.
- Case-insensitive address uniqueness and explicit destructive confirmation.

## [0.3.0] - 2026-08-11

### Added

- Up to 10 explicit executable aliases per game, each with optional exact-path matching.
- Alias editing in the game form and process-detection mappings on game details.
- Normalized active executable registry with case-insensitive library-wide uniqueness.

### Changed

- Process matching now combines primary and alias processes into one game-level session.
- Archiving releases all executable mappings, while restore reclaims them atomically.
- Demo data includes safe alternate-executable examples.

## [0.2.0] - 2026-08-11

### Added

- Local purchase ledger for base games, DLC, subscriptions, and other spending.
- Separate-currency totals without implicit exchange-rate conversion.
- Global and per-game cost-per-played-hour analytics.
- Spending page with game filtering, add/edit flows, and explicit deletion confirmation.
- Phase 9 privacy, failure-mode, and acceptance proposal.

### Changed

- Demo mode now includes deterministic, non-financial purchase records.
- Diagnostics report purchase counts, and verified backups include the ledger.

## [0.1.0] - 2026-08-11

### Added

- Local game library with search, filters, archiving, favorites, priorities, ratings, and lifecycle states.
- Automatic Windows process monitoring with restart grace, crash recovery, and simultaneous-game support.
- Auditable manual session creation, correction, deletion, and overlap protection.
- Timezone-aware dashboard and analytics with clipped calendar intervals and rankings.
- Actionable backlog and deterministic Play Next ordering.
- SQLite migrations, verified online backups, diagnostics, rotating logs, and bounded lock handling.
- Responsive React interface with loading, empty, error, keyboard, and reduced-motion states.
- Deterministic sample-data command, Windows setup helpers, CI, screenshots, and release documentation.
