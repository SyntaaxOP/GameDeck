import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { archiveGame, deleteGamePermanently, listGames, restoreGame } from '@/api/games'
import { GameLibrary } from '@/features/games/game-library'
import type { Game } from '@/types/game'

vi.mock('@/api/settings', () => ({
  getTrackerStatus: vi.fn().mockResolvedValue({ active_game_ids: [] }),
}))

vi.mock('@/api/games', () => ({
  archiveGame: vi.fn(),
  createGame: vi.fn(),
  deleteGamePermanently: vi.fn(),
  listGames: vi.fn(),
  restoreGame: vi.fn(),
  updateGame: vi.fn(),
}))

const game: Game = {
  id: 1,
  title: 'Hades',
  platform: 'steam',
  executable_name: 'hades.exe',
  executable_path: 'C:\\Games\\Hades\\hades.exe',
  cover_path: null,
  genre: 'Action roguelike',
  status: 'backlog',
  priority: 2,
  personal_rating: null,
  notes: null,
  favorite: true,
  date_added: '2026-08-11T00:00:00',
  date_completed: null,
  archived_at: null,
  created_at: '2026-08-11T00:00:00',
  updated_at: '2026-08-11T00:00:00',
}

const mockedListGames = vi.mocked(listGames)
const mockedArchiveGame = vi.mocked(archiveGame)
const mockedRestoreGame = vi.mocked(restoreGame)
const mockedDeleteGame = vi.mocked(deleteGamePermanently)

describe('GameLibrary', () => {
  beforeEach(() => {
    mockedListGames.mockReset()
    mockedArchiveGame.mockReset()
    mockedRestoreGame.mockReset()
    mockedDeleteGame.mockReset()
    mockedListGames.mockResolvedValue({ items: [game], total: 1, page: 1, page_size: 12 })
    mockedArchiveGame.mockResolvedValue()
    mockedDeleteGame.mockResolvedValue()
  })

  it('permanently deletes only after explicit confirmation', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><GameLibrary /></MemoryRouter>)
    expect(await screen.findByText('Hades')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Delete' }))
    await user.click(screen.getByRole('button', { name: 'Delete permanently' }))
    await waitFor(() => expect(mockedDeleteGame).toHaveBeenCalledWith(1))
  })

  it('loads games and confirms archive without deleting history directly', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><GameLibrary /></MemoryRouter>)

    expect(await screen.findByText('Hades')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Archive' }))
    await user.click(screen.getByRole('button', { name: 'Archive game' }))

    await waitFor(() => expect(mockedArchiveGame).toHaveBeenCalledWith(1))
  })

  it('shows a designed empty state', async () => {
    mockedListGames.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 12 })
    render(<MemoryRouter><GameLibrary /></MemoryRouter>)

    expect(await screen.findByText('Your library is ready')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add your first game' })).toBeInTheDocument()
  })

  it('renders cached artwork through the game cover endpoint', async () => {
    mockedListGames.mockResolvedValue({
      items: [{ ...game, cover_path: 'C:\\Users\\player\\AppData\\Local\\GameDeck\\artwork\\hades.jpg' }],
      total: 1,
      page: 1,
      page_size: 12,
    })
    render(<MemoryRouter><GameLibrary /></MemoryRouter>)

    const artwork = await screen.findByRole('img', { name: 'Hades artwork' })
    expect(artwork).toHaveAttribute('src', '/api/v1/games/1/cover?v=hades.jpg')
  })
})
