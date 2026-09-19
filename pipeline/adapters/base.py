from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pipeline.models import CountryAccount, HarmonisedRecord


@dataclass
class AdapterResult:
    country_code: str
    source_filename: str
    source_format: str
    records: list[HarmonisedRecord]
    accounts: list[CountryAccount] = field(default_factory=list)
    extracted_at: datetime | None = None
    notes: str | None = None


class CountryAdapter:
    country_code: str
    source_filename: str
    source_format: str

    def source_path(self, data_dir: Path) -> Path:
        return data_dir / self.source_filename

    def load(self, data_dir: Path) -> AdapterResult:
        raise NotImplementedError
