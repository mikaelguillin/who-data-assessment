export function formatAmount(amount: number | null | undefined, currency: string): string {
  if (amount == null) return "—"
  try {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(amount)
  } catch {
    return `${amount.toLocaleString()} ${currency}`
  }
}

export function formatShare(value: number): string {
  return `${Math.round(value * 100)}%`
}
