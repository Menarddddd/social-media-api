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
from app.exceptions.exception import FieldNotFoundException
from app.models.user import Role, User
from app.repositories.comment import get_comment_by_id_db
from app.repositories.post import get_post_by_id_db
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


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


async def post_owner(
    post_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    post = await get_post_by_id_db(post_id, db)
    if not post:
        raise FieldNotFoundException("post", str(post_id))

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not own this post to modify it",
        )

    return post


async def comment_owner(
    comment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    comment = await get_comment_by_id_db(comment_id, db)
    if not comment:
        raise FieldNotFoundException("comment", str(comment_id))

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not own this comment to modify it",
        )

    return comment
