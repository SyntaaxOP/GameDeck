import { useEffect, useState, type FormEvent } from 'react'
import { LoaderCircle } from 'lucide-react'

import { createPurchase, updatePurchase } from '@/api/purchases'
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
import { Textarea } from '@/components/ui/textarea'
import { inputToMinor, minorToInput } from '@/lib/money'
import type { Game } from '@/types/game'
import { purchaseKindLabels, type Purchase, type PurchaseKind } from '@/types/purchase'

interface PurchaseFormDialogProps {
  games: Game[]
  defaultCurrency: string
  open: boolean
  purchase: Purchase | null
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}

export function PurchaseFormDialog({
  games,
  defaultCurrency,
  open,
  purchase,
  onOpenChange,
  onSaved,
}: PurchaseFormDialogProps) {
  const [gameId, setGameId] = useState('unassigned')
  const [kind, setKind] = useState<PurchaseKind>('base_game')
  const [amount, setAmount] = useState('')
  const [currencyCode, setCurrencyCode] = useState(defaultCurrency)
  const [purchasedOn, setPurchasedOn] = useState('')
  const [platform, setPlatform] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    const currency = purchase?.currency_code ?? defaultCurrency
    setGameId(purchase?.game_id ? String(purchase.game_id) : 'unassigned')
    setKind(purchase?.kind ?? 'base_game')
    setCurrencyCode(currency)
    setAmount(purchase ? minorToInput(purchase.amount_minor, currency) : '')
    setPurchasedOn(purchase?.purchased_on ?? '')
    setPlatform(purchase?.platform ?? '')
    setNotes(purchase?.notes ?? '')
    setError(null)
  }, [defaultCurrency, open, purchase])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalizedCurrency = currencyCode.trim().toUpperCase()
    const amountMinor = inputToMinor(amount, normalizedCurrency)
    if (!/^[A-Z]{3}$/.test(normalizedCurrency)) {
      setError('Enter a three-letter currency code such as PHP or USD.')
      return
    }
    if (amountMinor === null) {
      setError('Enter a non-negative purchase amount.')
      return
    }
    setSaving(true)
    setError(null)
    const input = {
      game_id: gameId === 'unassigned' ? null : Number(gameId),
      kind,
      amount_minor: amountMinor,
      currency_code: normalizedCurrency,
      purchased_on: purchasedOn || null,
      platform: platform.trim() || null,
      notes: notes.trim() || null,
    }
    try {
      if (purchase) await updatePurchase(purchase.id, input)
      else await createPurchase(input)
      onSaved()
      onOpenChange(false)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to save this purchase.')
    } finally {
      setSaving(false)
    }
  }

  const selectedGameMissing = purchase?.game_id && !games.some((game) => game.id === purchase.game_id)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{purchase ? 'Edit purchase' : 'Add purchase'}</DialogTitle>
          <DialogDescription>
            Amounts stay local and currencies are reported separately without conversion.
          </DialogDescription>
        </DialogHeader>
        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="purchase-game">Game</Label>
              <Select value={gameId} onValueChange={setGameId}>
                <SelectTrigger id="purchase-game" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned / shared</SelectItem>
                  {selectedGameMissing ? <SelectItem value={String(purchase.game_id)}>{purchase.game_title ?? 'Archived game'}</SelectItem> : null}
                  {games.map((game) => <SelectItem key={game.id} value={String(game.id)}>{game.title}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="purchase-kind">Kind</Label>
              <Select value={kind} onValueChange={(value) => setKind(value as PurchaseKind)}>
                <SelectTrigger id="purchase-kind" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(Object.entries(purchaseKindLabels) as [PurchaseKind, string][]).map(([value, label]) => <SelectItem key={value} value={value}>{label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-[1fr_110px_1fr]">
            <div className="space-y-2">
              <Label htmlFor="purchase-amount">Amount</Label>
              <Input id="purchase-amount" inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="0.00" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="purchase-currency">Currency</Label>
              <Input id="purchase-currency" value={currencyCode} onChange={(event) => setCurrencyCode(event.target.value.toUpperCase())} maxLength={3} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="purchase-date">Purchased</Label>
              <Input id="purchase-date" type="date" value={purchasedOn} onChange={(event) => setPurchasedOn(event.target.value)} />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="purchase-platform">Store or platform</Label>
            <Input id="purchase-platform" value={platform} onChange={(event) => setPlatform(event.target.value)} maxLength={100} placeholder="Steam, Xbox, local store…" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="purchase-notes">Notes</Label>
            <Textarea id="purchase-notes" value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={2000} rows={3} placeholder="Edition, sale, or shared subscription context" />
          </div>
          {error ? <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>Cancel</Button>
            <Button type="submit" disabled={saving}>
              {saving ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : null}
              {purchase ? 'Save purchase' : 'Add purchase'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
