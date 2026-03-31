import jwt
import hmac
import secrets
import hashlib
from uuid import UUID
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.account_recovery import AccountRecoveryToken
from app.repositories.recovery_token import (
    get_user_from_recovery_token,
    mark_token_used_db,
)


password_hash = PasswordHash.recommended()


def hash_password(pwd: str) -> str:
    return password_hash.hash(pwd)


def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    return password_hash.verify(plain_pwd, hashed_pwd)


def create_access_token(sub: dict):
    to_encode = sub.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_MINUTES_EXPIRE
    )

    payload = jwt.encode(
        to_encode,
        settings.ACCESS_SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    return payload


def create_refresh_token(sub: dict):
    to_encode = sub.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_DAYS_EXPIRE
    )

    payload = jwt.encode(
        to_encode,
        settings.REFRESH_SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    return payload


def hash_refresh_token(token: str):
    return hmac.new(
        key=settings.REFRESH_SECRET_KEY.get_secret_value().encode(),
        msg=token.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


def verify_token(plain_token: str, hashed_token: str) -> bool:
    computed_hash = hash_refresh_token(plain_token)

    return secrets.compare_digest(computed_hash, hashed_token)


def hash_recovery_token(token: str):
    return hmac.new(
        key=settings.RECOVERY_SECRET_KEY.get_secret_value().encode(),
        msg=token.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


async def generate_recovery_token(user_id: UUID, db: AsyncSession):
    token = secrets.token_hex(32)
    token_hash = hash_recovery_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.RECOVERY_MINUTES
    )

    db_token = AccountRecoveryToken(
        user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )

    db.add(db_token)
    await db.flush()

    return token


async def verify_recovery_token(token: str, db: AsyncSession):
    token_hash = hash_recovery_token(token)

    db_token = await get_user_from_recovery_token(token_hash, db)
    if (
        not db_token
        or db_token.used
        or db_token.expires_at < datetime.now(timezone.utc)
    ):
        return None

    return db_token.user_id


async def mark_token_used(token: str, db: AsyncSession):
    token_hash = hash_recovery_token(token)
    await mark_token_used_db(token_hash, db)
