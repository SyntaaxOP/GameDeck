import { useCallback, useEffect, useState } from 'react'
import { Check, RotateCcw, ShieldX } from 'lucide-react'
import { confirmDetection, getDetections, getIgnored, ignoreDetection, removeIgnored, type IgnoredExecutable } from '@/api/detections'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { Game } from '@/types/game'

export function DetectionReviewPage() {
  const [pending, setPending] = useState<Game[]>([])
  const [ignored, setIgnored] = useState<IgnoredExecutable[]>([])
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    try {
      const [review, rules] = await Promise.all([getDetections(), getIgnored()])
      setPending(review.items); setIgnored(rules.items); setError(null)
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to load detection review.') }
  }, [])
  useEffect(() => { void load() }, [load])
  async function confirm(game: Game, title: string) { await confirmDetection(game.id, title); await load() }
  async function ignore(gameId: number) { await ignoreDetection(gameId); await load() }
  async function restore(id: number) { await removeIgnored(id); await load() }
  return <div className="space-y-7">
    <header><p className="text-sm font-medium text-primary">Detection safety</p><h1 className="mt-1 text-3xl font-semibold">Review detected games</h1><p className="mt-2 text-sm text-muted-foreground">Confirm real games or ignore applications permanently. Ignored paths will not be detected again.</p></header>
    {error ? <p role="alert" className="rounded-lg border border-destructive/40 p-4 text-destructive">{error}</p> : null}
    <section className="space-y-3"><h2 className="text-lg font-medium">Needs review ({pending.length})</h2>
      {pending.length ? pending.map((game) => <DetectionCard key={game.id} game={game} onConfirm={confirm} onIgnore={ignore} />) : <Card><CardContent className="py-10 text-center text-sm text-muted-foreground">No detections need review.</CardContent></Card>}
    </section>
    <section className="space-y-3"><h2 className="text-lg font-medium">Ignored applications ({ignored.length})</h2>
      {ignored.map((item) => <Card key={item.id}><CardContent className="flex items-center gap-4 py-4"><ShieldX className="size-5 text-muted-foreground" /><div className="min-w-0 flex-1"><p className="font-medium">{item.executable_name}</p><p className="truncate text-xs text-muted-foreground">{item.executable_path ?? 'Any matching executable name'}</p></div><Button variant="outline" size="sm" onClick={() => void restore(item.id)}><RotateCcw /> Allow again</Button></CardContent></Card>)}
    </section>
  </div>
}

function DetectionCard({ game, onConfirm, onIgnore }: { game: Game; onConfirm: (game: Game, title: string) => Promise<void>; onIgnore: (id: number) => Promise<void> }) {
  const [title, setTitle] = useState(game.title)
  const [busy, setBusy] = useState(false)
  const run = async (action: () => Promise<void>) => { setBusy(true); try { await action() } finally { setBusy(false) } }
  return <Card><CardHeader><CardTitle className="text-base">{game.executable_name}</CardTitle></CardHeader><CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center"><Input value={title} onChange={(event) => setTitle(event.target.value)} aria-label={`Title for ${game.executable_name}`} /><Button disabled={busy || !title.trim()} onClick={() => void run(() => onConfirm(game, title.trim()))}><Check /> Confirm game</Button><Button variant="outline" disabled={busy} onClick={() => void run(() => onIgnore(game.id))}><ShieldX /> Ignore app</Button></CardContent></Card>
}
