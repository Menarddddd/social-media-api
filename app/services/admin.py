from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


from app.exceptions.exception import (
    FieldNotFoundException,
)
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


async def promote_user_to_admin_service(user_id: UUID, db: AsyncSession):
    user = await get_active_user_by_id_db(user_id, db)

    if not user:
        raise FieldNotFoundException("user", str(user_id))

    user.role = Role.ADMIN

    return {"message": f"You've successfuly promoted {user.username} to admin"}


async def admin_delete_profile_service(
    reason: str, user_id: UUID, admin: User, db: AsyncSession
):
    """Service to delet user by Admin"""
    user = await get_active_user_by_id_db(user_id, db)
    if not user:
        raise FieldNotFoundException("user", str(user_id))

    user.is_deleted = True

    user_deletion = UserDeletion(
        reason=reason, username=user.username, user=user, deleted_by=admin.id
    )

    db.add(user_deletion)

    await db.flush()


async def get_user_deletion_by_user_id_service(user_id: UUID, db: AsyncSession):
    """Service to get user deletion by user ID"""
    user_deletion = await get_user_deletion_by_user_id_db(user_id, db)
    if not user_deletion:
        raise FieldNotFoundException("user deletion", str(user_id))

    return UserDeletionLoadedResponse(
        user=UserResponse.model_validate(user_deletion.user),
        user_deletion=UserDeletionResponse.model_validate(user_deletion),
    )


async def get_user_deletion_by_deletion_id_service(deletion_id: UUID, db: AsyncSession):
    """Service to get user deletion by deletion ID"""
    user_deletion = await get_user_deletion_by_id_db(deletion_id, db)
    if not user_deletion:
        raise FieldNotFoundException("user deletion", str(deletion_id))

    return UserDeletionLoadedResponse(
        user=UserResponse.model_validate(user_deletion.user),
        user_deletion=UserDeletionResponse.model_validate(user_deletion),
    )
