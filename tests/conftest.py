import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from api.database import db
from api.v1.dependencies.auth import get_current_user_id
from main import app

TEST_USER_ID = "111111111111111111111111"


@pytest.fixture
def mongo_db():
    """Point the `db` singleton at an in-memory Mongo double for the test."""
    database = AsyncMongoMockClient()["mink_test"]
    db._db = database
    yield database
    db._db = None


@pytest.fixture
def client(mongo_db):
    # Instantiated without `with TestClient(...)` so the app's lifespan
    # (real db.connect() / create_indexes) never runs — `mongo_db` already
    # stands in for the database.
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.pop(get_current_user_id, None)
