from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependency import comment_owner, get_current_user
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentLoadedAllResponse,
    CommentLoadedResponse,
    CommentResponse,
    CommentUpdate,
)
from app.services.comment import (
    create_comment_service,
    get_comment_service,
    my_comments_service,
    update_comment_service,
)


router = APIRouter()


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    form_data: CommentCreate,
    post_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await create_comment_service(form_data.message, post_id, current_user, db)


@router.get(
    "", response_model=list[CommentLoadedResponse], status_code=status.HTTP_200_OK
)
async def my_comments(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await my_comments_service(current_user, db)


@router.get(
    "/{comment_id}",
    response_model=CommentLoadedAllResponse,
    status_code=status.HTTP_200_OK,
)
async def get_comment(
    comment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_comment_service(comment_id, db)


@router.patch(
    "/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK
)
async def update_comment(
    form_data: CommentUpdate, comment: Annotated[Comment, Depends(comment_owner)]
):
    return await update_comment_service(form_data.message, comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment: Annotated[Comment, Depends(comment_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.delete(comment)
