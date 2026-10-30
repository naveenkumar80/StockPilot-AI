import pytest
import os
import sys

# Ensure services/api and workspace root are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.services.seed_data import seed_database_if_empty


@pytest.fixture(scope="session", autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database_if_empty(db)
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
