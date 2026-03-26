from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.models.user import User


async def _get_active_user_db(filter, db: AsyncSession, *options):
    stmt = select(User).where(filter, User.is_deleted.is_(False))

    if options:
        stmt.options(*options)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def get_active_user_by_id_db(user_id: UUID, db: AsyncSession, *options):
    return await _get_active_user_db(User.id == user_id, db, *options)


async def get_active_user_by_username_db(username: str, db: AsyncSession, *options):
    return await _get_active_user_db(User.username == username, db, *options)


async def get_active_admin_by_id_db(id: UUID, db: AsyncSession):
    result = await db.execute(
        select(User).where(User.id == id, User.is_deleted.is_(False))
    )

    return result.scalar_one_or_none()


# for account recovery
async def get_user_by_email_db(email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


# REFRESH TOKEN
async def get_refresh_token_db(hashed_refersh_token: str, db: AsyncSession):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.hashed_token == hashed_refersh_token)
    )

    return result.scalar_one_or_none()
