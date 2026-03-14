from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.utils import parse_user_info
from app.exceptions.exception import (
    CredentialsException,
    DuplicateEntryException,
    FieldNotFoundException,
    get_unique_constraint_name,
    raise_duplicate_from_integrity_error,
)
from app.models.user import User, UserDeletion
from app.repositories.user import get_active_user_by_id_db
from app.schemas.user import UserCreate, UserUpdate

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


async def delete_profile_service(
    password: str, reason: str | None, current_user: User, db: AsyncSession
):
    if not verify_password(password, current_user.password):
        raise CredentialsException("Incorrect password")

    current_user.is_deleted = True  # soft delete

    user_deletion = UserDeletion(reason=reason, user=current_user)

    db.add(user_deletion)

    await db.flush()  # if error raise now
