import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { getDashboard } from '@/api/analytics'
import { getTrackerStatus } from '@/api/settings'
import { DashboardPage } from '@/features/analytics/dashboard-page'
import type { DashboardAnalytics } from '@/types/analytics'

vi.mock('@/api/analytics', () => ({ getDashboard: vi.fn() }))
vi.mock('@/api/settings', () => ({ getTrackerStatus: vi.fn() }))

const dashboard: DashboardAnalytics = {
  at: '2026-08-11T08:00:00Z',
  time_zone: 'Asia/Shanghai',
  today_seconds: 3600,
  week_seconds: 7200,
  month_seconds: 10800,
  lifetime: { total_seconds: 10800, session_count: 2, average_session_seconds: 5400, longest_session_seconds: 7200 },
  top_game: { game_id: 1, game_title: 'Hades', total_seconds: 10800, session_count: 2 },
  current_sessions: [],
  recent_sessions: [{
    id: 1, game_id: 1, game_title: 'Hades', started_at: '2026-08-11T01:00:00Z', ended_at: '2026-08-11T02:00:00Z', last_seen_at: '2026-08-11T02:00:00Z', duration_seconds: 3600, detection_method: 'manual', end_reason: 'manual', active: false, created_at: '2026-08-11T02:00:00Z', updated_at: '2026-08-11T02:00:00Z',
  }],
  daily_series: [{ bucket_start: '2026-08-11T00:00:00Z', label: 'Aug 11', total_seconds: 3600 }],
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(getDashboard).mockReset().mockResolvedValue(dashboard)
    vi.mocked(getTrackerStatus).mockReset().mockResolvedValue({ running: true, enabled: true, last_successful_scan_at: '2026-08-11T08:00:00Z', last_error: null, active_game_ids: [], scan_interval_seconds: 5, restart_grace_seconds: 15 })
  })

  it('renders populated cards, trend, and recent play', async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('This week')).toBeInTheDocument()
    expect(screen.getAllByText('Hades').length).toBeGreaterThan(0)
    expect(screen.getByRole('img', { name: 'Daily playtime for the last seven days' })).toBeInTheDocument()
  })

  it('renders a designed empty state', async () => {
    vi.mocked(getDashboard).mockResolvedValue({ ...dashboard, lifetime: { ...dashboard.lifetime, total_seconds: 0 }, top_game: null, recent_sessions: [], daily_series: [] })
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('Your dashboard is ready')).toBeInTheDocument()
  })

  it('keeps analytics visible when tracker status fails', async () => {
    vi.mocked(getTrackerStatus).mockRejectedValue(new Error('Tracker unavailable'))
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('Tracker issue')).toBeInTheDocument()
    expect(screen.getAllByText('This month').length).toBeGreaterThan(0)
  })
})
