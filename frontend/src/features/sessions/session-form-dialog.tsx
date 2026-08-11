import { useEffect, useState, type FormEvent } from 'react'
import { LoaderCircle } from 'lucide-react'

import { createManualSession, updateSession } from '@/api/sessions'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { localInputToIso, toDateTimeLocal } from '@/lib/date-time'
import type { Game } from '@/types/game'
import type { GameSession } from '@/types/session'

interface SessionFormDialogProps {
  games: Game[]
  fixedGameId?: number
  open: boolean
  session: GameSession | null
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}

function defaultTimes() {
  const endedAt = new Date()
  endedAt.setSeconds(0, 0)
  const startedAt = new Date(endedAt.getTime() - 60 * 60 * 1_000)
  return { startedAt: toDateTimeLocal(startedAt), endedAt: toDateTimeLocal(endedAt) }
}

export function SessionFormDialog({
  games,
  fixedGameId,
  open,
  session,
  onOpenChange,
  onSaved,
}: SessionFormDialogProps) {
  const [gameId, setGameId] = useState('')
  const [startedAt, setStartedAt] = useState('')
  const [endedAt, setEndedAt] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    const defaults = defaultTimes()
    setGameId(String(session?.game_id ?? fixedGameId ?? games[0]?.id ?? ''))
    setStartedAt(session ? toDateTimeLocal(session.started_at) : defaults.startedAt)
    setEndedAt(session?.ended_at ? toDateTimeLocal(session.ended_at) : defaults.endedAt)
    setError(null)
  }, [fixedGameId, games, open, session])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!gameId) {
      setError('Choose a game before saving the session.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (session) {
        await updateSession(session.id, {
          started_at: localInputToIso(startedAt),
          ended_at: localInputToIso(endedAt),
        })
      } else {
        await createManualSession({
          game_id: Number(gameId),
          started_at: localInputToIso(startedAt),
          ended_at: localInputToIso(endedAt),
        })
      }
      onSaved()
      onOpenChange(false)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to save this session.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{session ? 'Correct session' : 'Add manual session'}</DialogTitle>
          <DialogDescription>
            {session
              ? 'Adjust the recorded start and end. Duration is recalculated automatically.'
              : 'Add playtime that GameDeck did not observe automatically.'}
          </DialogDescription>
        </DialogHeader>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="session-game">Game</Label>
            <Select value={gameId} onValueChange={setGameId} disabled={Boolean(session || fixedGameId)}>
              <SelectTrigger id="session-game" className="w-full"><SelectValue placeholder="Choose a game" /></SelectTrigger>
              <SelectContent>
                {games.map((game) => <SelectItem key={game.id} value={String(game.id)}>{game.title}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="session-start">Started</Label>
              <Input id="session-start" type="datetime-local" value={startedAt} onChange={(event) => setStartedAt(event.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="session-end">Ended</Label>
              <Input id="session-end" type="datetime-local" value={endedAt} onChange={(event) => setEndedAt(event.target.value)} required />
            </div>
          </div>

          <p className="text-xs leading-relaxed text-muted-foreground">
            Times are entered in your Windows timezone and stored as UTC. Sessions for the same game cannot overlap.
          </p>

          {error ? <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>Cancel</Button>
            <Button type="submit" disabled={saving || games.length === 0}>
              {saving ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : null}
              {session ? 'Save correction' : 'Add session'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

