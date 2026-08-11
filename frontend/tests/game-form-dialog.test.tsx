import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent, { PointerEventsCheckLevel } from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createGame, updateGame } from '@/api/games'
import { GameFormDialog } from '@/features/games/game-form-dialog'

vi.mock('@/api/games', () => ({
  createGame: vi.fn(),
  updateGame: vi.fn(),
}))

const mockedCreateGame = vi.mocked(createGame)
const mockedUpdateGame = vi.mocked(updateGame)

afterEach(() => {
  cleanup()
  document.body.replaceChildren()
  document.body.removeAttribute('style')
  document.body.removeAttribute('data-scroll-locked')
})

describe('GameFormDialog', () => {
  beforeEach(() => {
    mockedCreateGame.mockReset()
    mockedUpdateGame.mockReset()
  })

  it('submits a new game with optional fields represented consistently', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    const onSaved = vi.fn()
    const onOpenChange = vi.fn()
    mockedCreateGame.mockResolvedValue({} as never)

    render(
      <GameFormDialog
        game={null}
        open
        onOpenChange={onOpenChange}
        onSaved={onSaved}
      />,
    )

    await user.type(screen.getByLabelText('Title'), 'Hades')
    await user.type(screen.getByLabelText('Executable name'), 'Hades.exe')
    await user.click(screen.getByRole('button', { name: 'Add game' }))

    await waitFor(() => {
      expect(mockedCreateGame).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Hades',
          executable_name: 'Hades.exe',
          platform: 'steam',
          status: 'backlog',
          executable_path: null,
          priority: null,
          personal_rating: null,
          favorite: false,
        }),
      )
    })
    expect(onSaved).toHaveBeenCalledOnce()
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('keeps the dialog open and presents API errors', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    mockedCreateGame.mockRejectedValue(new Error('That executable is already assigned.'))

    render(
      <GameFormDialog game={null} open onOpenChange={vi.fn()} onSaved={vi.fn()} />,
    )

    await user.type(screen.getByLabelText('Title'), 'Hades')
    await user.type(screen.getByLabelText('Executable name'), 'Hades.exe')
    await user.click(screen.getByRole('button', { name: 'Add game' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'That executable is already assigned.',
    )
  })

  it('adds an executable alias to the submitted game', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    mockedCreateGame.mockResolvedValue({} as never)

    render(<GameFormDialog game={null} open onOpenChange={vi.fn()} onSaved={vi.fn()} />)

    await user.type(screen.getByLabelText('Title'), 'Hades')
    await user.type(screen.getByLabelText('Executable name'), 'Hades.exe')
    await user.click(screen.getByRole('button', { name: 'Add alias' }))
    await user.type(screen.getByLabelText('Alias 1 filename'), 'Hades-Win64-Shipping.exe')
    await user.type(
      screen.getByLabelText(/Exact path/),
      'C:\\Games\\Hades\\Hades-Win64-Shipping.exe',
    )
    await user.click(screen.getByRole('button', { name: 'Add game' }))

    await waitFor(() => {
      expect(mockedCreateGame).toHaveBeenCalledWith(
        expect.objectContaining({
          executable_aliases: [{
            executable_name: 'Hades-Win64-Shipping.exe',
            executable_path: 'C:\\Games\\Hades\\Hades-Win64-Shipping.exe',
          }],
        }),
      )
    })
  })
})
