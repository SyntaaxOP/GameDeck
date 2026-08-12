export const isDesktop = () => window.location.protocol === 'tauri:' || window.location.hostname === 'tauri.localhost'

export async function openAuthorGithub(): Promise<void> {
  const url = 'https://github.com/syntax-000'
  if (!isDesktop()) {
    window.open(url, '_blank', 'noopener,noreferrer')
    return
  }
  const { invoke } = await import('@tauri-apps/api/core')
  await invoke('open_author_github')
}

export async function notify(title: string, body: string): Promise<'sent' | 'denied'> {
  if (!isDesktop()) throw new Error('Notifications are available only in the installed desktop app.')
  const notifications = await import('@tauri-apps/plugin-notification')
  let granted = await notifications.isPermissionGranted()
  if (!granted) granted = (await notifications.requestPermission()) === 'granted'
  if (!granted) return 'denied'
  await notifications.sendNotification({ title, body })
  return 'sent'
}

export async function getAutostart(): Promise<boolean> {
  if (!isDesktop()) return false
  return (await import('@tauri-apps/plugin-autostart')).isEnabled()
}
export async function setAutostart(enabled: boolean): Promise<void> {
  if (!isDesktop()) return
  const autostart = await import('@tauri-apps/plugin-autostart')
  await (enabled ? autostart.enable() : autostart.disable())
}
