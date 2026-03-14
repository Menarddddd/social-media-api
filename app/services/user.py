from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions.exception import CredentialsException, FieldNotFoundException
from app.models.user import User, UserDeletion
from app.schemas.user import UserCreate, UserUpdate


async def login_service(username: str, password: str, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise FieldNotFoundException("user", username)

    if not verify_password(password, user.password):
        raise CredentialsException("Username or password is incorrect")

    access_token = create_access_token({"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "Bearer", "refersh_token": ""}


async def create_user_service(form_data: UserCreate, db: AsyncSession) -> dict:
    user = User(
        first_name=form_data.first_name,
        last_name=form_data.last_name,
        username=form_data.username,
        email=form_data.email,
        password=hash_password(form_data.password),
    )

    db.add(user)

    return {
        "message": "You've successfully created your account. You can now login with it"
    }


async def get_user_service(user_id: UUID, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_profile_service(
    form_data: UserUpdate, current_user: User, db: AsyncSession
) -> User:
    data = form_data.model_dump(
        exclude_unset=True
    )  # converts pydantic to a dict, exclude unset

    for key, val in data.items():
        setattr(current_user, key, val)

    await db.flush()  # raise constraint error

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
