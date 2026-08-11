# Local game nights and Discord-ready sharing

GameDeck stores game-night schedules, optional library games, duration, status, notes, and up to 50 attendee responses. It generates a plain-text Discord announcement and copies it only after a user action.

No Discord token, account, webhook, network request, or automatic message sending is used. Attendee names remain local. Saves replace the attendee roster atomically; duplicate names are rejected case-insensitively.

Acceptance requires CRUD, RSVP counts, local-time display, UTC storage, copyable announcement output, validation, and responsive empty/error states.
