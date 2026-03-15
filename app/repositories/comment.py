from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.comment import Comment


async def get_comment_by_id_db(
    comment_id: UUID, db: AsyncSession, *options
) -> Comment | None:
    stmt = (
        select(Comment)
        .join(User)
        .where(Comment.id == comment_id, User.is_deleted.is_(False))
    )

    if options:
        stmt = stmt.options(*options)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def get_all_comments_db(
    user_id: UUID, db: AsyncSession, *options
) -> Sequence[Comment]:
    stmt = (
        select(Comment)
        .join(User)
        .where(Comment.user_id == user_id, User.is_deleted.is_(False))
        .order_by(Comment.date_created.desc())
    )

    if options:
        stmt = stmt.options(*options)

    result = await db.execute(stmt)

    return result.scalars().all()
