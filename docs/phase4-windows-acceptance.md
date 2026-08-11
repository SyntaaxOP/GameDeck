# Phase 4 Windows acceptance matrix

Run these checks on Windows with the backend and frontend open. Use short-lived test executables or registered games whose session history can be removed afterward.

| Scenario | Action | Expected result |
|---|---|---|
| Normal launch | Register an executable, launch it, wait one scan, then close it beyond the grace period | One process session appears and ends at the last observed time |
| Brief restart | Close and relaunch the executable within restart grace | The same active session continues; no duplicate is created |
| Long restart | Close beyond restart grace, then relaunch | The first session ends and a new session starts |
| Multiple games | Launch two registered executables together | Both games show Running and each has one active session |
| Child processes | Launch a game that creates multiple same-name processes | Only one active session exists for the game |
| Restricted process | Observe a process whose path cannot be read | The tracker remains healthy and uses safe name matching when possible |
| Backend restart | Restart GameDeck while the game remains open | The existing active session continues after reconciliation |
| Stale recovery | Stop GameDeck, close the game, then restart GameDeck | The stale session closes at its previous last-seen time with recovered reason |
| Tracking pause | Pause tracking, close a game, then resume | The open session is preserved while paused and reconciled on resume |
| Clean shutdown | Stop GameDeck while a game is running | A final successful snapshot refreshes the open session for next-start recovery |
| Scan failure | Temporarily deny process enumeration | No sessions close solely because the scan failed; health displays the error |

Confirm the Settings page reports a recent scan, the Library Running badge agrees with Task Manager, and session history contains no duplicates after every scenario.
