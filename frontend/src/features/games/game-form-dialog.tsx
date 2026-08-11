import { useEffect, useState, type FormEvent } from 'react'
import { LoaderCircle, Plus, Trash2 } from 'lucide-react'

import { createGame, updateGame } from '@/api/games'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
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
import {
  libraryStatuses,
  platformLabels,
  platforms,
  statusLabels,
  type Game,
  type GameInput,
} from '@/types/game'

interface GameFormDialogProps {
  game: Game | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}

interface FormState {
  title: string
  platform: GameInput['platform']
  executableName: string
  executablePath: string
  executableAliases: AliasFormRow[]
  genre: string
  status: GameInput['status']
  priority: string
  personalRating: string
  notes: string
  favorite: boolean
}

interface AliasFormRow {
  key: string
  executableName: string
  executablePath: string
}

let nextAliasKey = 0

function aliasKey(): string {
  nextAliasKey += 1
  return `alias-${nextAliasKey}`
}

const emptyForm: FormState = {
  title: '',
  platform: 'steam',
  executableName: '',
  executablePath: '',
  executableAliases: [],
  genre: '',
  status: 'backlog',
  priority: '',
  personalRating: '',
  notes: '',
  favorite: false,
}

function formFromGame(game: Game | null): FormState {
  if (!game) return emptyForm
  return {
    title: game.title,
    platform: game.platform,
    executableName: game.executable_name,
    executablePath: game.executable_path ?? '',
    executableAliases: game.executable_aliases.map((alias) => ({
      key: aliasKey(),
      executableName: alias.executable_name,
      executablePath: alias.executable_path ?? '',
    })),
    genre: game.genre ?? '',
    status: game.status,
    priority: game.priority?.toString() ?? '',
    personalRating: game.personal_rating?.toString() ?? '',
    notes: game.notes ?? '',
    favorite: game.favorite,
  }
}

function optionalNumber(value: string): number | null {
  return value ? Number(value) : null
}

export function GameFormDialog({ game, open, onOpenChange, onSaved }: GameFormDialogProps) {
  const [form, setForm] = useState<FormState>(() => formFromGame(game))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setForm(formFromGame(game))
      setError(null)
    }
  }, [game, open])

  function updateField<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function addAlias() {
    setForm((current) => ({
      ...current,
      executableAliases: [
        ...current.executableAliases,
        { key: aliasKey(), executableName: '', executablePath: '' },
      ],
    }))
  }

  function updateAlias(key: string, field: 'executableName' | 'executablePath', value: string) {
    setForm((current) => ({
      ...current,
      executableAliases: current.executableAliases.map((alias) =>
        alias.key === key ? { ...alias, [field]: value } : alias,
      ),
    }))
  }

  function removeAlias(key: string) {
    setForm((current) => ({
      ...current,
      executableAliases: current.executableAliases.filter((alias) => alias.key !== key),
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    const payload: GameInput = {
      title: form.title,
      platform: form.platform,
      executable_name: form.executableName,
      executable_path: form.executablePath || null,
      executable_aliases: form.executableAliases.map((alias) => ({
        executable_name: alias.executableName,
        executable_path: alias.executablePath || null,
      })),
      genre: form.genre || null,
      status: form.status,
      priority: optionalNumber(form.priority),
      personal_rating: optionalNumber(form.personalRating),
      notes: form.notes || null,
      favorite: form.favorite,
    }
    try {
      if (game) await updateGame(game.id, payload)
      else await createGame(payload)
      onSaved()
      onOpenChange(false)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to save this game.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{game ? 'Edit game' : 'Add a game'}</DialogTitle>
          <DialogDescription>
            Register the exact Windows executable that GameDeck should recognize later.
          </DialogDescription>
        </DialogHeader>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={form.title}
                onChange={(event) => updateField('title', event.target.value)}
                placeholder="Palworld"
                maxLength={200}
                required
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="platform">Platform</Label>
              <Select value={form.platform} onValueChange={(value) => updateField('platform', value as GameInput['platform'])}>
                <SelectTrigger id="platform" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {platforms.map((platform) => (
                    <SelectItem key={platform} value={platform}>{platformLabels[platform]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Library status</Label>
              <Select value={form.status} onValueChange={(value) => updateField('status', value as GameInput['status'])}>
                <SelectTrigger id="status" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {libraryStatuses.map((status) => (
                    <SelectItem key={status} value={status}>{statusLabels[status]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="executable-name">Executable name</Label>
              <Input
                id="executable-name"
                value={form.executableName}
                onChange={(event) => updateField('executableName', event.target.value)}
                placeholder="Palworld-Win64-Shipping.exe"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="genre">Genre</Label>
              <Input id="genre" value={form.genre} onChange={(event) => updateField('genre', event.target.value)} placeholder="Survival" />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="executable-path">Executable path <span className="text-muted-foreground">(optional)</span></Label>
              <Input
                id="executable-path"
                value={form.executablePath}
                onChange={(event) => updateField('executablePath', event.target.value)}
                placeholder="C:\Games\Palworld\Palworld-Win64-Shipping.exe"
                className="font-mono text-xs"
              />
              <p className="text-xs text-muted-foreground">The filename must match the executable name. GameDeck stores this path but never executes it.</p>
            </div>

            <div className="space-y-3 rounded-md border bg-muted/20 p-4 sm:col-span-2">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium">Additional executables</p>
                  <p className="mt-1 text-xs text-muted-foreground">Add launchers or alternate builds that should count as this same game.</p>
                </div>
                <Button type="button" size="sm" variant="outline" onClick={addAlias} disabled={form.executableAliases.length >= 10}>
                  <Plus aria-hidden="true" /> Add alias
                </Button>
              </div>
              {form.executableAliases.length ? (
                <div className="space-y-3">
                  {form.executableAliases.map((alias, index) => (
                    <div key={alias.key} className="grid gap-2 border-t pt-3 sm:grid-cols-[1fr_1.5fr_auto]">
                      <div className="space-y-1.5">
                        <Label htmlFor={`${alias.key}-name`}>Alias {index + 1} filename</Label>
                        <Input
                          id={`${alias.key}-name`}
                          value={alias.executableName}
                          onChange={(event) => updateAlias(alias.key, 'executableName', event.target.value)}
                          placeholder="Game-Win64-Shipping.exe"
                          required
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor={`${alias.key}-path`}>Exact path <span className="text-muted-foreground">(optional)</span></Label>
                        <Input
                          id={`${alias.key}-path`}
                          value={alias.executablePath}
                          onChange={(event) => updateAlias(alias.key, 'executablePath', event.target.value)}
                          placeholder="C:\Games\Game\Game-Win64-Shipping.exe"
                          className="font-mono text-xs"
                        />
                      </div>
                      <Button type="button" size="icon" variant="ghost" className="self-end" onClick={() => removeAlias(alias.key)} aria-label={`Remove alias ${index + 1}`}>
                        <Trash2 aria-hidden="true" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : <p className="text-xs text-muted-foreground">No aliases configured. The primary executable above is used for detection.</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Input id="priority" type="number" min="1" max="5" value={form.priority} onChange={(event) => updateField('priority', event.target.value)} placeholder="1–5" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="rating">Personal rating</Label>
              <Input id="rating" type="number" min="1" max="10" value={form.personalRating} onChange={(event) => updateField('personalRating', event.target.value)} placeholder="1–10" />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" value={form.notes} onChange={(event) => updateField('notes', event.target.value)} placeholder="What makes this worth playing next?" rows={3} />
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-md border bg-muted/30 p-3">
            <Checkbox id="favorite" checked={form.favorite} onCheckedChange={(checked) => updateField('favorite', checked === true)} />
            <Label htmlFor="favorite" className="cursor-pointer">Mark as favorite</Label>
          </div>

          {error ? <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>Cancel</Button>
            <Button type="submit" disabled={saving}>
              {saving ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : null}
              {game ? 'Save changes' : 'Add game'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
