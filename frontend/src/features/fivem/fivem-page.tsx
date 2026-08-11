import { useEffect, useState, type FormEvent } from 'react'
import { Clock3, Edit3, ExternalLink, Heart, LoaderCircle, MapPin, Plus, Radio, Trash2 } from 'lucide-react'

import { createFiveMServer, deleteFiveMServer, listFiveMServers, markFiveMServerJoined, updateFiveMServer } from '@/api/fivem'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { formatDuration } from '@/lib/date-time'
import type { FiveMServer, FiveMServerInput } from '@/types/fivem'

export function FiveMPage() {
  const [servers, setServers] = useState<FiveMServer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<FiveMServer | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<FiveMServer | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    listFiveMServers(controller.signal).then((result) => setServers(result.items)).catch((caught: unknown) => {
      if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load FiveM servers.')
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [refreshKey])

  function refresh() { setRefreshKey((value) => value + 1) }
  function openCreate() { setEditing(null); setDialogOpen(true) }

  async function markJoined(server: FiveMServer) {
    setError(null)
    try { await markFiveMServerJoined(server.id); refresh() } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to update this server.') }
  }

  async function confirmDelete() {
    if (!deleting) return
    try { await deleteFiveMServer(deleting.id); setDeleting(null); refresh() } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to delete this server.') }
  }

  return <div className="space-y-6">
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-medium text-primary">Your roleplay shortcuts</p><h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">FiveM companion</h1><p className="mt-2 max-w-2xl text-sm text-muted-foreground">Keep favorite servers, connect codes, notes, and manual playtime together. GameDeck never connects automatically.</p></div><Button onClick={openCreate}><Plus aria-hidden="true" /> Add server</Button></header>
    {error ? <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
    {loading ? <div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-56" /><Skeleton className="h-56" /></div> : servers.length ? <div className="grid gap-4 md:grid-cols-2">{servers.map((server) => <Card key={server.id}><CardContent className="space-y-4 py-5"><div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-2"><h2 className="text-lg font-semibold">{server.name}</h2>{server.favorite ? <Badge><Heart className="fill-current" aria-hidden="true" /> Favorite</Badge> : null}</div><p className="mt-1 flex items-center gap-2 font-mono text-xs text-muted-foreground"><MapPin className="size-3.5" aria-hidden="true" /> {server.address}</p></div><div className="flex"><Button size="icon" variant="ghost" onClick={() => { setEditing(server); setDialogOpen(true) }} aria-label={`Edit ${server.name}`}><Edit3 aria-hidden="true" /></Button><Button size="icon" variant="ghost" onClick={() => setDeleting(server)} aria-label={`Delete ${server.name}`}><Trash2 aria-hidden="true" /></Button></div></div><div className="grid grid-cols-2 gap-3 text-sm"><div><p className="text-xs text-muted-foreground">Manual playtime</p><p className="mt-1 font-mono">{formatDuration(server.tracked_playtime_seconds)}</p></div><div><p className="text-xs text-muted-foreground">Last joined</p><p className="mt-1">{server.last_joined_at ? new Date(server.last_joined_at).toLocaleString() : 'Not recorded'}</p></div></div>{server.notes ? <p className="text-sm leading-relaxed text-muted-foreground">{server.notes}</p> : null}<div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={() => void markJoined(server)}><Clock3 aria-hidden="true" /> Mark joined now</Button>{server.discord_url ? <Button size="sm" variant="ghost" asChild><a href={server.discord_url} target="_blank" rel="noreferrer">Discord <ExternalLink aria-hidden="true" /></a></Button> : null}{server.connect_code ? <Badge variant="outline" className="font-mono">{server.connect_code}</Badge> : null}</div></CardContent></Card>)}</div> : <Card className="border-dashed"><CardContent className="flex min-h-64 flex-col items-center justify-center text-center"><Radio className="size-8 text-muted-foreground" aria-hidden="true" /><h2 className="mt-4 text-lg font-medium">No FiveM servers saved</h2><p className="mt-2 max-w-sm text-sm text-muted-foreground">Add servers manually. Live status checks stay off until a reliable, privacy-safe source is justified.</p><Button className="mt-5" variant="outline" onClick={openCreate}><Plus aria-hidden="true" /> Add first server</Button></CardContent></Card>}
    <FiveMFormDialog server={editing} open={dialogOpen} onOpenChange={setDialogOpen} onSaved={refresh} />
    <AlertDialog open={deleting !== null} onOpenChange={(open) => { if (!open) setDeleting(null) }}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Delete this saved server?</AlertDialogTitle><AlertDialogDescription>This removes only the manual FiveM companion record. It does not affect game sessions.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction onClick={() => void confirmDelete()}>Delete server</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
  </div>
}

const emptyInput: FiveMServerInput = { name: '', address: '', connect_code: null, discord_url: null, notes: null, favorite: false, last_joined_at: null, tracked_playtime_seconds: 0 }

function FiveMFormDialog({ server, open, onOpenChange, onSaved }: { server: FiveMServer | null; open: boolean; onOpenChange: (open: boolean) => void; onSaved: () => void }) {
  const [form, setForm] = useState<FiveMServerInput>(emptyInput)
  const [hours, setHours] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { if (open) { setForm(server ? { name: server.name, address: server.address, connect_code: server.connect_code, discord_url: server.discord_url, notes: server.notes, favorite: server.favorite, last_joined_at: server.last_joined_at, tracked_playtime_seconds: server.tracked_playtime_seconds } : emptyInput); setHours(server?.tracked_playtime_seconds ? String(server.tracked_playtime_seconds / 3600) : ''); setError(null) } }, [open, server])
  function field<K extends keyof FiveMServerInput>(key: K, value: FiveMServerInput[K]) { setForm((current) => ({ ...current, [key]: value })) }
  async function submit(event: FormEvent) { event.preventDefault(); setSaving(true); setError(null); const payload = { ...form, tracked_playtime_seconds: Math.round((Number(hours) || 0) * 3600) }; try { if (server) await updateFiveMServer(server.id, payload); else await createFiveMServer(payload); onSaved(); onOpenChange(false) } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to save this server.') } finally { setSaving(false) } }
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl"><DialogHeader><DialogTitle>{server ? 'Edit FiveM server' : 'Add FiveM server'}</DialogTitle><DialogDescription>Save only information you choose. Addresses and connect codes are never executed.</DialogDescription></DialogHeader><form className="space-y-4" onSubmit={(event) => void submit(event)}><div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2 sm:col-span-2"><Label htmlFor="fivem-name">Server name</Label><Input id="fivem-name" value={form.name} onChange={(e) => field('name', e.target.value)} required autoFocus /></div><div className="space-y-2"><Label htmlFor="fivem-address">Address</Label><Input id="fivem-address" className="font-mono" value={form.address} onChange={(e) => field('address', e.target.value)} placeholder="play.example.com:30120" required /></div><div className="space-y-2"><Label htmlFor="fivem-code">Connect code</Label><Input id="fivem-code" value={form.connect_code ?? ''} onChange={(e) => field('connect_code', e.target.value || null)} placeholder="cfx.re/join/abc123" /></div><div className="space-y-2 sm:col-span-2"><Label htmlFor="fivem-discord">Discord invite <span className="text-muted-foreground">(optional)</span></Label><Input id="fivem-discord" type="url" value={form.discord_url ?? ''} onChange={(e) => field('discord_url', e.target.value || null)} placeholder="https://discord.gg/example" /></div><div className="space-y-2"><Label htmlFor="fivem-hours">Tracked hours</Label><Input id="fivem-hours" type="number" min="0" step="0.1" value={hours} onChange={(e) => setHours(e.target.value)} /></div><div className="flex items-end gap-3 pb-2"><Checkbox id="fivem-favorite" checked={form.favorite} onCheckedChange={(value) => field('favorite', value === true)} /><Label htmlFor="fivem-favorite">Favorite server</Label></div><div className="space-y-2 sm:col-span-2"><Label htmlFor="fivem-notes">Notes</Label><Textarea id="fivem-notes" rows={4} value={form.notes ?? ''} onChange={(e) => field('notes', e.target.value || null)} /></div></div>{error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}<DialogFooter><Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button><Button type="submit" disabled={saving}>{saving ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : null} Save server</Button></DialogFooter></form></DialogContent></Dialog>
}
