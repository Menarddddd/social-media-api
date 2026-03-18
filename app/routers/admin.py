from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.user import get_active_admins_db, get_all_active_users_db
from app.schemas.user import AdminDelete, UserResponse
from app.services.comment import admin_delete_comment_service
from app.services.post import admin_delete_post_service
from app.services.user import (
    delete_user_service,
    promote_user_to_admin_service,
)

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
    return await get_all_active_users_db(db, limit, (page - 1) * page)  # offset


@router.post("/delete_user", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    form_data: AdminDelete, user_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    await delete_user_service(user_id, form_data.reason, db)


@router.delete("/delete_post", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    await admin_delete_post_service(post_id, db)


@router.delete("/delete_comment", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    await admin_delete_comment_service(comment_id, db)
