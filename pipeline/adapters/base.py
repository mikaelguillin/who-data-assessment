from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pipeline.models import CountryAccount, HarmonisedRecord

LAYOUT_CSV_A = "csv_a"
LAYOUT_XLSX_B = "xlsx_b"
LAYOUT_JSON_C = "json_c"

TEMPLATE_COUNTRY_CODES: dict[str, str] = {
    LAYOUT_CSV_A: "CTA",
    LAYOUT_XLSX_B: "CTB",
    LAYOUT_JSON_C: "CTC",
}


class UnsupportedLayoutError(ValueError):
    """Raised when a file is not one of the three supported extract layouts."""


@dataclass
class AdapterResult:
    country_code: str
    source_filename: str
    source_format: str
    layout_id: str
    records: list[HarmonisedRecord]
    accounts: list[CountryAccount] = field(default_factory=list)
    extracted_at: datetime | None = None
    notes: str | None = None
    primary_currency: str = ""
    language: str = "en"


class CountryAdapter:
    source_format: str
    layout_id: str
    default_currency: str
    default_language: str = "en"

    def load(self, path: Path, country_code: str) -> AdapterResult:
        raise NotImplementedError
