"""
Pytest Fixtures for AICTE ONE Testing
Uses an isolated temporary database for repeatable testing.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.main import app
from backend.seed import seed_database
import backend.database as db_module

TEST_DB_FILE = "./test_aicte.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

@pytest.fixture(scope="session", autouse=True)
def test_db_session():
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db_module.engine = test_engine
    db_module.SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=test_engine)
    test_session = TestingSessionLocal()
    seed_database(test_session)
    test_session.close()

    yield TestingSessionLocal

    app.dependency_overrides.clear()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
