import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent, { PointerEventsCheckLevel } from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { listGames } from '@/api/games'
import { createPurchase, deletePurchase, getSpendingSummary, listPurchases, updatePurchase } from '@/api/purchases'
import { getSettings } from '@/api/settings'
import { SpendingPage } from '@/features/spending/spending-page'
import type { Game } from '@/types/game'
import type { Purchase } from '@/types/purchase'

vi.mock('@/api/games', () => ({ listGames: vi.fn() }))
vi.mock('@/api/settings', () => ({ getSettings: vi.fn() }))
vi.mock('@/api/purchases', () => ({
  createPurchase: vi.fn(),
  deletePurchase: vi.fn(),
  getSpendingSummary: vi.fn(),
  listPurchases: vi.fn(),
  updatePurchase: vi.fn(),
}))

const game = {
  id: 1, title: 'Hades II', platform: 'steam', executable_name: 'hades2.exe', executable_path: null, cover_path: null,
  genre: null, status: 'currently_playing', priority: 1, personal_rating: 9, notes: null, favorite: true,
  date_added: '2026-08-11T00:00:00Z', date_completed: null, archived_at: null, created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z',
} satisfies Game

const purchase = {
  id: 10,
  game_id: 1,
  game_title: 'Hades II',
  kind: 'base_game',
  amount_minor: 59_900,
  currency_code: 'PHP',
  purchased_on: '2026-08-01',
  platform: 'Steam',
  notes: 'Early access',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z',
} satisfies Purchase

const settings = {
  scan_interval_seconds: 5, restart_grace_seconds: 15, tracking_enabled: true,
  week_starts_on: 0, time_zone: 'UTC', theme: 'dark', currency_code: 'PHP', updated_at: '2026-08-11T00:00:00Z',
}

afterEach(() => {
  cleanup()
  document.body.replaceChildren()
  document.body.removeAttribute('style')
  document.body.removeAttribute('data-scroll-locked')
})

describe('SpendingPage', () => {
  beforeEach(() => {
    vi.mocked(listGames).mockReset().mockResolvedValue({ items: [game], total: 1, page: 1, page_size: 100 })
    vi.mocked(listPurchases).mockReset().mockResolvedValue({ items: [purchase], total: 1, page: 1, page_size: 100 })
    vi.mocked(getSpendingSummary).mockReset().mockResolvedValue({
      currencies: [{ currency_code: 'PHP', amount_minor: 59_900, purchase_count: 1, attributed_amount_minor: 59_900, played_seconds: 36_000, cost_per_hour_minor: 5_990 }],
      unassigned_purchase_count: 0,
    })
    vi.mocked(getSettings).mockReset().mockResolvedValue(settings)
    vi.mocked(createPurchase).mockReset().mockResolvedValue(purchase)
    vi.mocked(updatePurchase).mockReset().mockResolvedValue(purchase)
    vi.mocked(deletePurchase).mockReset().mockResolvedValue()
  })

  it('shows separate-currency totals and creates a minor-unit purchase', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    render(<SpendingPage />)

    expect(await screen.findByText('PHP total')).toBeInTheDocument()
    expect(screen.getAllByText((content) => content.includes('599.00')).length).toBeGreaterThan(0)
    expect(screen.getByText((content) => content.includes('59.90 per played hour'))).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Add purchase' }))
    await user.type(screen.getByLabelText('Amount'), '49.99')
    const submitButtons = screen.getAllByRole('button', { name: 'Add purchase' })
    await user.click(submitButtons.at(-1)!)

    await waitFor(() => expect(createPurchase).toHaveBeenCalledOnce())
    expect(createPurchase).toHaveBeenCalledWith(expect.objectContaining({
      amount_minor: 4_999,
      currency_code: 'PHP',
      game_id: null,
    }))
  })

  it('requires explicit confirmation before deleting a ledger entry', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    render(<SpendingPage />)

    await user.click(await screen.findByRole('button', { name: 'Delete Base game purchase' }))
    expect(screen.getByText('Delete this purchase?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Delete purchase' }))
    await waitFor(() => expect(deletePurchase).toHaveBeenCalledWith(10))
  })
})
