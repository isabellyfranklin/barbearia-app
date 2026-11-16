import os

os.environ["DATABASE_URL"] = "sqlite:///./test_barbearia.db"
os.environ["JWT_SECRET"] = "test-secret-only"
os.environ["MIN_LEAD_MINUTES"] = "0"
os.environ["SEED_ON_STARTUP"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.seed import DEMO_PASSWORD, seed_demo


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def demo(client):
    with SessionLocal() as db:
        return seed_demo(db)


@pytest.fixture()
def login(client):
    def _login(email: str, password: str = DEMO_PASSWORD) -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login


@pytest.fixture()
def admin_headers(login, demo):
    return login(demo["admin"])


@pytest.fixture()
def barber_headers(login, demo):
    return login(demo["barber"])


@pytest.fixture()
def client_headers(login, demo):
    return login(demo["client"])
