import { ApiError } from '@/api/games'
import { apiUrl } from '@/lib/api-url'
import type { GameNight, GameNightInput, GameNightList } from '@/types/game-night'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), { ...init, headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: { message?: string; code?: string } }
    throw new ApiError(body.error?.message ?? `Request failed with status ${response.status}.`, body.error?.code)
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}
export const listGameNights = (signal?: AbortSignal) => request<GameNightList>('/api/v1/game-nights', { signal })
export const createGameNight = (input: GameNightInput) => request<GameNight>('/api/v1/game-nights', { method: 'POST', body: JSON.stringify(input) })
export const updateGameNight = (id: number, input: Partial<GameNightInput>) => request<GameNight>(`/api/v1/game-nights/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteGameNight = (id: number) => request<void>(`/api/v1/game-nights/${id}`, { method: 'DELETE' })
export const getDiscordAnnouncement = (id: number) => request<{ message: string }>(`/api/v1/game-nights/${id}/discord-announcement`)
