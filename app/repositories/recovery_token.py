from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_recovery import AccountRecoveryToken


async def get_user_from_recovery_token(hashed_token: str, db: AsyncSession):
    result = await db.execute(
        select(AccountRecoveryToken).where(
            AccountRecoveryToken.token_hash == hashed_token,
            AccountRecoveryToken.expires_at > datetime.now(timezone.utc),
            AccountRecoveryToken.used.is_(False),
        )
    )

    return result.scalar_one_or_none()


async def mark_token_used_db(hashed_token: str, db: AsyncSession):
    result = await db.execute(
        select(AccountRecoveryToken).where(
            AccountRecoveryToken.token_hash == hashed_token
        )
    )

    token_db = result.scalar_one_or_none()

    if token_db:
        token_db.used = True
