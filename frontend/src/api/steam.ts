import { ApiError } from '@/api/games'
import { apiUrl } from '@/lib/api-url'
import type {
  SteamConfiguration,
  SteamLocalLibrary,
  SteamLocalSync,
  SteamPreview,
} from '@/types/steam'


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as {
      error?: { message?: string; code?: string }
    }
    throw new ApiError(
      body.error?.message ?? `Request failed with status ${response.status}.`,
      body.error?.code,
    )
  }
  return response.json() as Promise<T>
}


export const getLocalSteamLibrary = (signal?: AbortSignal) =>
  request<SteamLocalLibrary>('/api/v1/steam/local-library', { signal })

export const syncLocalSteamLibrary = () =>
  request<SteamLocalSync>('/api/v1/steam/local-library/sync', { method: 'POST' })

export const getSteamConfiguration = (signal?: AbortSignal) =>
  request<SteamConfiguration>('/api/v1/steam/configuration', { signal })

export const previewSteam = (steamId: string | null) =>
  request<SteamPreview>('/api/v1/steam/preview', {
    method: 'POST',
    body: JSON.stringify({ steam_id: steamId || null }),
  })

export const importSteam = (items: { app_id: number; name: string }[]) =>
  request<{ imported_game_ids: number[]; skipped_app_ids: number[] }>('/api/v1/steam/import', {
    method: 'POST',
    body: JSON.stringify({ items }),
  })
