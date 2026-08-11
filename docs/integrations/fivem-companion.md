# FiveM companion

## Scope

GameDeck stores manually curated FiveM server names, addresses, connect codes, Discord links, notes, favorites, last-joined timestamps, and manual playtime. It does not execute connect codes, launch FiveM, query live server status, or contact Discord.

## Privacy and failure behavior

All records stay in local SQLite and verified backups. Address uniqueness is case-insensitive. Saves are atomic, invalid Discord links are rejected, and unavailable external services cannot affect this page because it performs no network requests.

## Acceptance criteria

- Create, edit, favorite, mark joined, and delete a server.
- Duplicate addresses return a conflict without partial changes.
- Manual playtime is nonnegative and rendered as a duration.
- Empty, loading, API-error, destructive-confirmation, desktop, and narrow states are usable.
