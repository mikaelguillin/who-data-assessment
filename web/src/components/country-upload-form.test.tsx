import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { SWRConfig } from "swr"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { CountryUploadForm } from "@/components/country-upload-form"
import { chooseFile } from "@/test/choose-file"

const ingestOut = {
  country_code: "KENYA",
  country_name: "Kenya",
  source_filename: "kenya.csv",
  source_format: "csv",
  layout_id: "csv_a",
  record_count: 1,
  flag_count: 0,
  classification_count: 1,
  replaced: false,
}

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
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url === "/api/ingest" && init?.method === "POST") {
        return jsonResponse(ingestOut)
      }
      if (url === "/api/overview" || url === "/api/countries") {
        return jsonResponse([])
      }
      return jsonResponse({ detail: "unhandled" }, 500)
    })
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function renderForm() {
  return render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0, shouldRetryOnError: false }}>
      <CountryUploadForm />
    </SWRConfig>
  )
}

test("uploads an extract and calls ingest", async () => {
  const user = userEvent.setup()
  renderForm()
  const file = new File(["TXN_ID,ACCOUNT_CODE,AMOUNT_KES,DATE\n"], "kenya.csv", { type: "text/csv" })
  chooseFile(screen.getByLabelText(/extract file/i), file)
  await user.type(screen.getByLabelText(/country name/i), "Kenya")
  await user.click(screen.getByRole("button", { name: /upload extract/i }))
  await waitFor(() => {
    expect(fetch).toHaveBeenCalledWith(
      "/api/ingest",
      expect.objectContaining({ method: "POST" })
    )
  })
})

test("shows a client error when file or name is missing", async () => {
  const user = userEvent.setup()
  renderForm()
  await user.click(screen.getByRole("button", { name: /upload extract/i }))
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /choose a csv, excel, or json extract and enter a country name/i
  )
  expect(fetch).not.toHaveBeenCalled()
})

test("shows an error when ingest fails", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url === "/api/ingest") {
        return jsonResponse({ detail: "This CSV does not match the supported expenditure layout." }, 400)
      }
      return jsonResponse([])
    })
  )
  const user = userEvent.setup()
  renderForm()
  const file = new File(["id,amount\n1,2\n"], "other.csv", { type: "text/csv" })
  chooseFile(screen.getByLabelText(/extract file/i), file)
  await user.type(screen.getByLabelText(/country name/i), "Mystery")
  await user.click(screen.getByRole("button", { name: /upload extract/i }))
  expect(await screen.findByRole("alert")).toHaveTextContent(/does not match the supported expenditure layout/i)
})
