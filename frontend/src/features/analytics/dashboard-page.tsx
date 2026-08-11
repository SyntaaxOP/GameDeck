import { useEffect, useState } from 'react'
import { Activity, CalendarDays, Clock3, Gamepad2, Trophy } from 'lucide-react'
import { Link } from 'react-router-dom'

import { getDashboard } from '@/api/analytics'
import { getTrackerStatus } from '@/api/settings'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { TrendChart } from '@/features/analytics/analytics-visuals'
import { formatDuration } from '@/lib/date-time'
import type { DashboardAnalytics } from '@/types/analytics'
import type { TrackerStatus } from '@/types/settings'

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardAnalytics | null>(null)
  const [tracker, setTracker] = useState<TrackerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [trackerError, setTrackerError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    getDashboard(new Date().toISOString(), controller.signal)
      .then(setDashboard)
      .catch((caught: unknown) => {
        if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load dashboard analytics.')
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [refreshKey])

  useEffect(() => {
    const controller = new AbortController()
    getTrackerStatus(controller.signal).then(setTracker).catch((caught: unknown) => {
      if (!(caught instanceof DOMException && caught.name === 'AbortError')) setTrackerError(caught instanceof Error ? caught.message : 'Tracker status is unavailable.')
    })
    return () => controller.abort()
  }, [refreshKey])

  if (loading) return <div className="space-y-5"><Skeleton className="h-12 w-80" /><div className="grid gap-4 md:grid-cols-3"><Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" /></div><Skeleton className="h-80" /></div>
  if (error) return <div className="space-y-4"><p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">{error}</p><Button variant="outline" onClick={() => setRefreshKey((value) => value + 1)}>Try again</Button></div>
  if (!dashboard) return null

  const hasHistory = dashboard.lifetime.total_seconds > 0
  return (
    <div className="space-y-7">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="text-sm font-medium text-primary">Your gaming overview</p><h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">Dashboard</h1><p className="mt-2 text-sm text-muted-foreground">Playtime calculated in {dashboard.time_zone}.</p></div>
        <Button variant="outline" asChild><Link to="/analytics">Explore analytics</Link></Button>
      </header>

      <Card className={dashboard.current_sessions.length ? 'border-primary/40 bg-primary/5' : undefined}>
        <CardContent className="flex flex-col gap-4 py-5 sm:flex-row sm:items-center">
          <div className="flex size-11 items-center justify-center rounded-full bg-primary/15 text-primary"><Activity className="size-5" aria-hidden="true" /></div>
          <div className="min-w-0 flex-1">
            <p className="font-medium">{dashboard.current_sessions.length ? `${dashboard.current_sessions.length} game${dashboard.current_sessions.length === 1 ? '' : 's'} running` : 'No game running'}</p>
            <p className="mt-1 truncate text-sm text-muted-foreground">{dashboard.current_sessions.map((session) => session.game_title).join(', ') || 'GameDeck will show registered games here when detected.'}</p>
          </div>
          <Badge variant={tracker?.last_error || trackerError ? 'destructive' : 'secondary'}>{tracker?.last_error || trackerError ? 'Tracker issue' : tracker ? (tracker.enabled ? 'Tracker healthy' : 'Tracking paused') : 'Checking tracker'}</Badge>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={Clock3} label="Today" value={formatDuration(dashboard.today_seconds)} />
        <MetricCard icon={CalendarDays} label="This week" value={formatDuration(dashboard.week_seconds)} />
        <MetricCard icon={CalendarDays} label="This month" value={formatDuration(dashboard.month_seconds)} />
        <MetricCard icon={Trophy} label="Top game this month" value={dashboard.top_game?.game_title ?? 'No playtime'} detail={dashboard.top_game ? formatDuration(dashboard.top_game.total_seconds) : undefined} />
      </div>

      {!hasHistory ? (
        <Card className="border-dashed"><CardContent className="flex min-h-72 flex-col items-center justify-center text-center"><div className="rounded-full bg-muted p-4"><Gamepad2 className="size-6 text-muted-foreground" aria-hidden="true" /></div><h2 className="mt-4 text-lg font-medium">Your dashboard is ready</h2><p className="mt-2 max-w-md text-sm text-muted-foreground">Play a registered game or add a manual session to begin building trustworthy trends.</p><Button className="mt-5" asChild><Link to="/library">Open library</Link></Button></CardContent></Card>
      ) : (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.6fr)_minmax(280px,0.8fr)]">
          <Card><CardHeader><CardTitle>Last seven days</CardTitle></CardHeader><CardContent><TrendChart points={dashboard.daily_series} label="Daily playtime for the last seven days" /></CardContent></Card>
          <Card><CardHeader><CardTitle>Recently played</CardTitle></CardHeader><CardContent>{dashboard.recent_sessions.length ? <ul className="divide-y">{dashboard.recent_sessions.map((session) => <li key={session.id} className="flex items-center gap-3 py-3"><div className="min-w-0 flex-1"><Link to={`/games/${session.game_id}`} className="truncate font-medium hover:text-primary">{session.game_title}</Link><p className="mt-1 text-xs text-muted-foreground">{new Date(session.started_at).toLocaleString()}</p></div><span className="font-mono text-xs">{formatDuration(session.duration_seconds ?? 0)}</span></li>)}</ul> : <p className="py-8 text-center text-sm text-muted-foreground">No completed sessions yet.</p>}</CardContent></Card>
        </div>
      )}
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, detail }: { icon: typeof Clock3; label: string; value: string; detail?: string }) {
  return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm text-muted-foreground"><Icon className="size-4 text-primary" aria-hidden="true" /> {label}</CardTitle></CardHeader><CardContent><p className="truncate font-mono text-2xl font-semibold">{value}</p>{detail ? <p className="mt-1 text-xs text-muted-foreground">{detail}</p> : null}</CardContent></Card>
}
