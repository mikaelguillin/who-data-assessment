from typing import Annotated

from fastapi import APIRouter, Query
from sqlmodel import select

from api.deps import SessionDep
from api.schemas import AccountMapOut, MappingListOut, RefItem
from pipeline.models import AccountMap, CountryAccount, ShaRef, SrhrRef

router = APIRouter(prefix="/api", tags=["mappings"])


@router.get("/mappings")
def list_mappings(
    session: SessionDep,
    country: Annotated[str | None, Query()] = None,
) -> MappingListOut:
    accounts = session.exec(select(CountryAccount).order_by(CountryAccount.country_code)).all()
    maps = session.exec(select(AccountMap)).all()
    map_index = {(item.country_code, item.account_code): item for item in maps}

    items: list[AccountMapOut] = []
    seen: set[tuple[str, str]] = set()
    for account in accounts:
        if country and account.country_code != country:
            continue
        mapped = map_index.get((account.country_code, account.account_code))
        seen.add((account.country_code, account.account_code))
        items.append(
            AccountMapOut(
                country_code=account.country_code,
                account_code=account.account_code,
                account_label=account.account_label,
                sha_code=mapped.sha_code if mapped else None,
                srhr_code=mapped.srhr_code if mapped else None,
                confidence=mapped.confidence if mapped else None,
                generic=mapped.generic if mapped else False,
                notes=mapped.notes if mapped else None,
                mapped=mapped is not None,
            )
        )

    for mapped in maps:
        key = (mapped.country_code, mapped.account_code)
        if key in seen:
            continue
        if country and mapped.country_code != country:
            continue
        items.append(
            AccountMapOut(
                country_code=mapped.country_code,
                account_code=mapped.account_code,
                account_label=None,
                sha_code=mapped.sha_code,
                srhr_code=mapped.srhr_code,
                confidence=mapped.confidence,
                generic=mapped.generic,
                notes=mapped.notes,
                mapped=True,
            )
        )
    return MappingListOut(items=items)


@router.get("/refs/sha")
def list_sha(session: SessionDep) -> list[RefItem]:
    rows = session.exec(select(ShaRef).order_by(ShaRef.sha_code)).all()
    return [RefItem(code=row.sha_code, description=row.sha_description) for row in rows]


@router.get("/refs/srhr")
def list_srhr(session: SessionDep) -> list[RefItem]:
    rows = session.exec(select(SrhrRef).order_by(SrhrRef.srhr_code)).all()
    return [RefItem(code=row.srhr_code, description=row.srhr_description) for row in rows]
