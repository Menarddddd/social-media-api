from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions.exception import FieldNotFoundException
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.repositories.comment import get_all_comments_db, get_comment_by_id_db


async def create_comment_service(
    message: str, post_id: UUID, current_user: User, db: AsyncSession
) -> Comment:
    comment = Comment(message=message, post_id=post_id, user_id=current_user.id)

    db.add(comment)

    await db.flush()

    return comment


async def my_comments_service(
    current_user: User,
    db: AsyncSession,
) -> Sequence[Comment]:
    comments = await get_all_comments_db(
        current_user.id, db, selectinload(Comment.post).selectinload(Post.author)
    )

    return comments


async def get_comment_service(comment_id: UUID, db: AsyncSession):
    comment = await get_comment_by_id_db(
        comment_id,
        db,
        selectinload(Comment.author),
        selectinload(Comment.post).selectinload(Post.author),
    )

    if not comment:
        raise FieldNotFoundException("comment", str(comment_id))

    return comment


async def update_comment_service(message: str, comment: Comment) -> Comment:
    comment.message = message

    return comment
