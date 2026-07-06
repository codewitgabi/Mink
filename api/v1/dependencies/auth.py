from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Header, HTTPException, status


async def get_current_user_id(x_user_id: Optional[str] = Header(default=None)) -> str:
    """
    Temporary auth stub: trusts the ``X-User-Id`` header as the caller's identity.

    Replace with real JWT/session auth later — callers only depend on this
    function's signature, not its implementation.
    """
    if not x_user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-User-Id header")

    try:
        ObjectId(x_user_id)
    except InvalidId:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid X-User-Id header")

    return x_user_id
