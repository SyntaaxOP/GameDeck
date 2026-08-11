import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { AppShell } from '@/components/app-shell'

describe('AppShell accessibility', () => {
  it('provides skip navigation and a focusable main landmark', () => {
    render(<MemoryRouter><AppShell><h1>Page content</h1></AppShell></MemoryRouter>)

    expect(screen.getByRole('link', { name: 'Skip to main content' })).toHaveAttribute('href', '#main-content')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content')
    expect(screen.getByRole('main')).toHaveAttribute('tabindex', '-1')
  })
})
