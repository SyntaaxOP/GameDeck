# ADR 0003: Detect games with periodic process polling

- Status: accepted for Phase 1; implementation begins in Phase 4
- Date: 2026-08-11

## Context

GameDeck must notice registered Windows game executables starting and stopping. Detection needs to be understandable, testable without real games, and resilient to process access errors.

## Decision

Use `psutil` snapshots every five seconds by default. Match only registered executable basenames, optionally strengthened by exact paths. Feed snapshot changes into an idempotent session service and allow a 15-second restart grace period.

Phase 1 deliberately records this decision but does not install `psutil` or start a monitor.

## Consequences

- Polling is portable across supported Windows versions and easily replaced with a fake source in tests.
- Idle cost should be negligible when only required process fields are requested.
- Sessions shorter than the interval can be missed.
- Permission errors and transient process disappearance must be handled per process.
- Event-based WMI/ETW integration can be reconsidered only if measured polling behavior is inadequate.

## Alternatives considered

- A one-second interval is more responsive but unnecessary for normal gaming sessions.
- WMI or ETW events may reduce detection delay but add Windows-specific complexity and more difficult tests.
- Tracking launchers is unreliable; V1 will register actual game executables explicitly.

