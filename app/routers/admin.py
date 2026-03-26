from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependency import require_admin
from app.models.user import User
from app.repositories.admin import (
    get_active_admins_db,
    get_all_active_users_db,
    get_users_deletions_db,
)
from app.repositories.user import get_active_admin_by_id_db
from app.schemas.user import (
    AdminDelete,
    UserDeletionLoadedResponse,
    UserDeletionResponse,
    UserResponse,
)
from app.services.admin import (
    admin_delete_profile_service,
    get_user_deletion_by_deletion_id_service,
    get_user_deletion_by_user_id_service,
    promote_user_to_admin_service,
)
from app.services.comment import admin_delete_comment_service
from app.services.post import admin_delete_post_service


router = APIRouter()


@router.get(
    "/admins", response_model=list[UserResponse], status_code=status.HTTP_200_OK
)
async def get_all_admins(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
):
    return await get_active_admins_db(db, limit, (page - 1) * page)


@router.post("/promote", status_code=status.HTTP_200_OK)
async def promote_user_to_admin(
    user_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await promote_user_to_admin_service(user_id, db)


@router.get("", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
):
    return await get_all_active_users_db(db, limit, (page - 1) * limit)  # offset


@router.get(
    "/user_deletions",
    response_model=list[UserDeletionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_users_deletions(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
):
    return await get_users_deletions_db(db, limit, (page - 1) * limit)


@router.get(
    "/user_deletions/{id}",
    response_model=UserDeletionLoadedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_deletion_by_id(
    deletion_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await get_user_deletion_by_deletion_id_service(deletion_id, db)


@router.get(
    "/user_deletions/user/{user_id}",
    response_model=UserDeletionLoadedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_deletion_by_user_id(
    user_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await get_user_deletion_by_user_id_service(user_id, db)


@router.post("/delete_user", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    form_data: AdminDelete,
    user_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await admin_delete_profile_service(form_data.reason, user_id, admin, db)


@router.delete("/delete_post", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    await admin_delete_post_service(post_id, db)


@router.delete("/delete_comment", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    await admin_delete_comment_service(comment_id, db)


@router.delete("/hard-delete", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_user(user_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await get_active_admin_by_id_db(user_id, db)

    await db.delete(user)
