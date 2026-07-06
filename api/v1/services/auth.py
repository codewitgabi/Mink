import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from magic_admin import Magic

from api.database import db
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.utils.config import config
from api.v1.utils.jwt import encode_access_token

magic_client = Magic(
    api_secret_key=config.MAGIC_SECRET_KEY, client_id=config.MAGIC_CLIENT_ID
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    """Business logic for Magic (magic.link) authentication and session tokens."""

    @property
    def _refresh_tokens(self):
        return db.get_db()["refresh_tokens"]

    async def _issue_tokens(self, user_id: str) -> tuple[str, str]:
        access_token = encode_access_token(user_id)

        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=config.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self._refresh_tokens.insert_one(
            {
                "user_id": user_id,
                "token_hash": _hash_token(refresh_token),
                "expires_at": expires_at,
                "revoked_at": None,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return access_token, refresh_token

    async def login(self, authorization_header: str) -> tuple[User, str, str]:
        did_token = magic_client.Utils.parse_authorization_header(authorization_header)
        magic_client.Token.validate(did_token)
        issuer = magic_client.Token.get_issuer(did_token)
        metadata = magic_client.User.get_metadata_by_issuer(issuer)

        user = await user_service.get_or_create_by_magic_issuer(
            issuer, metadata.data["email"]
        )
        access_token, refresh_token = await self._issue_tokens(user.id)
        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        doc = await self._refresh_tokens.find_one(
            {
                "token_hash": _hash_token(refresh_token),
                "revoked_at": None,
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            }
        )
        if doc is None:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token"
            )

        await self._refresh_tokens.update_one(
            {"_id": doc["_id"]}, {"$set": {"revoked_at": datetime.now(timezone.utc)}}
        )
        return await self._issue_tokens(doc["user_id"])

    async def logout(self, refresh_token: str) -> None:
        await self._refresh_tokens.update_one(
            {"token_hash": _hash_token(refresh_token), "revoked_at": None},
            {"$set": {"revoked_at": datetime.now(timezone.utc)}},
        )


auth_service = AuthService()
