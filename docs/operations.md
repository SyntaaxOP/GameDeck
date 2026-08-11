# GameDeck operations and recovery

## Backups

Create a backup from **Settings and diagnostics**. GameDeck uses SQLite's online backup API, runs `PRAGMA integrity_check` against the result, and publishes the file only after the check returns `ok`. The active application can remain running while the backup is created.

Backups are written to `backend/backups` by default. Override this with `GAMEDECK_BACKUP_DIR`. Backup files contain the complete local library and play history and are not encrypted; protect them like the main database.

### Restore a backup

1. Stop the GameDeck backend.
2. Note the database path shown in Settings.
3. Move the current database and any adjacent `-wal` and `-shm` files into a separate recovery folder. Do not delete them until the restore is verified.
4. Copy the chosen `.db` backup to the configured database path and rename it to the expected database filename.
5. Run `alembic upgrade head` from `backend`.
6. Start GameDeck and check `/health`, Settings diagnostics, game count, and recent sessions.

GameDeck deliberately does not expose an in-app restore button because replacing the live database is a destructive operation that should occur while the backend is stopped.

## Database contention

SQLite uses WAL mode and a bounded busy timeout (`GAMEDECK_SQLITE_BUSY_TIMEOUT_MS`, 5 seconds by default). If another writer holds the database beyond that window, the API returns HTTP 503 with code `database_busy` and `Retry-After: 1`. Wait briefly and retry. GameDeck rolls the failed request back before returning the error.

Repeated busy responses usually mean a second backend worker, database inspection tool, sync client, or backup utility is holding a write transaction. GameDeck must run with one Uvicorn worker.

## Tracker troubleshooting

- A failed process snapshot never means every game stopped. Active sessions remain open until a successful snapshot reconciles them.
- Check the latest successful scan and error in Settings.
- Confirm tracking is enabled and the executable name/path matches Task Manager.
- Check the displayed `gamedeck.log` path. Logs rotate at 2 MB with three retained archives and do not record unrelated process command lines.
- Restart the single backend worker if successful scans do not resume.
- Correct estimated or stale times from Session history when Windows access or application downtime made the exact stop time unknowable.

## Health and performance checks

`GET /health` verifies database connectivity. `GET /api/v1/system/diagnostics` additionally reports the SQLite quick-check result, journal mode, bounded busy timeout, database/WAL/log sizes, record counts, and probe latency.

Automated reliability coverage includes 300 consecutive monitor scans without sleeping, lock exhaustion, malformed JSON, crossed calendar boundaries, backup integrity, and the complete API/component regression suite. Monitor writes remain limited to state transitions and 15-second heartbeats; successful scans do not generate log entries.

## Known limitations

- Sessions shorter than the scan interval can be missed.
- Playtime while GameDeck is offline is estimated when the game is still running at restart.
- Restricted Windows process paths can require unique name-only matching.
- One backend worker is required; multi-worker ownership is unsupported.
- Interactive analytics ranges are limited to 366 days per request.
- Backlog loads the first 100 active-library records in this personal V1.
- Backups are local, manual, and unencrypted; automatic scheduling and off-device copies are deferred.
- The repository path's `#` character triggers an upstream Vite/Vitest Windows resolution issue; use a path such as `C:\Projects\GameDeck` for direct component-test execution.
