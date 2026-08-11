export interface AppSettings {
  scan_interval_seconds: number
  restart_grace_seconds: number
  tracking_enabled: boolean
  week_starts_on: number
  time_zone: string
  theme: string
  currency_code: string
  updated_at: string
}

export interface TrackerStatus {
  running: boolean
  enabled: boolean
  last_successful_scan_at: string | null
  last_error: string | null
  active_game_ids: number[]
  scan_interval_seconds: number
  restart_grace_seconds: number
}

export type SettingsUpdate = Partial<Pick<AppSettings,
  'scan_interval_seconds' | 'restart_grace_seconds' | 'tracking_enabled'>>
