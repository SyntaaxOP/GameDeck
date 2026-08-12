import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getSettings, getTrackerStatus, updateSettings } from '@/api/settings'
import { createBackup, getDiagnostics, listBackups } from '@/api/system'
import { SettingsPage } from '@/features/settings/settings-page'

vi.mock('@/api/settings', () => ({
  getSettings: vi.fn(),
  getTrackerStatus: vi.fn(),
  updateSettings: vi.fn(),
}))
vi.mock('@/api/system', () => ({ createBackup: vi.fn(), getDiagnostics: vi.fn(), listBackups: vi.fn() }))

const settings = {
  scan_interval_seconds: 5,
  restart_grace_seconds: 15,
  tracking_enabled: true,
  week_starts_on: 0,
  time_zone: 'UTC',
  time_zone_auto: false,
  theme: 'dark',
  currency_code: 'PHP',
  updated_at: '2026-08-11T08:00:00Z',
}

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.mocked(getSettings).mockResolvedValue(settings)
    vi.mocked(getTrackerStatus).mockResolvedValue({
      running: true,
      enabled: true,
      last_successful_scan_at: '2026-08-11T08:00:00Z',
      last_error: null,
      active_game_ids: [1],
      scan_interval_seconds: 5,
      restart_grace_seconds: 15,
    })
    vi.mocked(updateSettings).mockResolvedValue({ ...settings, tracking_enabled: false })
    vi.mocked(getDiagnostics).mockResolvedValue({
      database_path: 'C:\\GameDeck\\gamedeck.db', database_size_bytes: 4096, wal_size_bytes: 0,
      log_path: 'C:\\GameDeck\\logs\\gamedeck.log', log_size_bytes: 512,
      backup_directory: 'C:\\GameDeck\\backups', sqlite_busy_timeout_ms: 5000,
      database_journal_mode: 'wal', database_integrity: 'ok', database_probe_ms: 1.2,
      game_count: 3, session_count: 8, purchase_count: 2,
    })
    vi.mocked(listBackups).mockResolvedValue([])
    vi.mocked(createBackup).mockResolvedValue({ filename: 'gamedeck-test.db', path: 'C:\\GameDeck\\backups\\gamedeck-test.db', size_bytes: 4096, created_at: '2026-08-11T08:00:00Z', integrity_check: 'ok' })
  })

  it('shows health and saves tracking controls', async () => {
    const user = userEvent.setup()
    render(<SettingsPage />)

    expect(await screen.findByText('Games detected')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Automatic tracking' }))
    await user.click(screen.getByRole('button', { name: 'Save tracking settings' }))

    await waitFor(() => expect(updateSettings).toHaveBeenCalledWith(expect.objectContaining({ tracking_enabled: false })))
  })

  it('shows diagnostics and reports a verified backup', async () => {
    const user = userEvent.setup()
    render(<SettingsPage />)

    expect(await screen.findByText('3 games · 8 sessions · 2 purchases')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Create backup now' }))

    expect(await screen.findByText('Verified backup created: gamedeck-test.db')).toBeInTheDocument()
    expect(createBackup).toHaveBeenCalledOnce()
  })

  it('turns tracker failures into recovery guidance', async () => {
    vi.mocked(getTrackerStatus).mockResolvedValue({
      running: true, enabled: true, last_successful_scan_at: '2026-08-11T08:00:00Z',
      last_error: 'Windows process enumeration failed.', active_game_ids: [1],
      scan_interval_seconds: 5, restart_grace_seconds: 15,
    })
    render(<SettingsPage />)

    expect(await screen.findByText(/GameDeck is preserving active sessions/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Refresh status' })).toBeInTheDocument()
  })
})
