import { expect, test } from "vitest"

import { COUNTRIES, findCountry, findCountryByFlag } from "@/lib/countries"

test("lists ISO countries with emoji flags", () => {
  expect(COUNTRIES.length).toBeGreaterThan(190)
  const kenya = findCountry("KE")
  expect(kenya).toEqual({ iso2: "KE", name: "Kenya", flag: "🇰🇪" })
  const rwanda = COUNTRIES.find((country) => country.name === "Rwanda")
  expect(rwanda?.flag).toBe("🇷🇼")
  expect(findCountryByFlag("🇫🇷")?.iso2).toBe("FR")
})
