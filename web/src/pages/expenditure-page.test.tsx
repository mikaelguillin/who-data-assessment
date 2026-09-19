import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { SWRConfig } from "swr"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { ExpenditurePage } from "@/pages/expenditure-page"
import type { ExpenditureDetailOut } from "@/types"

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  })
}

const detail: ExpenditureDetailOut = {
  id: 42,
  country_code: "KENYA",
  source_transaction_id: "TXN-42",
  source_row_ref: "row-12",
  transaction_date: "2024-03-19",
  fiscal_year: "2024",
  ministry_code: "MOH",
  ministry_name: "Health",
  account_code: "2211102",
  description_raw: "Contraceptives",
  description_norm: "contraceptives",
  supplier: "Supplier",
  amount_original: "1000",
  amount_native: 1000,
  currency_original: "KES",
  payment_method: "EFT",
  raw_payload_json: "{}",
  ingestion_run: {
    id: 1,
    country_code: "KENYA",
    source_filename: "kenya.csv",
    source_format: "csv",
    ingested_at: "2024-07-20T12:00:00+00:00",
    record_count: 1,
    notes: null,
  },
  flags: [],
  lines: [],
  classification: {
    sha_code: "HC.5.1",
    sha_description: "Pharmaceuticals",
    srhr_code: "SRHR.FP",
    srhr_description: "Family planning",
    method: "rules",
    confidence: "high",
    rationale: "Account map",
    classified_at: "2024-06-15T12:00:00+00:00",
    classified_by: "pipeline",
  },
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url === "/api/expenditures/42") return jsonResponse(detail)
      if (url === "/api/refs/sha") return jsonResponse([])
      if (url === "/api/refs/srhr") return jsonResponse([])
      return jsonResponse({ detail: `unhandled ${url}` }, 500)
    })
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function renderDetail(path = "/transactions/42") {
  return render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0, shouldRetryOnError: false }}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="transactions/:id" element={<ExpenditurePage />} />
        </Routes>
      </MemoryRouter>
    </SWRConfig>
  )
}

test("shows formatted dates instead of raw ISO strings", async () => {
  renderDetail()
  await screen.findByRole("heading", { name: "TXN-42" })
  expect(screen.getByText(/19 Mar 2024/)).toBeInTheDocument()
  expect(screen.getByText(/15 Jun 2024/)).toBeInTheDocument()
  expect(screen.getByText(/20 Jul 2024/)).toBeInTheDocument()
  expect(screen.queryByText("2024-03-19")).not.toBeInTheDocument()
  expect(screen.queryByText(/2024-06-15T12:00:00/)).not.toBeInTheDocument()
  expect(screen.queryByText(/2024-07-20T12:00:00/)).not.toBeInTheDocument()
})
