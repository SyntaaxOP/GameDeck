export interface BackupInfo {
  filename: string
  path: string
  size_bytes: number
  created_at: string
  integrity_check: string
}

export interface Diagnostics {
  database_path: string
  database_size_bytes: number
  wal_size_bytes: number
  log_path: string
  log_size_bytes: number
  backup_directory: string
  sqlite_busy_timeout_ms: number
  database_journal_mode: string
  database_integrity: string
  database_probe_ms: number
  game_count: number
  session_count: number
  purchase_count: number
}
