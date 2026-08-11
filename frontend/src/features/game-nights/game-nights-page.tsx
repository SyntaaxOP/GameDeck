import { useEffect, useState, type FormEvent } from 'react'
import { CalendarDays, Check, Clipboard, Edit3, Plus, Trash2, Users } from 'lucide-react'
import { createGameNight, deleteGameNight, getDiscordAnnouncement, listGameNights, updateGameNight } from '@/api/game-nights'
import { listGames } from '@/api/games'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import type { Game } from '@/types/game'
import type { AttendeeStatus, GameNight, GameNightInput, GameNightStatus } from '@/types/game-night'

export function GameNightsPage() {
  const [nights, setNights] = useState<GameNight[]>([])
  const [games, setGames] = useState<Game[]>([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<GameNight | null>(null)
  const [deleting, setDeleting] = useState<GameNight | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [copied, setCopied] = useState<number | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([
      listGameNights(controller.signal),
      listGames({ query: '', platform: 'all', status: 'all', favorite: null, archived: false, page: 1, pageSize: 100 }, controller.signal),
    ]).then(([nightResult, gameResult]) => { setNights(nightResult.items); setGames(gameResult.items) })
      .catch((caught: unknown) => {
        if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load game nights.')
      })
    return () => controller.abort()
  }, [refreshKey])

  function refresh() { setRefreshKey((value) => value + 1) }
  async function copy(night: GameNight) {
    try { const { message } = await getDiscordAnnouncement(night.id); await navigator.clipboard.writeText(message); setCopied(night.id) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to copy announcement.') }
  }
  async function confirmDelete() {
    if (!deleting) return
    try { await deleteGameNight(deleting.id); setDeleting(null); refresh() }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to delete game night.') }
  }

  return <div className="space-y-6">
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-medium text-primary">Plan together, keep it local</p><h1 className="mt-1 text-3xl font-semibold sm:text-4xl">Game nights</h1><p className="mt-2 text-sm text-muted-foreground">Track RSVPs and copy a ready-to-post Discord announcement without storing a bot token.</p></div><Button onClick={() => { setEditing(null); setDialogOpen(true) }}><Plus aria-hidden="true" />Plan game night</Button></header>
    {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
    {nights.length ? <div className="grid gap-4 lg:grid-cols-2">{nights.map((night) => <Card key={night.id}><CardContent className="space-y-4 py-5"><div className="flex justify-between gap-3"><div><div className="flex gap-2"><h2 className="font-semibold">{night.title}</h2><Badge variant={night.status === 'planned' ? 'default' : 'secondary'}>{night.status}</Badge></div><p className="mt-2 flex gap-2 text-sm text-muted-foreground"><CalendarDays className="size-4" aria-hidden="true" />{new Date(night.scheduled_at).toLocaleString()} · {night.duration_minutes} min</p></div><div><Button size="icon" variant="ghost" onClick={() => { setEditing(night); setDialogOpen(true) }} aria-label={`Edit ${night.title}`}><Edit3 aria-hidden="true" /></Button><Button size="icon" variant="ghost" onClick={() => setDeleting(night)} aria-label={`Delete ${night.title}`}><Trash2 aria-hidden="true" /></Button></div></div><p className="text-sm">{night.game_title ?? 'Game to be decided'}</p><div className="flex flex-wrap gap-2"><Badge variant="outline"><Users aria-hidden="true" />{night.attendees.filter((attendee) => attendee.response === 'confirmed').length} confirmed</Badge><Badge variant="outline">{night.attendees.filter((attendee) => attendee.response === 'maybe').length} maybe</Badge></div>{night.notes ? <p className="text-sm text-muted-foreground">{night.notes}</p> : null}<Button size="sm" variant="outline" onClick={() => void copy(night)}>{copied === night.id ? <Check aria-hidden="true" /> : <Clipboard aria-hidden="true" />}{copied === night.id ? 'Copied' : 'Copy Discord post'}</Button></CardContent></Card>)}</div> : <Card className="border-dashed"><CardContent className="flex min-h-64 flex-col items-center justify-center text-center"><Users className="size-8 text-muted-foreground" aria-hidden="true" /><h2 className="mt-4 text-lg font-medium">No game nights planned</h2><Button className="mt-5" onClick={() => setDialogOpen(true)}><Plus aria-hidden="true" />Plan the first one</Button></CardContent></Card>}
    <GameNightDialog open={dialogOpen} night={editing} games={games} onOpenChange={setDialogOpen} onSaved={refresh} />
    <AlertDialog open={deleting !== null} onOpenChange={(open) => { if (!open) setDeleting(null) }}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Delete this game night?</AlertDialogTitle><AlertDialogDescription>The schedule and attendee responses will be removed from this computer.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction onClick={() => void confirmDelete()}>Delete game night</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
  </div>
}

function parseNames(value: string, response: AttendeeStatus) { return value.split(',').map((name) => name.trim()).filter(Boolean).map((name) => ({ name, response })) }

function GameNightDialog({ open, night, games, onOpenChange, onSaved }: { open: boolean; night: GameNight | null; games: Game[]; onOpenChange: (value: boolean) => void; onSaved: () => void }) {
  const [title, setTitle] = useState(''); const [gameId, setGameId] = useState('none'); const [scheduled, setScheduled] = useState(''); const [duration, setDuration] = useState('120'); const [status, setStatus] = useState<GameNightStatus>('planned'); const [confirmed, setConfirmed] = useState(''); const [maybe, setMaybe] = useState(''); const [notes, setNotes] = useState(''); const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!open) return
    setTitle(night?.title ?? ''); setGameId(night?.game_id ? String(night.game_id) : 'none'); setScheduled(night?.scheduled_at ? night.scheduled_at.slice(0, 16) : ''); setDuration(String(night?.duration_minutes ?? 120)); setStatus(night?.status ?? 'planned'); setConfirmed(night?.attendees.filter((attendee) => attendee.response === 'confirmed').map((attendee) => attendee.name).join(', ') ?? ''); setMaybe(night?.attendees.filter((attendee) => attendee.response === 'maybe').map((attendee) => attendee.name).join(', ') ?? ''); setNotes(night?.notes ?? ''); setError(null)
  }, [open, night])
  async function submit(event: FormEvent) {
    event.preventDefault()
    const payload: GameNightInput = { title, game_id: gameId === 'none' ? null : Number(gameId), scheduled_at: new Date(scheduled).toISOString(), duration_minutes: Number(duration), status, notes: notes || null, attendees: [...parseNames(confirmed, 'confirmed'), ...parseNames(maybe, 'maybe')] }
    try { if (night) await updateGameNight(night.id, payload); else await createGameNight(payload); onSaved(); onOpenChange(false) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to save game night.') }
  }
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="sm:max-w-xl"><DialogHeader><DialogTitle>{night ? 'Edit' : 'Plan'} game night</DialogTitle><DialogDescription>Times are shown locally and stored in UTC. Attendee names stay on this computer.</DialogDescription></DialogHeader><form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => void submit(event)}><div className="space-y-2 sm:col-span-2"><Label htmlFor="night-title">Title</Label><Input id="night-title" value={title} onChange={(event) => setTitle(event.target.value)} required /></div><div className="space-y-2"><Label>Game</Label><Select value={gameId} onValueChange={setGameId}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">Decide later</SelectItem>{games.map((game) => <SelectItem key={game.id} value={String(game.id)}>{game.title}</SelectItem>)}</SelectContent></Select></div><div className="space-y-2"><Label>Status</Label><Select value={status} onValueChange={(value) => setStatus(value as GameNightStatus)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="planned">Planned</SelectItem><SelectItem value="completed">Completed</SelectItem><SelectItem value="cancelled">Cancelled</SelectItem></SelectContent></Select></div><div className="space-y-2"><Label htmlFor="night-at">Date and time</Label><Input id="night-at" type="datetime-local" value={scheduled} onChange={(event) => setScheduled(event.target.value)} required /></div><div className="space-y-2"><Label htmlFor="night-duration">Minutes</Label><Input id="night-duration" type="number" min="30" max="720" value={duration} onChange={(event) => setDuration(event.target.value)} required /></div><div className="space-y-2"><Label htmlFor="confirmed">Confirmed names</Label><Input id="confirmed" value={confirmed} onChange={(event) => setConfirmed(event.target.value)} placeholder="Alex, Sam" /></div><div className="space-y-2"><Label htmlFor="maybe">Maybe names</Label><Input id="maybe" value={maybe} onChange={(event) => setMaybe(event.target.value)} placeholder="Jordan" /></div><div className="space-y-2 sm:col-span-2"><Label htmlFor="night-notes">Notes</Label><Textarea id="night-notes" value={notes} onChange={(event) => setNotes(event.target.value)} /></div>{error ? <p role="alert" className="text-sm text-destructive sm:col-span-2">{error}</p> : null}<DialogFooter className="sm:col-span-2"><Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button><Button type="submit">Save game night</Button></DialogFooter></form></DialogContent></Dialog>
}
