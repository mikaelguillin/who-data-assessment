from pathlib import Path

from pipeline.adapters.base import (
    LAYOUT_CSV_A,
    LAYOUT_JSON_C,
    LAYOUT_XLSX_B,
    TEMPLATE_COUNTRY_CODES,
    AdapterResult,
    CountryAdapter,
    UnsupportedLayoutError,
)
from pipeline.adapters.country_a import CountryAAdapter
from pipeline.adapters.country_b import CountryBAdapter
from pipeline.adapters.country_c import CountryCAdapter
from pipeline.adapters.detect import detect_layout

LAYOUT_ADAPTERS: dict[str, CountryAdapter] = {
    LAYOUT_CSV_A: CountryAAdapter(),
    LAYOUT_XLSX_B: CountryBAdapter(),
    LAYOUT_JSON_C: CountryCAdapter(),
}


def load_extract(path: Path, country_code: str) -> AdapterResult:
    layout_id = detect_layout(path)
    return LAYOUT_ADAPTERS[layout_id].load(path, country_code)


__all__ = [
    "LAYOUT_ADAPTERS",
    "TEMPLATE_COUNTRY_CODES",
    "AdapterResult",
    "CountryAdapter",
    "UnsupportedLayoutError",
    "detect_layout",
    "load_extract",
]
