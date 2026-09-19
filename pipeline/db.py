from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from pipeline import models as _models  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
VAR_DIR = ROOT / "var"
DB_PATH = VAR_DIR / "harmonized.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)


def ensure_var_dir() -> None:
    VAR_DIR.mkdir(parents=True, exist_ok=True)


def reset_database() -> None:
    ensure_var_dir()
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
