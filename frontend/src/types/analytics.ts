import type { GameSession } from '@/types/session'

export type TimeBucket = 'day' | 'week' | 'month'
export type DistributionDimension = 'weekday' | 'hour'

export interface AnalyticsSummary {
  total_seconds: number
  session_count: number
  average_session_seconds: number
  longest_session_seconds: number
}

export interface GamePlaytime {
  game_id: number
  game_title: string
  total_seconds: number
  session_count: number
}

export interface SeriesPoint {
  bucket_start: string
  label: string
  total_seconds: number
}

export interface DistributionPoint {
  key: number
  label: string
  total_seconds: number
}

export interface DashboardAnalytics {
  at: string
  time_zone: string
  today_seconds: number
  week_seconds: number
  month_seconds: number
  lifetime: AnalyticsSummary
  top_game: GamePlaytime | null
  current_sessions: GameSession[]
  recent_sessions: GameSession[]
  daily_series: SeriesPoint[]
}

export interface PlaytimeAnalytics {
  from_at: string
  to_at: string
  time_zone: string
  bucket: TimeBucket
  summary: AnalyticsSummary
  series: SeriesPoint[]
  games: GamePlaytime[]
}

export interface DistributionAnalytics {
  from_at: string
  to_at: string
  time_zone: string
  dimension: DistributionDimension
  buckets: DistributionPoint[]
}

export interface GameAnalytics {
  game_id: number
  game_title: string
  from_at: string
  to_at: string
  time_zone: string
  summary: AnalyticsSummary
  daily_series: SeriesPoint[]
}
