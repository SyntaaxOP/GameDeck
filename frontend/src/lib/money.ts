export function currencyFractionDigits(currencyCode: string): number {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currencyCode,
    }).resolvedOptions().maximumFractionDigits ?? 2
  } catch {
    return 2
  }
}

export function formatMoney(amountMinor: number, currencyCode: string): string {
  const divisor = 10 ** currencyFractionDigits(currencyCode)
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currencyCode,
    }).format(amountMinor / divisor)
  } catch {
    return `${currencyCode} ${(amountMinor / divisor).toFixed(2)}`
  }
}

export function minorToInput(amountMinor: number, currencyCode: string): string {
  const digits = currencyFractionDigits(currencyCode)
  return (amountMinor / 10 ** digits).toFixed(digits)
}

export function inputToMinor(value: string, currencyCode: string): number | null {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed < 0) return null
  return Math.round(parsed * 10 ** currencyFractionDigits(currencyCode))
}
