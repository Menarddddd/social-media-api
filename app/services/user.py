import asyncio
import logging
import resend
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.settings import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_recovery_token,
    hash_password,
    hash_recovery_token,
    hash_refresh_token,
    mark_token_used,
    verify_password,
    verify_recovery_token,
    verify_token,
)
from app.core.utils import (
    _send_recovery_email_task,
    check_rate_limit_memory,
    decode_cursor,
    encode_cursor,
    parse_user_info,
)
from app.exceptions.exception import (
    BadRequestException,
    CredentialsException,
    FieldNotFoundException,
    raise_duplicate_from_integrity_error,
)
from app.models.comment import Comment
from app.models.post import Post
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserDeletion
from app.repositories.admin import (
    delete_user_deletion_by_username_db,
    get_user_deletion_by_user_id_db,
    get_user_deletion_by_user_username_db,
)
from app.repositories.comment import get_all_comments_db
from app.repositories.post import get_user_posts_db
from app.repositories.user import (
    get_active_user_by_id_db,
    get_active_user_by_username_db,
    get_refresh_token_db,
    get_user_by_email_db,
)
from app.schemas.user import (
    ActivityListPageInfo,
    ChangePassword,
    CommentPublic,
    PostPublic,
    UserActivity,
    UserCreate,
    UserUpdate,
)


logger = logging.getLogger(__name__)

UPDATE_USER_ALLOWED = {"first_name", "last_name", "username", "email"}


async def login_service(
    username: str, password: str, db: AsyncSession, request: Request | None = None
) -> dict:
    """Handles login and gives access/refresh token"""

    username = username.lower()

    logger.info(f"Login attempt: {username}")

    user = await get_active_user_by_username_db(username, db)

    if not user:
        user = await get_user_deletion_by_user_username_db(username, db)
        if user:
            logger.warning(f"Login failed - deactivated account: {username}")
            raise CredentialsException("Your account is deactivated, activate it first")

        logger.warning(f"Login failed - user not found: {username}")
        raise FieldNotFoundException("user", username)

    if not verify_password(password, user.password):
        logger.warning(f"Login failed - invalid password: {username}")
        raise CredentialsException("Username or password is incorrect")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token_plain = create_refresh_token({"sub": str(user.id)})
    refresh_token_hash = hash_refresh_token(refresh_token_plain)

    device_name = None
    user_agent = None

    if request:
        user_agent = request.headers.get("User-Agent")
        device_name = user_agent[:100] if user_agent else None

    db_refresh_token = RefreshToken(
        user_id=user.id,
        hashed_token=refresh_token_hash,
        date_expire=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_DAYS_EXPIRE),
        device_name=device_name,
        user_agent=user_agent,
        revoke=False,
    )

    # db.add(db_refresh_token) # remove comment if you are gonna use refresh token

    logger.info(f"Login successful: {username} (user_id: {user.id})")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token_plain,
    }


async def create_user_service(form_data: UserCreate, db: AsyncSession) -> User:
    """Create a user and return it"""

    logger.info(f"Creating user: {form_data.username}")

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

        logger.info(f"User created successfully: {user.username} (id: {user.id})")
        return user

    except IntegrityError as e:
        logger.warning(
            f"Duplicate user attempt: username={user.username}, email={user.email}"
        )
        raise_duplicate_from_integrity_error(
            e, {"username": user.username, "email": user.email}
        )
        raise


async def get_user_service(user_id: UUID, db: AsyncSession) -> User | None:
    """Fetch a user from the DB"""

    logger.info(f"Fetching user: {user_id}")

    user = await get_active_user_by_id_db(user_id, db)
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise FieldNotFoundException("user", str(user_id))

    return user


async def my_activities_service(
    current_user: User,
    db: AsyncSession,
    limit: int,
    posts_cursor_token: str | None,
    comments_cursor_token: str | None,
):
    """Fetch user post & comment activities"""

    logger.info(f"Fetching activities for user: {current_user.username}")

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

    logger.info(
        f"Activities fetched: {len(posts)} posts, {len(comments)} comments for {current_user.username}"
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
    """Update user info and return it"""

    username = current_user.username

    logger.info(f"Updating profile for user: {username}")

    data = form_data.model_dump(exclude_unset=True)
    data = parse_user_info(data)
    data = {k: v for k, v in data.items() if k in UPDATE_USER_ALLOWED}

    try:
        for key, val in data.items():
            setattr(current_user, key, val)

        await db.flush()

        logger.info(f"Profile updated successfully: {username}")

    except IntegrityError as e:
        logger.warning(
            f"Profile update failed - duplicate entry: {username}"
        )  # ← Now uses captured variable
        raise_duplicate_from_integrity_error(
            e, {"username": data.get("username"), "email": data.get("email")}
        )
        raise

    return current_user


async def change_password_service(form_data: ChangePassword, current_user: User):
    """Allows user to change password"""

    logger.info(f"Password change attempt for user: {current_user.username}")

    if not verify_password(form_data.current_password, current_user.password):
        logger.warning(
            f"Password change failed - invalid current password: {current_user.username}"
        )
        raise CredentialsException("Invalid credentials")

    current_user.password = hash_password(form_data.new_password)

    logger.info(f"Password changed successfully: {current_user.username}")


async def delete_profile_service(
    password: str,
    reason: str | None,
    current_user: User,
    db: AsyncSession,
):
    """User soft deletion before hard deleting after 30 days"""

    logger.info(f"Account deletion attempt: {current_user.username}")

    if not verify_password(password, current_user.password):
        logger.warning(
            f"Account deletion failed - incorrect password: {current_user.username}"
        )
        raise CredentialsException("Incorrect password")

    current_user.is_deleted = True  # soft delete

    user_deletion = UserDeletion(
        reason=reason,
        username=current_user.username,
        user=current_user,
        deleted_by=current_user.id,
    )

    db.add(user_deletion)

    await db.flush()  # if error raise now

    logger.info(f"Account deleted: {current_user.username}, reason: {reason}")


async def refresh_token_service(
    refresh_token: str, db: AsyncSession, request: Request | None = None
) -> dict:
    """Gives new access and refresh token"""

    logger.info("Refresh token attempt")

    hashed_token = hash_refresh_token(refresh_token)
    db_token = await get_refresh_token_db(hashed_token, db)

    if not db_token:
        logger.warning("Refresh token failed - invalid token")
        raise CredentialsException("Invalid refresh token")

    if db_token.revoke:
        logger.warning(f"Refresh token failed - revoked token")
        raise CredentialsException("Refresh token has been revoked")

    if db_token.date_expire < datetime.now(timezone.utc):
        db_token.revoke = True
        await db.flush()
        logger.warning("Refresh token failed - expired token")
        raise CredentialsException("Refresh token has expired")

    if not verify_token(refresh_token, db_token.hashed_token):
        logger.warning("Refresh token failed - verification failed")
        raise CredentialsException("Invalid refresh token")

    user = await get_active_user_by_id_db(db_token.user_id, db)

    if not user:
        db_token.revoke = True
        await db.flush()
        logger.warning("Refresh token failed - user not found")
        raise CredentialsException("User not found")

    if user.is_deleted:
        db_token.revoke = True
        await db.flush()
        logger.warning(f"Refresh token failed - deleted account: {user.username}")
        raise CredentialsException("User account has been deleted")

    db_token.revoke = True

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token_plain = create_refresh_token({"sub": str(user.id)})
    new_refresh_token_hash = hash_refresh_token(new_refresh_token_plain)

    device_name = None
    user_agent = None

    if request:
        user_agent = request.headers.get("User-Agent")
        device_name = user_agent[:100] if user_agent else None

    new_db_refresh_token = RefreshToken(
        user_id=user.id,
        hashed_token=new_refresh_token_hash,
        date_expire=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_DAYS_EXPIRE),
        device_name=device_name,
        user_agent=user_agent,
        revoke=False,
    )

    db.add(new_db_refresh_token)

    logger.info(f"Refresh token successful: {user.username}")

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token_plain,
    }


async def account_recovery_service(email: str, db: AsyncSession):
    """Send recovery token to user email."""
    logger.info("Account recovery attempt")

    # Rate limit (in-memory, no Redis needed)
    is_allowed = check_rate_limit_memory(email.lower())

    if not is_allowed:
        logger.warning(f"Account recovery rate limited: {email}")
        raise BadRequestException("Too many recovery attempts. Please try again later.")

    msg = {
        "message": "If the email exists, a recovery token was sent. You need to put it in /reset password"
    }

    user = await get_user_by_email_db(email, db)
    if not user:
        logger.info("Account recovery - email not found")
        return msg

    token = await generate_recovery_token(user.id, db)

    # Send email in background
    asyncio.create_task(_send_recovery_email_task(user.email, token, user.username))

    return msg


async def reset_password_service(token: str, new_password: str, db: AsyncSession):
    """User can change their password once they have a token"""

    logger.info("Password reset attempt")

    user_id = await verify_recovery_token(token, db)
    if not user_id:
        logger.warning("Password reset failed - invalid recovery token")
        raise CredentialsException("Invalid recovery token")

    user_deletion = await get_user_deletion_by_user_id_db(user_id, db)
    if not user_deletion:
        logger.warning(f"Password reset failed - account past recovery period")
        raise BadRequestException(
            "Your account cannot be recovered since it's already past 30 days"
        )

    await delete_user_deletion_by_username_db(user_deletion.user.username, db)

    user = user_deletion.user

    user.password = hash_password(new_password)
    user.is_deleted = False
    await mark_token_used(hash_recovery_token(token), db)

    logger.info(f"Account recovered successfully: {user.username}")

    return {
        "message": "You've successfully recovered your account, you can now login with it."
    }
