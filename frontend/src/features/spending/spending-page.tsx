import { useEffect, useState } from 'react'
import { CircleDollarSign, Edit3, Plus, ReceiptText, Trash2 } from 'lucide-react'

import { listGames } from '@/api/games'
import { deletePurchase, getSpendingSummary, listPurchases } from '@/api/purchases'
import { getSettings } from '@/api/settings'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { PurchaseFormDialog } from '@/features/spending/purchase-form-dialog'
import { formatMoney } from '@/lib/money'
import type { Game } from '@/types/game'
import {
  purchaseKindLabels,
  type Purchase,
  type PurchaseList,
  type SpendingSummary,
} from '@/types/purchase'

export function SpendingPage() {
  const [games, setGames] = useState<Game[]>([])
  const [result, setResult] = useState<PurchaseList | null>(null)
  const [summary, setSummary] = useState<SpendingSummary | null>(null)
  const [defaultCurrency, setDefaultCurrency] = useState('PHP')
  const [gameFilter, setGameFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedPurchase, setSelectedPurchase] = useState<Purchase | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Purchase | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const filter = gameFilter === 'unassigned'
      ? { unassigned: true }
      : gameFilter === 'all' ? {} : { gameId: Number(gameFilter) }
    setLoading(true)
    setError(null)
    Promise.all([
      listGames(
        { query: '', platform: 'all', status: 'all', favorite: null, archived: false, page: 1, pageSize: 100 },
        controller.signal,
      ),
      listPurchases({ ...filter, pageSize: 100 }, controller.signal),
      getSpendingSummary(controller.signal),
      getSettings(controller.signal),
    ])
      .then(([gameResponse, purchaseResponse, summaryResponse, settingsResponse]) => {
        setGames(gameResponse.items)
        setResult(purchaseResponse)
        setSummary(summaryResponse)
        setDefaultCurrency(settingsResponse.currency_code)
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === 'AbortError') return
        setError(caught instanceof Error ? caught.message : 'Unable to load spending data.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [gameFilter, refreshKey])

  function refresh() {
    setRefreshKey((current) => current + 1)
  }

  function openCreate() {
    setSelectedPurchase(null)
    setDialogOpen(true)
  }

  function openEdit(purchase: Purchase) {
    setSelectedPurchase(purchase)
    setDialogOpen(true)
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    setDeleting(true)
    setError(null)
    try {
      await deletePurchase(deleteTarget.id)
      setDeleteTarget(null)
      refresh()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to delete this purchase.')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-7">
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Local spending</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">Spending</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Keep a private purchase ledger and compare game costs with recorded playtime.
          </p>
        </div>
        <Button onClick={openCreate}><Plus aria-hidden="true" /> Add purchase</Button>
      </header>

      {error ? <p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</p> : null}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><Skeleton className="h-36" /><Skeleton className="h-36" /></div>
      ) : summary?.currencies.length ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {summary.currencies.map((currency) => (
            <Card key={currency.currency_code}>
              <CardHeader><CardTitle className="flex items-center justify-between text-sm text-muted-foreground"><span className="flex items-center gap-2"><CircleDollarSign className="size-4" aria-hidden="true" /> {currency.currency_code} total</span><Badge variant="outline">{currency.purchase_count} records</Badge></CardTitle></CardHeader>
              <CardContent>
                <p className="font-mono text-2xl font-semibold">{formatMoney(currency.amount_minor, currency.currency_code)}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {currency.cost_per_hour_minor === null
                    ? 'Cost per hour becomes available after attributed games are played.'
                    : `${formatMoney(currency.cost_per_hour_minor, currency.currency_code)} per played hour`}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="border-dashed"><CardContent className="flex min-h-36 items-center justify-center text-sm text-muted-foreground">No spending totals yet.</CardContent></Card>
      )}

      <Card>
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
          <Select value={gameFilter} onValueChange={setGameFilter}>
            <SelectTrigger className="w-full sm:w-64" aria-label="Filter purchases by game"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All purchases</SelectItem>
              <SelectItem value="unassigned">Unassigned / shared</SelectItem>
              {games.map((game) => <SelectItem key={game.id} value={String(game.id)}>{game.title}</SelectItem>)}
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">{loading ? 'Loading purchases…' : `${result?.total ?? 0} purchase records`}</p>
        </CardContent>
      </Card>

      {loading ? (
        <Skeleton className="h-72 rounded-xl" />
      ) : result?.items.length ? (
        <Card>
          <Table>
            <TableHeader><TableRow><TableHead>Purchase</TableHead><TableHead>Game</TableHead><TableHead>Date</TableHead><TableHead>Store</TableHead><TableHead className="text-right">Amount</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {result.items.map((purchase) => (
                <TableRow key={purchase.id}>
                  <TableCell><Badge variant="secondary">{purchaseKindLabels[purchase.kind]}</Badge>{purchase.notes ? <p className="mt-1 max-w-52 truncate text-xs text-muted-foreground">{purchase.notes}</p> : null}</TableCell>
                  <TableCell>{purchase.game_title ?? <span className="text-muted-foreground">Unassigned</span>}</TableCell>
                  <TableCell>{purchase.purchased_on ? new Date(`${purchase.purchased_on}T00:00:00`).toLocaleDateString() : '—'}</TableCell>
                  <TableCell>{purchase.platform ?? '—'}</TableCell>
                  <TableCell className="text-right font-mono font-medium">{formatMoney(purchase.amount_minor, purchase.currency_code)}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button size="icon-sm" variant="ghost" onClick={() => openEdit(purchase)} aria-label={`Edit ${purchaseKindLabels[purchase.kind]} purchase`}><Edit3 aria-hidden="true" /></Button>
                      <Button size="icon-sm" variant="ghost" onClick={() => setDeleteTarget(purchase)} aria-label={`Delete ${purchaseKindLabels[purchase.kind]} purchase`}><Trash2 aria-hidden="true" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      ) : (
        <Card className="border-dashed">
          <CardContent className="flex min-h-64 flex-col items-center justify-center text-center">
            <ReceiptText className="size-8 text-muted-foreground" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-medium">No purchases found</h2>
            <p className="mt-2 max-w-sm text-sm text-muted-foreground">Add your first purchase or choose a different game filter.</p>
            <Button className="mt-5" variant="outline" onClick={openCreate}><Plus aria-hidden="true" /> Add purchase</Button>
          </CardContent>
        </Card>
      )}

      <PurchaseFormDialog games={games} defaultCurrency={defaultCurrency} open={dialogOpen} purchase={selectedPurchase} onOpenChange={setDialogOpen} onSaved={refresh} />

      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(open) => { if (!open && !deleting) setDeleteTarget(null) }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this purchase?</AlertDialogTitle>
            <AlertDialogDescription>This permanently removes the ledger entry. Game and session history are unchanged.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction variant="destructive" disabled={deleting} onClick={() => void confirmDelete()}>{deleting ? 'Deleting…' : 'Delete purchase'}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
