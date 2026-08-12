import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { FiveMPage } from '@/features/fivem/fivem-page'
import { GameNightsPage } from '@/features/game-nights/game-nights-page'
import { PCPage } from '@/features/pc/pc-page'
import { SteamImportPage } from '@/features/steam/steam-import-page'

vi.mock('@/api/fivem', () => ({ listFiveMServers: vi.fn().mockResolvedValue({ items: [], total: 0 }), createFiveMServer: vi.fn(), updateFiveMServer: vi.fn(), deleteFiveMServer: vi.fn(), markFiveMServerJoined: vi.fn() }))
vi.mock('@/api/game-nights', () => ({ listGameNights: vi.fn().mockResolvedValue({ items: [], total: 0 }), createGameNight: vi.fn(), updateGameNight: vi.fn(), deleteGameNight: vi.fn(), getDiscordAnnouncement: vi.fn() }))
vi.mock('@/api/games', () => ({ listGames: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100 }), ApiError: class extends Error {} }))
vi.mock('@/api/steam', () => ({
  getLocalSteamLibrary: vi.fn().mockResolvedValue({
    steam_path: 'C:\\Program Files (x86)\\Steam',
    library_paths: ['C:\\Program Files (x86)\\Steam'],
    games: [{ app_id: 1145360, name: 'Hades', install_directory: 'D:\\SteamLibrary\\Hades', already_imported: true, tracking_ready: true }],
    total: 1,
  }),
  syncLocalSteamLibrary: vi.fn(),
}))
vi.mock('@/api/pc', () => ({ getPCProfile: vi.fn().mockResolvedValue(null), getPCSnapshot: vi.fn().mockResolvedValue({ operating_system: 'Windows 11', cpu_label: 'Test CPU', gpu_label: 'Test GPU', motherboard: 'Test Board', logical_cpu_count: 16, memory_gb: 32, total_storage_gb: 1500, storage_volumes: [{ name: 'C:', total_gb: 500 }, { name: 'D:', total_gb: 1000 }] }), savePCProfile: vi.fn() }))

afterEach(() => cleanup())

describe('optional integration pages', () => {
  it('renders the FiveM empty state', async () => { render(<FiveMPage />); expect(await screen.findByText('No FiveM servers saved')).toBeVisible() })
  it('renders the game-night empty state', async () => { render(<GameNightsPage />); expect(await screen.findByText('No game nights planned')).toBeVisible() })
  it('renders automatic local Steam discovery without credentials', async () => { render(<SteamImportPage />); expect(await screen.findByText('Steam detected')).toBeVisible(); expect(screen.getByText('Hades')).toBeVisible(); expect(screen.getByText('Tracking ready')).toBeVisible() })
  it('renders the read-only PC snapshot', async () => { render(<PCPage />); expect(await screen.findByText('Windows 11')).toBeVisible(); expect(screen.getByText('32 GB')).toBeVisible() })
})
