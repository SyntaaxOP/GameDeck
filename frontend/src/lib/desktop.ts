export const isDesktop = () => window.location.protocol === 'tauri:' || window.location.hostname === 'tauri.localhost'

export async function notify(title: string, body: string): Promise<void> {
  if (!isDesktop()) return
  const notifications = await import('@tauri-apps/plugin-notification')
  let granted = await notifications.isPermissionGranted()
  if (!granted) granted = (await notifications.requestPermission()) === 'granted'
  if (granted) notifications.sendNotification({ title, body })
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
