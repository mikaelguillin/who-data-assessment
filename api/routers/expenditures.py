from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from sqlalchemy import func
from sqlmodel import col, or_, select

from api.deps import SessionDep
from api.schemas import (
    ClassificationOut,
    ExpenditureDetailOut,
    ExpenditureListItem,
    ExpenditureListOut,
    FlagOut,
    IngestionRunOut,
    LineOut,
    OverrideIn,
)
from pipeline.models import (
    Classification,
    Expenditure,
    ExpenditureLine,
    IngestionRun,
    QualityFlag,
    ShaRef,
    SrhrRef,
)

router = APIRouter(prefix="/api/expenditures", tags=["expenditures"])

ExpenditureId = Annotated[int, Path(ge=1, description="Expenditure surrogate id")]


def _current_classification(session: SessionDep, expenditure_id: int) -> Classification | None:
    return session.exec(
        select(Classification).where(
            Classification.expenditure_id == expenditure_id,
            Classification.is_current == True,  # noqa: E712
        )
    ).first()


@router.get("")
def list_expenditures(
    session: SessionDep,
    country: Annotated[str | None, Query()] = None,
    sha: Annotated[str | None, Query()] = None,
    srhr: Annotated[str | None, Query()] = None,
    confidence: Annotated[str | None, Query()] = None,
    flag: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
    review_only: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ExpenditureListOut:
    statement = (
        select(Expenditure, Classification)
        .outerjoin(
            Classification,
            (Classification.expenditure_id == Expenditure.id)
            & (Classification.is_current == True),  # noqa: E712
        )
    )
    if country:
        statement = statement.where(Expenditure.country_code == country)
    if sha:
        if sha == "unmapped":
            statement = statement.where(Classification.sha_code.is_(None))
        else:
            statement = statement.where(Classification.sha_code == sha)
    if srhr:
        statement = statement.where(Classification.srhr_code == srhr)
    if confidence:
        statement = statement.where(Classification.confidence == confidence)
    if flag:
        flagged_ids = select(QualityFlag.expenditure_id).where(QualityFlag.flag_code == flag)
        statement = statement.where(col(Expenditure.id).in_(flagged_ids))
    if review_only:
        untrusted_ids = select(QualityFlag.expenditure_id).where(
            QualityFlag.flag_code == "description_untrusted"
        )
        statement = statement.where(
            or_(
                Classification.confidence.in_(("low", "unmapped")),
                col(Expenditure.id).in_(untrusted_ids),
            )
        )
    if q:
        like = f"%{q}%"
        statement = statement.where(
            or_(
                Expenditure.source_transaction_id.like(like),
                Expenditure.description_raw.like(like),
                Expenditure.account_code.like(like),
            )
        )

    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    rows = session.exec(
        statement.order_by(Expenditure.id).offset(offset).limit(limit)
    ).all()

    ids = [exp.id for exp, _cls in rows if exp.id is not None]
    flags_by_id: dict[int, list[str]] = {exp_id: [] for exp_id in ids}
    if ids:
        flag_rows = session.exec(
            select(QualityFlag).where(col(QualityFlag.expenditure_id).in_(ids))
        ).all()
        for flag_row in flag_rows:
            flags_by_id.setdefault(flag_row.expenditure_id, []).append(flag_row.flag_code)

    items = [
        ExpenditureListItem(
            id=exp.id or 0,
            country_code=exp.country_code,
            source_transaction_id=exp.source_transaction_id,
            transaction_date=exp.transaction_date,
            ministry_code=exp.ministry_code,
            account_code=exp.account_code,
            description_raw=exp.description_raw,
            supplier=exp.supplier,
            amount_native=exp.amount_native,
            currency_original=exp.currency_original,
            sha_code=cls.sha_code if cls else None,
            srhr_code=cls.srhr_code if cls else None,
            method=cls.method if cls else None,
            confidence=cls.confidence if cls else None,
            flag_codes=sorted(set(flags_by_id.get(exp.id or 0, []))),
        )
        for exp, cls in rows
    ]
    return ExpenditureListOut(total=int(total), limit=limit, offset=offset, items=items)


@router.get("/{expenditure_id}")
def get_expenditure(session: SessionDep, expenditure_id: ExpenditureId) -> ExpenditureDetailOut:
    expenditure = session.get(Expenditure, expenditure_id)
    if expenditure is None:
        raise HTTPException(status_code=404, detail="Expenditure not found")

    run = session.get(IngestionRun, expenditure.ingestion_run_id)
    flags = session.exec(
        select(QualityFlag).where(QualityFlag.expenditure_id == expenditure_id)
    ).all()
    lines = session.exec(
        select(ExpenditureLine).where(ExpenditureLine.expenditure_id == expenditure_id)
    ).all()
    classification = _current_classification(session, expenditure_id)
    sha_desc = None
    srhr_desc = None
    if classification and classification.sha_code:
        sha = session.get(ShaRef, classification.sha_code)
        sha_desc = sha.sha_description if sha else None
    if classification and classification.srhr_code:
        srhr = session.get(SrhrRef, classification.srhr_code)
        srhr_desc = srhr.srhr_description if srhr else None

    return ExpenditureDetailOut(
        id=expenditure.id or 0,
        country_code=expenditure.country_code,
        source_transaction_id=expenditure.source_transaction_id,
        source_row_ref=expenditure.source_row_ref,
        transaction_date=expenditure.transaction_date,
        fiscal_year=expenditure.fiscal_year,
        ministry_code=expenditure.ministry_code,
        ministry_name=expenditure.ministry_name,
        account_code=expenditure.account_code,
        description_raw=expenditure.description_raw,
        description_norm=expenditure.description_norm,
        supplier=expenditure.supplier,
        amount_original=expenditure.amount_original,
        amount_native=expenditure.amount_native,
        currency_original=expenditure.currency_original,
        payment_method=expenditure.payment_method,
        raw_payload_json=expenditure.raw_payload_json,
        ingestion_run=IngestionRunOut(
            id=run.id or 0,
            country_code=run.country_code,
            source_filename=run.source_filename,
            source_format=run.source_format,
            ingested_at=run.ingested_at,
            record_count=run.record_count,
            notes=run.notes,
        )
        if run
        else None,
        flags=[FlagOut(flag_code=item.flag_code, detail=item.detail) for item in flags],
        lines=[
            LineOut(
                source_sub_id=item.source_sub_id,
                description=item.description,
                amount=item.amount,
            )
            for item in lines
        ],
        classification=ClassificationOut(
            sha_code=classification.sha_code,
            sha_description=sha_desc,
            srhr_code=classification.srhr_code,
            srhr_description=srhr_desc,
            method=classification.method,
            confidence=classification.confidence,
            rationale=classification.rationale,
            classified_at=classification.classified_at,
            classified_by=classification.classified_by,
        )
        if classification
        else None,
    )


@router.post("/{expenditure_id}/override")
def override_classification(
    session: SessionDep,
    expenditure_id: ExpenditureId,
    body: OverrideIn,
) -> ClassificationOut:
    expenditure = session.get(Expenditure, expenditure_id)
    if expenditure is None:
        raise HTTPException(status_code=404, detail="Expenditure not found")
    if body.sha_code and session.get(ShaRef, body.sha_code) is None:
        raise HTTPException(status_code=400, detail="Unknown SHA code")
    if body.srhr_code and session.get(SrhrRef, body.srhr_code) is None:
        raise HTTPException(status_code=400, detail="Unknown SRHR code")

    current = session.exec(
        select(Classification).where(
            Classification.expenditure_id == expenditure_id,
            Classification.is_current == True,  # noqa: E712
        )
    ).all()
    for row in current:
        row.is_current = False
        session.add(row)

    replacement = Classification(
        expenditure_id=expenditure_id,
        sha_code=body.sha_code,
        srhr_code=body.srhr_code,
        method="analyst_override",
        confidence="high",
        rationale=body.rationale,
        is_current=True,
        classified_at=datetime.now(UTC),
        classified_by=body.reviewer,
    )
    session.add(replacement)
    session.commit()
    session.refresh(replacement)

    sha_desc = None
    srhr_desc = None
    if replacement.sha_code:
        sha = session.get(ShaRef, replacement.sha_code)
        sha_desc = sha.sha_description if sha else None
    if replacement.srhr_code:
        srhr = session.get(SrhrRef, replacement.srhr_code)
        srhr_desc = srhr.srhr_description if srhr else None

    return ClassificationOut(
        sha_code=replacement.sha_code,
        sha_description=sha_desc,
        srhr_code=replacement.srhr_code,
        srhr_description=srhr_desc,
        method=replacement.method,
        confidence=replacement.confidence,
        rationale=replacement.rationale,
        classified_at=replacement.classified_at,
        classified_by=replacement.classified_by,
    )
