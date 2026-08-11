import { ApiError } from '@/api/games'
import { apiUrl } from '@/lib/api-url'
import type { FiveMServer, FiveMServerInput, FiveMServerList } from '@/types/fivem'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: { message?: string; code?: string } }
    throw new ApiError(body.error?.message ?? `Request failed with status ${response.status}.`, body.error?.code)
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}

export const listFiveMServers = (signal?: AbortSignal) => request<FiveMServerList>('/api/v1/fivem/servers', { signal })
export const createFiveMServer = (input: FiveMServerInput) => request<FiveMServer>('/api/v1/fivem/servers', { method: 'POST', body: JSON.stringify(input) })
export const updateFiveMServer = (id: number, input: Partial<FiveMServerInput>) => request<FiveMServer>(`/api/v1/fivem/servers/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const markFiveMServerJoined = (id: number) => request<FiveMServer>(`/api/v1/fivem/servers/${id}/joined`, { method: 'POST' })
export const deleteFiveMServer = (id: number) => request<void>(`/api/v1/fivem/servers/${id}`, { method: 'DELETE' })
