import csv
import json
from pathlib import Path

from openpyxl import Workbook

CSV_A_HEADER = [
    "TXN_ID",
    "DATE",
    "MINISTRY_CODE",
    "MINISTRY_NAME",
    "ACCOUNT_CODE",
    "DESCRIPTION",
    "VENDOR",
    "AMOUNT_KES",
    "PAYMENT_METHOD",
]


def write_csv_a(path: Path, rows: list[dict[str, str]] | None = None) -> Path:
    records = rows or [
        {
            "TXN_ID": "KE-1",
            "DATE": "01/02/2024",
            "MINISTRY_CODE": "MOH",
            "MINISTRY_NAME": "Health",
            "ACCOUNT_CODE": "2211102",
            "DESCRIPTION": "Contraceptives",
            "VENDOR": "Vendor",
            "AMOUNT_KES": "100.00",
            "PAYMENT_METHOD": "BANK",
        }
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_A_HEADER)
        writer.writeheader()
        writer.writerows(records)
    return path


def write_xlsx_b(path: Path, rows: list[list[object]] | None = None) -> Path:
    workbook = Workbook()
    depenses = workbook.active
    assert depenses is not None
    depenses.title = "Depenses"
    depenses.append(["Export preamble"])
    depenses.append(
        [
            "id_transaction",
            "date_ecriture",
            "ministere_code",
            "ministere_nom",
            "code_budgetaire",
            "libelle",
            "tiers",
            "montant_XOF",
        ]
    )
    for row in rows or [["TX-1", "01/02/2024", "MS", "Sante", "611015", "Contraceptifs", "Pharma", 1000]]:
        depenses.append(row)
    plan = workbook.create_sheet("Plan_comptable")
    plan.append(["code", "libelle"])
    plan.append(["611015", "Contraceptifs"])
    workbook.save(path)
    return path


def write_json_c(path: Path, transactions: list[dict[str, object]] | None = None) -> Path:
    payload = {
        "metadata": {
            "extractedAt": "2024-08-15T09:22:41Z",
            "primaryCurrency": "RWF",
            "fiscalYear": "FY2023/24",
        },
        "transactions": transactions
        or [
            {
                "transactionId": "RW-1",
                "postingDate": "2024-01-25",
                "fiscalYear": "FY2023/24",
                "ministryCode": "MINISANTE",
                "ministryName": "Ministry of Health",
                "coaCode": "2211005",
                "description": "Contraceptives",
                "supplier": "Central Medical Stores",
                "amount": 2500.0,
                "currency": "RWF",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
