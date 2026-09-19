import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { SWRConfig } from "swr"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { CountryUploadForm } from "@/components/country-upload-form"
import { chooseFile } from "@/test/choose-file"
import { chooseFlag } from "@/test/choose-flag"

const ingestOut = {
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

test("flag select lists emoji flags with accessible country names", async () => {
  const user = userEvent.setup()
  renderForm()
  await user.click(screen.getByRole("combobox", { name: /^flag$/i }))
  const kenya = await screen.findByRole("option", { name: /^kenya$/i })
  expect(kenya).toHaveTextContent("🇰🇪")
  expect(kenya).not.toHaveTextContent(/kenya/i)
  expect(screen.getByRole("option", { name: /^france$/i })).toHaveTextContent("🇫🇷")
})

test("uploads an extract with a free-text name and an independent flag", async () => {
  const user = userEvent.setup()
  renderForm()
  const file = new File(["TXN_ID,ACCOUNT_CODE,AMOUNT_KES,DATE\n"], "kenya.csv", { type: "text/csv" })
  chooseFile(screen.getByLabelText(/extract file/i), file)
  await user.type(screen.getByLabelText(/country name/i), "Kenya")
  await chooseFlag(user, "France")
  await user.click(screen.getByRole("button", { name: /upload extract/i }))
  await waitFor(() => {
    expect(fetch).toHaveBeenCalledWith(
      "/api/ingest",
      expect.objectContaining({ method: "POST" })
    )
  })
  const ingestCall = vi.mocked(fetch).mock.calls.find(([url]) => String(url) === "/api/ingest")
  expect(ingestCall).toBeDefined()
  const body = ingestCall?.[1]?.body as FormData
  expect(body.get("country_name")).toBe("Kenya")
  expect(body.get("flag_emoji")).toBe("🇫🇷")
})

test("uploads without a flag when none is selected", async () => {
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
  const ingestCall = vi.mocked(fetch).mock.calls.find(([url]) => String(url) === "/api/ingest")
  const body = ingestCall?.[1]?.body as FormData
  expect(body.get("country_name")).toBe("Kenya")
  expect(body.get("flag_emoji")).toBeNull()
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
