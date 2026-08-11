export type PurchaseKind = 'base_game' | 'dlc' | 'subscription' | 'other'

export interface Purchase {
  id: number
  game_id: number | null
  game_title: string | null
  kind: PurchaseKind
  amount_minor: number
  currency_code: string
  purchased_on: string | null
  platform: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PurchaseInput {
  game_id: number | null
  kind: PurchaseKind
  amount_minor: number
  currency_code: string
  purchased_on: string | null
  platform: string | null
  notes: string | null
}

export type PurchaseUpdateInput = Partial<PurchaseInput>

export interface PurchaseList {
  items: Purchase[]
  total: number
  page: number
  page_size: number
}

export interface CurrencySpending {
  currency_code: string
  amount_minor: number
  purchase_count: number
  attributed_amount_minor: number
  played_seconds: number
  cost_per_hour_minor: number | null
}

export interface SpendingSummary {
  currencies: CurrencySpending[]
  unassigned_purchase_count: number
}

export interface GameSpending {
  game_id: number
  game_title: string
  played_seconds: number
  purchase_count: number
  currencies: CurrencySpending[]
}

export const purchaseKindLabels: Record<PurchaseKind, string> = {
  base_game: 'Base game',
  dlc: 'DLC',
  subscription: 'Subscription',
  other: 'Other',
}
