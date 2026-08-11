import { AppShell } from '@/components/app-shell'
import { DetectionNotifier } from '@/components/detection-notifier'
import { AnalyticsPage } from '@/features/analytics/analytics-page'
import { DashboardPage } from '@/features/analytics/dashboard-page'
import { BacklogPage } from '@/features/backlog/backlog-page'
import { GameDetailPage } from '@/features/games/game-detail-page'
import { GameLibrary } from '@/features/games/game-library'
import { FiveMPage } from '@/features/fivem/fivem-page'
import { GameNightsPage } from '@/features/game-nights/game-nights-page'
import { DetectionReviewPage } from '@/features/detections/detection-review-page'
import { SteamImportPage } from '@/features/steam/steam-import-page'
import { PCPage } from '@/features/pc/pc-page'
import { SessionsPage } from '@/features/sessions/sessions-page'
import { SettingsPage } from '@/features/settings/settings-page'
import { SpendingPage } from '@/features/spending/spending-page'
import { Navigate, Route, Routes } from 'react-router-dom'

export default function App() {
  return (
    <AppShell>
      <DetectionNotifier />
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/backlog" element={<BacklogPage />} />
        <Route path="/library" element={<GameLibrary />} />
        <Route path="/detections" element={<DetectionReviewPage />} />
        <Route path="/games/:gameId" element={<GameDetailPage />} />
        <Route path="/fivem" element={<FiveMPage />} />
        <Route path="/game-nights" element={<GameNightsPage />} />
        <Route path="/steam-import" element={<SteamImportPage />} />
        <Route path="/pc" element={<PCPage />} />
        <Route path="/sessions" element={<SessionsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/spending" element={<SpendingPage />} />
        <Route path="*" element={<Navigate to="/library" replace />} />
      </Routes>
    </AppShell>
  )
}
