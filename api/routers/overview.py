from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import select

from api.deps import SessionDep
from api.schemas import (
    CountItem,
    CountrySummary,
    CurrencySpend,
    OverviewOut,
)
from pipeline.models import Classification, Country, Expenditure, QualityFlag, ShaRef, SrhrRef

router = APIRouter(prefix="/api/overview", tags=["overview"])

REVIEW_CONFIDENCE = ("low", "unmapped")
REVIEW_FLAGS = ("description_untrusted",)


def _review_expenditure_ids(session: SessionDep) -> set[int]:
    low = session.exec(
        select(Classification.expenditure_id).where(
            Classification.is_current == True,  # noqa: E712
            Classification.confidence.in_(REVIEW_CONFIDENCE),
        )
    ).all()
    flagged = session.exec(
        select(QualityFlag.expenditure_id).where(QualityFlag.flag_code.in_(REVIEW_FLAGS))
    ).all()
    return set(low) | set(flagged)


@router.get("")
def get_overview(session: SessionDep) -> OverviewOut:
    total = session.exec(select(func.count()).select_from(Expenditure)).one()
    review_ids = _review_expenditure_ids(session)
    review_count = len(review_ids)
    review_share = (review_count / total) if total else 0.0

    countries = session.exec(select(Country).order_by(Country.country_code)).all()
    country_summaries: list[CountrySummary] = []
    for country in countries:
        rows = session.exec(
            select(Expenditure.id, Expenditure.currency_original, Expenditure.amount_native).where(
                Expenditure.country_code == country.country_code
            )
        ).all()
        currencies: dict[str, CurrencySpend] = {}
        review_for_country = 0
        for exp_id, currency, amount in rows:
            bucket = currencies.setdefault(
                currency, CurrencySpend(currency=currency, amount=0.0, count=0)
            )
            bucket.count += 1
            if amount is not None:
                bucket.amount += amount
            if exp_id in review_ids:
                review_for_country += 1
        country_summaries.append(
            CountrySummary(
                country_code=country.country_code,
                country_name=country.country_name,
                record_count=len(rows),
                review_count=review_for_country,
                currencies=sorted(currencies.values(), key=lambda item: item.currency),
            )
        )

    sha_rows = session.exec(
        select(
            Classification.sha_code,
            ShaRef.sha_description,
            func.count(),
        )
        .select_from(Classification)
        .outerjoin(ShaRef, ShaRef.sha_code == Classification.sha_code)
        .where(Classification.is_current == True)  # noqa: E712
        .group_by(Classification.sha_code, ShaRef.sha_description)
    ).all()
    by_sha = [
        CountItem(key=code or "unmapped", label=label or "Unmapped", count=count)
        for code, label, count in sha_rows
    ]

    srhr_rows = session.exec(
        select(
            Classification.srhr_code,
            SrhrRef.srhr_description,
            func.count(),
        )
        .select_from(Classification)
        .outerjoin(SrhrRef, SrhrRef.srhr_code == Classification.srhr_code)
        .where(Classification.is_current == True)  # noqa: E712
        .group_by(Classification.srhr_code, SrhrRef.srhr_description)
    ).all()
    by_srhr = [
        CountItem(key=code or "unmapped", label=label or "Unmapped", count=count)
        for code, label, count in srhr_rows
    ]

    confidence_rows = session.exec(
        select(Classification.confidence, func.count())
        .where(Classification.is_current == True)  # noqa: E712
        .group_by(Classification.confidence)
    ).all()
    by_confidence = [CountItem(key=key, count=count) for key, count in confidence_rows]

    flag_rows = session.exec(
        select(QualityFlag.flag_code, func.count()).group_by(QualityFlag.flag_code)
    ).all()
    by_flag = [CountItem(key=key, count=count) for key, count in flag_rows]

    spend_rows = session.exec(
        select(
            Expenditure.currency_original,
            func.count(),
            func.coalesce(func.sum(Expenditure.amount_native), 0.0),
        ).group_by(Expenditure.currency_original)
    ).all()
    spend_by_currency = [
        CurrencySpend(currency=currency, count=count, amount=float(amount))
        for currency, count, amount in spend_rows
    ]

    return OverviewOut(
        expenditure_count=int(total),
        review_count=review_count,
        review_share=review_share,
        countries=country_summaries,
        by_sha=sorted(by_sha, key=lambda item: item.count, reverse=True),
        by_srhr=sorted(by_srhr, key=lambda item: item.count, reverse=True),
        by_confidence=by_confidence,
        by_flag=sorted(by_flag, key=lambda item: item.count, reverse=True),
        spend_by_currency=spend_by_currency,
    )
