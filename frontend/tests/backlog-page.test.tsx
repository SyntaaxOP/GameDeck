import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { listGames, updateGame } from '@/api/games'
import { BacklogPage } from '@/features/backlog/backlog-page'
import type { Game, GameUpdateInput } from '@/types/game'

vi.mock('@/api/games', () => ({ listGames: vi.fn(), updateGame: vi.fn() }))

function game(overrides: Partial<Game>): Game {
  return {
    id: 1, title: 'Hades', platform: 'steam', executable_name: 'hades.exe', executable_path: null, cover_path: null,
    genre: null, status: 'backlog', priority: 1, personal_rating: null, notes: null, favorite: false,
    date_added: '2026-08-11T00:00:00Z', date_completed: null, archived_at: null, created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z',
    ...overrides,
  }
}

describe('BacklogPage', () => {
  let games: Game[]

  beforeEach(() => {
    games = [
      game({ id: 1, title: 'Favorite Later', executable_name: 'favorite.exe', favorite: true, priority: 5 }),
      game({ id: 2, title: 'First Priority', executable_name: 'first.exe', priority: 1 }),
      game({ id: 3, title: 'Paused Game', executable_name: 'paused.exe', status: 'paused', priority: 2 }),
    ]
    vi.mocked(listGames).mockReset().mockResolvedValue({ items: games, total: games.length, page: 1, page_size: 100 })
    vi.mocked(updateGame).mockReset().mockImplementation(async (gameId: number, input: GameUpdateInput) => {
      const current = games.find((item) => item.id === gameId)!
      const updated = { ...current, ...input, priority: input.status === 'completed' ? null : (input.priority === undefined ? current.priority : input.priority), updated_at: '2026-08-12T00:00:00Z' }
      games = games.map((item) => item.id === gameId ? updated : item)
      return updated
    })
  })

  it('uses play-next ordering and applies favorite and status actions', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><BacklogPage /></MemoryRouter>)

    expect(await screen.findByRole('heading', { name: 'Favorite Later' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Add First Priority to favorites' }))
    await waitFor(() => expect(updateGame).toHaveBeenCalledWith(2, { favorite: true }))
    expect(await screen.findByRole('heading', { name: 'First Priority' })).toBeInTheDocument()

    await user.click(screen.getByRole('combobox', { name: 'Priority for Paused Game' }))
    await user.click(await screen.findByRole('option', { name: 'Priority 4' }))
    await waitFor(() => expect(updateGame).toHaveBeenCalledWith(3, { priority: 4 }))

    await user.click(screen.getByRole('combobox', { name: 'Status for First Priority' }))
    await user.click(await screen.findByRole('option', { name: 'Completed', exact: true }))
    await waitFor(() => expect(updateGame).toHaveBeenCalledWith(2, { status: 'completed' }))
    expect(await screen.findByText('Finished games you can revisit.')).toBeInTheDocument()
  })

  it('shows a designed empty state', async () => {
    vi.mocked(listGames).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100 })
    render(<MemoryRouter><BacklogPage /></MemoryRouter>)
    expect(await screen.findByText('No games to organize yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open library' })).toBeInTheDocument()
  })
})
