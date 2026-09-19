import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from api.deps import get_db
from api.main import app
from pipeline import models as _models  # noqa: F401


@pytest.fixture
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    return test_engine


@pytest.fixture
def session(engine):
    with Session(engine) as item:
        yield item


@pytest.fixture
def client(engine):
    def override_get_db():
        with Session(engine) as item:
            yield item

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
