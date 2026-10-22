"""
Test Configuration & Isolated Test Fixtures for AICTE ONE
Uses in-memory SQLite database to ensure zero mutation of production records.
"""
import pytest
import os
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment variable
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-aicte-one-2026-isolated"

from backend.database import Base, get_db
from backend.main import app
from backend.seed import seed_database
from backend.models import User, Institution, Application, Complaint, ComplianceObligation, Document

# In-memory SQLite for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(session=db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def get_user_token(client: TestClient, username: str, password: str = "AicteOne@2026!") -> str:
    for pwd in [password, "AicteOne@2026!", "NewSecurePassword@2026!", "AdminPass@2026!"]:
        resp = client.post("/api/auth/login", json={"username": username, "password": pwd})
        if resp.status_code == 200:
            return resp.json()["access_token"]
    assert False, f"Login failed for {username}: {resp.text}"

@pytest.fixture
def superadmin_token(client: TestClient) -> str:
    return get_user_token(client, "superadmin")

@pytest.fixture
def compliance_token(client: TestClient) -> str:
    return get_user_token(client, "compliance.officer")

@pytest.fixture
def security_token(client: TestClient) -> str:
    return get_user_token(client, "security.officer")

@pytest.fixture
def institute_head_token(client: TestClient) -> str:
    return get_user_token(client, "principal.gitm")

@pytest.fixture
def student_token(client: TestClient) -> str:
    return get_user_token(client, "student.aarav")
