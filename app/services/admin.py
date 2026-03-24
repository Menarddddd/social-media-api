from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


from app.exceptions.exception import (
    FieldNotFoundException,
)
from app.models.user import Role, User, UserDeletion
from app.repositories.user import (
    get_active_user_by_id_db,
    get_user_deletion_by_user_id_db,
    get_user_from_user_deletion_id_db,
)
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
    user = await get_user_deletion_by_user_id_db(user_id, db)
    if not user:
        raise FieldNotFoundException("user", str(user_id))

    user_deletion_data = user.user_deletion

    return UserDeletionLoadedResponse(
        user=UserResponse.model_validate(user),
        user_deletion=UserDeletionResponse.model_validate(user_deletion_data),
    )


async def get_user_deletion_by_deletion_id_service(deletion_id: UUID, db: AsyncSession):
    user_deletion_data = await get_user_from_user_deletion_id_db(deletion_id, db)
    if not user_deletion_data:
        raise FieldNotFoundException("user deletion", str(deletion_id))

    user = user_deletion_data.user

    return UserDeletionLoadedResponse(
        user=UserResponse.model_validate(user),
        user_deletion=UserDeletionResponse.model_validate(user_deletion_data),
    )
