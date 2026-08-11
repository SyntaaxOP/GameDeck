import { ApiError } from '@/api/games'
import type {
  DashboardAnalytics,
  DistributionAnalytics,
  DistributionDimension,
  GameAnalytics,
  PlaytimeAnalytics,
  TimeBucket,
} from '@/types/analytics'

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(apiUrl(path), { signal })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: { message?: string } }
    throw new ApiError(body.error?.message ?? `Request failed with status ${response.status}.`)
  }
  return response.json() as Promise<T>
}

function rangeParams(from: string, to: string, at: string): URLSearchParams {
  return new URLSearchParams({ from, to, at })
}

export function getDashboard(at: string, signal?: AbortSignal): Promise<DashboardAnalytics> {
  return request<DashboardAnalytics>(`/api/v1/analytics/dashboard?${new URLSearchParams({ at })}`, signal)
}

export function getPlaytime(
  from: string,
  to: string,
  bucket: TimeBucket,
  at: string,
  signal?: AbortSignal,
): Promise<PlaytimeAnalytics> {
  const params = rangeParams(from, to, at)
  params.set('bucket', bucket)
  return request<PlaytimeAnalytics>(`/api/v1/analytics/playtime?${params}`, signal)
}

export function getDistribution(
  from: string,
  to: string,
  dimension: DistributionDimension,
  at: string,
  signal?: AbortSignal,
): Promise<DistributionAnalytics> {
  const params = rangeParams(from, to, at)
  params.set('dimension', dimension)
  return request<DistributionAnalytics>(`/api/v1/analytics/distribution?${params}`, signal)
}

export function getGameAnalytics(
  gameId: number,
  from: string,
  to: string,
  at: string,
  signal?: AbortSignal,
): Promise<GameAnalytics> {
  return request<GameAnalytics>(`/api/v1/analytics/games/${gameId}?${rangeParams(from, to, at)}`, signal)
}
import { apiUrl } from '@/lib/api-url'
