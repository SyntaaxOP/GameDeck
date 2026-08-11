import { useEffect, useMemo, useState } from 'react'
import { CalendarRange, Clock3, Timer, Trophy } from 'lucide-react'

import { getDistribution, getPlaytime } from '@/api/analytics'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { DistributionBars, GameRanking, TrendChart } from '@/features/analytics/analytics-visuals'
import { formatDuration } from '@/lib/date-time'
import type { DistributionAnalytics, PlaytimeAnalytics, TimeBucket } from '@/types/analytics'

const presets = [{ label: '7 days', days: 7 }, { label: '30 days', days: 30 }, { label: '90 days', days: 90 }]

export function AnalyticsPage() {
  const [days, setDays] = useState(30)
  const [bucket, setBucket] = useState<TimeBucket>('day')
  const [playtime, setPlaytime] = useState<PlaytimeAnalytics | null>(null)
  const [weekday, setWeekday] = useState<DistributionAnalytics | null>(null)
  const [hour, setHour] = useState<DistributionAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const range = useMemo(() => {
    const to = new Date()
    const from = new Date(to)
    from.setDate(from.getDate() - days)
    return { from: from.toISOString(), to: to.toISOString(), at: to.toISOString() }
  }, [days])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    Promise.all([
      getPlaytime(range.from, range.to, bucket, range.at, controller.signal),
      getDistribution(range.from, range.to, 'weekday', range.at, controller.signal),
      getDistribution(range.from, range.to, 'hour', range.at, controller.signal),
    ]).then(([playtimeResult, weekdayResult, hourResult]) => {
      setPlaytime(playtimeResult); setWeekday(weekdayResult); setHour(hourResult)
    }).catch((caught: unknown) => {
      if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load analytics.')
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [bucket, range, refreshKey])

  return (
    <div className="space-y-7">
      <header><p className="text-sm font-medium text-primary">Explore your habits</p><h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">Analytics</h1><p className="mt-2 text-sm text-muted-foreground">Range-clipped playtime grouped by your local calendar.</p></header>
      <Card><CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center"><CalendarRange className="size-5 text-primary" aria-hidden="true" /><div className="flex flex-1 flex-wrap gap-2">{presets.map((preset) => <Button key={preset.days} size="sm" variant={days === preset.days ? 'secondary' : 'outline'} aria-pressed={days === preset.days} onClick={() => setDays(preset.days)}>{preset.label}</Button>)}</div><Select value={bucket} onValueChange={(value) => setBucket(value as TimeBucket)}><SelectTrigger className="w-full sm:w-40" aria-label="Trend grouping"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="day">Daily</SelectItem><SelectItem value="week">Weekly</SelectItem><SelectItem value="month">Monthly</SelectItem></SelectContent></Select></CardContent></Card>
      {error ? <div className="flex items-center justify-between gap-4 rounded-lg border border-destructive/40 bg-destructive/5 p-4"><p role="alert" className="text-sm text-destructive">{error}</p><Button variant="outline" size="sm" onClick={() => setRefreshKey((value) => value + 1)}>Try again</Button></div> : null}
      {loading ? <><div className="grid gap-4 sm:grid-cols-3"><Skeleton className="h-28" /><Skeleton className="h-28" /><Skeleton className="h-28" /></div><Skeleton className="h-80" /></> : playtime ? <>
        <div className="grid gap-4 sm:grid-cols-3"><SummaryCard icon={Clock3} label="Total playtime" value={formatDuration(playtime.summary.total_seconds)} /><SummaryCard icon={Timer} label="Average session" value={formatDuration(playtime.summary.average_session_seconds)} /><SummaryCard icon={Trophy} label="Longest session" value={formatDuration(playtime.summary.longest_session_seconds)} /></div>
        <Card><CardHeader><CardTitle>Playtime trend</CardTitle></CardHeader><CardContent>{playtime.summary.total_seconds ? <TrendChart points={playtime.series} label={`Playtime over the last ${days} days`} /> : <p className="py-20 text-center text-sm text-muted-foreground">No playtime recorded in this range.</p>}</CardContent></Card>
        <div className="grid gap-5 xl:grid-cols-2"><Card><CardHeader><CardTitle>Top games</CardTitle></CardHeader><CardContent><GameRanking games={playtime.games} /></CardContent></Card><Card><CardHeader><CardTitle>Weekday activity</CardTitle></CardHeader><CardContent><DistributionBars points={weekday?.buckets ?? []} /></CardContent></Card></div>
        <Card><CardHeader><CardTitle>Time of day</CardTitle></CardHeader><CardContent><DistributionBars points={hour?.buckets ?? []} /></CardContent></Card>
      </> : null}
    </div>
  )
}

function SummaryCard({ icon: Icon, label, value }: { icon: typeof Clock3; label: string; value: string }) {
  return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm text-muted-foreground"><Icon className="size-4 text-primary" aria-hidden="true" /> {label}</CardTitle></CardHeader><CardContent><p className="font-mono text-2xl font-semibold">{value}</p></CardContent></Card>
}
