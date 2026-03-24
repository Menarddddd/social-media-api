from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account_recovery import AccountRecoveryToken
from app.models.refresh_token import RefreshToken
from app.models.user import Role, User, UserDeletion


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


# for account recovery
async def get_user_by_email_db(email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all_active_users_db(db: AsyncSession, limit: int, offset: int):
    result = await db.execute(
        select(User)
        .where(User.is_deleted.is_(False), User.role != Role.ADMIN)
        .offset(offset)
        .limit(limit)
        .order_by(User.username)
    )

    return result.scalars().all()


async def get_active_admins_db(db: AsyncSession, limit: int, offset: int):
    result = await db.execute(
        select(User)
        .where(User.role == Role.ADMIN, User.is_deleted.is_(False))
        .offset(offset)
        .limit(limit)
    )

    return result.scalars().all()


# USER DELETION
async def get_users_deletions_db(db: AsyncSession, limit: int, offset: int):
    result = await db.execute(
        select(UserDeletion)
        .options(
            selectinload(UserDeletion.user), selectinload(UserDeletion.deleted_by_user)
        )
        .offset(offset)
        .limit(limit)
    )

    return result.scalars().all()


async def get_user_from_user_deletion_id_db(deletion_id: UUID, db: AsyncSession):
    result = await db.execute(
        select(func.count())
        .where(UserDeletion.id == deletion_id)
        .options(selectinload(UserDeletion.user).selectinload(User.user_deletion))
    )

    return result.scalar_one_or_none()


async def get_user_deletion_by_user_id_db(user_id: UUID, db: AsyncSession):
    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.is_deleted.is_(True))
        .options(
            selectinload(User.user_deletion).selectinload(UserDeletion.deleted_by_user)
        )
    )

    return result.scalar_one_or_none()


async def get_user_deletion_by_user_username_db(username: str, db: AsyncSession):
    result = await db.execute(
        select(User)
        .where(User.username == username, User.is_deleted.is_(True))
        .options(
            selectinload(User.user_deletion).selectinload(UserDeletion.deleted_by_user)
        )
    )

    return result.scalar_one_or_none()


async def delete_user_deletion_by_username_db(username, db: AsyncSession):
    await db.execute(delete(UserDeletion).where(UserDeletion.username == username))


# REFRESH TOKEN
async def get_refresh_token_db(hashed_refersh_token: str, db: AsyncSession):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.hashed_token == hashed_refersh_token)
    )

    return result.scalar_one_or_none()
