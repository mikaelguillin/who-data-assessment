from datetime import date, datetime

from pydantic import BaseModel, Field


class FlagOut(BaseModel):
    flag_code: str
    detail: str | None = None


class LineOut(BaseModel):
    source_sub_id: str
    description: str | None = None
    amount: float | None = None


class ClassificationOut(BaseModel):
    sha_code: str | None = None
    sha_description: str | None = None
    srhr_code: str | None = None
    srhr_description: str | None = None
    method: str
    confidence: str
    rationale: str
    classified_at: datetime
    classified_by: str | None = None


class ExpenditureListItem(BaseModel):
    id: int
    country_code: str
    source_transaction_id: str
    transaction_date: date | None = None
    ministry_code: str | None = None
    account_code: str | None = None
    description_raw: str | None = None
    supplier: str | None = None
    amount_native: float | None = None
    currency_original: str
    sha_code: str | None = None
    srhr_code: str | None = None
    method: str | None = None
    confidence: str | None = None
    flag_codes: list[str] = Field(default_factory=list)


class ExpenditureListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ExpenditureListItem]


class IngestionRunOut(BaseModel):
    id: int
    country_code: str
    source_filename: str
    source_format: str
    ingested_at: datetime
    record_count: int
    notes: str | None = None


class ExpenditureDetailOut(BaseModel):
    id: int
    country_code: str
    source_transaction_id: str
    source_row_ref: str
    transaction_date: date | None = None
    fiscal_year: str | None = None
    ministry_code: str | None = None
    ministry_name: str | None = None
    account_code: str | None = None
    description_raw: str | None = None
    description_norm: str | None = None
    supplier: str | None = None
    amount_original: str | None = None
    amount_native: float | None = None
    currency_original: str
    payment_method: str | None = None
    raw_payload_json: str
    ingestion_run: IngestionRunOut | None = None
    flags: list[FlagOut] = Field(default_factory=list)
    lines: list[LineOut] = Field(default_factory=list)
    classification: ClassificationOut | None = None


class OverrideIn(BaseModel):
    sha_code: str | None = None
    srhr_code: str | None = None
    reviewer: str = "analyst"
    rationale: str = "Analyst override"


class CountItem(BaseModel):
    key: str
    label: str | None = None
    count: int
    amount: float | None = None
    currency: str | None = None


class CurrencySpend(BaseModel):
    currency: str
    amount: float
    count: int


class CountrySummary(BaseModel):
    country_code: str
    country_name: str
    record_count: int
    review_count: int
    currencies: list[CurrencySpend] = Field(default_factory=list)


class OverviewOut(BaseModel):
    expenditure_count: int
    review_count: int
    review_share: float
    countries: list[CountrySummary]
    by_sha: list[CountItem]
    by_srhr: list[CountItem]
    by_confidence: list[CountItem]
    by_flag: list[CountItem]
    spend_by_currency: list[CurrencySpend]


class AccountMapOut(BaseModel):
    country_code: str
    account_code: str
    account_label: str | None = None
    sha_code: str | None = None
    srhr_code: str | None = None
    confidence: str | None = None
    generic: bool = False
    notes: str | None = None
    mapped: bool


class MappingListOut(BaseModel):
    items: list[AccountMapOut]


class RefItem(BaseModel):
    code: str
    description: str
