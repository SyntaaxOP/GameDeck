import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent, { PointerEventsCheckLevel } from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createManualSession, updateSession } from '@/api/sessions'
import { SessionFormDialog } from '@/features/sessions/session-form-dialog'
import type { Game } from '@/types/game'

vi.mock('@/api/sessions', () => ({
  createManualSession: vi.fn(),
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

const mockedCreate = vi.mocked(createManualSession)
const mockedUpdate = vi.mocked(updateSession)

afterEach(() => {
  cleanup()
  document.body.replaceChildren()
  document.body.removeAttribute('style')
  document.body.removeAttribute('data-scroll-locked')
})

describe('SessionFormDialog', () => {
  beforeEach(() => {
    mockedCreate.mockReset()
    mockedUpdate.mockReset()
  })

  it('submits a timezone-aware manual session for the selected game', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    const onSaved = vi.fn()
    mockedCreate.mockResolvedValue({} as never)
    render(<SessionFormDialog games={[game]} open session={null} onOpenChange={vi.fn()} onSaved={onSaved} />)

    await user.click(screen.getByRole('button', { name: 'Add session' }))

    await waitFor(() => expect(mockedCreate).toHaveBeenCalledOnce())
    expect(mockedCreate.mock.calls[0][0].game_id).toBe(1)
    expect(mockedCreate.mock.calls[0][0].started_at).toMatch(/Z$/)
    expect(mockedCreate.mock.calls[0][0].ended_at).toMatch(/Z$/)
    expect(onSaved).toHaveBeenCalledOnce()
  })

  it('shows an overlap error without closing the dialog', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    mockedCreate.mockRejectedValue(new Error('This session overlaps another session.'))
    render(<SessionFormDialog games={[game]} open session={null} onOpenChange={vi.fn()} onSaved={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: 'Add session' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('overlaps another session')
  })
})

