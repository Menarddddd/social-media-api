import logging

from sqlalchemy import delete, select

from app.core.settings import settings
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserDeletion


from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)


async def hard_delete_expired_user(ctx):
    cutoff_date = datetime.now(timezone.utc) - timedelta(
        days=settings.SOFT_DELETE_RETENTION_DAYS
    )

    async with AsyncSessionLocal() as db:
        async with db.begin():
            subquery = select(UserDeletion.user_id).where(
                UserDeletion.deleted_at < cutoff_date
            )

            stmt = (
                delete(User)
                .where(User.id.in_(subquery), User.is_deleted.is_(True))
                .returning(User.id)
            )

            result = await db.execute(stmt)
            deleted_count = sum(1 for _ in result.scalars())

            logger.info(f"Hard deleted {deleted_count} users")
