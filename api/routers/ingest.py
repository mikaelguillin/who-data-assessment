from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlmodel import select

from api.deps import SessionDep
from api.schemas import CountryOut, IngestOut
from pipeline.adapters.base import UnsupportedLayoutError
from pipeline.db import UPLOADS_DIR
from pipeline.ingest import ingest_file
from pipeline.models import Country

router = APIRouter(prefix="/api", tags=["ingest"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".json"}


def _safe_filename(name: str | None) -> str:
    filename = Path(name or "upload").name
    if not filename or filename in {".", ".."}:
        return "upload"
    return filename


def _save_upload(upload: UploadFile) -> Path:
    filename = _safe_filename(upload.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a CSV, Excel (.xlsx), or JSON extract.",
        )
    dest_dir = UPLOADS_DIR / uuid4().hex
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    size = 0
    try:
        with dest.open("wb") as handle:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=400, detail="File is too large (maximum 20 MB).")
                handle.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        dest_dir.rmdir()
        raise
    if size == 0:
        dest.unlink(missing_ok=True)
        dest_dir.rmdir()
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    return dest


@router.get("/countries")
def list_countries(session: SessionDep) -> list[CountryOut]:
    countries = session.exec(select(Country).order_by(Country.country_name)).all()
    return [
        CountryOut(
            country_code=item.country_code,
            country_name=item.country_name,
            primary_currency=item.primary_currency,
            language=item.language,
        )
        for item in countries
    ]


@router.post("/ingest")
def ingest_country(
    session: SessionDep,
    file: Annotated[UploadFile, File()],
    country_name: Annotated[str, Form()],
    country_code: Annotated[str | None, Form()] = None,
) -> IngestOut:
    name = country_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="country_name is required")
    code = country_code.strip() if country_code and country_code.strip() else None
    saved = _save_upload(file)
    try:
        outcome = ingest_file(saved, name, code, session=session)
    except UnsupportedLayoutError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestOut(
        country_code=outcome.country_code,
        country_name=outcome.country_name,
        source_filename=outcome.source_filename,
        source_format=outcome.source_format,
        layout_id=outcome.layout_id,
        record_count=outcome.record_count,
        flag_count=outcome.flag_count,
        classification_count=outcome.classification_count,
        replaced=outcome.replaced,
    )
