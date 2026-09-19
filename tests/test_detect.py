from pathlib import Path

import pytest

from pipeline.adapters.base import LAYOUT_CSV_A, LAYOUT_JSON_C, LAYOUT_XLSX_B, UnsupportedLayoutError
from pipeline.adapters.detect import detect_layout
from tests.helpers import write_csv_a, write_json_c, write_xlsx_b


def test_detects_csv_layout(tmp_path: Path) -> None:
    path = write_csv_a(tmp_path / "extract.csv")
    assert detect_layout(path) == LAYOUT_CSV_A


def test_detects_xlsx_layout(tmp_path: Path) -> None:
    path = write_xlsx_b(tmp_path / "extract.xlsx")
    assert detect_layout(path) == LAYOUT_XLSX_B


def test_detects_json_layout(tmp_path: Path) -> None:
    path = write_json_c(tmp_path / "extract.json")
    assert detect_layout(path) == LAYOUT_JSON_C


def test_rejects_unknown_extension(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("not an extract", encoding="utf-8")
    with pytest.raises(UnsupportedLayoutError, match="Unsupported file type"):
        detect_layout(path)


def test_rejects_csv_with_wrong_columns(tmp_path: Path) -> None:
    path = tmp_path / "other.csv"
    path.write_text("id,amount\n1,2\n", encoding="utf-8")
    with pytest.raises(UnsupportedLayoutError, match="TXN_ID"):
        detect_layout(path)


def test_rejects_json_without_transactions(tmp_path: Path) -> None:
    path = tmp_path / "other.json"
    path.write_text('{"hello": []}', encoding="utf-8")
    with pytest.raises(UnsupportedLayoutError, match="metadata"):
        detect_layout(path)
