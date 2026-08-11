export interface FiveMServer {
  id: number
  name: string
  address: string
  connect_code: string | null
  discord_url: string | null
  notes: string | null
  favorite: boolean
  last_joined_at: string | null
  tracked_playtime_seconds: number
  created_at: string
  updated_at: string
}

export interface FiveMServerInput {
  name: string
  address: string
  connect_code: string | null
  discord_url: string | null
  notes: string | null
  favorite: boolean
  last_joined_at: string | null
  tracked_playtime_seconds: number
}

export interface FiveMServerList { items: FiveMServer[]; total: number }
