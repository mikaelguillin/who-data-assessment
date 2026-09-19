export type FlagOut = {
  flag_code: string
  detail: string | null
}

export type LineOut = {
  source_sub_id: string
  description: string | null
  amount: number | null
}

export type ClassificationOut = {
  sha_code: string | null
  sha_description: string | null
  srhr_code: string | null
  srhr_description: string | null
  method: string
  confidence: string
  rationale: string
  classified_at: string
  classified_by: string | null
}

export type ExpenditureListItem = {
  id: number
  country_code: string
  source_transaction_id: string
  transaction_date: string | null
  ministry_code: string | null
  account_code: string | null
  description_raw: string | null
  supplier: string | null
  amount_native: number | null
  currency_original: string
  sha_code: string | null
  srhr_code: string | null
  method: string | null
  confidence: string | null
  flag_codes: string[]
}

export type ExpenditureListOut = {
  total: number
  limit: number
  offset: number
  items: ExpenditureListItem[]
}

export type IngestionRunOut = {
  id: number
  country_code: string
  source_filename: string
  source_format: string
  ingested_at: string
  record_count: number
  notes: string | null
}

export type ExpenditureDetailOut = {
  id: number
  country_code: string
  source_transaction_id: string
  source_row_ref: string
  transaction_date: string | null
  fiscal_year: string | null
  ministry_code: string | null
  ministry_name: string | null
  account_code: string | null
  description_raw: string | null
  description_norm: string | null
  supplier: string | null
  amount_original: string | null
  amount_native: number | null
  currency_original: string
  payment_method: string | null
  raw_payload_json: string
  ingestion_run: IngestionRunOut | null
  flags: FlagOut[]
  lines: LineOut[]
  classification: ClassificationOut | null
}

export type CountItem = {
  key: string
  label: string | null
  count: number
  amount: number | null
  currency: string | null
}

export type CurrencySpend = {
  currency: string
  amount: number
  count: number
}

export type CountrySummary = {
  country_code: string
  country_name: string
  flag_emoji: string | null
  record_count: number
  review_count: number
  currencies: CurrencySpend[]
}

export type OverviewOut = {
  expenditure_count: number
  review_count: number
  review_share: number
  countries: CountrySummary[]
  by_sha: CountItem[]
  by_srhr: CountItem[]
  by_confidence: CountItem[]
  by_flag: CountItem[]
  spend_by_currency: CurrencySpend[]
}

export type AccountMapOut = {
  country_code: string
  account_code: string
  account_label: string | null
  sha_code: string | null
  srhr_code: string | null
  confidence: string | null
  generic: boolean
  mapped: boolean
  notes: string | null
}

export type MappingListOut = {
  items: AccountMapOut[]
}

export type RefItem = {
  code: string
  description: string
}

export type ExpenditureQuery = {
  country?: string
  sha?: string
  srhr?: string
  confidence?: string
  flag?: string
  q?: string
  review_only?: boolean
  limit?: number
  offset?: number
}

export type CountryOut = {
  country_code: string
  country_name: string
  primary_currency: string
  language: string
  flag_emoji: string | null
}

export type IngestOut = {
  country_code: string
  country_name: string
  flag_emoji: string | null
  source_filename: string
  source_format: string
  layout_id: string
  record_count: number
  flag_count: number
  classification_count: number
  replaced: boolean
}
