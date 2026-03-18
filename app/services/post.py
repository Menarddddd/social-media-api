from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.utils import decode_cursor, encode_cursor
from app.exceptions.exception import (
    FieldNotFoundException,
)
from app.models.post import Post
from app.models.user import User
from app.models.comment import Comment
from app.repositories.post import feed_post_db, get_post_by_id_db, get_user_posts_db
from app.schemas.cursor import CursorPageInfo
from app.schemas.post import (
    FeedPageResponse,
    FeedResponse,
    PostCreate,
    PostUpdate,
    ProfilePostPageResponse,
    ProfileResponse,
)


async def create_post_service(
    form_data: PostCreate, current_user: User, db: AsyncSession
) -> Post:
    post = Post(
        title=form_data.title.title(), content=form_data.content, author=current_user
    )

    db.add(post)

    await db.flush()

    return post


async def feed_service(db: AsyncSession, limit: int, cursor_token: str | None = None):
    decoded_cursor = decode_cursor(cursor_token) if cursor_token else None

    posts = list(
        await feed_post_db(
            db,
            limit,
            decoded_cursor,
            selectinload(Post.author),
            selectinload(Post.comments).selectinload(Comment.author),
        )
    )

    has_next_page = len(posts) > limit

    if has_next_page:
        posts = posts[:limit]

    next_cursor = None
    if has_next_page and posts:
        last_post = posts[-1]
        next_cursor = encode_cursor(
            date_created=last_post.date_created, item_id=last_post.id
        )

    return FeedPageResponse(
        items=[FeedResponse.model_validate(post) for post in posts],
        page_info=CursorPageInfo(next_cursor=next_cursor, has_next_page=has_next_page),
    )


async def my_posts_service(
    current_user: User, db: AsyncSession, limit: int, cursor_token: str | None = None
):
    decoded_token = decode_cursor(cursor_token) if cursor_token else None

    posts = list(
        await get_user_posts_db(
            current_user.id,
            db,
            limit,
            decoded_token,
            selectinload(Post.comments).selectinload(Comment.author),
        )
    )

    has_next_page = len(posts) > limit

    if has_next_page:
        posts = posts[:limit]

    next_cursor = None
    if has_next_page and posts:
        last_post = posts[-1]
        next_cursor = encode_cursor(
            date_created=last_post.date_created, item_id=last_post.id
        )

    return ProfilePostPageResponse(
        items=[ProfileResponse.model_validate(post) for post in posts],
        page_info=CursorPageInfo(next_cursor=next_cursor, has_next_page=has_next_page),
    )


async def get_post_service(post_id: UUID, db: AsyncSession):
    post = await get_post_by_id_db(post_id, db)
    if not post:
        raise FieldNotFoundException("post", str(post_id))

    return post


async def update_post_service(form_data: PostUpdate, post: Post):
    data = form_data.model_dump(exclude_unset=True)

    for k, v in data.items():
        setattr(post, k, v)

    return post


# ADMIN
async def admin_delete_post_service(post_id: UUID, db: AsyncSession):
    post = await get_post_by_id_db(post_id, db)
    if not post:
        raise FieldNotFoundException("post", str(post_id))

    await db.delete(post)
