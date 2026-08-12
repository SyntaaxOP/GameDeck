#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::sync::Mutex;
#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, WindowEvent,
};
use tauri_plugin_autostart::MacosLauncher;
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct Backend(Mutex<Option<CommandChild>>);

#[cfg(target_os = "windows")]
fn stop_stale_backend() {
    const CREATE_NO_WINDOW: u32 = 0x08000000;
    let _ = Command::new("taskkill")
        .args([
            "/F",
            "/T",
            "/IM",
            "gamedeck-api-x86_64-pc-windows-msvc.exe",
        ])
        .creation_flags(CREATE_NO_WINDOW)
        .output();
}

#[cfg(not(target_os = "windows"))]
fn stop_stale_backend() {}

#[tauri::command]
fn open_author_github() -> Result<(), String> {
    const AUTHOR_URL: &str = "https://github.com/syntax-000";

    #[cfg(target_os = "windows")]
    {
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        Command::new("explorer.exe")
            .arg(AUTHOR_URL)
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .map(|_| ())
            .map_err(|error| format!("Could not open the author profile: {error}"))
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(AUTHOR_URL)
            .spawn()
            .map(|_| ())
            .map_err(|error| format!("Could not open the author profile: {error}"))
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        Command::new("xdg-open")
            .arg(AUTHOR_URL)
            .spawn()
            .map(|_| ())
            .map_err(|error| format!("Could not open the author profile: {error}"))
    }
}

fn show_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
}

fn stop_backend(app: &AppHandle) {
    if let Some(backend) = app.try_state::<Backend>() {
        if let Ok(mut child) = backend.0.lock() {
            if let Some(child) = child.take() {
                let _ = child.kill();
            }
        }
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![open_author_github])
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_autostart::init(
            MacosLauncher::LaunchAgent,
            None,
        ))
        .setup(|app| {
            stop_stale_backend();
            let (_events, child) = app.shell().sidecar("gamedeck-api")?.spawn()?;
            app.manage(Backend(Mutex::new(Some(child))));

            let show = MenuItem::with_id(app, "show", "Show GameDeck", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit GameDeck", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &quit])?;
            let icon = app
                .default_window_icon()
                .cloned()
                .ok_or("GameDeck window icon is missing")?;

            TrayIconBuilder::new()
                .icon(icon)
                .tooltip("GameDeck")
                .menu(&menu)
                .on_menu_event(|app, event| match event.id().as_ref() {
                    "show" => show_main_window(app),
                    "quit" => {
                        stop_backend(app);
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        show_main_window(tray.app_handle());
                    }
                })
                .build(app)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .run(tauri::generate_context!())
        .expect("failed to run GameDeck desktop shell");
}
