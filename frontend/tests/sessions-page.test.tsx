import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { listGames } from '@/api/games'
import { listSessions } from '@/api/sessions'
import { SessionsPage } from '@/features/sessions/sessions-page'
import type { Game } from '@/types/game'
import type { GameSession } from '@/types/session'

vi.mock('@/api/games', () => ({ listGames: vi.fn() }))
vi.mock('@/api/sessions', () => ({
  createManualSession: vi.fn(),
  deleteSession: vi.fn(),
  listSessions: vi.fn(),
  updateSession: vi.fn(),
}))

const game = {
  id: 1,
  title: 'Hades',
  platform: 'steam',
  executable_name: 'hades.exe',
  executable_path: null,
  cover_path: null,
  genre: null,
  status: 'backlog',
  priority: null,
  personal_rating: null,
  notes: null,
  favorite: false,
  date_added: '2026-08-11T00:00:00',
  date_completed: null,
  archived_at: null,
  created_at: '2026-08-11T00:00:00',
  updated_at: '2026-08-11T00:00:00',
} satisfies Game

const session = {
  id: 5,
  game_id: 1,
  game_title: 'Hades',
  started_at: '2026-08-11T10:00:00Z',
  ended_at: '2026-08-11T12:00:00Z',
  last_seen_at: '2026-08-11T12:00:00Z',
  duration_seconds: 7_200,
  detection_method: 'manual',
  end_reason: 'manual',
  active: false,
  created_at: '2026-08-11T12:00:00Z',
  updated_at: '2026-08-11T12:00:00Z',
} satisfies GameSession

const mockedListGames = vi.mocked(listGames)
const mockedListSessions = vi.mocked(listSessions)

describe('SessionsPage', () => {
  beforeEach(() => {
    mockedListGames.mockReset()
    mockedListSessions.mockReset()
    mockedListGames.mockResolvedValue({ items: [game], total: 1, page: 1, page_size: 100 })
    mockedListSessions.mockResolvedValue({ items: [session], total: 1, page: 1, page_size: 25 })
  })

  it('renders auditable session history with formatted duration', async () => {
    render(<SessionsPage />)

    expect(await screen.findByText('Hades')).toBeInTheDocument()
    expect(screen.getByText('2h 0m')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit Hades session' })).toBeEnabled()
  })

  it('renders a useful empty state', async () => {
    mockedListSessions.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 25 })
    render(<SessionsPage />)

    expect(await screen.findByText('No sessions found')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add session' })).toBeInTheDocument()
  })
})
