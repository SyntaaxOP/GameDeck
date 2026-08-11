import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, ListTodo, Search, Sparkles, Star } from 'lucide-react'
import { Link } from 'react-router-dom'

import { listGames, updateGame } from '@/api/games'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { libraryStatuses, platformLabels, statusLabels, type Game, type GameList, type GameUpdateInput, type LibraryStatus } from '@/types/game'

const queueStatuses = new Set<LibraryStatus>(['currently_playing', 'backlog', 'paused'])
const groups: { status: LibraryStatus; description: string }[] = [
  { status: 'currently_playing', description: 'Games in your active rotation.' },
  { status: 'backlog', description: 'Games waiting for their turn.' },
  { status: 'paused', description: 'Set aside for now, but still in the queue.' },
  { status: 'completed', description: 'Finished games you can revisit.' },
  { status: 'completed_100', description: 'Every goal checked off.' },
  { status: 'dropped', description: 'Games you chose not to continue.' },
]

function playNextCompare(left: Game, right: Game): number {
  if (left.favorite !== right.favorite) return left.favorite ? -1 : 1
  if (left.priority === null && right.priority !== null) return 1
  if (left.priority !== null && right.priority === null) return -1
  if (left.priority !== right.priority) return (left.priority ?? 99) - (right.priority ?? 99)
  return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime() || left.title.localeCompare(right.title)
}

export function BacklogPage() {
  const [result, setResult] = useState<GameList | null>(null)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyGameId, setBusyGameId] = useState<number | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    listGames({ query: '', platform: 'all', status: 'all', favorite: null, archived: false, page: 1, pageSize: 100, sort: 'play_next' }, controller.signal)
      .then(setResult)
      .catch((caught: unknown) => {
        if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load your backlog.')
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [refreshKey])

  const visibleGames = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase()
    return (result?.items ?? []).filter((game) => !normalized || game.title.toLocaleLowerCase().includes(normalized))
  }, [query, result])
  const queue = visibleGames.filter((game) => queueStatuses.has(game.status)).sort(playNextCompare)
  const playNext = queue[0] ?? null

  async function changeGame(game: Game, update: GameUpdateInput) {
    setBusyGameId(game.id)
    setError(null)
    try {
      const updated = await updateGame(game.id, update)
      setResult((current) => current ? { ...current, items: current.items.map((item) => item.id === game.id ? updated : item).sort(playNextCompare) } : current)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to update this game.')
    } finally {
      setBusyGameId(null)
    }
  }

  if (loading) return <div className="space-y-5"><Skeleton className="h-12 w-72" /><Skeleton className="h-40" /><div className="grid gap-4 xl:grid-cols-3"><Skeleton className="h-72" /><Skeleton className="h-72" /><Skeleton className="h-72" /></div></div>

  return (
    <div className="space-y-7">
      <header><p className="text-sm font-medium text-primary">Choose what comes next</p><h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">Backlog</h1><p className="mt-2 max-w-2xl text-sm text-muted-foreground">Favorites lead the queue, followed by priority 1 through 5 and your most recently updated games.</p></header>
      {error ? <div className="flex items-center justify-between gap-4 rounded-lg border border-destructive/40 bg-destructive/5 p-4"><p role="alert" className="text-sm text-destructive">{error}</p><Button variant="outline" size="sm" onClick={() => setRefreshKey((value) => value + 1)}>Try again</Button></div> : null}
      {playNext ? <Card className="border-primary/40 bg-primary/5"><CardContent className="flex flex-col gap-5 py-6 sm:flex-row sm:items-center"><div className="flex size-12 items-center justify-center rounded-full bg-primary/15 text-primary"><Sparkles className="size-5" aria-hidden="true" /></div><div className="min-w-0 flex-1"><p className="text-xs font-medium uppercase tracking-wider text-primary">Play next</p><h2 className="mt-1 truncate text-xl font-semibold">{playNext.title}</h2><p className="mt-1 text-sm text-muted-foreground">{platformLabels[playNext.platform]}{playNext.priority ? ` · Priority ${playNext.priority}` : ''}{playNext.favorite ? ' · Favorite' : ''}</p></div><Button asChild><Link to={`/games/${playNext.id}`}>View game <ArrowRight aria-hidden="true" /></Link></Button></CardContent></Card> : null}
      <Card><CardContent className="py-4"><div className="relative max-w-md"><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search backlog" aria-label="Search backlog" className="pl-9" /></div></CardContent></Card>
      {!result?.items.length ? <Card className="border-dashed"><CardContent className="flex min-h-72 flex-col items-center justify-center text-center"><div className="rounded-full bg-muted p-4"><ListTodo className="size-6 text-muted-foreground" aria-hidden="true" /></div><h2 className="mt-4 text-lg font-medium">No games to organize yet</h2><p className="mt-2 max-w-sm text-sm text-muted-foreground">Add games to your Library, then return here to build a play-next queue.</p><Button className="mt-5" asChild><Link to="/library">Open library</Link></Button></CardContent></Card> : <div className="grid items-start gap-5 xl:grid-cols-3">{groups.map((group) => {
        const games = visibleGames.filter((game) => game.status === group.status).sort(playNextCompare)
        if (!games.length) return null
        return <Card key={group.status}><CardHeader><div className="flex items-center justify-between gap-3"><CardTitle>{statusLabels[group.status]}</CardTitle><Badge variant="secondary">{games.length}</Badge></div><p className="text-xs text-muted-foreground">{group.description}</p></CardHeader><CardContent className="space-y-3">{games.map((game) => <BacklogGame key={game.id} game={game} busy={busyGameId === game.id} onChange={(update) => void changeGame(game, update)} />)}</CardContent></Card>
      })}</div>}
      {result?.items.length && !visibleGames.length ? <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">No games match “{query}”.</p> : null}
    </div>
  )
}

function BacklogGame({ game, busy, onChange }: { game: Game; busy: boolean; onChange: (update: GameUpdateInput) => void }) {
  const inQueue = queueStatuses.has(game.status)
  return <div className="rounded-lg border bg-background/40 p-3"><div className="flex items-start gap-3"><div className="min-w-0 flex-1"><Link to={`/games/${game.id}`} className="font-medium hover:text-primary">{game.title}</Link><p className="mt-1 text-xs text-muted-foreground">{platformLabels[game.platform]}</p></div><Button variant="ghost" size="icon-sm" disabled={busy} aria-label={game.favorite ? `Remove ${game.title} from favorites` : `Add ${game.title} to favorites`} onClick={() => onChange({ favorite: !game.favorite })}><Star className={game.favorite ? 'fill-primary text-primary' : ''} aria-hidden="true" /></Button></div><div className="mt-3 grid grid-cols-2 gap-2"><Select value={game.status} disabled={busy} onValueChange={(value) => onChange({ status: value as LibraryStatus })}><SelectTrigger className="w-full" aria-label={`Status for ${game.title}`}><SelectValue /></SelectTrigger><SelectContent>{libraryStatuses.map((status) => <SelectItem key={status} value={status}>{statusLabels[status]}</SelectItem>)}</SelectContent></Select><Select value={game.priority ? String(game.priority) : 'none'} disabled={busy || !inQueue} onValueChange={(value) => onChange({ priority: value === 'none' ? null : Number(value) })}><SelectTrigger className="w-full" aria-label={`Priority for ${game.title}`}><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">No priority</SelectItem>{[1, 2, 3, 4, 5].map((priority) => <SelectItem key={priority} value={String(priority)}>Priority {priority}</SelectItem>)}</SelectContent></Select></div></div>
}
