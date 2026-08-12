import { useEffect, useState } from 'react'
import { Activity, Bell, CheckCircle2, Database, FolderArchive, Globe2, MonitorUp, Power, RefreshCw, Save, TriangleAlert } from 'lucide-react'

import { getSettings, getTrackerStatus, updateSettings } from '@/api/settings'
import { createBackup, getDiagnostics, listBackups } from '@/api/system'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { AppSettings, TrackerStatus } from '@/types/settings'
import type { BackupInfo, Diagnostics } from '@/types/system'
import { getAutostart, isDesktop, notify, setAutostart } from '@/lib/desktop'

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [tracker, setTracker] = useState<TrackerStatus | null>(null)
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null)
  const [backups, setBackups] = useState<BackupInfo[]>([])
  const [error, setError] = useState<string | null>(null)
  const [trackerError, setTrackerError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [backingUp, setBackingUp] = useState(false)
  const [autostartEnabled, setAutostartEnabled] = useState<boolean | null>(null)
  const desktop = isDesktop()

  useEffect(() => {
    const controller = new AbortController()
    getSettings(controller.signal).then(async (loaded) => {
      const detected = Intl.DateTimeFormat().resolvedOptions().timeZone
      if (loaded.time_zone_auto && detected && loaded.time_zone !== detected) {
        const updated = await updateSettings({ time_zone: detected, time_zone_auto: true })
        if (!controller.signal.aborted) setSettings(updated)
      } else setSettings(loaded)
    }).catch((caught: unknown) => {
      if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load settings.')
    })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!desktop) return
    getAutostart().then(setAutostartEnabled).catch((caught: unknown) => {
      setError(caught instanceof Error ? caught.message : 'Unable to read Windows startup settings.')
    })
  }, [desktop])

  useEffect(() => {
    const controller = new AbortController()
    const refresh = () => getTrackerStatus(controller.signal).then((status) => {
      setTracker(status); setTrackerError(null)
    }).catch((caught: unknown) => {
      if (!(caught instanceof DOMException && caught.name === 'AbortError')) setTrackerError(caught instanceof Error ? caught.message : 'Unable to read tracker status.')
    })
    void refresh()
    const interval = window.setInterval(() => void refresh(), 5_000)
    return () => { controller.abort(); window.clearInterval(interval) }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([getDiagnostics(controller.signal), listBackups(controller.signal)])
      .then(([details, existingBackups]) => { setDiagnostics(details); setBackups(existingBackups) })
      .catch((caught: unknown) => {
        if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load local diagnostics.')
      })
    return () => controller.abort()
  }, [])

  async function save() {
    if (!settings) return
    setSaving(true); setError(null); setNotice(null)
    try {
      setSettings(await updateSettings({ tracking_enabled: settings.tracking_enabled, scan_interval_seconds: settings.scan_interval_seconds, restart_grace_seconds: settings.restart_grace_seconds, time_zone: settings.time_zone, time_zone_auto: settings.time_zone_auto }))
      setTracker(await getTrackerStatus())
      setNotice('Tracking settings saved.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to save settings.')
    } finally {
      setSaving(false)
    }
  }

  async function refreshTracker() {
    setTrackerError(null)
    try {
      setTracker(await getTrackerStatus())
    } catch (caught) {
      setTrackerError(caught instanceof Error ? caught.message : 'Unable to read tracker status.')
    }
  }

  async function backup() {
    setBackingUp(true); setError(null); setNotice(null)
    try {
      const created = await createBackup()
      setBackups((current) => [created, ...current])
      setNotice(`Verified backup created: ${created.filename}`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to create a backup.')
    } finally {
      setBackingUp(false)
    }
  }

  async function toggleAutostart() {
    if (autostartEnabled === null) return
    setError(null)
    const next = !autostartEnabled
    try {
      await setAutostart(next)
      setAutostartEnabled(next)
      setNotice(next ? 'GameDeck will start with Windows.' : 'GameDeck will no longer start with Windows.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to change Windows startup settings.')
    }
  }

  async function testNotification() {
    setError(null); setNotice(null)
    try {
      const result = await notify('GameDeck notifications are ready', 'Newly detected games will appear here for review.')
      if (result === 'denied') setError('Windows notification permission is denied. Enable GameDeck in Windows Settings → System → Notifications.')
      else setNotice('Test notification sent. Check Windows Notification Center if the banner was hidden by Focus Assist.')
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to send the test notification.') }
  }

  const reportedTrackerError = tracker?.last_error ?? trackerError
  return (
    <div className="space-y-7">
      <header><p className="text-sm font-medium text-primary">Local operations</p><h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">Settings and diagnostics</h1><p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">Configure tracking, inspect local health, and create verified SQLite backups.</p></header>
      {error ? <p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">{error}</p> : null}
      {notice ? <p role="status" className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm text-primary">{notice}</p> : null}
      <div className="grid items-start gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Process tracking</CardTitle><CardDescription>Changes take effect without restarting GameDeck.</CardDescription></CardHeader>
          <CardContent className="space-y-5">
            <div className="flex flex-col gap-4 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between"><div><Label htmlFor="tracking-toggle">Automatic tracking</Label><p className="mt-1 text-xs text-muted-foreground">Pausing preserves open sessions for later reconciliation.</p></div><Button id="tracking-toggle" type="button" variant={settings?.tracking_enabled ? 'secondary' : 'outline'} aria-pressed={settings?.tracking_enabled ?? false} disabled={!settings} onClick={() => setSettings((current) => current ? { ...current, tracking_enabled: !current.tracking_enabled } : current)}><Power aria-hidden="true" /> {settings?.tracking_enabled ? 'Enabled' : 'Paused'}</Button></div>
            <div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><Label htmlFor="scan-interval">Scan interval (seconds)</Label><Input id="scan-interval" type="number" min={2} max={60} value={settings?.scan_interval_seconds ?? 5} disabled={!settings} onChange={(event) => setSettings((current) => current ? { ...current, scan_interval_seconds: Number(event.target.value) } : current)} /><p className="text-xs text-muted-foreground">Allowed range: 2–60 seconds.</p></div><div className="space-y-2"><Label htmlFor="restart-grace">Restart grace (seconds)</Label><Input id="restart-grace" type="number" min={0} max={120} value={settings?.restart_grace_seconds ?? 15} disabled={!settings} onChange={(event) => setSettings((current) => current ? { ...current, restart_grace_seconds: Number(event.target.value) } : current)} /><p className="text-xs text-muted-foreground">Keeps one session across brief restarts.</p></div></div>
            <Button disabled={!settings || saving} onClick={() => void save()}><Save aria-hidden="true" /> {saving ? 'Saving…' : 'Save tracking settings'}</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><div className="flex items-center justify-between gap-4"><CardTitle>Tracker health</CardTitle><Badge variant={reportedTrackerError ? 'destructive' : 'secondary'}>{reportedTrackerError ? 'Needs attention' : tracker?.running ? 'Running' : 'Stopped'}</Badge></div><CardDescription>Scan failures never close sessions by themselves.</CardDescription></CardHeader>
          <CardContent className="space-y-4 text-sm"><StatusRow icon={reportedTrackerError ? TriangleAlert : CheckCircle2} label="Latest successful scan" value={tracker?.last_successful_scan_at ? new Date(tracker.last_successful_scan_at).toLocaleString() : 'Waiting for first scan'} /><StatusRow icon={Activity} label="Games detected" value={String(tracker?.active_game_ids.length ?? 0)} />{reportedTrackerError ? <div role="alert" className="space-y-2 rounded-md bg-destructive/10 p-3 text-destructive"><p className="font-medium">{reportedTrackerError}</p><p className="text-xs leading-relaxed">GameDeck is preserving active sessions. Check the log path below, then refresh; restart the single backend worker if successful scans do not resume.</p></div> : null}{tracker && !tracker.enabled ? <p className="rounded-md bg-muted p-3 text-muted-foreground">Tracking is paused. Existing open sessions are preserved until tracking resumes.</p> : null}<Button variant="outline" size="sm" onClick={() => void refreshTracker()}><RefreshCw aria-hidden="true" /> Refresh status</Button></CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Globe2 className="size-5 text-primary" aria-hidden="true" /> Time zone</CardTitle><CardDescription>Analytics follows your detected local calendar, or a time zone you choose manually.</CardDescription></CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-[auto_minmax(240px,1fr)_auto] sm:items-end">
          <Button type="button" variant={settings?.time_zone_auto ? 'secondary' : 'outline'} aria-pressed={settings?.time_zone_auto ?? false} disabled={!settings} onClick={() => setSettings((current) => current ? { ...current, time_zone_auto: !current.time_zone_auto, time_zone: !current.time_zone_auto ? Intl.DateTimeFormat().resolvedOptions().timeZone : current.time_zone } : current)}><Globe2 aria-hidden="true" /> Automatic: {settings?.time_zone_auto ? 'On' : 'Off'}</Button>
          <div className="space-y-2"><Label htmlFor="time-zone">IANA time zone</Label><Input id="time-zone" list="time-zone-options" value={settings?.time_zone ?? ''} disabled={!settings || settings.time_zone_auto} onChange={(event) => setSettings((current) => current ? { ...current, time_zone: event.target.value, time_zone_auto: false } : current)} /><datalist id="time-zone-options"><option value="Asia/Shanghai" /><option value="Asia/Manila" /><option value="America/New_York" /><option value="America/Chicago" /><option value="America/Denver" /><option value="America/Los_Angeles" /><option value="Europe/London" /><option value="Europe/Paris" /><option value="Australia/Sydney" /><option value="UTC" /></datalist></div>
          <Button disabled={!settings || saving} onClick={() => void save()}><Save aria-hidden="true" /> Save time zone</Button>
        </CardContent>
      </Card>
      {desktop ? (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><MonitorUp className="size-5 text-primary" aria-hidden="true" /> Desktop behavior</CardTitle><CardDescription>Keep detection available in the system tray and control Windows integration.</CardDescription></CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row">
            <Button variant="outline" disabled={autostartEnabled === null} aria-pressed={autostartEnabled ?? false} onClick={() => void toggleAutostart()}><Power aria-hidden="true" /> Start with Windows: {autostartEnabled ? 'On' : 'Off'}</Button>
            <Button variant="outline" onClick={() => void testNotification()}><Bell aria-hidden="true" /> Test notification</Button>
          </CardContent>
        </Card>
      ) : null}
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.25fr)_minmax(280px,0.75fr)]">
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Database className="size-5 text-primary" aria-hidden="true" /> Local diagnostics</CardTitle><CardDescription>Paths and probes are shown only in this local application.</CardDescription></CardHeader><CardContent>{diagnostics ? <dl className="grid gap-4 text-sm sm:grid-cols-2"><Diagnostic label="Database" value={diagnostics.database_path} detail={`${formatBytes(diagnostics.database_size_bytes)} · WAL ${formatBytes(diagnostics.wal_size_bytes)}`} /><Diagnostic label="Log" value={diagnostics.log_path} detail={formatBytes(diagnostics.log_size_bytes)} /><Diagnostic label="Backup folder" value={diagnostics.backup_directory} /><Diagnostic label="Database health" value={`${diagnostics.database_integrity} · ${diagnostics.database_journal_mode.toUpperCase()}`} detail={`${diagnostics.database_probe_ms.toFixed(2)} ms probe · ${diagnostics.sqlite_busy_timeout_ms} ms busy timeout`} /><Diagnostic label="Local records" value={`${diagnostics.game_count} games · ${diagnostics.session_count} sessions · ${diagnostics.purchase_count} purchases`} /></dl> : <p className="py-10 text-center text-sm text-muted-foreground">Loading diagnostics…</p>}</CardContent></Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><FolderArchive className="size-5 text-primary" aria-hidden="true" /> Verified backups</CardTitle><CardDescription>Uses SQLite’s online backup and integrity-check APIs.</CardDescription></CardHeader><CardContent className="space-y-4"><Button className="w-full" disabled={backingUp} onClick={() => void backup()}><FolderArchive aria-hidden="true" /> {backingUp ? 'Creating backup…' : 'Create backup now'}</Button>{backups.length ? <ul className="space-y-3">{backups.slice(0, 3).map((item) => <li key={item.filename} className="rounded-md border p-3"><p className="truncate font-mono text-xs" title={item.filename}>{item.filename}</p><p className="mt-1 text-xs text-muted-foreground">{formatBytes(item.size_bytes)} · {new Date(item.created_at).toLocaleString()}</p></li>)}</ul> : <p className="py-4 text-center text-xs text-muted-foreground">No backups created yet.</p>}</CardContent></Card>
      </div>
    </div>
  )
}

function StatusRow({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: string }) {
  return <div className="flex items-center gap-3 rounded-lg border p-3"><Icon className="size-4 text-primary" aria-hidden="true" /><span className="text-muted-foreground">{label}</span><span className="ml-auto text-right font-medium">{value}</span></div>
}

function Diagnostic({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <div><dt className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</dt><dd className="mt-1 break-all font-mono text-xs">{value}</dd>{detail ? <dd className="mt-1 text-xs text-muted-foreground">{detail}</dd> : null}</div>
}

function formatBytes(bytes: number): string {
  if (bytes < 1_024) return `${bytes} B`
  if (bytes < 1_048_576) return `${(bytes / 1_024).toFixed(1)} KB`
  return `${(bytes / 1_048_576).toFixed(1)} MB`
}
