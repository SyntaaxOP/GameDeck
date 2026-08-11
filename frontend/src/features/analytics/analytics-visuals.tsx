import { Link } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { formatDuration } from '@/lib/date-time'
import type { DistributionPoint, GamePlaytime, SeriesPoint } from '@/types/analytics'

export function TrendChart({ points, label }: { points: SeriesPoint[]; label: string }) {
  const maximum = Math.max(...points.map((point) => point.total_seconds), 1)
  return (
    <div className="space-y-3" role="img" aria-label={label}>
      <div className="flex h-52 items-end gap-2 border-b border-l px-3 pt-4">
        {points.map((point) => (
          <div key={point.bucket_start} className="group flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-2">
            <span className="sr-only">{point.label}: {formatDuration(point.total_seconds)}</span>
            <div
              className="w-full min-w-2 rounded-t-sm bg-primary/75 transition-colors group-hover:bg-primary"
              style={{ height: `${Math.max(point.total_seconds ? 6 : 1, (point.total_seconds / maximum) * 100)}%` }}
              title={`${point.label}: ${formatDuration(point.total_seconds)}`}
            />
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{points[0]?.label ?? 'Start'}</span><span>{points.at(-1)?.label ?? 'Now'}</span>
      </div>
    </div>
  )
}

export function DistributionBars({ points }: { points: DistributionPoint[] }) {
  const visible = points.filter((point) => point.total_seconds > 0)
  const maximum = Math.max(...visible.map((point) => point.total_seconds), 1)
  if (!visible.length) return <p className="py-10 text-center text-sm text-muted-foreground">No activity in this range.</p>
  return (
    <div className="space-y-3">
      {visible.map((point) => (
        <div key={point.key} className="grid grid-cols-[72px_1fr_auto] items-center gap-3 text-sm">
          <span className="truncate text-muted-foreground">{point.label}</span>
          <div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${(point.total_seconds / maximum) * 100}%` }} /></div>
          <span className="w-16 text-right font-mono text-xs">{formatDuration(point.total_seconds)}</span>
        </div>
      ))}
    </div>
  )
}

export function GameRanking({ games }: { games: GamePlaytime[] }) {
  if (!games.length) return <p className="py-10 text-center text-sm text-muted-foreground">No games played in this range.</p>
  return (
    <ol className="divide-y">
      {games.slice(0, 8).map((game, index) => (
        <li key={game.game_id} className="flex items-center gap-3 py-3">
          <Badge variant="outline" className="size-7 justify-center rounded-full p-0">{index + 1}</Badge>
          <Link className="min-w-0 flex-1 truncate font-medium hover:text-primary" to={`/games/${game.game_id}`}>{game.game_title}</Link>
          <span className="font-mono text-sm">{formatDuration(game.total_seconds)}</span>
        </li>
      ))}
    </ol>
  )
}
