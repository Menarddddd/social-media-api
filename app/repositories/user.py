from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
