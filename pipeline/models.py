from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import UniqueConstraint
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


class QualityIssue(BaseModel):
    flag_code: str
    detail: str | None = None


class ExpenditureLineDraft(BaseModel):
    source_sub_id: str
    description: str | None = None
    amount: float | None = None


class HarmonisedRecord(BaseModel):
    """Common structure produced by every country adapter."""

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
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    official_account_label: str | None = None
    flags: list[QualityIssue] = Field(default_factory=list)
    lines: list[ExpenditureLineDraft] = Field(default_factory=list)


class Country(SQLModel, table=True):
    __tablename__ = "country"

    country_code: str = SQLField(primary_key=True)
    country_name: str
    primary_currency: str
    language: str


class ShaRef(SQLModel, table=True):
    __tablename__ = "sha_ref"

    sha_code: str = SQLField(primary_key=True)
    sha_description: str
    notes: str | None = None


class SrhrRef(SQLModel, table=True):
    __tablename__ = "srhr_ref"

    srhr_code: str = SQLField(primary_key=True)
    srhr_description: str
    notes: str | None = None


class IngestionRun(SQLModel, table=True):
    __tablename__ = "ingestion_run"

    id: int | None = SQLField(default=None, primary_key=True)
    country_code: str = SQLField(foreign_key="country.country_code")
    source_filename: str
    source_format: str
    extracted_at: datetime | None = None
    ingested_at: datetime
    record_count: int
    notes: str | None = None


class CountryAccount(SQLModel, table=True):
    __tablename__ = "country_account"
    __table_args__ = (UniqueConstraint("country_code", "account_code"),)

    id: int | None = SQLField(default=None, primary_key=True)
    country_code: str = SQLField(foreign_key="country.country_code")
    account_code: str
    account_label: str
    source: str


class Expenditure(SQLModel, table=True):
    __tablename__ = "expenditure"

    id: int | None = SQLField(default=None, primary_key=True)
    country_code: str = SQLField(index=True, foreign_key="country.country_code")
    ingestion_run_id: int = SQLField(foreign_key="ingestion_run.id")
    source_transaction_id: str = SQLField(index=True)
    source_row_ref: str
    transaction_date: date | None = None
    fiscal_year: str | None = None
    ministry_code: str | None = None
    ministry_name: str | None = None
    account_code: str | None = SQLField(default=None, index=True)
    description_raw: str | None = None
    description_norm: str | None = None
    supplier: str | None = None
    amount_original: str | None = None
    amount_native: float | None = None
    currency_original: str
    payment_method: str | None = None
    raw_payload_json: str


class ExpenditureLine(SQLModel, table=True):
    __tablename__ = "expenditure_line"

    id: int | None = SQLField(default=None, primary_key=True)
    expenditure_id: int = SQLField(foreign_key="expenditure.id")
    source_sub_id: str
    description: str | None = None
    amount: float | None = None


class QualityFlag(SQLModel, table=True):
    __tablename__ = "quality_flag"

    id: int | None = SQLField(default=None, primary_key=True)
    expenditure_id: int = SQLField(index=True, foreign_key="expenditure.id")
    flag_code: str = SQLField(index=True)
    detail: str | None = None


class Classification(SQLModel, table=True):
    __tablename__ = "classification"

    id: int | None = SQLField(default=None, primary_key=True)
    expenditure_id: int = SQLField(index=True, foreign_key="expenditure.id")
    sha_code: str | None = SQLField(default=None, foreign_key="sha_ref.sha_code")
    srhr_code: str | None = SQLField(default=None, foreign_key="srhr_ref.srhr_code")
    method: str
    confidence: str = SQLField(index=True)
    rationale: str
    is_current: bool = True
    classified_at: datetime
    classified_by: str | None = None


class AccountMap(SQLModel, table=True):
    __tablename__ = "account_map"
    __table_args__ = (UniqueConstraint("country_code", "account_code"),)

    id: int | None = SQLField(default=None, primary_key=True)
    country_code: str = SQLField(foreign_key="country.country_code")
    account_code: str
    sha_code: str | None = None
    srhr_code: str | None = None
    confidence: str
    generic: bool = False
    notes: str | None = None


class KeywordRule(SQLModel, table=True):
    __tablename__ = "keyword_rule"

    id: int | None = SQLField(default=None, primary_key=True)
    language: str
    pattern: str
    sha_code: str | None = None
    srhr_code: str | None = None
    priority: int
    notes: str | None = None
