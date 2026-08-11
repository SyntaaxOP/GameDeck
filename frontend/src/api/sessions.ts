import { ApiError } from '@/api/games'
import type {
  GameSession,
  ManualSessionInput,
  SessionList,
  SessionUpdateInput,
} from '@/types/session'

interface ErrorEnvelope {
  error?: { code?: string; message?: string; details?: unknown }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
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
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export interface SessionFilters {
  gameId?: number
  from?: string
  to?: string
  active?: boolean
  page?: number
  pageSize?: number
}

export function listSessions(
  filters: SessionFilters = {},
  signal?: AbortSignal,
): Promise<SessionList> {
  const params = new URLSearchParams({
    page: String(filters.page ?? 1),
    page_size: String(filters.pageSize ?? 25),
  })
  if (filters.gameId) params.set('game_id', String(filters.gameId))
  if (filters.from) params.set('from', filters.from)
  if (filters.to) params.set('to', filters.to)
  if (filters.active !== undefined) params.set('active', String(filters.active))
  return request<SessionList>(`/api/v1/sessions?${params.toString()}`, { signal })
}

export function createManualSession(input: ManualSessionInput): Promise<GameSession> {
  return request<GameSession>('/api/v1/sessions', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateSession(
  sessionId: number,
  input: SessionUpdateInput,
): Promise<GameSession> {
  return request<GameSession>(`/api/v1/sessions/${sessionId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function deleteSession(sessionId: number): Promise<void> {
  return request<void>(`/api/v1/sessions/${sessionId}`, { method: 'DELETE' })
}
import { apiUrl } from '@/lib/api-url'
