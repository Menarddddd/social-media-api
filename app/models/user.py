import uuid
from typing import TYPE_CHECKING
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.comment import Comment
    from app.models.refresh_token import RefreshToken
    from app.models.account_recovery import AccountRecoveryToken


class Role:
    USER = "user"
    ADMIN = "admin"


class UserDeletion(Base):
    __tablename__ = "user_deletions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id"), nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        sa.String(200), unique=True, nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(
        sa.String(200), default=None, nullable=True
    )
    deleted_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    deleted_by: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id"), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="user_deletion",
    )

    deleted_by_user: Mapped["User"] = relationship("User", foreign_keys=[deleted_by])


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    username: Mapped[str] = mapped_column(
        sa.String(200), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(sa.String(200), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    role: Mapped[str] = mapped_column(
        sa.String(100),
        default=Role.USER,
        server_default=sa.text("'user'"),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, server_default=sa.false(), nullable=False, index=True
    )

    posts: Mapped[list["Post"]] = relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    user_deletion: Mapped["UserDeletion"] = relationship(
        "UserDeletion",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys=[UserDeletion.user_id],
        uselist=False,
    )

    account_recovery: Mapped[list["AccountRecoveryToken"]] = relationship(
        "AccountRecoveryToken", back_populates="user", cascade="all, delete-orphan"
    )

    performed_deletions: Mapped["UserDeletion"] = relationship(
        "UserDeletion", foreign_keys=[UserDeletion.deleted_by]
    )

    __table_args__ = (
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
