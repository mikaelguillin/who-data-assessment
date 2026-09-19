import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

from pipeline.adapters.base import AdapterResult, CountryAdapter
from pipeline.models import CountryAccount, HarmonisedRecord, QualityIssue
from pipeline.quality import DATE_MAX_YEAR, DATE_MIN_YEAR, is_untrusted_description, normalize_text


def parse_amount_kes(raw: str | None) -> tuple[float | None, str | None]:
    if raw is None or not str(raw).strip():
        return None, "missing_amount"
    text = str(raw).strip().strip('"').strip("'")
    text = text.replace(",", "")
    try:
        return float(text), None
    except ValueError:
        return None, "unparseable_amount"


def parse_date_dmy(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


class CountryAAdapter(CountryAdapter):
    country_code = "CTA"
    source_filename = "country_a_expenditure.csv"
    source_format = "csv"

    def load(self, data_dir: Path) -> AdapterResult:
        path = self.source_path(data_dir)
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        id_counts = Counter((row.get("TXN_ID") or "").strip() for row in rows)
        accounts: dict[str, str] = {}
        records: list[HarmonisedRecord] = []

        for index, row in enumerate(rows, start=2):
            source_id = (row.get("TXN_ID") or "").strip()
            description = row.get("DESCRIPTION")
            account_code = (row.get("ACCOUNT_CODE") or "").strip() or None
            amount_raw = row.get("AMOUNT_KES")
            amount, amount_flag = parse_amount_kes(amount_raw)
            parsed_date = parse_date_dmy(row.get("DATE"))

            flags: list[QualityIssue] = []
            if amount_flag:
                flags.append(QualityIssue(flag_code=amount_flag, detail=amount_raw or None))
            if amount is not None and amount < 0:
                flags.append(QualityIssue(flag_code="negative_amount", detail=str(amount)))
            if id_counts[source_id] > 1:
                flags.append(
                    QualityIssue(
                        flag_code="duplicate_source_id",
                        detail=f"{source_id} appears {id_counts[source_id]} times",
                    )
                )
            if parsed_date is None:
                flags.append(QualityIssue(flag_code="unparseable_date", detail=row.get("DATE")))
            elif not DATE_MIN_YEAR <= parsed_date.year <= DATE_MAX_YEAR:
                flags.append(
                    QualityIssue(flag_code="date_out_of_range", detail=parsed_date.date().isoformat())
                )
            if not (description or "").strip():
                flags.append(QualityIssue(flag_code="missing_description"))
            if is_untrusted_description(description):
                flags.append(QualityIssue(flag_code="description_untrusted"))

            desc_norm = normalize_text(description)
            if account_code and desc_norm:
                accounts.setdefault(account_code, desc_norm)

            records.append(
                HarmonisedRecord(
                    country_code=self.country_code,
                    source_transaction_id=source_id,
                    source_row_ref=f"{self.source_filename}:line:{index}",
                    transaction_date=parsed_date.date() if parsed_date else None,
                    fiscal_year=str(parsed_date.year) if parsed_date else None,
                    ministry_code=row.get("MINISTRY_CODE"),
                    ministry_name=row.get("MINISTRY_NAME"),
                    account_code=account_code,
                    description_raw=description,
                    description_norm=desc_norm,
                    supplier=row.get("VENDOR") or None,
                    amount_original=amount_raw if amount_raw not in (None, "") else None,
                    amount_native=amount,
                    currency_original="KES",
                    payment_method=row.get("PAYMENT_METHOD") or None,
                    raw_payload=dict(row),
                    flags=flags,
                )
            )

        country_accounts = [
            CountryAccount(
                country_code=self.country_code,
                account_code=code,
                account_label=label,
                source="derived",
            )
            for code, label in sorted(accounts.items())
        ]
        return AdapterResult(
            country_code=self.country_code,
            source_filename=self.source_filename,
            source_format=self.source_format,
            records=records,
            accounts=country_accounts,
        )
