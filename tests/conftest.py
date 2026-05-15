import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_orders.db")

from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./test_orders.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def isolated_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    return {"X-API-Key": "test-api-key"}


@pytest.fixture
def sample_pdf_bytes():
    path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        "DME Patient Demo Document CPAP.fax.pdf",
    )
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    pytest.skip("Sample PDF not found — skipping PDF regression test")


@pytest.fixture
def created_order(client, auth):
    resp = client.post(
        "/api/v1/orders/",
        json={
            "patient_first_name": "Marie",
            "patient_last_name": "Curie",
            "patient_dob": "12/05/1900",
        },
        headers=auth,
    )
    assert resp.status_code == 201
    return resp.json()
