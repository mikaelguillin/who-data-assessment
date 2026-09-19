from __future__ import annotations

import os
import tempfile
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

from pipeline import models as _models  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent


def resolve_var_dir() -> Path:
    override = os.environ.get("VAR_DIR")
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path
    if os.environ.get("VERCEL"):
        path = Path(tempfile.gettempdir()) / "who-data-assessment"
        path.mkdir(parents=True, exist_ok=True)
        return path
    path = ROOT / "var"
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        path = Path(tempfile.gettempdir()) / "who-data-assessment"
        path.mkdir(parents=True, exist_ok=True)
        return path


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://") or url.startswith("sqlite:"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def resolve_database_url(var_dir: Path | None = None) -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if url:
        return normalize_database_url(url)
    directory = var_dir if var_dir is not None else resolve_var_dir()
    return f"sqlite:///{directory / 'harmonized.db'}"


def create_db_engine(url: str | None = None) -> Engine:
    database_url = url or resolve_database_url()
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return create_engine(
        database_url,
        echo=False,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )


VAR_DIR = resolve_var_dir()
UPLOADS_DIR = VAR_DIR / "uploads"
DB_PATH = VAR_DIR / "harmonized.db"
DATABASE_URL = resolve_database_url(VAR_DIR)
engine = create_db_engine(DATABASE_URL)


def ensure_var_dir() -> None:
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_schema(db_engine: Engine | None = None) -> None:
    target = db_engine if db_engine is not None else engine
    inspector = inspect(target)
    if "country" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("country")}
    if "flag_emoji" not in columns:
        with target.begin() as connection:
            connection.execute(text("ALTER TABLE country ADD COLUMN flag_emoji VARCHAR"))


def init_database() -> None:
    ensure_var_dir()
    SQLModel.metadata.create_all(engine)
    ensure_schema()


def reset_database() -> None:
    ensure_var_dir()
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    init_database()
    return Session(engine)
