export function apiUrl(path: string): string {
  const desktop = window.location.protocol === 'tauri:' || window.location.hostname === 'tauri.localhost'
  return desktop ? `http://127.0.0.1:8000${path}` : path
}
