import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from pipeline.adapters import ADAPTERS
from pipeline.classify import classify_record, load_account_maps, load_keyword_rules, to_classification_row
from pipeline.db import ROOT, get_session, reset_database
from pipeline.models import (
    Country,
    CountryAccount,
    Expenditure,
    ExpenditureLine,
    IngestionRun,
    QualityFlag,
    ShaRef,
    SrhrRef,
)
from pipeline.quality import labels_consistent

DATA_DIR = ROOT / "data"
MAPPINGS_DIR = ROOT / "mappings"


def _load_csv_refs(session: Session) -> None:
    with (DATA_DIR / "ref_countries.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            session.add(Country(**row))
    with (DATA_DIR / "ref_sha_classification.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            session.add(
                ShaRef(
                    sha_code=row["sha_code"],
                    sha_description=row["sha_description"],
                    notes=row.get("notes") or None,
                )
            )
    with (DATA_DIR / "ref_srhr_classification.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            session.add(
                SrhrRef(
                    srhr_code=row["srhr_code"],
                    srhr_description=row["srhr_description"],
                    notes=row.get("notes") or None,
                )
            )


def run_ingest(data_dir: Path | None = None) -> dict[str, int]:
    data_dir = data_dir or DATA_DIR
    reset_database()
    account_maps = load_account_maps(MAPPINGS_DIR / "account_map.csv")
    keyword_rules = load_keyword_rules(MAPPINGS_DIR / "keyword_rules.csv")
    maps_by_key = {(item.country_code, item.account_code): item for item in account_maps}

    counts = {"runs": 0, "expenditures": 0, "flags": 0, "classifications": 0}

    with get_session() as session:
        _load_csv_refs(session)
        for item in account_maps:
            session.add(item)
        for item in keyword_rules:
            session.add(item)
        session.commit()

        for adapter in ADAPTERS:
            result = adapter.load(data_dir)
            run = IngestionRun(
                country_code=result.country_code,
                source_filename=result.source_filename,
                source_format=result.source_format,
                extracted_at=result.extracted_at,
                ingested_at=datetime.now(UTC),
                record_count=len(result.records),
                notes=result.notes,
            )
            session.add(run)
            session.flush()
            counts["runs"] += 1

            seen_accounts: set[str] = set()
            for account in result.accounts:
                session.add(account)
                seen_accounts.add(account.account_code)

            for record in result.records:
                if record.account_code and record.account_code not in seen_accounts:
                    label = record.official_account_label or record.description_norm or record.account_code
                    session.add(
                        CountryAccount(
                            country_code=record.country_code,
                            account_code=record.account_code,
                            account_label=label,
                            source="derived",
                        )
                    )
                    seen_accounts.add(record.account_code)

                if record.official_account_label is None and record.account_code:
                    derived = next(
                        (acc.account_label for acc in result.accounts if acc.account_code == record.account_code),
                        None,
                    )
                    record.official_account_label = derived

                if (
                    record.official_account_label
                    and record.description_raw
                    and not labels_consistent(record.description_raw, record.official_account_label)
                    and not any(flag.flag_code == "coa_label_mismatch" for flag in record.flags)
                    and not any(flag.flag_code == "description_untrusted" for flag in record.flags)
                ):
                    # Case-only variants are consistent; leave as-is.
                    pass

                expenditure = Expenditure(
                    country_code=record.country_code,
                    ingestion_run_id=run.id or 0,
                    source_transaction_id=record.source_transaction_id,
                    source_row_ref=record.source_row_ref,
                    transaction_date=record.transaction_date,
                    fiscal_year=record.fiscal_year,
                    ministry_code=record.ministry_code,
                    ministry_name=record.ministry_name,
                    account_code=record.account_code,
                    description_raw=record.description_raw,
                    description_norm=record.description_norm,
                    supplier=record.supplier,
                    amount_original=record.amount_original,
                    amount_native=record.amount_native,
                    currency_original=record.currency_original,
                    payment_method=record.payment_method,
                    raw_payload_json=json.dumps(record.raw_payload, default=str),
                )
                session.add(expenditure)
                session.flush()
                counts["expenditures"] += 1

                for line in record.lines:
                    session.add(
                        ExpenditureLine(
                            expenditure_id=expenditure.id or 0,
                            source_sub_id=line.source_sub_id,
                            description=line.description,
                            amount=line.amount,
                        )
                    )

                draft = classify_record(record, maps_by_key, keyword_rules)
                for flag in [*record.flags, *draft.extra_flags]:
                    session.add(
                        QualityFlag(
                            expenditure_id=expenditure.id or 0,
                            flag_code=flag.flag_code,
                            detail=flag.detail,
                        )
                    )
                    counts["flags"] += 1

                session.add(to_classification_row(expenditure.id or 0, draft))
                counts["classifications"] += 1

            session.commit()

    return counts
