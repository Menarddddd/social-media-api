from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.utils import decode_cursor, encode_cursor, parse_user_info
from app.exceptions.exception import (
    CredentialsException,
    FieldNotFoundException,
    raise_duplicate_from_integrity_error,
)
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User, UserDeletion
from app.repositories.comment import get_all_comments_db
from app.repositories.post import get_user_posts_db
from app.repositories.user import get_active_user_by_id_db
from app.schemas.user import (
    ActivityListPageInfo,
    ChangePassword,
    CommentPublic,
    PostPublic,
    UserActivity,
    UserCreate,
    UserUpdate,
)

UPDATE_USER_ALLOWED = {"first_name", "last_name", "username", "email"}


async def login_service(username: str, password: str, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise FieldNotFoundException("user", username)

    if not verify_password(password, user.password):
        raise CredentialsException("Username or password is incorrect")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "refersh_token": refresh_token,
    }


async def create_user_service(form_data: UserCreate, db: AsyncSession) -> dict:
    data = parse_user_info(form_data.model_dump())

    user = User(
        first_name=data["first_name"],
        last_name=data["last_name"],
        username=data["username"],
        email=data["email"],
        password=hash_password(data["password"]),
    )

    try:
        db.add(user)
        await db.flush()

    except IntegrityError as e:
        raise_duplicate_from_integrity_error(
            e, {"username": user.username, "email": user.email}
        )
        raise  # unkown error

    return {
        "message": "You've successfully created your account. You can now login with it"
    }


async def get_user_service(user_id: UUID, db: AsyncSession) -> User | None:
    user = await get_active_user_by_id_db(user_id, db)
    if not user:
        raise FieldNotFoundException("user", str(user_id))

    return user


async def my_activities_service(
    current_user: User,
    db: AsyncSession,
    limit: int,
    posts_cursor_token: str | None,
    comments_cursor_token: str | None,
):
    posts_cursor = decode_cursor(posts_cursor_token) if posts_cursor_token else None
    comments_cursor = (
        decode_cursor(comments_cursor_token) if comments_cursor_token else None
    )

    posts = list(await get_user_posts_db(current_user.id, db, limit, posts_cursor))

    comments = list(
        await get_all_comments_db(
            current_user.id,
            db,
            limit,
            comments_cursor,
            selectinload(Comment.post).selectinload(Post.author),
        )
    )

    post_next_page = len(posts) > limit
    comment_next_page = len(comments) > limit

    if post_next_page:
        posts = posts[:limit]

    if comment_next_page:
        comments = comments[:limit]

    post_next_cursor = None
    if post_next_page and posts:
        last_post = posts[-1]
        post_next_cursor = encode_cursor(
            date_created=last_post.date_created, item_id=last_post.id
        )

    comment_next_cursor = None
    if comment_next_page and comments:
        last_comment = comments[-1]
        comment_next_cursor = encode_cursor(
            date_created=last_comment.date_created, item_id=last_comment.id
        )

    return UserActivity(
        posts=[PostPublic.model_validate(post) for post in posts],
        comments=[CommentPublic.model_validate(comment) for comment in comments],
        page_info=ActivityListPageInfo(
            posts_next_cursor=post_next_cursor,
            posts_next_page=post_next_page,
            comments_next_cursor=comment_next_cursor,
            comments_next_page=comment_next_page,
        ),
    )


async def update_profile_service(
    form_data: UserUpdate, current_user: User, db: AsyncSession
) -> User:

    data = form_data.model_dump(
        exclude_unset=True
    )  # converts pydantic to a dict, exclude unset

    data = parse_user_info(data)  # clean user info input

    data = {
        k: v for k, v in data.items() if k in UPDATE_USER_ALLOWED
    }  # checks allowed field

    try:
        for key, val in data.items():
            setattr(current_user, key, val)

        await db.flush()  # raise constraint error

    except IntegrityError as e:
        raise_duplicate_from_integrity_error(
            e, {"username": data.get("username"), "email": data.get("email")}
        )
        raise  # not know error

    return current_user


async def change_password_service(form_data: ChangePassword, current_user: User):
    if not verify_password(form_data.current_password, current_user.password):
        raise CredentialsException("Invalid credentials")

    current_user.password = hash_password(form_data.new_password)

    return {"message": "You've successfully changed your password"}


async def delete_profile_service(
    password: str, reason: str | None, current_user: User, db: AsyncSession
):
    if not verify_password(password, current_user.password):
        raise CredentialsException("Incorrect password")

    current_user.is_deleted = True  # soft delete

    user_deletion = UserDeletion(reason=reason, user=current_user)

    db.add(user_deletion)

    await db.flush()  # if error raise now
