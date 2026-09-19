from pathlib import Path

import pytest
from sqlmodel import Session, select

from pipeline.ingest import ingest_file
from pipeline.models import Classification, Country, Expenditure
from tests.helpers import write_csv_a, write_json_c, write_xlsx_b


def test_ingest_creates_country_and_classifies_from_layout_maps(session: Session, tmp_path: Path) -> None:
    path = write_csv_a(tmp_path / "kenya.csv")
    outcome = ingest_file(path, "Kenya", session=session)
    assert outcome.country_code == "KENYA"
    assert outcome.record_count == 1
    assert outcome.replaced is False

    country = session.get(Country, "KENYA")
    assert country is not None
    assert country.country_name == "Kenya"
    assert country.primary_currency == "KES"

    expenditure = session.exec(select(Expenditure)).one()
    assert expenditure.account_code == "2211102"
    classification = session.exec(select(Classification).where(Classification.expenditure_id == expenditure.id)).one()
    assert classification.sha_code == "HC.5.1"
    assert classification.srhr_code == "SRHR.FP"


def test_second_country_coexists_and_reupload_replaces(session: Session, tmp_path: Path) -> None:
    first = write_csv_a(tmp_path / "kenya.csv")
    ingest_file(first, "Kenya", session=session)
    second = write_json_c(tmp_path / "rwanda.json")
    ingest_file(second, "Rwanda", session=session)

    codes = {item.country_code for item in session.exec(select(Country)).all()}
    assert codes == {"KENYA", "RWANDA"}
    assert len(session.exec(select(Expenditure)).all()) == 2
    rwanda = session.exec(select(Expenditure).where(Expenditure.country_code == "RWANDA")).one()
    rwanda_class = session.exec(
        select(Classification).where(Classification.expenditure_id == rwanda.id)
    ).one()
    assert rwanda_class.sha_code == "HC.5.1"
    assert rwanda_class.srhr_code == "SRHR.FP"

    replacement_rows = [
        {
            "TXN_ID": "KE-2",
            "DATE": "02/02/2024",
            "MINISTRY_CODE": "MOH",
            "MINISTRY_NAME": "Health",
            "ACCOUNT_CODE": "2211102",
            "DESCRIPTION": "Contraceptives",
            "VENDOR": "Vendor",
            "AMOUNT_KES": "50.00",
            "PAYMENT_METHOD": "BANK",
        },
        {
            "TXN_ID": "KE-3",
            "DATE": "03/02/2024",
            "MINISTRY_CODE": "MOH",
            "MINISTRY_NAME": "Health",
            "ACCOUNT_CODE": "2211101",
            "DESCRIPTION": "Essential medicines",
            "VENDOR": "Vendor",
            "AMOUNT_KES": "75.00",
            "PAYMENT_METHOD": "BANK",
        },
    ]
    replacement = write_csv_a(tmp_path / "kenya-again.csv", replacement_rows)
    outcome = ingest_file(replacement, "Kenya", session=session)
    assert outcome.replaced is True
    assert outcome.record_count == 2

    kenya_rows = session.exec(select(Expenditure).where(Expenditure.country_code == "KENYA")).all()
    assert len(kenya_rows) == 2
    assert {row.source_transaction_id for row in kenya_rows} == {"KE-2", "KE-3"}
    assert len(session.exec(select(Country)).all()) == 2
    rwanda_rows = session.exec(select(Expenditure).where(Expenditure.country_code == "RWANDA")).all()
    assert len(rwanda_rows) == 1


def test_ingest_xlsx_copies_layout_b_maps(session: Session, tmp_path: Path) -> None:
    path = write_xlsx_b(tmp_path / "senegal.xlsx")
    outcome = ingest_file(path, "Senegal", session=session)
    assert outcome.country_code == "SENEGAL"
    assert outcome.source_format == "xlsx"
    assert outcome.layout_id == "xlsx_b"

    country = session.get(Country, "SENEGAL")
    assert country is not None
    assert country.primary_currency == "XOF"
    assert country.language == "fr"

    expenditure = session.exec(select(Expenditure)).one()
    assert expenditure.account_code == "611015"
    classification = session.exec(select(Classification).where(Classification.expenditure_id == expenditure.id)).one()
    assert classification.sha_code == "HC.5.1"
    assert classification.srhr_code == "SRHR.FP"


def test_ingest_rejects_empty_file_and_blank_name(session: Session, tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        ingest_file(empty, "Kenya", session=session)

    path = write_csv_a(tmp_path / "kenya.csv")
    with pytest.raises(ValueError, match="country_name is required"):
        ingest_file(path, "   ", session=session)


def test_ingest_suffixes_code_when_slug_is_taken(session: Session, tmp_path: Path) -> None:
    first = write_csv_a(tmp_path / "occupied.csv")
    ingest_file(first, "Occupied", country_code="GHANA", session=session)
    second = write_xlsx_b(tmp_path / "ghana.xlsx")
    outcome = ingest_file(second, "Ghana", session=session)
    assert outcome.country_code == "GHANA2"
    assert outcome.replaced is False
    codes = {item.country_code for item in session.exec(select(Country)).all()}
    assert codes == {"GHANA", "GHANA2"}
