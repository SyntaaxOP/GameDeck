import { useDeferredValue, useEffect, useRef, useState } from 'react'
import { LibraryBig, Plus, Search, Star } from 'lucide-react'

import { deleteGamePermanently, listGames } from '@/api/games'
import { getTrackerStatus } from '@/api/settings'
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
import { GameCard } from '@/features/games/game-card'
import { GameFormDialog } from '@/features/games/game-form-dialog'
import {
  libraryStatuses,
  platformLabels,
  platforms,
  statusLabels,
  type Game,
  type GameList,
  type LibraryStatus,
  type Platform,
} from '@/types/game'

const pageSize = 12

export function GameLibrary() {
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query)
  const [platform, setPlatform] = useState<Platform | 'all'>('all')
  const [status, setStatus] = useState<LibraryStatus | 'all'>('all')
  const [favoriteOnly, setFavoriteOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [result, setResult] = useState<GameList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedGame, setSelectedGame] = useState<Game | null>(null)
  const [busyGameId, setBusyGameId] = useState<number | null>(null)
  const [runningGameIds, setRunningGameIds] = useState<Set<number>>(new Set())
  const listedGameIds = useRef<Set<number>>(new Set())
  const refreshedForDetectedIds = useRef<Set<number>>(new Set())

  useEffect(() => {
    const controller = new AbortController()
    const refresh = () => getTrackerStatus(controller.signal)
      .then((tracker) => {
        setRunningGameIds(new Set(tracker.active_game_ids))
        const newlyDetectedIds = tracker.active_game_ids.filter(
          (gameId) => !listedGameIds.current.has(gameId) && !refreshedForDetectedIds.current.has(gameId),
        )
        if (newlyDetectedIds.length) {
          newlyDetectedIds.forEach((gameId) => refreshedForDetectedIds.current.add(gameId))
          setRefreshKey((current) => current + 1)
        }
      })
      .catch(() => undefined)
    void refresh()
    const interval = window.setInterval(() => void refresh(), 5_000)
    return () => { controller.abort(); window.clearInterval(interval) }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    listGames(
      {
        query: deferredQuery,
        platform,
        status,
        favorite: favoriteOnly ? true : null,
        archived: false,
        page,
        pageSize,
      },
      controller.signal,
    )
      .then((games) => {
        listedGameIds.current = new Set(games.items.map((game) => game.id))
        setResult(games)
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === 'AbortError') return
        setError(caught instanceof Error ? caught.message : 'Unable to load your library.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [deferredQuery, favoriteOnly, page, platform, refreshKey, status])

  function refresh() {
    setRefreshKey((current) => current + 1)
  }

  function resetPageAnd(action: () => void) {
    setPage(1)
    action()
  }

  function openCreateDialog() {
    setSelectedGame(null)
    setDialogOpen(true)
  }

  function openEditDialog(game: Game) {
    setSelectedGame(game)
    setDialogOpen(true)
  }

  async function runGameMutation(game: Game, action: (gameId: number) => Promise<unknown>) {
    setBusyGameId(game.id)
    setError(null)
    try {
      await action(game.id)
      refresh()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to update this game.')
    } finally {
      setBusyGameId(null)
    }
  }

  const totalPages = result ? Math.max(1, Math.ceil(result.total / pageSize)) : 1

  return (
    <div className="space-y-7">
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Your collection</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">Game library</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Games are discovered automatically from Steam or sustained foreground gameplay. You can also add and edit entries manually.
          </p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus aria-hidden="true" /> Add game
        </Button>
      </header>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-[minmax(220px,1fr)_180px_190px_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              value={query}
              onChange={(event) => resetPageAnd(() => setQuery(event.target.value))}
              placeholder="Search games"
              aria-label="Search games"
              className="pl-9"
            />
          </div>
          <Select value={platform} onValueChange={(value) => resetPageAnd(() => setPlatform(value as Platform | 'all'))}>
            <SelectTrigger className="w-full" aria-label="Filter by platform"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All platforms</SelectItem>
              {platforms.map((item) => <SelectItem key={item} value={item}>{platformLabels[item]}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={(value) => resetPageAnd(() => setStatus(value as LibraryStatus | 'all'))}>
            <SelectTrigger className="w-full" aria-label="Filter by status"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {libraryStatuses.map((item) => <SelectItem key={item} value={item}>{statusLabels[item]}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button variant={favoriteOnly ? 'secondary' : 'outline'} onClick={() => resetPageAnd(() => setFavoriteOnly((current) => !current))} aria-pressed={favoriteOnly}>
            <Star className={favoriteOnly ? 'fill-current' : ''} aria-hidden="true" /> Favorites
          </Button>
        </CardContent>
      </Card>

      {error ? (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="flex items-center justify-between gap-4 py-4">
            <p role="alert" className="text-sm text-destructive">{error}</p>
            <Button variant="outline" size="sm" onClick={refresh}>Try again</Button>
          </CardContent>
        </Card>
      ) : null}

      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          {loading ? 'Loading library…' : `${result?.total ?? 0} games`}
        </p>
        {result && result.total > pageSize ? <p className="text-xs text-muted-foreground">Page {page} of {totalPages}</p> : null}
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => <Skeleton key={index} className="h-64 rounded-xl" />)}
        </div>
      ) : result?.items.length ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {result.items.map((game) => (
            <GameCard
              key={game.id}
              game={game}
              busy={busyGameId === game.id}
              running={runningGameIds.has(game.id)}
              onEdit={openEditDialog}
              onDelete={(item) => void runGameMutation(item, deleteGamePermanently)}
            />
          ))}
        </div>
      ) : (
        <Card className="border-dashed">
          <CardContent className="flex min-h-72 flex-col items-center justify-center text-center">
            <div className="rounded-full bg-muted p-4"><LibraryBig className="size-6 text-muted-foreground" aria-hidden="true" /></div>
            <h2 className="mt-4 text-lg font-medium">Your library is ready</h2>
            <p className="mt-2 max-w-sm text-sm text-muted-foreground">
              Add your first game and configure the executable GameDeck should recognize.
            </p>
            <Button className="mt-5" onClick={openCreateDialog}><Plus aria-hidden="true" /> Add your first game</Button>
          </CardContent>
        </Card>
      )}

      {result && result.total > pageSize ? (
        <div className="flex justify-end gap-2">
          <Button variant="outline" disabled={page === 1} onClick={() => setPage((current) => current - 1)}>Previous</Button>
          <Button variant="outline" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</Button>
        </div>
      ) : null}

      <GameFormDialog
        game={selectedGame}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSaved={refresh}
      />
    </div>
  )
}
