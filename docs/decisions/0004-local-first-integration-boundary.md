# ADR 0004: Keep external transmission and cloud sync out of GameDeck

Status: accepted, 2026-08-11

## Decision

GameDeck 0.8 closes its optional-integration roadmap without automatic Discord messages, webhooks, Rich Presence, cloud sync, PostgreSQL, accounts, or authentication.

Discord-facing value is delivered as a locally generated announcement copied only after a user action. Steam is the sole network integration: an explicit, preview-only read through Valve's official API, with its key retained in the backend environment. All writes remain local.

## Rationale

Automatic Discord transmission introduces bot applications, tokens, channel permissions, rate limits, and accidental disclosure risks for a personal planning feature already served by copyable output. Cloud sync is a different multi-user product: it requires identity, authorization on every row, TLS, hosted operations, stable cross-device IDs, conflict resolution, secret management, data export/deletion policy, and offline reconciliation.

Neither is justified by the approved personal, cheap, offline-first scope. Adding placeholder cloud code would weaken the portfolio by implying guarantees the application does not provide.

## Reconsideration threshold

Revisit cloud sync only after documented multi-device usage demand and a separate threat model, data ownership policy, conflict strategy, operating budget, and migration plan are approved. Revisit Discord sending only when repeated manual posting demonstrates value and a narrowly scoped webhook destination can be protected and revoked.
