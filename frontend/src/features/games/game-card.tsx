import { useState } from 'react'
import { Activity, Archive, Edit3, Play, RotateCcw, Star } from 'lucide-react'
import { Link } from 'react-router-dom'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { platformLabels, statusLabels, type Game } from '@/types/game'
import { apiUrl } from '@/lib/api-url'
import { launchGame } from '@/api/games'

interface GameCardProps {
  game: Game
  busy: boolean
  running: boolean
  onEdit: (game: Game) => void
  onArchive: (game: Game) => void
  onRestore: (game: Game) => void
}

export function GameCard({ game, busy, running, onEdit, onArchive, onRestore }: GameCardProps) {
  const [launching, setLaunching] = useState(false)
  const [launchError, setLaunchError] = useState<string | null>(null)
  const artworkVersion = game.cover_path?.split(/[\\/]/).pop()

  async function launch() {
    setLaunching(true)
    setLaunchError(null)
    try {
      await launchGame(game.id)
    } catch (caught) {
      setLaunchError(caught instanceof Error ? caught.message : 'Unable to launch this game.')
    } finally {
      setLaunching(false)
    }
  }
  return (
    <Card className="flex min-h-64 flex-col overflow-hidden transition-colors hover:border-primary/35">
      {game.cover_path ? (
        <div className="aspect-[16/7] overflow-hidden border-b bg-muted">
          <img
            src={apiUrl(`/api/v1/games/${game.id}/cover?v=${encodeURIComponent(artworkVersion ?? game.updated_at)}`)}
            alt={`${game.title} artwork`}
            className="size-full object-cover"
            loading="lazy"
            onError={(event) => { event.currentTarget.parentElement?.classList.add('hidden') }}
          />
        </div>
      ) : null}
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <CardTitle className="truncate text-lg">{game.title}</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">{platformLabels[game.platform]}</p>
          </div>
          {game.favorite ? <Star className="size-5 shrink-0 fill-primary text-primary" aria-label="Favorite" /> : null}
        </div>
        <div className="flex flex-wrap gap-2 pt-2">
          {running ? <Badge className="gap-1"><Activity className="size-3" aria-hidden="true" /> Running</Badge> : null}
          <Badge variant="secondary">{statusLabels[game.status]}</Badge>
          {game.priority ? <Badge variant="outline">Priority {game.priority}</Badge> : null}
          {game.personal_rating ? <Badge variant="outline">{game.personal_rating}/10</Badge> : null}
        </div>
      </CardHeader>

      <CardContent className="flex-1 space-y-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Executable</p>
          <p className="mt-1 truncate font-mono text-xs" title={game.executable_path ?? game.executable_name}>{game.executable_name}</p>
        </div>
        {game.genre ? <p className="text-sm text-muted-foreground">{game.genre}</p> : null}
        {game.notes ? <p className="line-clamp-2 text-sm text-muted-foreground">{game.notes}</p> : null}
      </CardContent>

      <CardFooter className="justify-end gap-2 border-t bg-muted/15">
        {game.archived_at ? (
          <Button variant="outline" size="sm" disabled={busy} onClick={() => onRestore(game)}>
            <RotateCcw aria-hidden="true" /> Restore
          </Button>
        ) : (
          <>
            <Button size="sm" disabled={busy || launching} onClick={() => void launch()}>
              <Play aria-hidden="true" /> {launching ? 'Launching…' : 'Play'}
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <Link to={`/games/${game.id}`}>Details</Link>
            </Button>
            <Button variant="ghost" size="sm" disabled={busy} onClick={() => onEdit(game)}>
              <Edit3 aria-hidden="true" /> Edit
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm" disabled={busy}>
                  <Archive aria-hidden="true" /> Archive
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Archive {game.title}?</AlertDialogTitle>
                  <AlertDialogDescription>
                    The game leaves your active library and will not be tracked. Its history is preserved, and you can restore it later.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => onArchive(game)}>Archive game</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </>
        )}
      </CardFooter>
      {launchError ? <p role="alert" className="border-t px-6 py-2 text-xs text-destructive">{launchError}</p> : null}
    </Card>
  )
}
