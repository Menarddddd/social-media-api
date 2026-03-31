import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.exceptions.exception import FieldNotFoundException
from app.models.user import Role, User, UserDeletion
from app.repositories.admin import (
    get_user_deletion_by_id_db,
    get_user_deletion_by_user_id_db,
)
from app.repositories.user import get_active_user_by_id_db
from app.schemas.user import (
    UserDeletionLoadedResponse,
    UserDeletionResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)


async def promote_user_to_admin_service(user_id: UUID, db: AsyncSession):
    """Promote user to admin role"""

    logger.info(f"Promoting user to admin: {user_id}")

    user = await get_active_user_by_id_db(user_id, db)

    if not user:
        logger.warning(f"Promotion failed - user not found: {user_id}")
        raise FieldNotFoundException("user", str(user_id))

    user.role = Role.ADMIN

    logger.info(f"User promoted to admin: {user.username} (id: {user_id})")

    return {"message": f"You've successfuly promoted {user.username} to admin"}


async def admin_delete_profile_service(
    reason: str, user_id: UUID, admin: User, db: AsyncSession
):
    """Service to delete user by Admin"""
    logger.info(f"Admin deleting user: {user_id} by admin: {admin.username}")

    user = await get_active_user_by_id_db(user_id, db)
    if not user:
        logger.warning(f"Admin delete failed - user not found: {user_id}")
        raise FieldNotFoundException("user", str(user_id))

    user.is_deleted = True

    user_deletion = UserDeletion(
        reason=reason, username=user.username, user=user, deleted_by=admin.id
    )

    db.add(user_deletion)
    await db.flush()

    logger.info(
        f"User deleted by admin: {user.username} (id: {user_id}), reason: {reason}, deleted_by: {admin.username}"
    )


async def get_user_deletion_by_user_id_service(user_id: UUID, db: AsyncSession):
    """Service to get user deletion by user ID"""
    logger.info(f"Fetching user deletion by user_id: {user_id}")

    user_deletion = await get_user_deletion_by_user_id_db(user_id, db)
    if not user_deletion:
        logger.warning(f"User deletion not found for user_id: {user_id}")
        raise FieldNotFoundException("user deletion", str(user_id))

    logger.info(
        f"User deletion found: {user_deletion.id} for user: {user_deletion.username}"
    )

    return UserDeletionLoadedResponse(
        user=UserResponse.model_validate(user_deletion.user),
        user_deletion=UserDeletionResponse.model_validate(user_deletion),
    )


async def get_user_deletion_by_deletion_id_service(deletion_id: UUID, db: AsyncSession):
    """Service to get user deletion by deletion ID"""
    logger.info(f"Fetching user deletion by deletion_id: {deletion_id}")

    user_deletion = await get_user_deletion_by_id_db(deletion_id, db)
    if not user_deletion:
        logger.warning(f"User deletion not found: {deletion_id}")
        raise FieldNotFoundException("user deletion", str(deletion_id))

    logger.info(
        f"User deletion found: {deletion_id} for user: {user_deletion.username}"
    )

    return UserDeletionLoadedResponse(
        user=UserResponse.model_validate(user_deletion.user),
        user_deletion=UserDeletionResponse.model_validate(user_deletion),
    )


async def cleanup_expired_users_service(db: AsyncSession) -> int:
    """Hard delete users past retention period."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import delete, select

    logger.info("Starting expired user cleanup")

    cutoff_date = datetime.now(timezone.utc) - timedelta(
        days=settings.SOFT_DELETE_RETENTION_DAYS
    )

    subquery = select(UserDeletion.user_id).where(UserDeletion.deleted_at < cutoff_date)

    stmt = (
        delete(User)
        .where(User.id.in_(subquery), User.is_deleted.is_(True))
        .returning(User.id)
    )

    result = await db.execute(stmt)
    deleted_count = sum(1 for _ in result.scalars())

    logger.info(f"Hard deleted {deleted_count} expired users")

    return deleted_count
