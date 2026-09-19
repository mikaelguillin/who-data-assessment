import { expect, test } from "vitest"

import { formatCountryLabel, formatDate, formatDateTime } from "@/lib/format"

test("formats an ISO calendar date without a UTC day shift", () => {
  expect(formatDate("2024-03-19")).toBe("19 Mar 2024")
})

test("formats null and empty dates as an em dash", () => {
  expect(formatDate(null)).toBe("—")
  expect(formatDate(undefined)).toBe("—")
  expect(formatDate("")).toBe("—")
})

test("keeps unparseable date strings so analysts can still read them", () => {
  expect(formatDate("not-a-date")).toBe("not-a-date")
  expect(formatDateTime("yesterday")).toBe("yesterday")
})

test("formats an ISO datetime with hours and minutes", () => {
  const formatted = formatDateTime("2024-06-15T12:00:00+00:00")
  expect(formatted).toMatch(/15 Jun 2024/)
  expect(formatted).toMatch(/\d{2}:\d{2}/)
  expect(formatted).not.toContain("T12:00:00")
})


test("prefixes the country name with a flag when present", () => {
  expect(formatCountryLabel({ country_name: "Kenya" })).toBe("Kenya")
  expect(formatCountryLabel({ country_name: "Kenya", flag_emoji: null })).toBe("Kenya")
  expect(formatCountryLabel({ country_name: "Kenya", flag_emoji: "🇫🇷" })).toBe("🇫🇷 Kenya")
})
