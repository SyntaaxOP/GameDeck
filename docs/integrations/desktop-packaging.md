# Windows desktop packaging

GameDeck's Tauri 2 shell bundles the production React build and a PyInstaller FastAPI sidecar. The shell starts exactly that scoped sidecar, and destroys it when the window closes. The sidecar migrates and stores its database, logs, and backups under `%LOCALAPPDATA%\GameDeck`; it does not write inside the installation directory.

The WebView can connect only to the loopback API under the configured content-security policy. Tauri capability permissions allow spawning only `binaries/gamedeck-api`. The normal browser development workflow remains supported.

Run `scripts/build-sidecar.ps1`, then `cargo tauri build --manifest-path src-tauri/Cargo.toml` on a Windows machine with Rust, Microsoft C++ Build Tools, and WebView2. The manual/tagged Windows packaging workflow performs the same reproducible build. This workstation lacks Rust and C++ Build Tools, so installer compilation is delegated to that workflow rather than silently installing system toolchains.

For a native development window after installing the Windows prerequisites, run `powershell -ExecutionPolicy Bypass -File .\scripts\run-desktop.ps1`. The script builds the React frontend and FastAPI sidecar before starting the Tauri window; no separate browser or backend terminal is required.

References: [Tauri sidecars](https://v2.tauri.app/develop/sidecar/), [Windows prerequisites](https://v2.tauri.app/start/prerequisites/), and [Windows installer guidance](https://v2.tauri.app/distribute/windows-installer/).
