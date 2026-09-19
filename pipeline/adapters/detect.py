import csv
import json
from pathlib import Path

from pipeline.adapters.base import (
    LAYOUT_CSV_A,
    LAYOUT_JSON_C,
    LAYOUT_XLSX_B,
    UnsupportedLayoutError,
)

CSV_A_REQUIRED_COLUMNS = {"TXN_ID", "ACCOUNT_CODE", "AMOUNT_KES", "DATE"}
XLSX_B_REQUIRED_SHEETS = {"Depenses", "Plan_comptable"}

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm", ".json"}


def detect_layout(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _detect_csv(path)
    if suffix in {".xlsx", ".xlsm"}:
        return _detect_xlsx(path)
    if suffix == ".json":
        return _detect_json(path)
    raise UnsupportedLayoutError(
        "Unsupported file type. Upload a CSV, Excel (.xlsx), or JSON extract matching a known layout."
    )


def _detect_csv(path: Path) -> str:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        header = next(csv.reader(handle), None)
    if not header:
        raise UnsupportedLayoutError("This CSV file is empty or has no header row.")
    columns = {col.strip() for col in header if col is not None}
    if CSV_A_REQUIRED_COLUMNS <= columns:
        return LAYOUT_CSV_A
    expected = ", ".join(sorted(CSV_A_REQUIRED_COLUMNS))
    raise UnsupportedLayoutError(
        f"This CSV does not match the supported expenditure layout (expected columns {expected})."
    )


def _detect_xlsx(path: Path) -> str:
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        names = set(workbook.sheetnames)
    finally:
        workbook.close()
    if XLSX_B_REQUIRED_SHEETS <= names:
        return LAYOUT_XLSX_B
    expected = " and ".join(sorted(XLSX_B_REQUIRED_SHEETS))
    raise UnsupportedLayoutError(
        f"This Excel file does not match the supported layout (expected sheets {expected})."
    )


def _detect_json(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UnsupportedLayoutError("This JSON file could not be parsed.") from exc
    if not isinstance(payload, dict):
        raise UnsupportedLayoutError(
            "This JSON does not match the supported layout "
            "(expected an object with metadata and a transactions array)."
        )
    metadata = payload.get("metadata")
    transactions = payload.get("transactions")
    if not isinstance(metadata, dict) or not isinstance(transactions, list):
        raise UnsupportedLayoutError(
            "This JSON does not match the supported layout "
            "(expected an object with metadata and a transactions array including coaCode)."
        )
    if transactions:
        first = transactions[0]
        if not isinstance(first, dict) or ("coaCode" not in first and "transactionId" not in first):
            raise UnsupportedLayoutError(
                "This JSON does not match the supported layout "
                "(expected transactions with coaCode or transactionId)."
            )
    return LAYOUT_JSON_C
