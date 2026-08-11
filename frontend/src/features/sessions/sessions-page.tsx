import { useEffect, useState } from 'react'
import { CalendarDays, Plus } from 'lucide-react'

import { listGames } from '@/api/games'
import { deleteSession, listSessions } from '@/api/sessions'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { SessionFormDialog } from '@/features/sessions/session-form-dialog'
import { SessionTable } from '@/features/sessions/session-table'
import { inclusiveDateRange } from '@/lib/date-time'
import type { Game } from '@/types/game'
import type { GameSession, SessionList } from '@/types/session'

const pageSize = 25

export function SessionsPage() {
  const [games, setGames] = useState<Game[]>([])
  const [result, setResult] = useState<SessionList | null>(null)
  const [gameFilter, setGameFilter] = useState('all')
  const [activityFilter, setActivityFilter] = useState<'all' | 'active' | 'completed'>('all')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedSession, setSelectedSession] = useState<GameSession | null>(null)
  const [busySessionId, setBusySessionId] = useState<number | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listGames(
      { query: '', platform: 'all', status: 'all', favorite: null, archived: false, page: 1, pageSize: 100 },
      controller.signal,
    )
      .then((response) => setGames(response.items))
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === 'AbortError') return
        setError(caught instanceof Error ? caught.message : 'Unable to load games.')
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const range = inclusiveDateRange(fromDate, toDate)
    setLoading(true)
    setError(null)
    listSessions(
      {
        gameId: gameFilter === 'all' ? undefined : Number(gameFilter),
        active: activityFilter === 'all' ? undefined : activityFilter === 'active',
        from: range.from,
        to: range.to,
        page,
        pageSize,
      },
      controller.signal,
    )
      .then(setResult)
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === 'AbortError') return
        setError(caught instanceof Error ? caught.message : 'Unable to load sessions.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [activityFilter, fromDate, gameFilter, page, refreshKey, toDate])

  function resetPageAnd(action: () => void) {
    setPage(1)
    action()
  }

  function refresh() {
    setRefreshKey((current) => current + 1)
  }

  function openCreate() {
    setSelectedSession(null)
    setDialogOpen(true)
  }

  function openEdit(session: GameSession) {
    setSelectedSession(session)
    setDialogOpen(true)
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

  const totalPages = result ? Math.max(1, Math.ceil(result.total / pageSize)) : 1

  return (
    <div className="space-y-7">
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Audit your playtime</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">Sessions</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Review the source records behind GameDeck analytics and correct anything it missed.
          </p>
        </div>
        <Button onClick={openCreate} disabled={games.length === 0}><Plus aria-hidden="true" /> Add manual session</Button>
      </header>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-[220px_180px_1fr_1fr]">
          <Select value={gameFilter} onValueChange={(value) => resetPageAnd(() => setGameFilter(value))}>
            <SelectTrigger className="w-full" aria-label="Filter sessions by game"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All games</SelectItem>
              {games.map((game) => <SelectItem key={game.id} value={String(game.id)}>{game.title}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={activityFilter} onValueChange={(value) => resetPageAnd(() => setActivityFilter(value as typeof activityFilter))}>
            <SelectTrigger className="w-full" aria-label="Filter sessions by activity"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sessions</SelectItem>
              <SelectItem value="active">Active only</SelectItem>
              <SelectItem value="completed">Completed only</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <CalendarDays className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            <Input type="date" value={fromDate} onChange={(event) => resetPageAnd(() => setFromDate(event.target.value))} aria-label="Sessions from date" />
          </div>
          <Input type="date" value={toDate} min={fromDate || undefined} onChange={(event) => resetPageAnd(() => setToDate(event.target.value))} aria-label="Sessions through date" />
        </CardContent>
      </Card>

      {error ? <p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</p> : null}

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{loading ? 'Loading sessions…' : `${result?.total ?? 0} sessions`}</p>
        {result && result.total > pageSize ? <p className="text-xs text-muted-foreground">Page {page} of {totalPages}</p> : null}
      </div>

      {loading ? (
        <Skeleton className="h-80 rounded-xl" />
      ) : result?.items.length ? (
        <SessionTable sessions={result.items} busySessionId={busySessionId} onEdit={openEdit} onDelete={(session) => void handleDelete(session)} />
      ) : (
        <Card className="border-dashed">
          <CardContent className="flex min-h-64 flex-col items-center justify-center text-center">
            <CalendarDays className="size-8 text-muted-foreground" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-medium">No sessions found</h2>
            <p className="mt-2 max-w-sm text-sm text-muted-foreground">Add a manual session now, or adjust the filters to review older playtime.</p>
            {games.length ? <Button className="mt-5" onClick={openCreate}><Plus aria-hidden="true" /> Add session</Button> : null}
          </CardContent>
        </Card>
      )}

      {result && result.total > pageSize ? (
        <div className="flex justify-end gap-2">
          <Button variant="outline" disabled={page === 1} onClick={() => setPage((current) => current - 1)}>Previous</Button>
          <Button variant="outline" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</Button>
        </div>
      ) : null}

      <SessionFormDialog games={games} open={dialogOpen} session={selectedSession} onOpenChange={setDialogOpen} onSaved={refresh} />
    </div>
  )
}

