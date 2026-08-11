export function toDateTimeLocal(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

export function localInputToIso(value: string): string {
  return new Date(value).toISOString()
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null) return 'Running'
  const hours = Math.floor(seconds / 3_600)
  const minutes = Math.floor((seconds % 3_600) / 60)
  if (hours === 0) return `${minutes}m`
  return `${hours}h ${minutes}m`
}

export function inclusiveDateRange(from: string, to: string): { from?: string; to?: string } {
  const result: { from?: string; to?: string } = {}
  if (from) result.from = new Date(`${from}T00:00:00`).toISOString()
  if (to) {
    const exclusiveEnd = new Date(`${to}T00:00:00`)
    exclusiveEnd.setDate(exclusiveEnd.getDate() + 1)
    result.to = exclusiveEnd.toISOString()
  }
  return result
}
