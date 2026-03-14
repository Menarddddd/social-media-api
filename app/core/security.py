from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.settings import settings


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
