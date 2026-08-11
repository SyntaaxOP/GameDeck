# Spending and cost-per-hour integration

## Decision

Add a manual, local purchase ledger and derived cost-per-hour views. This is the first Phase 9 integration because it reuses trusted local game/session data and requires no external account, network request, secret, or platform-specific dependency.

## Scope

- Record base games, DLC, subscriptions, and other purchases in integer minor units.
- Optionally associate a purchase with one game; subscriptions may remain unassigned.
- List, add, edit, and delete ledger entries.
- Show totals grouped by ISO currency code without converting or combining currencies.
- Show cost per played hour for game-attributed purchases, per game and per currency.
- Include purchases in backups automatically because they share the SQLite database.

Deferred: storefront imports, receipt uploads, exchange rates, refunds/negative amounts, recurring billing automation, budgets, wish-list pricing, and cloud sync.

## Privacy and security

All purchase data stays in local SQLite and verified backups. GameDeck contacts no financial service and stores no account, card, receipt, or transaction identifier. Notes remain user-entered free text; users should not enter payment credentials. Logs do not include purchase notes or amounts.

## Failure behavior

- Money is stored as non-negative integer minor units, never floating point.
- Invalid currency codes, dates, kinds, missing games, and oversized text are rejected before commit.
- Deleting a game remains archival; purchase history is preserved.
- Deleting a ledger entry is explicit and permanent.
- Zero playtime produces an unavailable cost-per-hour value rather than division by zero.
- Different currencies remain separate. GameDeck never implies an exchange rate.
- Database busy and backup/recovery behavior remains the same as the rest of GameDeck.

## Acceptance criteria

- A user can create, edit, filter, and delete a purchase from the Spending page.
- An unassigned subscription is valid; an unknown game is not.
- Amount constraints and game deletion restrictions are enforced by SQLite as well as the API.
- Global totals and game cost-per-hour use completed session seconds and reconcile with deterministic tests.
- Multiple currencies render as separate totals with no conversion.
- A game with purchases but no playtime displays “Not played yet.”
- Demo mode seeds repeatable purchase records without changing existing data.
- Alembic upgrades both empty and existing Phase 8 databases without data loss.
