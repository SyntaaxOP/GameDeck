# ADR 0002: Use SQLite with migrations

- Status: accepted for Phase 1
- Date: 2026-08-11

## Context

GameDeck is a local, single-user application. Its normal workload is small: UI reads plus occasional session-transition and heartbeat writes. User history must survive application upgrades safely.

## Decision

Use SQLite through SQLAlchemy 2. Enable foreign keys, WAL journal mode, a five-second busy timeout, and short transactions. Manage schema changes through Alembic from the first revision.

## Consequences

- No database service or cloud account is required.
- WAL improves coexistence between dashboard reads and tracker writes.
- Database constraints provide a final defense for session correctness.
- The application must still handle temporary lock contention and keep one monitor owner.
- Migration tests become part of every schema change.

## Alternatives considered

- Calling SQLAlchemy `create_all()` is simpler initially but does not safely evolve a user's existing data.
- PostgreSQL adds operational cost with no V1 benefit; it remains an option if cloud sync or multiple users are introduced.

