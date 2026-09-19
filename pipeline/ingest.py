import csv
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete as sql_delete
from sqlmodel import Session, col, select

from pipeline.adapters import TEMPLATE_COUNTRY_CODES, load_extract
from pipeline.adapters.base import AdapterResult
from pipeline.classify import classify_record, load_account_maps, load_keyword_rules, to_classification_row
from pipeline.db import ROOT, get_session, init_database
from pipeline.models import (
    AccountMap,
    Classification,
    Country,
    CountryAccount,
    Expenditure,
    ExpenditureLine,
    IngestionRun,
    KeywordRule,
    QualityFlag,
    ShaRef,
    SrhrRef,
)
from pipeline.quality import labels_consistent

DATA_DIR = ROOT / "data"
MAPPINGS_DIR = ROOT / "mappings"

MAX_FLAG_EMOJI_LENGTH = 16


@dataclass
class IngestOutcome:
    country_code: str
    country_name: str
    flag_emoji: str | None
    source_filename: str
    source_format: str
    layout_id: str
    record_count: int
    flag_count: int
    classification_count: int
    replaced: bool


def seed_reference_data(session: Session) -> None:
    if session.exec(select(ShaRef).limit(1)).first() is None:
        with (DATA_DIR / "ref_sha_classification.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                session.add(
                    ShaRef(
                        sha_code=row["sha_code"],
                        sha_description=row["sha_description"],
                        notes=row.get("notes") or None,
                    )
                )
    if session.exec(select(SrhrRef).limit(1)).first() is None:
        with (DATA_DIR / "ref_srhr_classification.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                session.add(
                    SrhrRef(
                        srhr_code=row["srhr_code"],
                        srhr_description=row["srhr_description"],
                        notes=row.get("notes") or None,
                    )
                )
    if session.exec(select(KeywordRule).limit(1)).first() is None:
        for item in load_keyword_rules(MAPPINGS_DIR / "keyword_rules.csv"):
            session.add(item)
    session.flush()


def normalize_country_code(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    return cleaned[:12]


def normalize_flag_emoji(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_FLAG_EMOJI_LENGTH:
        raise ValueError("flag_emoji must be a short emoji (at most 16 characters)")
    return cleaned


def slug_country_code(name: str) -> str:
    cleaned = normalize_country_code(name)
    if len(cleaned) >= 3:
        return cleaned[:8]
    if cleaned:
        return (cleaned + "XXX")[:3]
    return "CTY"


def allocate_country_code(
    session: Session,
    country_name: str,
    requested_code: str | None = None,
) -> tuple[str, bool]:
    name = country_name.strip()
    if requested_code and requested_code.strip():
        code = normalize_country_code(requested_code)
        if not code:
            raise ValueError("country_code must contain letters or digits")
        existing = session.get(Country, code)
        return code, existing is not None

    existing_by_name = session.exec(
        select(Country).where(col(Country.country_name) == name)
    ).first()
    if existing_by_name is None:
        lowered = name.lower()
        for country in session.exec(select(Country)).all():
            if country.country_name.lower() == lowered:
                existing_by_name = country
                break
    if existing_by_name is not None:
        return existing_by_name.country_code, True

    base = slug_country_code(name)
    code = base
    suffix = 2
    while session.get(Country, code) is not None:
        token = str(suffix)
        code = f"{base[: max(1, 8 - len(token))]}{token}"
        suffix += 1
        if suffix > 99:
            raise ValueError("Could not allocate a unique country code")
    return code, False


def _delete_country_children(session: Session, country_code: str) -> None:
    expenditure_ids = session.exec(select(Expenditure.id).where(Expenditure.country_code == country_code)).all()
    if expenditure_ids:
        session.execute(sql_delete(Classification).where(Classification.expenditure_id.in_(expenditure_ids)))
        session.execute(sql_delete(QualityFlag).where(QualityFlag.expenditure_id.in_(expenditure_ids)))
        session.execute(sql_delete(ExpenditureLine).where(ExpenditureLine.expenditure_id.in_(expenditure_ids)))
        session.execute(sql_delete(Expenditure).where(Expenditure.country_code == country_code))
    session.execute(sql_delete(CountryAccount).where(CountryAccount.country_code == country_code))
    session.execute(sql_delete(AccountMap).where(AccountMap.country_code == country_code))
    session.execute(sql_delete(IngestionRun).where(IngestionRun.country_code == country_code))
    session.flush()


def _template_maps_for_layout(layout_id: str, country_code: str) -> list[AccountMap]:
    template_code = TEMPLATE_COUNTRY_CODES[layout_id]
    copied: list[AccountMap] = []
    for item in load_account_maps(MAPPINGS_DIR / "account_map.csv"):
        if item.country_code != template_code:
            continue
        copied.append(
            AccountMap(
                country_code=country_code,
                account_code=item.account_code,
                sha_code=item.sha_code,
                srhr_code=item.srhr_code,
                confidence=item.confidence,
                generic=item.generic,
                notes=item.notes,
            )
        )
    return copied


def _persist_result(
    session: Session,
    result: AdapterResult,
    maps_by_key: dict[tuple[str, str], AccountMap],
    keyword_rules: list[KeywordRule],
) -> tuple[int, int, int]:
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

    expenditures = 0
    flags = 0
    classifications = 0
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
        expenditures += 1

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
            flags += 1

        session.add(to_classification_row(expenditure.id or 0, draft))
        classifications += 1

    return expenditures, flags, classifications


def ingest_file(
    path: Path,
    country_name: str,
    country_code: str | None = None,
    *,
    session: Session,
    flag_emoji: str | None = None,
) -> IngestOutcome:
    name = country_name.strip()
    if not name:
        raise ValueError("country_name is required")
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("The uploaded file is empty")

    emoji = normalize_flag_emoji(flag_emoji)
    seed_reference_data(session)
    code, replaced = allocate_country_code(session, name, country_code)
    result = load_extract(path, code)

    existing = session.get(Country, code)
    if existing is None:
        session.add(
            Country(
                country_code=code,
                country_name=name,
                primary_currency=result.primary_currency or "XXX",
                language=result.language,
                flag_emoji=emoji,
            )
        )
    else:
        existing.country_name = name
        existing.primary_currency = result.primary_currency or existing.primary_currency
        existing.language = result.language
        if emoji is not None:
            existing.flag_emoji = emoji
        session.add(existing)
        replaced = True
    session.flush()

    if replaced:
        _delete_country_children(session, code)

    template_maps = _template_maps_for_layout(result.layout_id, code)
    for item in template_maps:
        session.add(item)
    session.flush()

    maps_by_key = {(item.country_code, item.account_code): item for item in template_maps}
    keyword_rules = load_keyword_rules(MAPPINGS_DIR / "keyword_rules.csv")
    expenditures, flags, classifications = _persist_result(session, result, maps_by_key, keyword_rules)
    country = session.get(Country, code)
    session.commit()

    return IngestOutcome(
        country_code=code,
        country_name=name,
        flag_emoji=country.flag_emoji if country is not None else emoji,
        source_filename=result.source_filename,
        source_format=result.source_format,
        layout_id=result.layout_id,
        record_count=expenditures,
        flag_count=flags,
        classification_count=classifications,
        replaced=replaced,
    )


def run_ingest(
    path: Path,
    country_name: str,
    country_code: str | None = None,
    flag_emoji: str | None = None,
) -> IngestOutcome:
    init_database()
    with get_session() as session:
        return ingest_file(path, country_name, country_code, session=session, flag_emoji=flag_emoji)
