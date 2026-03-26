from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.user import Role, User, UserDeletion


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


async def get_user_deletion_by_user_id_db(user_id: UUID, db: AsyncSession):
    """Get user deletion record by the deleted user's ID"""
    stmt = (
        select(UserDeletion)
        .join(User, User.id == UserDeletion.user_id)
        .where(User.id == user_id, User.is_deleted.is_(True))
        .options(joinedload(UserDeletion.deleted_by_user))
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_user_deletion_by_id_db(deletion_id: UUID, db: AsyncSession):
    """Get user deletion record by the deletion record ID"""
    stmt = (
        select(UserDeletion)
        .where(UserDeletion.id == deletion_id)
        .options(
            joinedload(UserDeletion.user), joinedload(UserDeletion.deleted_by_user)
        )
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()
