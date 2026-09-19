import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { SWRConfig } from "swr"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { MappingsPage } from "@/pages/mappings-page"

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  })
}

const kenyaMapping = {
  country_code: "KENYA",
  account_code: "2211102",
  account_label: "Contraceptives",
  sha_code: "HC.5.1",
  srhr_code: "SRHR.FP",
  confidence: "high",
  generic: false,
  notes: "Contraceptives and family planning commodities",
  mapped: true,
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
      if (url === "/api/mappings") {
        return jsonResponse({ items: [kenyaMapping] })
      }
      if (url.startsWith("/api/mappings?")) {
        return jsonResponse({ items: [kenyaMapping] })
      }
      return jsonResponse({ detail: `unhandled ${url}` }, 500)
    })
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function renderMappings() {
  return render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0, shouldRetryOnError: false }}>
      <MemoryRouter>
        <MappingsPage />
      </MemoryRouter>
    </SWRConfig>
  )
}

test("country filter uses API country names instead of hardcoded A/B/C", async () => {
  const user = userEvent.setup()
  renderMappings()
  await screen.findByRole("heading", { name: /chart-of-account maps/i })
  expect(await screen.findByText("2211102")).toBeInTheDocument()
  await user.click(screen.getByRole("combobox"))
  expect(await screen.findByText("🇰🇪 Kenya")).toBeInTheDocument()
  expect(screen.queryByText("Country A")).not.toBeInTheDocument()
  expect(screen.queryByText("Country B")).not.toBeInTheDocument()
  expect(screen.queryByText("Country C")).not.toBeInTheDocument()
  await user.click(screen.getByText("🇰🇪 Kenya"))
  await waitFor(() => {
    expect(fetch).toHaveBeenCalledWith("/api/mappings?country=KENYA")
  })
})

test("shows an empty state when no mappings exist", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url === "/api/countries") {
        return jsonResponse([])
      }
      if (url.startsWith("/api/mappings")) {
        return jsonResponse({ items: [] })
      }
      return jsonResponse({ detail: `unhandled ${url}` }, 500)
    })
  )
  renderMappings()
  expect(await screen.findByText(/no mappings/i)).toBeInTheDocument()
  expect(screen.getByText(/upload a country extract to populate country accounts/i)).toBeInTheDocument()
})
