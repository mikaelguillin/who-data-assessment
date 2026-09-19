import { expect, test } from "vitest"

import { formatCountryLabel } from "@/lib/format"

test("prefixes the country name with a flag when present", () => {
  expect(formatCountryLabel({ country_name: "Kenya" })).toBe("Kenya")
  expect(formatCountryLabel({ country_name: "Kenya", flag_emoji: null })).toBe("Kenya")
  expect(formatCountryLabel({ country_name: "Kenya", flag_emoji: "🇫🇷" })).toBe("🇫🇷 Kenya")
})
