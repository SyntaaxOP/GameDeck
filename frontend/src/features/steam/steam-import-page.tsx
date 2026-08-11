import { useCallback, useEffect, useState } from 'react'
import { Check, FolderSearch, Gamepad2, LoaderCircle, RefreshCw } from 'lucide-react'

import { getLocalSteamLibrary, syncLocalSteamLibrary } from '@/api/steam'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { SteamLocalLibrary } from '@/types/steam'


export function SteamImportPage() {
  const [library, setLibrary] = useState<SteamLocalLibrary | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const loadLibrary = useCallback(async (signal?: AbortSignal) => {
    setError(null)
    try {
      setLibrary(await getLocalSteamLibrary(signal))
    } catch (caught) {
      if (!(caught instanceof DOMException && caught.name === 'AbortError')) {
        setError(caught instanceof Error ? caught.message : 'Unable to scan the local Steam library.')
      }
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void loadLibrary(controller.signal)
    return () => controller.abort()
  }, [loadLibrary])

  async function rescan() {
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const result = await syncLocalSteamLibrary()
      setMessage(
        `${result.discovered} installed games found. `
        + `${result.imported_game_ids.length} added and ${result.updated_game_ids.length} updated.`,
      )
      await loadLibrary()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to synchronize the Steam library.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Automatic local discovery</p>
          <h1 className="mt-1 text-3xl font-semibold sm:text-4xl">Steam library</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            GameDeck reads Steam&apos;s local installation manifests. No Steam login or API key is required.
            Installed games are added automatically and tracked when a process starts inside their install folder.
          </p>
        </div>
        <Button onClick={() => void rescan()} disabled={busy}>
          {busy ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <RefreshCw aria-hidden="true" />}
          Scan again
        </Button>
      </header>

      {error ? (
        <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </p>
      ) : null}
      {message ? (
        <p role="status" className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
          <Check className="mr-2 inline size-4" aria-hidden="true" />
          {message}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderSearch className="size-5 text-primary" aria-hidden="true" />
            Local Steam installation
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Badge variant={library?.steam_path ? 'default' : 'secondary'}>
              {library?.steam_path ? 'Steam detected' : 'Steam not detected'}
            </Badge>
            {library ? <Badge variant="secondary">{library.total} installed games</Badge> : null}
          </div>
          <p className="break-all font-mono text-xs text-muted-foreground">
            {library?.steam_path ?? 'Install Steam or set GAMEDECK_STEAM_PATH to its installation folder.'}
          </p>
          {library?.library_paths.map((path) => (
            <p key={path} className="break-all text-xs text-muted-foreground">Library: {path}</p>
          ))}
        </CardContent>
      </Card>

      {library?.games.length ? (
        <Card>
          <CardHeader><CardTitle>Your installed games</CardTitle></CardHeader>
          <CardContent>
            <div className="divide-y rounded-md border">
              {library.games.map((game) => (
                <div key={game.app_id} className="flex items-center gap-3 p-3">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <Gamepad2 className="size-5" aria-hidden="true" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{game.name}</p>
                    <p className="truncate font-mono text-xs text-muted-foreground" title={game.install_directory}>
                      {game.install_directory}
                    </p>
                  </div>
                  <Badge variant={game.tracking_ready ? 'default' : 'secondary'}>
                    {game.tracking_ready ? 'Tracking ready' : 'Needs setup'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : library ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            No locally installed Steam games were found.
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
