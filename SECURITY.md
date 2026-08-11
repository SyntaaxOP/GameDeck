# Security and privacy

GameDeck is a single-user local application with no authentication boundary. Do not expose its backend port beyond the local machine. The SQLite database and backups contain library notes and detailed play history and are not encrypted by GameDeck.

Report a suspected vulnerability privately to the repository owner rather than opening a public issue. Include the affected version, reproduction steps, impact, and any suggested mitigation. Do not attach real databases, logs, usernames, or filesystem paths; reproduce with the demo-data command when possible.

Supported security fixes target the latest release. Dependencies are pinned by compatible version ranges and checked by the Windows CI suite.
