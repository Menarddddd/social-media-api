from typing import Sequence
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.post import Post
from app.schemas.cursor import CursorPayload


async def get_post_by_id_db(post_id: UUID, db: AsyncSession, *options) -> Post | None:
    stmt = (
        select(Post)
        .join(Post.author)
        .where(Post.id == post_id, User.is_deleted.is_(False))
    )

    if options:
        stmt = stmt.options(*options)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def get_user_posts_db(
    user_id: UUID,
    db: AsyncSession,
    limit: int,
    cursor: CursorPayload | None = None,
    *options,
) -> Sequence[Post]:
    stmt = (
        select(Post)
        .join(Post.author)
        .where(Post.user_id == user_id, User.is_deleted.is_(False))
        .order_by(Post.date_created.desc(), Post.id.desc())
        .limit(limit + 1)
    )

    if cursor:
        stmt = stmt.where(
            or_(
                Post.date_created < cursor.date_created,
                and_(
                    Post.date_created == cursor.date_created, Post.id < cursor.item_id
                ),
            )
        )

    if options:
        stmt = stmt.options(*options)

    result = await db.execute(stmt)

    return result.scalars().all()


async def feed_post_db(
    db: AsyncSession, limit: int, cursor: CursorPayload | None = None, *options
) -> Sequence[Post]:
    stmt = (
        select(Post)
        .join(Post.author)
        .where(User.is_deleted.is_(False))
        .order_by(Post.date_created.desc(), Post.id.desc())
        .limit(limit + 1)
    )

    if cursor:
        stmt = stmt.where(
            or_(
                Post.date_created < cursor.date_created,
                and_(
                    Post.date_created == cursor.date_created, Post.id < cursor.item_id
                ),
            )
        )

    if options:
        stmt = stmt.options(*options)

    result = await db.execute(stmt)

    return result.scalars().all()
