import type {
  CountryOut,
  ExpenditureDetailOut,
  ExpenditureListOut,
  ExpenditureQuery,
  IngestOut,
  MappingListOut,
  OverviewOut,
  RefItem,
} from "@/types"

export async function fetcher<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function expenditureListKey(query: ExpenditureQuery): string {
  const params = new URLSearchParams()
  if (query.country) params.set("country", query.country)
  if (query.sha) params.set("sha", query.sha)
  if (query.srhr) params.set("srhr", query.srhr)
  if (query.confidence) params.set("confidence", query.confidence)
  if (query.flag) params.set("flag", query.flag)
  if (query.q) params.set("q", query.q)
  if (query.review_only) params.set("review_only", "true")
  params.set("limit", String(query.limit ?? 50))
  params.set("offset", String(query.offset ?? 0))
  return `/api/expenditures?${params.toString()}`
}

export function fetchOverview() {
  return fetcher<OverviewOut>("/api/overview")
}

export function fetchExpenditureList(url: string) {
  return fetcher<ExpenditureListOut>(url)
}

export function fetchExpenditure(id: number) {
  return fetcher<ExpenditureDetailOut>(`/api/expenditures/${id}`)
}

export function fetchMappings(country?: string) {
  const suffix = country ? `?country=${encodeURIComponent(country)}` : ""
  return fetcher<MappingListOut>(`/api/mappings${suffix}`)
}

export function fetchShaRefs() {
  return fetcher<RefItem[]>("/api/refs/sha")
}

export function fetchSrhrRefs() {
  return fetcher<RefItem[]>("/api/refs/srhr")
}

export async function overrideClassification(
  id: number,
  body: { sha_code: string | null; srhr_code: string | null; reviewer: string; rationale: string }
) {
  const response = await fetch(`/api/expenditures/${id}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new Error(`Override failed: ${response.status}`)
  }
  return response.json()
}

export function fetchCountries() {
  return fetcher<CountryOut[]>("/api/countries")
}

function errorDetail(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail
    if (typeof detail === "string" && detail.trim()) return detail
  }
  return fallback
}

export async function uploadCountryExtract(formData: FormData): Promise<IngestOut> {
  const response = await fetch("/api/ingest", {
    method: "POST",
    body: formData,
  })
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null)
    throw new Error(errorDetail(payload, `Upload failed: ${response.status}`))
  }
  return response.json() as Promise<IngestOut>
}
