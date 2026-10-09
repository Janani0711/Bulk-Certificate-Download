import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
import app.database as database
from app.config import settings

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db(monkeypatch):
    test_engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    database.Base.metadata.create_all(bind=test_engine)

    # Patch SessionLocal so background workers use test database
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(database, "engine", test_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        database.Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db, tmp_path):
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    original_storage = settings.STORAGE_DIR
    settings.STORAGE_DIR = tmp_path

    app.dependency_overrides[database.get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    settings.STORAGE_DIR = original_storage
