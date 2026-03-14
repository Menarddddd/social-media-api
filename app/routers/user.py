from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependency import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserDeletion,
)
from app.services.user import (
    create_user_service,
    delete_profile_service,
    get_user_service,
    login_service,
    update_profile_service,
)

router = APIRouter()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await login_service(form_data.username, form_data.password, db)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    form_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await create_user_service(form_data, db)


@router.get("", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User))
    return result.scalars().all()


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


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    form_data: UserDeletion,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await delete_profile_service(
        form_data.password, form_data.reason, current_user, db
    )
