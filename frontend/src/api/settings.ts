import { ApiError } from '@/api/games'
import type { AppSettings, SettingsUpdate, TrackerStatus } from '@/types/settings'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: { message?: string } }
    throw new ApiError(body.error?.message ?? `Request failed with status ${response.status}.`)
  }
  return response.json() as Promise<T>
}

export function getSettings(signal?: AbortSignal): Promise<AppSettings> {
  return request<AppSettings>('/api/v1/settings', { signal })
}

export function updateSettings(input: SettingsUpdate): Promise<AppSettings> {
  return request<AppSettings>('/api/v1/settings', { method: 'PATCH', body: JSON.stringify(input) })
}

export function getTrackerStatus(signal?: AbortSignal): Promise<TrackerStatus> {
  return request<TrackerStatus>('/api/v1/tracker/status', { signal })
}
import { apiUrl } from '@/lib/api-url'
