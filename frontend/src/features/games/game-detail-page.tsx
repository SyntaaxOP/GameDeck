import { useEffect, useState } from 'react'
import { ArrowLeft, CalendarDays, CircleDollarSign, Clock3, Edit3, Gamepad2, ListOrdered, Play, Plus, ScanSearch, Star } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { getGameAnalytics } from '@/api/analytics'
import { getGame, launchGame } from '@/api/games'
import { getGameSpending } from '@/api/purchases'
import { deleteSession, listSessions } from '@/api/sessions'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { GameFormDialog } from '@/features/games/game-form-dialog'
import { TrendChart } from '@/features/analytics/analytics-visuals'
import { SessionFormDialog } from '@/features/sessions/session-form-dialog'
import { SessionTable } from '@/features/sessions/session-table'
import { formatDuration } from '@/lib/date-time'
import { formatMoney } from '@/lib/money'
import { platformLabels, statusLabels, type Game } from '@/types/game'
import type { GameSession, SessionList } from '@/types/session'
import type { GameAnalytics } from '@/types/analytics'
import type { GameSpending } from '@/types/purchase'

export function GameDetailPage() {
  const { gameId: gameIdParam } = useParams()
  const gameId = Number(gameIdParam)
  const [game, setGame] = useState<Game | null>(null)
  const [sessions, setSessions] = useState<SessionList | null>(null)
  const [analytics, setAnalytics] = useState<GameAnalytics | null>(null)
  const [spending, setSpending] = useState<GameSpending | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [gameDialogOpen, setGameDialogOpen] = useState(false)
  const [sessionDialogOpen, setSessionDialogOpen] = useState(false)
  const [selectedSession, setSelectedSession] = useState<GameSession | null>(null)
  const [busySessionId, setBusySessionId] = useState<number | null>(null)
  const [launching, setLaunching] = useState(false)

  useEffect(() => {
    if (!Number.isInteger(gameId) || gameId <= 0) {
      setError('This game link is invalid.')
      setLoading(false)
      return
    }
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    const at = new Date()
    const from = new Date(at)
    from.setDate(from.getDate() - 30)
    Promise.all([
      getGame(gameId, controller.signal),
      listSessions({ gameId, page: 1, pageSize: 100 }, controller.signal),
      getGameAnalytics(gameId, from.toISOString(), at.toISOString(), at.toISOString(), controller.signal),
      getGameSpending(gameId, controller.signal),
    ])
      .then(([gameResponse, sessionResponse, analyticsResponse, spendingResponse]) => {
        setGame(gameResponse)
        setSessions(sessionResponse)
        setAnalytics(analyticsResponse)
        setSpending(spendingResponse)
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === 'AbortError') return
        setError(caught instanceof Error ? caught.message : 'Unable to load this game.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [gameId, refreshKey])

  function refresh() {
    setRefreshKey((current) => current + 1)
  }

  function openCreateSession() {
    setSelectedSession(null)
    setSessionDialogOpen(true)
  }

  function openEditSession(session: GameSession) {
    setSelectedSession(session)
    setSessionDialogOpen(true)
  }

  async function handleDelete(session: GameSession) {
    setBusySessionId(session.id)
    setError(null)
    try {
      await deleteSession(session.id)
      refresh()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to delete this session.')
    } finally {
      setBusySessionId(null)
    }
  }

  async function launch() {
    setLaunching(true)
    setError(null)
    try {
      await launchGame(gameId)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to launch this game.')
    } finally {
      setLaunching(false)
    }
  }

  if (loading) return <div className="space-y-5"><Skeleton className="h-10 w-72" /><Skeleton className="h-40" /><Skeleton className="h-72" /></div>
  if (error && !game) return <div className="space-y-4"><Button variant="ghost" asChild><Link to="/library"><ArrowLeft aria-hidden="true" /> Library</Link></Button><p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</p></div>
  if (!game) return null

  const summary = analytics?.summary

  return (
    <div className="space-y-7">
      <Button variant="ghost" size="sm" asChild><Link to="/library"><ArrowLeft aria-hidden="true" /> Back to library</Link></Button>

      <header className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{statusLabels[game.status]}</Badge>
            <Badge variant="outline">{platformLabels[game.platform]}</Badge>
            {game.favorite ? <Badge><Star className="fill-current" aria-hidden="true" /> Favorite</Badge> : null}
          </div>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">{game.title}</h1>
          <p className="mt-2 font-mono text-xs text-muted-foreground">{game.executable_path ?? game.executable_name}</p>
        </div>
        <div className="flex gap-2">
          <Button disabled={launching} onClick={() => void launch()}><Play aria-hidden="true" /> {launching ? 'Launching…' : 'Play'}</Button>
          <Button variant="outline" onClick={() => setGameDialogOpen(true)}><Edit3 aria-hidden="true" /> Edit game</Button>
          <Button onClick={openCreateSession}><Plus aria-hidden="true" /> Add session</Button>
        </div>
      </header>

      {error ? <p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</p> : null}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm text-muted-foreground"><Clock3 className="size-4" aria-hidden="true" /> Past 30 days</CardTitle></CardHeader><CardContent><p className="font-mono text-2xl font-semibold">{formatDuration(summary?.total_seconds ?? 0)}</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm text-muted-foreground"><Gamepad2 className="size-4" aria-hidden="true" /> Sessions</CardTitle></CardHeader><CardContent><p className="font-mono text-2xl font-semibold">{summary?.session_count ?? 0}</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm text-muted-foreground"><Clock3 className="size-4" aria-hidden="true" /> Average session</CardTitle></CardHeader><CardContent><p className="font-mono text-2xl font-semibold">{formatDuration(summary?.average_session_seconds ?? 0)}</p></CardContent></Card>
      </div>

      {analytics?.summary.total_seconds ? <Card><CardHeader><CardTitle>Past 30 days</CardTitle></CardHeader><CardContent><TrendChart points={analytics.daily_series} label={`${game.title} daily playtime for the past 30 days`} /></CardContent></Card> : null}

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><ScanSearch className="size-5 text-primary" aria-hidden="true" /> Process detection</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <ExecutableMapping label="Primary" name={game.executable_name} path={game.executable_path} />
          {game.executable_aliases.map((alias, index) => (
            <ExecutableMapping key={alias.id} label={`Alias ${index + 1}`} name={alias.executable_name} path={alias.executable_path} />
          ))}
          {!game.executable_aliases.length ? <p className="text-xs text-muted-foreground">No additional executables are configured.</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2"><CircleDollarSign className="size-5 text-primary" aria-hidden="true" /> Spending</CardTitle>
          <Button variant="outline" size="sm" asChild><Link to="/spending">Open ledger</Link></Button>
        </CardHeader>
        <CardContent>
          {spending?.currencies.length ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {spending.currencies.map((currency) => (
                <div key={currency.currency_code}>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{currency.currency_code} purchases</p>
                  <p className="mt-2 font-mono text-xl font-semibold">{formatMoney(currency.amount_minor, currency.currency_code)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{currency.cost_per_hour_minor === null ? 'Not played yet' : `${formatMoney(currency.cost_per_hour_minor, currency.currency_code)} per hour`}</p>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted-foreground">No purchases are associated with this game.</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Game profile</CardTitle></CardHeader>
        <CardContent className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-5">
          <ProfileItem icon={Gamepad2} label="Genre" value={game.genre ?? 'Not set'} />
          <ProfileItem icon={ListOrdered} label="Queue priority" value={game.priority ? `Priority ${game.priority}` : 'No priority'} />
          <ProfileItem icon={Star} label="Personal rating" value={game.personal_rating ? `${game.personal_rating}/10` : 'Not rated'} />
          <ProfileItem icon={CalendarDays} label="Added" value={new Date(game.date_added).toLocaleDateString()} />
          <ProfileItem icon={CalendarDays} label="Completed" value={game.date_completed ? new Date(`${game.date_completed}T00:00:00`).toLocaleDateString() : 'Not completed'} />
        </CardContent>
      </Card>

      {game.notes ? <Card><CardHeader><CardTitle>Notes</CardTitle></CardHeader><CardContent><p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">{game.notes}</p></CardContent></Card> : null}

      <section className="space-y-4">
        <div><h2 className="text-xl font-semibold tracking-tight">Session history</h2><p className="mt-1 text-sm text-muted-foreground">The records used to calculate this game’s playtime.</p></div>
        {sessions?.items.length ? (
          <SessionTable sessions={sessions.items} showGame={false} busySessionId={busySessionId} onEdit={openEditSession} onDelete={(session) => void handleDelete(session)} />
        ) : (
          <Card className="border-dashed"><CardContent className="flex min-h-44 flex-col items-center justify-center text-center"><p className="text-sm text-muted-foreground">No play sessions recorded yet.</p><Button className="mt-4" variant="outline" onClick={openCreateSession}><Plus aria-hidden="true" /> Add first session</Button></CardContent></Card>
        )}
      </section>

      <GameFormDialog game={game} open={gameDialogOpen} onOpenChange={setGameDialogOpen} onSaved={refresh} />
      <SessionFormDialog games={[game]} fixedGameId={game.id} open={sessionDialogOpen} session={selectedSession} onOpenChange={setSessionDialogOpen} onSaved={refresh} />
    </div>
  )
}

function ProfileItem({ icon: Icon, label, value }: { icon: typeof Gamepad2; label: string; value: string }) {
  return <div><p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground"><Icon className="size-3.5 text-primary" aria-hidden="true" /> {label}</p><p className="mt-2 font-medium">{value}</p></div>
}

function ExecutableMapping({ label, name, path }: { label: string; name: string; path: string | null }) {
  return (
    <div className="grid gap-1 border-b pb-3 last:border-b-0 last:pb-0 sm:grid-cols-[7rem_1fr] sm:items-baseline">
      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="break-all font-mono text-xs">{path ?? name}</p>
    </div>
  )
}
