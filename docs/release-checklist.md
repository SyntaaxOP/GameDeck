# Release checklist

## Code and data

- [ ] Version is consistent in backend, frontend, changelog, desktop shell, and UI (`0.8.1`).
- [ ] Alembic upgrades an empty database to head and reports no pending operations.
- [ ] Demo seed succeeds twice without duplicates or changes to existing records.
- [ ] Backend, frontend, migration, lint, and production-build checks pass on Windows.
- [ ] Git status contains no database, log, backup, environment, or dependency artifacts.

## Manual acceptance

- [ ] Empty-state onboarding works before demo data is added.
- [ ] Library create/edit/archive/restore and executable conflict flows work.
- [ ] A harmless registered executable produces one start and one stop session.
- [ ] Brief restart, simultaneous games, monitor failure, and restart recovery match the acceptance matrix.
- [ ] Manual session correction updates details, dashboard, and analytics.
- [ ] Backlog quick actions and Play Next ordering work by keyboard.
- [ ] Purchase CRUD, separate-currency totals, and zero-playtime cost handling work.
- [ ] Executable alias create/edit/remove, active-library conflicts, archive/restore, and single-session matching work.
- [ ] FiveM CRUD, game-night RSVPs/announcement copy, Steam preview/import, and PC profile flows work.
- [ ] Desktop sidecar build and NSIS packaging workflow produce an artifact on a tagged/manual Windows run.
- [ ] Diagnostics report `ok`; a created backup passes integrity check and a restore rehearsal succeeds.
- [ ] Desktop and narrow layouts have no clipped controls or inaccessible dialogs.

## Portfolio handoff

- [ ] README quick start works in a clean Windows environment.
- [ ] Five screenshots match the current release and contain demo-only data.
- [ ] Demo script/video, architecture diagrams, decisions, limitations, and recovery guide are linked.
- [ ] `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, and `SECURITY.md` are present.
- [ ] Windows CI is green and the release tag is `v0.8.1`.
