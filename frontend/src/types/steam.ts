export interface SteamInstalledGame {
  app_id: number
  name: string
  install_directory: string
  already_imported: boolean
  tracking_ready: boolean
}

export interface SteamLocalLibrary {
  steam_path: string | null
  library_paths: string[]
  games: SteamInstalledGame[]
  total: number
}

export interface SteamLocalSync {
  discovered: number
  imported_game_ids: number[]
  updated_game_ids: number[]
}

export interface SteamGamePreview {
  app_id: number
  name: string
  playtime_minutes: number
  already_imported: boolean
}

export interface SteamPreview {
  steam_id: string
  games: SteamGamePreview[]
  total: number
}

export interface SteamConfiguration {
  configured: boolean
  steam_id: string | null
}
