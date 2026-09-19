import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { SWRConfig } from "swr"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { TransactionsPage } from "@/pages/transactions-page"

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  })
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url === "/api/countries") {
        return jsonResponse([
          {
            country_code: "KENYA",
            country_name: "Kenya",
            primary_currency: "KES",
            language: "en",
            flag_emoji: "🇰🇪",
          },
        ])
      }
      if (url.startsWith("/api/expenditures")) {
        return jsonResponse({ total: 0, limit: 25, offset: 0, items: [] })
      }
      return jsonResponse({ detail: `unhandled ${url}` }, 500)
    })
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

test("country filter uses API country names instead of hardcoded A/B/C", async () => {
  const user = userEvent.setup()
  render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0, shouldRetryOnError: false }}>
      <MemoryRouter>
        <TransactionsPage />
      </MemoryRouter>
    </SWRConfig>
  )
  await screen.findByRole("heading", { name: /transactions/i })
  const countryTrigger = screen.getAllByRole("combobox")[0]
  await user.click(countryTrigger)
  expect(await screen.findByText("🇰🇪 Kenya")).toBeInTheDocument()
  expect(screen.queryByText("Country A")).not.toBeInTheDocument()
  expect(screen.queryByText("Country B")).not.toBeInTheDocument()
  expect(screen.queryByText("Country C")).not.toBeInTheDocument()
})
