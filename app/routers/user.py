from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query, Request, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependency import get_current_user
from app.models.user import User
from app.schemas.user import (
    ChangePassword,
    RecoveryComplete,
    RecoveryRequest,
    Token,
    UserActivity,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserDeletion,
)
from app.services.user import (
    account_recovery_service,
    change_password_service,
    create_user_service,
    delete_profile_service,
    get_user_service,
    login_service,
    my_activities_service,
    refresh_token_service,
    reset_password_service,
    update_profile_service,
)


router = APIRouter()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await login_service(form_data.username, form_data.password, db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    form_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await create_user_service(form_data, db)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: Request, refresh_token: str, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await refresh_token_service(
        refresh_token=refresh_token, db=db, request=request
    )


@router.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return current_user


@router.get("/activity", response_model=UserActivity, status_code=status.HTTP_200_OK)
async def my_activities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    posts_cursor: Annotated[str | None, Query()] = None,
    comments_cursor: Annotated[str | None, Query()] = None,
):
    return await my_activities_service(
        current_user, db, limit, posts_cursor, comments_cursor
    )


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_user_service(user_id, db)


@router.patch("", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    form_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await update_profile_service(form_data, current_user, db)


@router.patch("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    form_data: ChangePassword,
    current_user: Annotated[User, Depends(get_current_user)],
):
    await change_password_service(form_data, current_user)


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    form_data: UserDeletion,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await delete_profile_service(
        form_data.password, form_data.reason, current_user, db
    )


@router.post("/recover", status_code=status.HTTP_200_OK)
async def account_recovery(
    form_data: RecoveryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await account_recovery_service(form_data.email, db)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    form_data: RecoveryComplete,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await reset_password_service(form_data.token, form_data.new_password, db)
