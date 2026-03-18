"""changed role type enum to str

Revision ID: 75109cb372dd
Revises: 3abd865a7987
Create Date: 2026-03-19 02:39:11.572428

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "75109cb372dd"
down_revision: Union[str, Sequence[str], None] = "3abd865a7987"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Convert role from ENUM to VARCHAR."""

    # ══════════════════════════════════════════════════════════════
    # Step 1: Alter column using CAST expression
    # ══════════════════════════════════════════════════════════════
    op.execute(
        """
        ALTER TABLE users 
        ALTER COLUMN role TYPE VARCHAR(100) 
        USING role::text
    """
    )
    #       ▲
    #       │ USING role::text tells PostgreSQL HOW to convert
    #       │ enum value 'user' → string 'user'

    # ══════════════════════════════════════════════════════════════
    # Step 2: Update the server default (remove enum cast)
    # ══════════════════════════════════════════════════════════════
    op.alter_column(
        "users", "role", server_default=sa.text("'user'")  # Simple string default now
    )

    # ══════════════════════════════════════════════════════════════
    # Step 3: Drop the old enum type (cleanup)
    # ══════════════════════════════════════════════════════════════
    op.execute("DROP TYPE IF EXISTS role")


def downgrade() -> None:
    """Downgrade schema: Convert role back to ENUM."""

    # Recreate the enum type
    op.execute("CREATE TYPE role AS ENUM ('user', 'admin')")

    # Convert back to enum
    op.execute(
        """
        ALTER TABLE users 
        ALTER COLUMN role TYPE role 
        USING role::role
    """
    )

    # Restore enum-style default
    op.alter_column("users", "role", server_default=sa.text("'user'::role"))
