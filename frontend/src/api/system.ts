import { ApiError } from '@/api/games'
import type { BackupInfo, Diagnostics } from '@/types/system'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), init)
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: { message?: string } }
    throw new ApiError(body.error?.message ?? `Request failed with status ${response.status}.`)
  }
  return response.json() as Promise<T>
}

export function getDiagnostics(signal?: AbortSignal): Promise<Diagnostics> {
  return request<Diagnostics>('/api/v1/system/diagnostics', { signal })
}

export function listBackups(signal?: AbortSignal): Promise<BackupInfo[]> {
  return request<BackupInfo[]>('/api/v1/system/backups', { signal })
}

export function createBackup(): Promise<BackupInfo> {
  return request<BackupInfo>('/api/v1/system/backups', { method: 'POST' })
}
import { apiUrl } from '@/lib/api-url'
