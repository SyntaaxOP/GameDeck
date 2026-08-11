# ADR 0001: Use a local browser application for V1

- Status: accepted for Phase 1
- Date: 2026-08-11

## Context

GameDeck needs a React user interface and Python access to Windows processes. It may eventually feel like an installed desktop application, but the core tracking behavior and product workflow are not yet proven.

## Decision

V1 will run FastAPI and React locally and open the frontend in the user's normal browser. Windows process and filesystem access will remain behind the backend REST API.

## Consequences

- Browser developer tools and separate frontend/backend development remain straightforward.
- V1 needs a documented local startup flow and uses a loopback HTTP connection.
- Native installation, auto-start, tray behavior, and auto-update are deferred.
- A later Tauri shell can launch the same backend and load the built React frontend without moving process access into TypeScript or rewriting domain logic.

## Alternatives considered

- FastAPI-rendered HTML would reduce tooling but weaken the requested React/full-stack experience.
- Tauri from the start would improve native presentation while adding Rust, packaging, lifecycle, and permission work before the core tracker is stable.

