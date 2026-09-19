import json
from datetime import datetime
from pathlib import Path

from pipeline.adapters.base import AdapterResult, CountryAdapter
from pipeline.models import (
    CountryAccount,
    ExpenditureLineDraft,
    HarmonisedRecord,
    QualityIssue,
)
from pipeline.quality import DATE_MAX_YEAR, DATE_MIN_YEAR, is_untrusted_description, normalize_text


class CountryCAdapter(CountryAdapter):
    country_code = "CTC"
    source_filename = "country_c_expenditure.json"
    source_format = "json"

    def load(self, data_dir: Path) -> AdapterResult:
        path = self.source_path(data_dir)
        payload = json.loads(path.read_text(encoding="utf-8"))
        metadata = payload.get("metadata") or {}
        transactions = payload.get("transactions") or []
        extracted_at = None
        if metadata.get("extractedAt"):
            extracted_at = datetime.fromisoformat(metadata["extractedAt"].replace("Z", "+00:00"))

        accounts: dict[str, str] = {}
        records: list[HarmonisedRecord] = []

        for index, row in enumerate(transactions):
            description = row.get("description")
            supplier = row.get("supplier")
            account_code = str(row.get("coaCode") or "").strip() or None
            amount = row.get("amount")
            amount_native = float(amount) if amount is not None else None
            currency = row.get("currency") or metadata.get("primaryCurrency") or "RWF"
            posting = row.get("postingDate")
            parsed_date = None
            if posting:
                try:
                    parsed_date = datetime.strptime(str(posting)[:10], "%Y-%m-%d")
                except ValueError:
                    parsed_date = None

            flags: list[QualityIssue] = []
            if description is None or not str(description).strip():
                flags.append(QualityIssue(flag_code="missing_description"))
            if supplier is None or not str(supplier).strip():
                flags.append(QualityIssue(flag_code="missing_supplier"))
            if is_untrusted_description(description):
                flags.append(QualityIssue(flag_code="description_untrusted"))
            if parsed_date is None:
                flags.append(QualityIssue(flag_code="unparseable_date", detail=str(posting)))
            elif not DATE_MIN_YEAR <= parsed_date.year <= DATE_MAX_YEAR:
                flags.append(
                    QualityIssue(flag_code="date_out_of_range", detail=parsed_date.date().isoformat())
                )
            if currency != metadata.get("primaryCurrency", "RWF"):
                flags.append(QualityIssue(flag_code="multi_currency", detail=currency))
            if amount_native is None:
                flags.append(QualityIssue(flag_code="missing_amount"))
            elif amount_native < 0:
                flags.append(QualityIssue(flag_code="negative_amount", detail=str(amount_native)))

            lines: list[ExpenditureLineDraft] = []
            subs = row.get("subTransactions") or []
            if subs:
                flags.append(
                    QualityIssue(
                        flag_code="has_subtransactions",
                        detail=f"{len(subs)} sub-lines stored for lineage; parent amount used",
                    )
                )
                for sub in subs:
                    lines.append(
                        ExpenditureLineDraft(
                            source_sub_id=str(sub.get("subId") or ""),
                            description=sub.get("description"),
                            amount=float(sub["amount"]) if sub.get("amount") is not None else None,
                        )
                    )

            desc_norm = normalize_text(description)
            if account_code and desc_norm:
                accounts.setdefault(account_code, desc_norm)

            records.append(
                HarmonisedRecord(
                    country_code=self.country_code,
                    source_transaction_id=str(row.get("transactionId") or ""),
                    source_row_ref=f"{self.source_filename}:transactions[{index}]",
                    transaction_date=parsed_date.date() if parsed_date else None,
                    fiscal_year=row.get("fiscalYear") or metadata.get("fiscalYear"),
                    ministry_code=row.get("ministryCode"),
                    ministry_name=row.get("ministryName"),
                    account_code=account_code,
                    description_raw=description,
                    description_norm=desc_norm,
                    supplier=supplier,
                    amount_original=None if amount is None else str(amount),
                    amount_native=amount_native,
                    currency_original=currency,
                    payment_method=None,
                    raw_payload=row,
                    flags=flags,
                    lines=lines,
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
            extracted_at=extracted_at,
            notes=metadata.get("notes"),
        )
