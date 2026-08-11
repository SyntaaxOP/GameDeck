import { Edit3, Radio, Trash2 } from 'lucide-react'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatDateTime, formatDuration } from '@/lib/date-time'
import type { GameSession } from '@/types/session'

interface SessionTableProps {
  sessions: GameSession[]
  busySessionId: number | null
  showGame?: boolean
  onEdit: (session: GameSession) => void
  onDelete: (session: GameSession) => void
}

export function SessionTable({
  sessions,
  busySessionId,
  showGame = true,
  onEdit,
  onDelete,
}: SessionTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            {showGame ? <TableHead>Game</TableHead> : null}
            <TableHead>Started</TableHead>
            <TableHead>Ended</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Source</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.map((session) => (
            <TableRow key={session.id}>
              {showGame ? <TableCell className="font-medium">{session.game_title}</TableCell> : null}
              <TableCell className="whitespace-nowrap">{formatDateTime(session.started_at)}</TableCell>
              <TableCell className="whitespace-nowrap">{session.ended_at ? formatDateTime(session.ended_at) : <Badge><Radio className="animate-pulse" aria-hidden="true" /> Running</Badge>}</TableCell>
              <TableCell className="font-mono text-xs">{formatDuration(session.duration_seconds)}</TableCell>
              <TableCell><Badge variant="outline" className="capitalize">{session.detection_method}</Badge></TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  <Button variant="ghost" size="icon-sm" aria-label={`Edit ${session.game_title} session`} disabled={session.active || busySessionId === session.id} onClick={() => onEdit(session)}>
                    <Edit3 aria-hidden="true" />
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="ghost" size="icon-sm" aria-label={`Delete ${session.game_title} session`} disabled={session.active || busySessionId === session.id}>
                        <Trash2 aria-hidden="true" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete this session?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This permanently removes {formatDuration(session.duration_seconds)} from {session.game_title}. This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction variant="destructive" onClick={() => onDelete(session)}>Delete session</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
