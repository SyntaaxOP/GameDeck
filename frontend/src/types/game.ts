export const platforms = [
  'steam',
  'xbox',
  'epic',
  'fivem',
  'local',
  'emulator',
  'other',
] as const

export const libraryStatuses = [
  'currently_playing',
  'backlog',
  'completed',
  'completed_100',
  'dropped',
  'paused',
] as const

export type Platform = (typeof platforms)[number]
export type LibraryStatus = (typeof libraryStatuses)[number]
export type GameSort = 'title' | 'date_added' | 'updated_at' | 'status' | 'priority' | 'play_next'

export interface ExecutableAlias {
  id: number
  executable_name: string
  executable_path: string | null
  steam_app_id?: number | null
}

export interface ExecutableAliasInput {
  executable_name: string
  executable_path: string | null
}

export interface Game {
  id: number
  title: string
  platform: Platform
  executable_name: string
  executable_path: string | null
  steam_app_id?: number | null
  install_directory?: string | null
  discovered_at?: string | null
  executable_aliases: ExecutableAlias[]
  cover_path: string | null
  genre: string | null
  status: LibraryStatus
  priority: number | null
  personal_rating: number | null
  notes: string | null
  favorite: boolean
  date_added: string
  date_completed: string | null
  archived_at: string | null
  created_at: string
  updated_at: string
}

export interface GameInput {
  title: string
  platform: Platform
  executable_name: string
  executable_path: string | null
  executable_aliases: ExecutableAliasInput[]
  genre: string | null
  status: LibraryStatus
  priority: number | null
  personal_rating: number | null
  notes: string | null
  favorite: boolean
}

export type GameUpdateInput = Partial<GameInput>

export interface GameList {
  items: Game[]
  total: number
  page: number
  page_size: number
}

export const platformLabels: Record<Platform, string> = {
  steam: 'Steam',
  xbox: 'Xbox',
  epic: 'Epic Games',
  fivem: 'FiveM',
  local: 'Local',
  emulator: 'Emulator',
  other: 'Other',
}

export const statusLabels: Record<LibraryStatus, string> = {
  currently_playing: 'Currently playing',
  backlog: 'Backlog',
  completed: 'Completed',
  completed_100: '100% completed',
  dropped: 'Dropped',
  paused: 'Paused',
}
