import uuid
from typing import TYPE_CHECKING
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.settings import settings

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id"), nullable=False, index=True
    )
    hashed_token: Mapped[str] = mapped_column(
        sa.String(128), nullable=False, index=True
    )
    date_created: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    date_expire: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_DAYS_EXPIRE),
    )
    device_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    revoke: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, server_default=sa.false(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
