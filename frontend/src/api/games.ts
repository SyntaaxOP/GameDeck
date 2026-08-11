import type {
  Game,
  GameInput,
  GameSort,
  GameUpdateInput,
  GameList,
  LibraryStatus,
  Platform,
} from '@/types/game'
import { apiUrl } from '@/lib/api-url'

interface ErrorEnvelope {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
}

export class ApiError extends Error {
  readonly code: string
  readonly details: unknown

  constructor(message: string, code = 'request_failed', details: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: init?.body
      ? { 'Content-Type': 'application/json', ...init.headers }
      : init?.headers,
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorEnvelope
    throw new ApiError(
      body.error?.message ?? `Request failed with status ${response.status}.`,
      body.error?.code,
      body.error?.details,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export interface GameFilters {
  query: string
  platform: Platform | 'all'
  status: LibraryStatus | 'all'
  favorite: boolean | null
  archived: boolean
  page: number
  pageSize: number
  priority?: number | null
  sort?: GameSort
  order?: 'asc' | 'desc'
}

export function listGames(filters: GameFilters, signal?: AbortSignal): Promise<GameList> {
  const params = new URLSearchParams({
    archived: String(filters.archived),
    page: String(filters.page),
    page_size: String(filters.pageSize),
    sort: filters.sort ?? 'title',
    order: filters.order ?? 'asc',
  })
  if (filters.query.trim()) params.set('q', filters.query.trim())
  if (filters.platform !== 'all') params.set('platform', filters.platform)
  if (filters.status !== 'all') params.set('status', filters.status)
  if (filters.favorite !== null) params.set('favorite', String(filters.favorite))
  if (filters.priority) params.set('priority', String(filters.priority))

  return request<GameList>(`/api/v1/games?${params.toString()}`, { signal })
}

export function createGame(input: GameInput): Promise<Game> {
  return request<Game>('/api/v1/games', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function getGame(gameId: number, signal?: AbortSignal): Promise<Game> {
  return request<Game>(`/api/v1/games/${gameId}`, { signal })
}

export function updateGame(gameId: number, input: GameUpdateInput): Promise<Game> {
  return request<Game>(`/api/v1/games/${gameId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function archiveGame(gameId: number): Promise<void> {
  return request<void>(`/api/v1/games/${gameId}`, { method: 'DELETE' })
}

export function restoreGame(gameId: number): Promise<Game> {
  return request<Game>(`/api/v1/games/${gameId}/restore`, { method: 'POST' })
}

export function launchGame(gameId: number): Promise<void> {
  return request<void>(`/api/v1/games/${gameId}/launch`, { method: 'POST' })
}
