from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure

from api.v1.utils.logger import get_logger

logger = get_logger("indexes")


async def create_indexes(database: AsyncIOMotorDatabase) -> None:
    """
    Ensure all collection indexes exist.
    """

    try:
        # Pre-auth builds indexed `handle` as unique+non-sparse; now that users can
        # be provisioned via magic-link login before picking a handle, multiple
        # `None` handles must be allowed, which requires a sparse index instead.
        await database["users"].drop_index("handle_1")
    except OperationFailure:
        pass
    await database["users"].create_index("handle", unique=True, sparse=True)
    await database["users"].create_index("email", unique=True, sparse=True)
    await database["users"].create_index("magic_issuer", unique=True, sparse=True)
    await database["users"].create_index([("handle", TEXT), ("display_name", TEXT)])

    await database["friendships"].create_index(
        [("requester_id", ASCENDING), ("addressee_id", ASCENDING)], unique=True
    )
    await database["friendships"].create_index(
        [("addressee_id", ASCENDING), ("status", ASCENDING)]
    )

    await database["payment_requests"].create_index(
        [("payer_id", ASCENDING), ("status", ASCENDING)]
    )
    await database["payment_requests"].create_index(
        [("requester_id", ASCENDING), ("status", ASCENDING)]
    )
    await database["payment_requests"].create_index("expires_at")

    await database["activities"].create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)]
    )
    await database["activities"].create_index(
        [("user_id", ASCENDING), ("direction", ASCENDING)]
    )

    await database["notifications"].create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)]
    )
    await database["notifications"].create_index(
        [("user_id", ASCENDING), ("read_at", ASCENDING)]
    )

    await database["refresh_tokens"].create_index("token_hash", unique=True)
    await database["refresh_tokens"].create_index("user_id")
    await database["refresh_tokens"].create_index("expires_at", expireAfterSeconds=0)

    logger.info("Indexes ensured")
