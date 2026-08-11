# Executable aliases

## Scope

GameDeck may associate one primary Windows executable and up to 10 explicitly configured aliases with a game. Each mapping has a required `.exe` filename and an optional absolute path. The tracker treats every mapping as another way to identify the same game, so simultaneous matching processes still produce one game session.

This integration does not discover aliases, infer launcher-child relationships, execute stored paths, or upload process information.

## Data and conflict rules

- Active executable filenames are unique case-insensitively across the entire library, including primary mappings and aliases.
- An optional path narrows a mapping to that exact normalized Windows path when process path data is available.
- A path's filename must match its executable filename.
- Archiving preserves mappings but releases their active filename claims.
- Restoring reclaims every mapping atomically. Any conflict leaves the game archived.
- Editing an archived game preserves its mappings as inactive until restore.

## Failure and privacy behavior

- A validation or uniqueness failure rolls back the full save; partial alias lists are never retained.
- Process-snapshot failures retain the existing tracker failure-safety behavior and do not end sessions.
- No additional process metadata is stored. Sessions remain keyed to the game and retain only the existing process ID and start-time fields.

## Acceptance criteria

- Existing databases receive a primary mapping for every existing game during migration.
- Primary and alias conflicts return the same `executable_conflict` API error.
- Matching any alias starts or maintains the game's single active session.
- Matching multiple aliases together never creates multiple active sessions.
- Users can add, edit, and remove aliases in the game form and see them on game details.
- Backend tests, frontend tests, lint, build, and migration verification pass.
