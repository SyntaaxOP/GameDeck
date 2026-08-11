# Local Steam library discovery

GameDeck discovers installed Steam games locally without credentials. On backend startup it locates Steam through `GAMEDECK_STEAM_PATH`, the Windows registry, or the standard Program Files locations. It then reads `steamapps/libraryfolders.vdf` and the `appmanifest_*.acf` files in every configured library.

Only installations whose `steamapps/common/<installdir>` directory exists are imported. Steam app IDs make synchronization idempotent, so rescans do not create duplicate games or overwrite personal status, ratings, notes, or session history. The Steam library page also exposes an explicit **Scan again** action.

Known Steam runtimes, SDKs, samples, redistributables, and always-running desktop utilities are excluded so they cannot create false gaming sessions.

For process tracking, each discovered game stores its install directory. A running executable underneath that directory identifies the game even when the executable filename differs from the title or changes after an update. Known Steam, installer, redistributable, and crash-reporting helpers are ignored. Explicit executable mappings remain available when a game requires a narrower match.

The older optional Steam Web API preview remains available for importing owned but uninstalled titles. Those titles cannot be process-tracked until Steam installs them and local discovery supplies an install directory.

GameDeck never reads Steam credentials, modifies Steam manifests, launches downloads, or scans unrelated personal folders.
