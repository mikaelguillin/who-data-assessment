import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { SWRConfig } from "swr"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { OverviewPage } from "@/pages/overview-page"
import { chooseFile } from "@/test/choose-file"
import { chooseFlag } from "@/test/choose-flag"
import type { OverviewOut } from "@/types"

const emptyOverview: OverviewOut = {
  expenditure_count: 0,
  review_count: 0,
  review_share: 0,
  countries: [],
  by_sha: [],
  by_srhr: [],
  by_confidence: [],
  by_flag: [],
  spend_by_currency: [],
}

const populatedOverview: OverviewOut = {
  ...emptyOverview,
  expenditure_count: 1,
  countries: [
    {
      country_code: "KENYA",
      country_name: "Kenya",
      flag_emoji: "🇫🇷",
      record_count: 1,
      review_count: 0,
      currencies: [{ currency: "KES", amount: 100, count: 1 }],
    },
  ],
}

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  })
}

let ingested = false

beforeEach(() => {
  ingested = false
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url === "/api/overview") {
        return jsonResponse(ingested ? populatedOverview : emptyOverview)
      }
      if (url === "/api/ingest" && init?.method === "POST") {
        ingested = true
        return jsonResponse({
          country_code: "KENYA",
          country_name: "Kenya",
          flag_emoji: "🇫🇷",
          source_filename: "kenya.csv",
          source_format: "csv",
          layout_id: "csv_a",
          record_count: 1,
          flag_count: 0,
          classification_count: 1,
          replaced: false,
        })
      }
      if (url === "/api/countries") {
        return jsonResponse(
          ingested
            ? [{ country_code: "KENYA", country_name: "Kenya", primary_currency: "KES", language: "en", flag_emoji: "🇫🇷" }]
            : []
        )
      }
      return jsonResponse({ detail: `unhandled ${url}` }, 500)
    })
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function renderOverview() {
  return render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0, shouldRetryOnError: false }}>
      <MemoryRouter>
        <OverviewPage />
      </MemoryRouter>
    </SWRConfig>
  )
}

test("shows an error when overview cannot be loaded", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => jsonResponse({ detail: "down" }, 500))
  )
  renderOverview()
  expect(await screen.findByRole("alert")).toHaveTextContent(/could not load overview/i)
})

test("shows an empty state with the upload form", async () => {
  renderOverview()
  expect(await screen.findByText(/no countries ingested yet/i)).toBeInTheDocument()
  expect(screen.getByRole("button", { name: /upload extract/i })).toBeInTheDocument()
  expect(screen.queryByText(/countries a, b and c/i)).not.toBeInTheDocument()
})

test("shows the ingested country after a successful upload", async () => {
  const user = userEvent.setup()
  renderOverview()
  await screen.findByText(/no countries ingested yet/i)
  const file = new File(["TXN_ID,ACCOUNT_CODE,AMOUNT_KES,DATE\n"], "kenya.csv", { type: "text/csv" })
  chooseFile(screen.getByLabelText(/extract file/i), file)
  await user.type(screen.getByLabelText(/country name/i), "Kenya")
  await chooseFlag(user, "France")
  await user.click(screen.getByRole("button", { name: /upload extract/i }))
  await waitFor(() => {
    expect(screen.getByText("Kenya")).toBeInTheDocument()
  })
  expect(screen.getByText("Kenya").parentElement).toHaveTextContent("🇫🇷")
  expect(screen.queryByText(/no countries ingested yet/i)).not.toBeInTheDocument()
  expect(screen.getByText(/records ingested/i)).toBeInTheDocument()
})
