from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions.exception import (
    FieldNotFoundException,
)
from app.models.post import Post
from app.models.user import User
from app.models.comment import Comment
from app.repositories.post import feed_post_db, get_post_by_id_db, get_user_posts_db
from app.schemas.post import PostCreate, PostUpdate


async def create_post_service(
    form_data: PostCreate, current_user: User, db: AsyncSession
) -> Post:
    post = Post(
        title=form_data.title.title(), content=form_data.content, author=current_user
    )

    db.add(post)

    await db.flush()

    return post


async def feed_service(db: AsyncSession):
    posts = await feed_post_db(
        db,
        selectinload(Post.author),
        selectinload(Post.comments).selectinload(Comment.author),
    )

    return posts


async def my_posts_service(current_user: User, db: AsyncSession) -> Sequence[Post]:
    posts = await get_user_posts_db(
        current_user.id, db, selectinload(Post.comments).selectinload(Comment.author)
    )

    return posts


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
