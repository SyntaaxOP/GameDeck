import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { getDistribution, getPlaytime } from '@/api/analytics'
import { AnalyticsPage } from '@/features/analytics/analytics-page'

vi.mock('@/api/analytics', () => ({ getDistribution: vi.fn(), getPlaytime: vi.fn() }))

describe('AnalyticsPage', () => {
  beforeEach(() => {
    vi.mocked(getPlaytime).mockReset().mockResolvedValue({
      from_at: '2026-07-11T00:00:00Z', to_at: '2026-08-11T00:00:00Z', time_zone: 'UTC', bucket: 'day',
      summary: { total_seconds: 7200, session_count: 2, average_session_seconds: 3600, longest_session_seconds: 5400 },
      series: [{ bucket_start: '2026-08-10T00:00:00Z', label: 'Aug 10', total_seconds: 7200 }],
      games: [{ game_id: 1, game_title: 'Hades', total_seconds: 7200, session_count: 2 }],
    })
    vi.mocked(getDistribution).mockReset().mockImplementation(async (_from, _to, dimension) => ({
      from_at: '2026-07-11T00:00:00Z', to_at: '2026-08-11T00:00:00Z', time_zone: 'UTC', dimension,
      buckets: [{ key: 0, label: dimension === 'weekday' ? 'Monday' : '12 AM', total_seconds: 7200 }],
    }))
  })

  it('shows summaries, ranking, and refreshes for a range preset', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><AnalyticsPage /></MemoryRouter>)
    expect(await screen.findByText('Total playtime')).toBeInTheDocument()
    expect(screen.getByText('Top games')).toBeInTheDocument()
    expect(screen.getByText('Hades')).toBeInTheDocument()
    expect(screen.getByText('Your gaming FAQ')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '7 days' }))
    expect(await screen.findByRole('img', { name: 'Playtime over the last 7 days' })).toBeInTheDocument()
  })
})
