import asyncio

import pytest
from bson import ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.v1.services.user import user_service
from main import app
from tests.conftest import TEST_USER_ID


async def _seed_user(mongo_db, user_id: str = TEST_USER_ID, **overrides) -> dict:
    doc = {
        "_id": ObjectId(user_id),
        "display_name": "Test User",
        "email": "test@example.com",
        "login_provider": "magic_link",
        **overrides,
    }
    await mongo_db["users"].insert_one(doc)
    return doc


@pytest.mark.asyncio
async def test_new_user_defaults_onboarding_to_incomplete(mongo_db):
    await _seed_user(mongo_db)
    user = await user_service.get_by_id(TEST_USER_ID)
    assert user.onboarding_completed is False


@pytest.mark.asyncio
async def test_complete_onboarding_persists_flag(mongo_db):
    await _seed_user(mongo_db)

    updated = await user_service.complete_onboarding(TEST_USER_ID)
    assert updated.onboarding_completed is True

    refetched = await user_service.get_by_id(TEST_USER_ID)
    assert refetched.onboarding_completed is True


@pytest.mark.asyncio
async def test_complete_onboarding_missing_user_raises_404(mongo_db):
    with pytest.raises(HTTPException) as exc_info:
        await user_service.complete_onboarding(str(ObjectId()))
    assert exc_info.value.status_code == 404


def test_get_me_returns_onboarding_status(client, mongo_db):
    asyncio.run(_seed_user(mongo_db))

    res = client.get("/api/v1/users/me")
    assert res.status_code == 200
    assert res.json()["data"]["onboarding_completed"] is False


def test_complete_onboarding_endpoint_marks_user_complete(client, mongo_db):
    asyncio.run(_seed_user(mongo_db))

    res = client.post("/api/v1/users/me/onboarding/complete")
    assert res.status_code == 200
    assert res.json()["data"]["onboarding_completed"] is True

    follow_up = client.get("/api/v1/users/me")
    assert follow_up.json()["data"]["onboarding_completed"] is True


def test_complete_onboarding_requires_auth(mongo_db):
    anon_client = TestClient(app, raise_server_exceptions=False)
    res = anon_client.post("/api/v1/users/me/onboarding/complete")
    assert res.status_code == 401
