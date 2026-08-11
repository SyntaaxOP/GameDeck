import { request } from '@/api/games'
import type { Game } from '@/types/game'

export interface DetectionReview { items: Game[]; total: number }
export interface IgnoredExecutable { id: number; executable_name: string; executable_path: string | null; created_at: string }
export interface IgnoredList { items: IgnoredExecutable[]; total: number }

export const getDetections = (signal?: AbortSignal) => request<DetectionReview>('/api/v1/detections', { signal })
export const confirmDetection = (gameId: number, title?: string) => request<Game>(`/api/v1/detections/${gameId}/confirm`, { method: 'POST', body: JSON.stringify({ title: title || null }) })
export const ignoreDetection = (gameId: number) => request<void>(`/api/v1/detections/${gameId}/ignore`, { method: 'POST' })
export const getIgnored = (signal?: AbortSignal) => request<IgnoredList>('/api/v1/detections/ignored', { signal })
export const removeIgnored = (ignoredId: number) => request<void>(`/api/v1/detections/ignored/${ignoredId}`, { method: 'DELETE' })
