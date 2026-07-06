from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT

from api.v1.utils.logger import get_logger

logger = get_logger("indexes")


async def create_indexes(database: AsyncIOMotorDatabase) -> None:
    """
    Ensure all collection indexes exist.
    """

    await database["users"].create_index("handle", unique=True)
    await database["users"].create_index("email", unique=True, sparse=True)
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

    logger.info("Indexes ensured")
