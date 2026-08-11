import { useEffect, useRef } from 'react'
import { getDetections } from '@/api/detections'
import { notify } from '@/lib/desktop'

export function DetectionNotifier() {
  const notified = useRef(new Set<number>())
  useEffect(() => {
    const controller = new AbortController()
    const refresh = async () => {
      try {
        const result = await getDetections(controller.signal)
        for (const game of result.items) {
          if (notified.current.has(game.id)) continue
          notified.current.add(game.id)
          await notify('Game detected', `${game.title} is ready for review in GameDeck.`)
        }
      } catch { /* transient polling failures are surfaced elsewhere */ }
    }
    void refresh()
    const interval = window.setInterval(() => void refresh(), 5_000)
    return () => { controller.abort(); window.clearInterval(interval) }
  }, [])
  return null
}
