const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/

function parseDateValue(value: string): Date | null {
  const dateOnly = DATE_ONLY.exec(value)
  if (dateOnly) {
    const year = Number(dateOnly[1])
    const month = Number(dateOnly[2])
    const day = Number(dateOnly[3])
    const parsed = new Date(year, month - 1, day)
    if (parsed.getFullYear() !== year || parsed.getMonth() !== month - 1 || parsed.getDate() !== day) {
      return null
    }
    return parsed
  }
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function formatWith(value: string | null | undefined, options: Intl.DateTimeFormatOptions): string {
  if (value == null || value === "") return "—"
  const parsed = parseDateValue(value)
  if (!parsed) return value
  return new Intl.DateTimeFormat("en-GB", options).format(parsed)
}

export function formatDate(value: string | null | undefined): string {
  return formatWith(value, { day: "numeric", month: "short", year: "numeric" })
}

export function formatDateTime(value: string | null | undefined): string {
  return formatWith(value, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
}

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

export function formatCountryLabel(country: {
  country_name: string
  flag_emoji?: string | null
}): string {
  return country.flag_emoji ? `${country.flag_emoji} ${country.country_name}` : country.country_name
}
