import { ApiError } from '@/api/games'
import type {
  GameSpending,
  Purchase,
  PurchaseInput,
  PurchaseList,
  PurchaseUpdateInput,
  SpendingSummary,
} from '@/types/purchase'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: { code?: string; message?: string } }
    throw new ApiError(
      body.error?.message ?? `Request failed with status ${response.status}.`,
      body.error?.code,
    )
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function listPurchases(
  options: { gameId?: number; unassigned?: boolean; page?: number; pageSize?: number } = {},
  signal?: AbortSignal,
): Promise<PurchaseList> {
  const params = new URLSearchParams({
    page: String(options.page ?? 1),
    page_size: String(options.pageSize ?? 50),
  })
  if (options.gameId) params.set('game_id', String(options.gameId))
  if (options.unassigned) params.set('unassigned', 'true')
  return request<PurchaseList>(`/api/v1/purchases?${params.toString()}`, { signal })
}

export function createPurchase(input: PurchaseInput): Promise<Purchase> {
  return request<Purchase>('/api/v1/purchases', { method: 'POST', body: JSON.stringify(input) })
}

export function updatePurchase(id: number, input: PurchaseUpdateInput): Promise<Purchase> {
  return request<Purchase>(`/api/v1/purchases/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
}

export function deletePurchase(id: number): Promise<void> {
  return request<void>(`/api/v1/purchases/${id}`, { method: 'DELETE' })
}

export function getSpendingSummary(signal?: AbortSignal): Promise<SpendingSummary> {
  return request<SpendingSummary>('/api/v1/spending/summary', { signal })
}

export function getGameSpending(gameId: number, signal?: AbortSignal): Promise<GameSpending> {
  return request<GameSpending>(`/api/v1/spending/games/${gameId}`, { signal })
}
import { apiUrl } from '@/lib/api-url'
