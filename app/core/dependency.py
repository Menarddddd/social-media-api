from typing import Annotated
from uuid import UUID


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from jwt import ExpiredSignatureError, PyJWTError

from app.core.database import get_db
from app.core.settings import settings
from app.models.user import User
from app.repositories.user import get_active_user_by_id_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WwW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.ACCESS_SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exc

        try:
            user_id = UUID(user_id)

        except ValueError:
            raise credentials_exc

        user = await get_active_user_by_id_db(user_id, db)

        if not user:
            raise credentials_exc

        return user

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except PyJWTError:
        raise credentials_exc
