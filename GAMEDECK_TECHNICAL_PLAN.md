# GameDeck Technical Plan

Status: proposed for review; no application code has been started.

## 1. Product summary

GameDeck is a single-user, local-first Windows application that turns configured game processes into a trustworthy personal game library, play-session history, backlog, and analytics dashboard.

The product's distinctive technical feature is not library CRUD; it is reliable session tracking despite crashes, restarts, permissions errors, duplicate process observations, and multiple games running at once. That reliability, plus clear SQL analytics and tests, should be the center of both the implementation and the portfolio story.

Success for V1 means a user can register a game executable, leave GameDeck running, launch and close games normally, and later trust the recorded playtime.

### Product principles

- Local by default: all data remains in SQLite on the user's computer.
- Explicit over magical: only registered executables are tracked.
- Recoverable: interrupted sessions and application restarts do not corrupt history.
- Understandable: modular monolith, direct REST calls, conventional SQL, no infrastructure services.
- Portfolio-ready: important decisions, limitations, tests, and failure handling are documented.

## 2. V1 scope

V1 includes:

1. A local React interface and FastAPI backend.
2. Manual game creation, editing, archiving, search, sort, and filtering.
3. One configured executable name and optional exact executable path per game.
4. Windows process polling for registered games.
5. Automatic session start, heartbeat, stop, and interrupted-session recovery.
6. Multiple simultaneously running games, with one active session per game.
7. Manual session creation and correction for inaccurate or missed data.
8. Dashboard totals for today, week, and month; current games; recent games; most-played game; longest and average session.
9. Game-specific session history and playtime.
10. Backlog status, priority, favorite, rating, notes, and completion date.
11. SQLite persistence, migrations, structured local logs, settings, and pytest coverage.
12. Dark, responsive UI suitable for desktop browser widths.

### V1 acceptance outcome

The app should run locally without an internet connection or third-party account. After a ten-minute test game run, the dashboard and game details should show one session with a duration within one polling interval plus the configured restart grace period.

## 3. Features deliberately excluded from V1

- Steam, Xbox, Epic, or other account/library imports.
- FiveM server detection or server-status APIs.
- Discord bot, game nights, or Rich Presence.
- Spending analytics, DLC, subscriptions, and multi-currency conversion.
- Cover-art downloads or external metadata APIs; V1 may accept a local image path or omit covers.
- Hardware/resource monitoring.
- Cloud sync, remote access, accounts, and authentication.
- Automatic discovery of every installed game.
- Tauri packaging, auto-update, and OS installer.
- Launcher-to-child-process heuristics beyond direct registered-process matching.
- Overlapping-session normalization. If two registered games run together, each correctly receives playtime.

These are excluded because they add integration uncertainty before the core session engine has proved reliable. None is necessary to validate the product.

## 4. Recommended architecture

### Recommendation

Use a modular monolith in one repository:

```text
React + TypeScript UI
        |
        | HTTP on localhost
        v
FastAPI routes -> application services -> SQLAlchemy repositories -> SQLite
                         ^
                         |
             process monitor + session coordinator
```

The process monitor is a backend component, not a second deployable service. For V1, run one FastAPI process with one worker and start one monitor task during application startup. Development reload must explicitly disable the parent/reloader copy so only the serving process owns the monitor. Tests construct the API with monitoring disabled.

### Key decisions

#### Local browser application first

Recommendation: run FastAPI and Vite locally and open the React app in a normal browser.

Why: this is the easiest arrangement to debug, preserves browser developer tools, and avoids desktop packaging work while product behavior is changing.

Simpler alternative: server-rendered FastAPI templates. It reduces processes but abandons the requested React portfolio experience.

More complex alternative: Tauri immediately. It provides a native shell and installer but adds Rust, inter-process lifecycle, permissions, and packaging before they create product value.

Migration path: keep the frontend dependent only on the REST contract and keep filesystem/process access exclusively in Python. A future Tauri shell can launch the bundled backend on a loopback port, wait for a health check, load the React build, and stop the backend on exit without rewriting domain logic.

#### SQLite with migrations

Recommendation: SQLite in WAL mode, foreign keys enabled, a short busy timeout, and Alembic migrations from the first schema.

Why: one local writer plus UI reads is an excellent SQLite use case. WAL improves read/write coexistence. Migrations demonstrate good practice and protect user data.

Simpler alternative: `create_all()` without migrations. It is acceptable for a throwaway prototype but makes upgrades unsafe.

More complex alternative: PostgreSQL. Reserve it for optional cloud sync or multi-user access.

#### Service boundaries without generic abstractions

Routes validate HTTP input and call focused services. Services enforce business rules. Repositories contain reusable database access and analytics queries. Avoid a generic `BaseRepository` until repeated code clearly justifies one.

#### Time handling

Store all timestamps in UTC. Read the system time zone into settings and apply it when calculating calendar days/weeks/months and displaying dates. A week begins Monday by default. Never derive duration from formatted local timestamps.

## 5. Proposed project folder structure

```text
gamedeck/
|-- README.md
|-- docs/
|   |-- architecture.md
|   `-- decisions/
|-- backend/
|   |-- pyproject.toml
|   |-- alembic.ini
|   |-- migrations/
|   |-- src/gamedeck/
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- db.py
|   |   |-- api/
|   |   |   |-- games.py
|   |   |   |-- sessions.py
|   |   |   |-- analytics.py
|   |   |   `-- settings.py
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- repositories/
|   |   |-- services/
|   |   |-- monitoring/
|   |   |   |-- process_source.py
|   |   |   |-- matcher.py
|   |   |   `-- monitor.py
|   |   `-- logging_config.py
|   `-- tests/
|       |-- unit/
|       |-- integration/
|       `-- fixtures/
|-- frontend/
|   |-- package.json
|   |-- src/
|   |   |-- api/
|   |   |-- components/
|   |   |-- features/
|   |   |   |-- games/
|   |   |   |-- sessions/
|   |   |   |-- analytics/
|   |   |   `-- settings/
|   |   |-- pages/
|   |   |-- routes/
|   |   |-- types/
|   |   `-- utils/
|   `-- tests/
`-- scripts/
    |-- dev.ps1
    `-- start.ps1
```

Organize frontend code by product feature, while keeping truly shared UI primitives in `components`. Do not create a separate backend package for every table.

## 6. Database schema

SQLite foreign-key enforcement must be enabled for every connection. Primary keys can be integer IDs for readability. Timestamps are UTC and are exposed as ISO 8601 strings by the API.

### V1 tables

#### `games`

| Column | Type | Rules |
|---|---|---|
| `id` | INTEGER | primary key |
| `title` | TEXT | required, trimmed, 1-200 characters |
| `platform` | TEXT | required; checked enum: `steam`, `xbox`, `epic`, `fivem`, `local`, `emulator`, `other` |
| `executable_name` | TEXT | required for automatic tracking; store normalized lower-case basename, no directory separators |
| `executable_path` | TEXT | nullable; normalized absolute path; never executed by GameDeck |
| `cover_path` | TEXT | nullable local image path |
| `genre` | TEXT | nullable, maximum 100 characters |
| `status` | TEXT | required; checked enum: `currently_playing`, `backlog`, `completed`, `completed_100`, `dropped`, `paused` |
| `priority` | INTEGER | nullable, check 1-5 |
| `personal_rating` | INTEGER | nullable, check 1-10 |
| `notes` | TEXT | nullable |
| `favorite` | BOOLEAN | required, default false |
| `date_added` | DATETIME | required UTC |
| `date_completed` | DATE | nullable; normally set only for completion statuses |
| `archived_at` | DATETIME | nullable; soft-delete marker |
| `created_at` | DATETIME | required UTC |
| `updated_at` | DATETIME | required UTC |

Constraints and indexes:

- Unique index on lower-case `executable_name` for non-archived games in V1. This avoids ambiguous matching. If aliases become necessary, migrate executable mappings to a separate table later.
- Index on `(status, archived_at)` for backlog/library filters.
- Index on `(favorite, archived_at)`.
- Validate `executable_path` basename agrees with `executable_name` when both are supplied.
- Duplicate titles are allowed because editions can differ; executable identity is what matters to tracking.

#### `game_sessions`

| Column | Type | Rules |
|---|---|---|
| `id` | INTEGER | primary key |
| `game_id` | INTEGER | required foreign key to `games.id`, delete restricted |
| `started_at` | DATETIME | required UTC |
| `ended_at` | DATETIME | nullable while active |
| `last_seen_at` | DATETIME | required UTC; last successful observation of the process |
| `duration_seconds` | INTEGER | nullable while active; otherwise required and non-negative |
| `detection_method` | TEXT | checked enum: `process`, `manual`, `recovered` |
| `end_reason` | TEXT | nullable; checked values such as `process_stopped`, `tracker_shutdown`, `recovered`, `manual` |
| `process_id` | INTEGER | nullable diagnostic value; not treated as durable identity |
| `process_started_at` | DATETIME | nullable; combines with PID to reduce PID-reuse mistakes |
| `created_at` | DATETIME | required UTC |
| `updated_at` | DATETIME | required UTC |

Constraints and indexes:

- Check: `ended_at IS NULL OR ended_at >= started_at`.
- Check: active sessions have null duration; ended sessions have non-null duration.
- Check: `duration_seconds >= 0` when present.
- Partial unique index on `game_id WHERE ended_at IS NULL`, guaranteeing at most one active session for a game even if monitor events repeat.
- Index on `(game_id, started_at DESC)` for game details.
- Index on `(started_at, ended_at)` for time-range analytics.
- Index on `ended_at` for recovery and current-session queries.
- Service-computed duration is `max(0, floor(ended_at - started_at))`. Manual edits recalculate it transactionally.

The database constraint is the final duplicate-session defense; the service should still treat repeated starts idempotently.

#### `settings`

Use one typed single-row table instead of an unvalidated key/value store.

| Column | Type | Rules |
|---|---|---|
| `id` | INTEGER | primary key, constrained to 1 |
| `scan_interval_seconds` | INTEGER | default 5, check 2-60 |
| `restart_grace_seconds` | INTEGER | default 15, check 0-120 |
| `tracking_enabled` | BOOLEAN | default true |
| `week_starts_on` | INTEGER | default 0/Monday, check 0-6 |
| `time_zone` | TEXT | required IANA-compatible value captured from system/configuration |
| `theme` | TEXT | default `dark`; checked enum |
| `currency_code` | TEXT | default `PHP`, exactly 3 uppercase characters; reserved for later spending UI |
| `updated_at` | DATETIME | required UTC |

No separate excluded-applications setting is needed because V1 only tracks registered games.

### Post-V1 tables

Do not create these in the first migration. Their proposed shape prevents V1 decisions from blocking future work.

#### `purchases`

- `id` INTEGER primary key
- `game_id` INTEGER nullable foreign key to games, delete restricted
- `kind` TEXT checked: `base_game`, `dlc`, `subscription`, `other`
- `amount_minor` INTEGER required, non-negative (centavos, avoiding floating-point money)
- `currency_code` TEXT required, default `PHP`
- `purchased_on` DATE nullable
- `platform` TEXT nullable
- `notes` TEXT nullable
- `created_at`, `updated_at` DATETIME required
- Indexes on `(game_id, purchased_on)` and `purchased_on`

Subscriptions may not belong to one game, so `game_id` is nullable. V1 should not put a single `purchase_price` column on `games`; the future table models repeated purchases correctly.

#### `fivem_servers`

- `id` INTEGER primary key
- `name` TEXT required
- `connect_code` TEXT required unique
- `favorite` BOOLEAN default false
- `notes` TEXT nullable
- `discord_url` TEXT nullable and URL-validated
- `last_joined_at` DATETIME nullable
- `created_at`, `updated_at` DATETIME required
- Index on `(favorite, last_joined_at DESC)`

Keep server playtime manual or omit it until a reliable association between a FiveM process session and a server exists. Do not guess it from total FiveM time.

### Tables intentionally omitted

- `game_notes`: one notes field per game is enough until multiple timestamped notes are a proven need.
- Daily/monthly aggregate tables: calculate from sessions; the expected personal dataset is small.
- Process observations: logs are sufficient; persisting every five-second observation would create noise.

## 7. Backend services

### `GameService`

- Validate and normalize executable names and paths.
- Enforce non-ambiguous executable mappings.
- Create, update, archive, restore, search, sort, and filter games.
- Apply status rules, such as setting or clearing completion dates intentionally.

### `SessionService`

- Idempotently start or resume a process-detected session.
- Record heartbeats (`last_seen_at`).
- End sessions after the grace period and calculate duration.
- Create and edit manual sessions with overlap warnings.
- Recover sessions left active after an unclean stop.
- Keep each transaction short and retry only transient SQLite-busy failures.

### `ProcessMonitor`

- Obtain process snapshots through a `ProcessSource` interface.
- Catch per-process access-denied/no-such-process errors.
- Match normalized basename first and configured path when present.
- Diff observations against its in-memory state.
- Call `SessionService`; it never writes database rows directly.

### `AnalyticsService`

- Define local calendar boundaries and convert them to UTC query ranges.
- Aggregate session intersections with a requested range rather than counting only sessions that started within it.
- Compute dashboard, trends, game totals, weekday/hour distributions, streak, and cost-per-hour later.
- Include active sessions using the current time without prematurely closing them.

### `SettingsService`

- Read/update the typed settings row.
- Validate polling and grace ranges.
- Notify the running monitor of safe setting changes or apply them on its next loop.

### Repository responsibilities

Repositories own SQLAlchemy queries, not business policy. Begin with `GameRepository`, `SessionRepository`, `SettingsRepository`, and `AnalyticsRepository`. Analytics can use explicit SQLAlchemy Core queries where aggregation is clearer than ORM object loading.

## 8. Process-monitoring design

### Polling cycle

1. Every five seconds by default, request a snapshot of running processes from `psutil.process_iter` using only needed fields: PID, name, executable path when accessible, and process creation time.
2. Normalize names with case-insensitive Windows semantics and reduce configured names to basenames.
3. Load/cached-map active, non-archived registered games by executable name. Refresh the map after a game/settings mutation and periodically as a fallback.
4. Match exact executable path if the game has one and the process exposes one. Otherwise use the unique registered executable name.
5. Group matched processes by game. Multiple OS processes for one game still represent one game-running state.
6. For newly observed games, call idempotent session start/resume.
7. For still observed games, update heartbeat at a throttled interval (for example every 15 seconds, not on every scan).
8. For games no longer observed, start an in-memory missing timer. End the session only after `restart_grace_seconds` has elapsed.
9. Log state transitions and errors, not every successful scan.

Five seconds is responsive enough for gaming sessions while generating negligible CPU load. A two-second minimum prevents accidental busy polling. Short sessions under the poll interval can be missed; this is an explicit V1 limitation.

### Reliability details

- Catch `AccessDenied`, `NoSuchProcess`, and processes that disappear while inspected; skip only that process.
- A total snapshot failure does not mean every game stopped. Log it and retain the last known state until a successful snapshot.
- Use monotonic time for grace-period decisions inside a running process and UTC wall-clock time for persisted timestamps.
- Use `(pid, process_create_time)` only as diagnostic process identity. Game-level running state is authoritative.
- One monitor owner only. The production startup script must use one Uvicorn worker. A second monitor is still contained by the partial unique index, but duplicate ownership is a deployment error and should be logged.
- SQLite writes happen only on transitions and throttled heartbeats, not every process observation.

### Matching rules

1. No registered executable: never track it.
2. Configured path and observable process path: require normalized paths to match.
3. Configured path but inaccessible process path: allow the unique basename match and log that fallback was used; make this behavior a later setting if false positives appear.
4. Only configured name: require exact case-insensitive basename equality.
5. Ambiguous executable names are rejected at game creation in V1.

## 9. Session-tracking algorithm

### Start or resume

Within one transaction:

1. Query for the game's active session.
2. If one exists, update its heartbeat/process diagnostics and return it.
3. Otherwise insert an active session with `started_at = last_seen_at = now`, null end/duration, and `detection_method = process`.
4. If a concurrent insert hits the partial unique index, fetch and return the winning active session.

### Temporary disappearance and process restart

When a game vanishes, do not end immediately. Mark it missing in memory. If it reappears within the 15-second default grace period, keep the same session and update diagnostics. If it remains absent, end the session at `last_seen_at` rather than at the later grace-expiry time. This avoids inflating playtime.

### Clean GameDeck shutdown

On a normal shutdown, take a final process snapshot. For games still running, leave sessions active and persist a fresh heartbeat; for games confirmed absent, end them. Leaving a live game's session open makes restart reconciliation honest.

### Startup reconciliation

Before normal polling:

1. Take a successful process snapshot.
2. Load all active database sessions.
3. If the matching game is currently running, keep the existing session and update `last_seen_at`; this treats GameDeck downtime as continuous play. Document that the unobserved interval is an estimate.
4. If it is not running, close the session at its prior `last_seen_at`, set `end_reason = recovered`, and retain the original detection method.
5. Start sessions for any currently running registered games without an active session, using startup time as `started_at` because earlier start time cannot be known reliably.

If the initial snapshot fails entirely, do not close anything; retry. Recovery based on an incomplete snapshot would destroy useful state.

### Manual correction

Users must be able to add, edit, and delete manual sessions and edit automatic session times. Validation rejects negative durations. Overlaps for the same game should produce a clear validation error in V1, because double-counting would make analytics misleading. Sessions for different games may overlap.

## 10. REST API design

Prefix all routes with `/api/v1`. Return consistent JSON errors with a stable code, human-readable message, and optional field details. For this local app, offset pagination is sufficient.

### System

- `GET /health` — backend/database readiness; used by startup and eventual desktop shell.

### Games

- `GET /api/v1/games?q=&platform=&status=&favorite=&archived=&sort=&page=&page_size=` — library and backlog list.
- `POST /api/v1/games` — create a manually configured game.
- `GET /api/v1/games/{game_id}` — metadata plus compact lifetime playtime/current status summary.
- `PATCH /api/v1/games/{game_id}` — partial metadata/status update.
- `DELETE /api/v1/games/{game_id}` — archive, preserving session history.
- `POST /api/v1/games/{game_id}/restore` — restore an archived game.

### Sessions

- `GET /api/v1/sessions?game_id=&from=&to=&active=&page=&page_size=` — session table/history.
- `GET /api/v1/sessions/active` — zero or more current games; plural because simultaneous play is supported.
- `POST /api/v1/sessions` — create a manual session.
- `PATCH /api/v1/sessions/{session_id}` — correct start/end and optional end reason.
- `DELETE /api/v1/sessions/{session_id}` — delete only after confirmation in the UI; useful for erroneous detections.

No public `start`/`stop` process endpoint is needed. The monitor calls the service directly, and exposing internal transitions would enlarge the invalid-state surface.

### Analytics

- `GET /api/v1/analytics/dashboard?at=` — all dashboard cards and recent/current items in one response.
- `GET /api/v1/analytics/playtime?from=&to=&bucket=day|week|month&game_id=` — chart series.
- `GET /api/v1/analytics/distribution?from=&to=&dimension=weekday|hour` — activity distributions.
- `GET /api/v1/analytics/games/{game_id}?from=&to=` — game-specific summary and trends.

The dashboard aggregation endpoint prevents many small requests and guarantees cards use the same time boundary. Keep specialized endpoints for interactive analytics filters.

### Settings and monitor status

- `GET /api/v1/settings`
- `PATCH /api/v1/settings`
- `GET /api/v1/tracker/status` — enabled/running state, last successful scan, last error, and active game IDs.

Changing `tracking_enabled` through settings is enough; no separate command endpoint is required in V1.

## 11. Frontend pages

### Dashboard (`/`)

Purpose: immediate gaming overview.

Components: current-game banner, today/week/month cards, most-played and longest-session cards, seven- or thirty-day playtime chart, recently played list, tracker health indicator.

Data: dashboard analytics and tracker status.

### Library (`/library`)

Purpose: maintain all registered games.

Components: search, platform/status filters, sort, card/table toggle if time permits, add/edit dialog, favorites, archive confirmation, empty state.

Data: paginated games endpoint; create/update/archive endpoints.

### Game details (`/games/:id`)

Purpose: inspect and manage one game.

Components: metadata/status editor, total playtime and average session, recent sessions, trend chart, notes, executable configuration, session correction actions.

Data: game detail, game analytics, filtered sessions.

### Sessions (`/sessions`)

Purpose: audit and correct the raw record behind analytics.

Components: date/game filters, active badges, duration table, manual-session dialog, edit/delete actions.

Data: sessions list and active sessions.

### Analytics (`/analytics`)

Purpose: explore time patterns.

Components: date-range presets, daily/weekly/monthly trend, top-games ranking, weekday distribution, hourly distribution, longest/average session.

Data: playtime, distribution, and dashboard summary endpoints.

### Backlog (`/backlog`)

Purpose: focused planning view over the same games data, not a second data model.

Components: status columns or grouped list, priority, “play next” sort, favorite/rating, quick status update. Prefer a grouped list for V1; drag-and-drop can wait.

Data: filtered games list and game patch endpoint.

### Settings (`/settings`)

Purpose: configure and troubleshoot local tracking.

Components: tracking toggle, polling/grace fields, timezone/week-start/theme, tracker status, data/database location, local log location.

Data: settings and tracker status.

### Visual direction

Use a neutral near-black/slate base, one restrained accent color, clear type hierarchy, shadcn/ui primitives, and accessible chart colors. Optimize first for a 1280px desktop view, remain usable on narrower screens, honor reduced motion, and meet keyboard/focus and color-contrast basics.

## 12. Data flow examples

### Register and track a game

```text
Add Game form
 -> POST /games
 -> GameService normalizes + validates executable
 -> GameRepository inserts row
 -> monitor mapping invalidated
 -> process snapshot matches executable
 -> SessionService starts one session
 -> dashboard reads active session + live elapsed duration
```

### Stop a game

```text
successful snapshot no longer sees game
 -> monitor starts missing timer
 -> grace period expires without reappearance
 -> SessionService ends at last_seen_at
 -> duration stored transactionally
 -> analytics queries include completed session
```

### Dashboard query

```text
GET /analytics/dashboard
 -> AnalyticsService calculates local date boundaries
 -> converts boundaries to UTC
 -> aggregate queries clip sessions to each boundary
 -> active durations use current UTC time
 -> one response populates coordinated dashboard cards
```

## 13. Important edge cases

| Case | V1 behavior |
|---|---|
| Same process appears in consecutive scans | Heartbeat existing session; never insert another. |
| Multiple processes for one registered game | One game-level active session. |
| Multiple different games run at once | One active session per game; durations may overlap. |
| Game briefly restarts | Preserve session if it returns inside grace period. |
| GameDeck starts after game | Start at observation time; do not invent earlier playtime. |
| GameDeck crashes while game runs | Active row is reconciled on next startup. |
| GameDeck is closed for hours while game remains running | Count gap as continuous and mark/document estimated continuity. |
| GameDeck closes and game later closes before restart | Recover end at last heartbeat; downtime after it is not counted. |
| Process enumeration partially fails | Skip affected process, log warning; grace period reduces false stops. |
| Entire process scan fails | Do not advance missing timers or close sessions. |
| PID reused | Creation time prevents treating PID alone as identity. |
| Duplicate executable configured | Reject non-archived duplicate mapping. |
| Executable renamed or moved | Show no detections until user updates configuration; tracker status aids diagnosis. |
| System clock changes | Persist UTC; use monotonic grace timers; duration still needs defensive non-negative validation. |
| Session crosses midnight/month boundary | Analytics clips duration to the requested interval. |
| Daylight-saving transition | Convert local boundaries to UTC before intersection calculations. |
| Archived game has history | Preserve game and sessions; exclude it from matching and default library view. |
| Database locked briefly | Short busy timeout and bounded retry; report persistent failure without discarding monitor state. |
| Backend starts twice | Warn via instance/monitor logging; database uniqueness prevents duplicate active sessions but installation should launch one instance. |

## 14. Testing strategy

Use a test pyramid: many fast service/algorithm tests, targeted database/API integration tests, and a small number of frontend flow tests. Tests use a temporary SQLite database with the same constraints and migrations as production.

### Unit tests

- Game normalization, enum/rating/priority/path validation.
- Matcher behavior for case, basename, exact path, inaccessible path, and ambiguity.
- Monitor state transitions from scripted process snapshots.
- Duplicate observations, multiple processes per game, simultaneous games, scan failure, access denied, and restart grace.
- Session duration and idempotent start/stop.
- Startup recovery branches.
- Time-range clipping for sessions crossing boundaries.
- Analytics totals, top game, longest/average session, weekday/hour buckets, and active sessions.

Create a fake `ProcessSource`; never require a real game or `psutil` process state in automated tests. Use a controllable clock rather than sleeping.

### Database integration tests

- Partial unique active-session index.
- Foreign-key restriction.
- End-before-start and duration consistency checks.
- Archive behavior preserves history.
- Analytics queries on overlapping ranges and empty datasets.
- Migrations apply to a blank database.

### API tests

- CRUD happy paths and not-found responses.
- Duplicate executable conflict.
- Query filters, sorting, and pagination.
- Manual-session validation and overlap rejection.
- Settings bounds.
- Dashboard response contract on empty and populated databases.

### Frontend tests

- Form validation and error presentation.
- Dashboard loading, empty, populated, and tracker-error states.
- Library filters and status updates.
- Session correction workflow.
- One end-to-end smoke flow against a test backend: add game, inject a fake process transition, verify the active then completed session and dashboard total.

### Manual Windows acceptance tests

- Track a harmless test executable through start/stop.
- Close/reopen GameDeck while it runs.
- Kill GameDeck uncleanly and verify recovery.
- Restart the test executable inside and outside the grace period.
- Run two configured test executables together.
- Confirm low idle CPU use and reasonable log volume over at least two hours.

## 15. Development phases and definitions of done

Each phase should end in a demonstrable, tested vertical or foundational result. Estimates are intentionally omitted until the developer's weekly availability is known.

### Phase 0 — Decisions and UX sketch

Goal: remove ambiguity before code.

- Work: approve this plan; write three short architecture decision records (local browser first, SQLite, polling); sketch Dashboard, Library, and Game Details; define API/error conventions.
- Tests: none; define acceptance test fixtures and sample data.
- Done: V1/exclusions, schema, session semantics, and wireframes are approved with unresolved questions recorded.

### Phase 1 — Backend foundation and database

Goal: produce a runnable, migration-backed local API shell.

- Backend: project setup, configuration, logging, FastAPI app factory/lifespan, SQLAlchemy session management, SQLite pragmas, Alembic, `games`, `game_sessions`, and `settings` migrations, health endpoint.
- Frontend: none beyond repository placeholder.
- Tests: health endpoint, blank migration, constraint tests, temporary database fixture.
- Done: a clean checkout can create the database, start the backend, return healthy, and pass tests. No game CRUD yet.

### Phase 2 — Game library vertical slice

Goal: register and manage trackable games through a basic UI.

- Backend: game schemas/service/repository/routes, normalization, archive/restore, filters.
- Frontend: Vite/React/Tailwind/shadcn setup, application shell, Library page, add/edit/archive flows.
- Tests: service validation, API CRUD/conflicts/filters, essential form tests.
- Done: user can add an executable, edit it, filter it, archive it, restore it, restart the app, and retain data.

### Phase 3 — Session domain and manual history

Goal: make session rules correct before adding live process input.

- Backend: SessionService/repository/routes, idempotent transitions, manual create/edit/delete, active uniqueness and overlap policy.
- Frontend: Sessions page and Game Details session table/editor.
- Tests: duplicate prevention, duration, invalid ranges, overlap, concurrent insert behavior.
- Done: scripted service calls and API actions cannot create invalid or duplicate active sessions.

### Phase 4 — Windows process tracking

Goal: reliably convert registered process state into sessions.

- Backend: process-source adapter, matcher, monitor state machine, grace handling, startup/shutdown reconciliation, status endpoint, cache invalidation.
- Frontend: tracker status and active game indicators; settings controls for tracking/interval/grace.
- Tests: fake snapshots cover all transition and failure cases; manual Windows acceptance matrix.
- Done: test executables generate correct sessions through normal, restart, simultaneous, denied-process, and GameDeck restart scenarios, with no duplicate sessions.

### Phase 5 — Analytics and dashboard

Goal: turn trustworthy sessions into useful insight.

- Backend: boundary/clipping helpers, dashboard/game/playtime/distribution queries.
- Frontend: Dashboard and Analytics pages, charts, range controls, empty/loading/error states.
- Tests: deterministic boundary and aggregation fixtures, API contracts, dashboard component states.
- Done: all numbers reconcile with seeded session data, including sessions crossing midnight and active sessions.

### Phase 6 — Backlog experience

Goal: make the library useful for deciding what to play.

- Backend: finish status/priority/favorite filters and update rules.
- Frontend: Backlog grouped view, quick status/priority actions, favorites/play-next ordering, polished Game Details metadata.
- Tests: filter/sort/status behavior and key interactions.
- Done: user can move games through the backlog lifecycle and reliably retrieve a prioritized play-next list.

### Phase 7 — Reliability and usability

Goal: make daily use safe and diagnosable.

- Backend: bounded database retry, log rotation, graceful error handling, backup/export design or simple database-copy instructions, performance checks.
- Frontend: accessibility pass, responsive layouts, confirmation dialogs, actionable tracker errors.
- Tests: long-running monitor smoke test, database-busy behavior, corrupted-input/error-state checks, full acceptance suite.
- Done: app survives expected failures without corrupting sessions; all priority tests pass; idle resource usage and known limitations are recorded.

### Phase 8 — Portfolio polish and release

Goal: present a coherent engineering project.

- Work: seeded demo mode or sample-data command, screenshots, architecture diagram, demo video/GIF, decision records, setup scripts, changelog, license, contribution notes, release checklist.
- Tests: clean-machine setup rehearsal and full CI suite on Windows.
- Done: a reviewer can understand the project in two minutes, run it from documented steps, and see a reliable end-to-end demo.

### Phase 9 — Optional integrations

Goal: add only features justified by actual use.

- Candidates: spending, multiple executable aliases, Steam import, Tauri packaging, FiveM favorites, Discord presence, cloud sync.
- Done: each integration gets its own small proposal, privacy/failure analysis, and acceptance criteria before implementation.

## 16. Overall V1 definition of done

V1 is complete when:

- A new Windows user can follow the README to install dependencies, initialize data, and start GameDeck locally.
- Registered games are the only processes tracked.
- Automatic sessions behave correctly for starts, stops, brief restarts, simultaneous games, startup while a game is running, clean shutdown, and crash recovery.
- Database constraints prevent invalid times and duplicate active sessions.
- Users can audit and correct session history.
- Dashboard and analytics reconcile with known seeded data.
- Library, backlog, details, sessions, analytics, and settings flows are usable with empty/loading/error states.
- Automated backend tests pass in Windows CI; the critical frontend flow and manual tracker acceptance matrix pass.
- No cloud service or secret is required.
- Logs do not expose unrelated process command lines or sensitive data.
- README, screenshots, architecture diagram, decisions, limitations, and demo are complete.

## 17. Future integrations

Recommended order after real V1 usage:

1. Spending and cost-per-hour, because it builds only on local data and the planned purchases schema.
2. Multiple executable mappings per game, if launchers/emulators reveal a real need.
3. Tauri packaging and startup integration, once lifecycle behavior is stable.
4. Steam metadata/library import, with API keys stored outside source control and graceful offline behavior.
5. FiveM favorite servers as manual records; add status/player APIs only after verifying reliability and terms.
6. Discord Rich Presence before a full bot, because it is smaller and personal.
7. Cloud sync/PostgreSQL/authentication only if multi-device use becomes valuable.

If cloud sync is added, introduce accounts, hashed/OAuth-backed authentication, authorization on every user-owned row, TLS, secret management, migrations from local IDs to stable UUIDs, conflict resolution, and a clear local/offline mode. This is a new product phase, not a database toggle.

## 18. Potential technical risks

| Risk | Impact | Mitigation |
|---|---|---|
| Windows process paths are inaccessible | False negative or weaker name-only match | Per-process error handling, unique basename rule, observable tracker status, manual tests. |
| Launchers do not equal game processes | Inaccurate sessions | Configure the actual game executable; defer launcher heuristics and support aliases later. |
| Monitor runs twice during development/package startup | Duplicate work/database contention | Single-worker rule, lifecycle guard, clear logs, database uniqueness. |
| App downtime makes exact end time unknowable | Estimated duration | Heartbeat and documented recovery policy; manual correction. |
| Calendar analytics are subtly wrong | Loss of trust | UTC storage, local-boundary conversion, interval clipping, deterministic tests. |
| SQLite lock contention | Missed transitions | WAL, short transactions, throttled heartbeats, busy timeout, bounded retries. |
| Frontend scope consumes time before core reliability | Weak central feature | Deliver library, session domain, and tracker before elaborate charts/polish. |
| Local image/file paths move | Broken covers/configuration | Treat covers as optional; later copy selected assets into app data. Never execute stored paths. |
| Soft-deleted games collide with new executable mapping | Confusing restore behavior | Enforce uniqueness only among active games and check conflicts on restore. |
| psutil or packaging behaves differently across Windows machines | Installation friction | Windows CI plus clean-machine rehearsal; package only after browser V1 stabilizes. |

## 19. Portfolio presentation strategy

### What to emphasize

- A state-machine-like process monitor with fake process sources and a controllable clock.
- Layered duplicate prevention: idempotent service logic plus a partial unique database index.
- Honest crash recovery under incomplete information using heartbeats.
- Correct interval-clipped, timezone-aware analytics instead of naive `started_at` filtering.
- Pragmatic architecture choices and explicitly rejected complexity.
- A tested migration-backed local application with useful failure states.

### Screenshots and demo sequence

Use five screenshots: dashboard, filtered library, game details/session history, analytics, and tracker settings/status. A 60-90 second demo should register a harmless test executable, launch it, show the live current-game state, stop it, and show the completed session updating analytics.

### Interview discussion prompts

- Why polling every five seconds is appropriate and why events/WMI were deferred.
- How the app avoids duplicate sessions across repeated observations and concurrent calls.
- What can and cannot be known after the tracker was offline.
- How a session crossing midnight contributes to two daily totals.
- Why SQLite is enough, what WAL changes, and when PostgreSQL would become justified.
- How the same backend/frontend boundary permits later desktop packaging.

### Example resume bullets

- Built a local-first Windows gaming dashboard with React, FastAPI, SQLAlchemy, and SQLite that detects registered game processes and records recoverable play sessions.
- Designed idempotent session tracking with database-enforced active-session uniqueness, heartbeat-based crash recovery, and tested restart-grace handling.
- Implemented timezone-aware SQL analytics for playtime trends and game rankings, backed by unit, API, migration, and mocked process-monitor tests.

### Example portfolio description

> GameDeck is a local-first Windows dashboard for managing a personal game library and automatically tracking play sessions. Its core engineering challenge is turning imperfect process observations into trustworthy history: it handles duplicate observations, brief restarts, simultaneous games, permission errors, and interrupted sessions without cloud infrastructure. The project uses a deliberately simple modular monolith and documents where its recovery estimates cannot be exact.

## 20. Suggested README structure

1. Project title, one-sentence value proposition, and hero dashboard image.
2. Demo GIF/video link.
3. Key features.
4. Why this project exists.
5. How session tracking works, including the recovery limitation.
6. Architecture diagram.
7. Technology choices and short tradeoffs.
8. Screenshots.
9. Requirements and Windows-local quick start.
10. Configuration and data/log locations.
11. Testing instructions.
12. Database/schema overview.
13. API overview or OpenAPI link.
14. Project structure.
15. Engineering decisions and challenges solved.
16. Privacy and security notes.
17. Known limitations.
18. Roadmap.
19. License and acknowledgements.

## Decisions to approve before implementation

The proposed defaults are:

- Local browser application for V1; Tauri later.
- Five-second scan interval and 15-second restart grace.
- One active session per game; different games may overlap.
- Unique non-archived executable basename, with optional exact path.
- UTC persistence and system-local analytics boundaries; Monday week start.
- Keep an active session through GameDeck downtime if the game is still running at restart; otherwise close it at the last heartbeat.
- Archive games rather than deleting their session history.
- Manual correction is part of V1 because recovery cannot always be exact.

# Recommended first implementation milestone

Build **Phase 1: the tested backend foundation and database**, and nothing from the live process tracker yet.

The milestone should contain exactly:

1. Python project and developer setup instructions.
2. FastAPI application factory with monitoring disabled.
3. Typed local configuration and structured/rotating logging configuration.
4. SQLAlchemy engine/session setup with SQLite foreign keys, WAL mode, and busy timeout.
5. Alembic configured from the beginning.
6. First migration containing only `games`, `game_sessions`, and the single-row `settings` table with the constraints and indexes in this plan.
7. `GET /health` that verifies application and database readiness.
8. Pytest fixtures using a temporary SQLite database.
9. Tests proving migrations apply and the critical session constraints reject invalid rows and duplicate active sessions.
10. A short architecture decision record for local-browser V1, SQLite, and process polling.

Milestone acceptance: from a clean checkout, one documented command installs/sets up the backend, one command applies migrations, one command starts the API, `/health` succeeds, and the full Phase 1 test suite passes. Stop there for review before implementing game CRUD.
