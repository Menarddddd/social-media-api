from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.utils import decode_cursor, encode_cursor
from app.exceptions.exception import FieldNotFoundException
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.repositories.comment import get_all_comments_db, get_comment_by_id_db
from app.repositories.post import get_post_by_id_db
from app.schemas.comment import CommentLoadedAllResponse, CommentPageResponse
from app.schemas.cursor import CursorPageInfo


async def create_comment_service(
    message: str, post_id: UUID, current_user: User, db: AsyncSession
) -> Comment:
    post = await get_post_by_id_db(post_id, db)
    if not post:
        raise FieldNotFoundException("post", str(post_id))

    comment = Comment(message=message, post_id=post_id, user_id=current_user.id)

    db.add(comment)

    await db.flush()

    return comment


async def my_comments_service(
    current_user: User,
    db: AsyncSession,
    limit: int,
    cursor_token: str | None = None,
):
    decoded_cursor = decode_cursor(cursor_token) if cursor_token else None

    comments = list(
        await get_all_comments_db(
            current_user.id,
            db,
            limit,
            decoded_cursor,
            selectinload(Comment.post).selectinload(Post.author),
        )
    )

    has_next_page = len(comments) > limit

    if has_next_page:
        comments = comments[:limit]

    next_cursor = None
    if has_next_page and comments:
        last_comment = comments[-1]
        next_cursor = encode_cursor(
            date_created=last_comment.date_created, item_id=last_comment.id
        )

    return CommentPageResponse(
        items=[
            CommentLoadedAllResponse.model_validate(comment) for comment in comments
        ],
        page_info=CursorPageInfo(next_cursor=next_cursor, has_next_page=has_next_page),
    )


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
