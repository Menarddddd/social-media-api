from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependency import get_current_user, post_owner
from app.models.post import Post
from app.models.user import User
from app.schemas.post import (
    FeedResponse,
    PostCreate,
    PostResponse,
    PostUpdate,
    ProfileResponse,
)
from app.services.post import (
    create_post_service,
    feed_service,
    get_post_service,
    my_posts_service,
    update_post_service,
)


router = APIRouter()


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    form_data: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await create_post_service(form_data, current_user, db)


@router.get("/feed", response_model=list[FeedResponse], status_code=status.HTTP_200_OK)
async def feed(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await feed_service(db)


@router.get("", response_model=list[ProfileResponse], status_code=status.HTTP_200_OK)
async def my_posts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await my_posts_service(current_user, db)


@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post(
    post_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_post_service(post_id, db)


@router.patch("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def update_post(
    form_data: PostUpdate,
    post: Annotated[Post, Depends(post_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await update_post_service(form_data, post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post: Annotated[Post, Depends(post_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.delete(post)
