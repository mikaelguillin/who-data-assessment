from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from pipeline.db import engine, ensure_var_dir


def get_db() -> Generator[Session, None, None]:
    ensure_var_dir()
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
