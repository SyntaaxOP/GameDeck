export type DetectionMethod = 'process' | 'manual' | 'recovered'
export type EndReason = 'process_stopped' | 'tracker_shutdown' | 'recovered' | 'manual'

export interface GameSession {
  id: number
  game_id: number
  game_title: string
  started_at: string
  ended_at: string | null
  last_seen_at: string
  duration_seconds: number | null
  detection_method: DetectionMethod
  end_reason: EndReason | null
  active: boolean
  created_at: string
  updated_at: string
}

export interface SessionList {
  items: GameSession[]
  total: number
  page: number
  page_size: number
}

export interface ManualSessionInput {
  game_id: number
  started_at: string
  ended_at: string
}

export interface SessionUpdateInput {
  started_at: string
  ended_at: string
}

