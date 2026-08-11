# 90-second demo

## Prepare

Run setup, then seed a separate demo database if you do not want sample records mixed into your normal library:

```powershell
.\scripts\seed-demo.ps1 -DatabaseUrl "sqlite:///data/gamedeck-demo.db" -At "2026-08-11T12:00:00Z"
```

Start the backend with that same `GAMEDECK_DATABASE_URL`, then start the frontend.

## Recording sequence

1. **Dashboard (10 seconds):** show the month totals, recent sessions, current queue, and top game. Explain that every value comes from local session history.
2. **Library and details (15 seconds):** filter the library, open a game, and point out the executable mapping and auditable sessions.
3. **Backlog (10 seconds):** change a favorite or priority and show the server-defined Play Next ordering.
4. **Analytics (12 seconds):** switch ranges and explain local-time calendar clipping for sessions that cross midnight.
5. **Spending (12 seconds):** show PHP and USD as separate totals, open a demo purchase, and point out cost-per-hour derived from recorded sessions.
6. **Live tracking (20 seconds):** register a harmless test executable, launch it, wait for the Running badge, stop it, then show the completed session. State that brief restarts keep one continuous session.
7. **Settings (11 seconds):** show tracker health, storage paths, SQLite integrity, and create a verified backup containing library, sessions, and purchases.

Close with: “GameDeck keeps process observations and play history local, handles imperfect recovery explicitly, and remains fully usable offline.”

Use the five checked-in screenshots for a silent portfolio carousel when a recording is not available.
