from typing import Mapping

from sqlalchemy.exc import IntegrityError


class BadRequestException(Exception):
    def __init__(self, message):
        self.message = message


class CredentialsException(Exception):
    def __init__(self, error):
        self.error = error


class FieldNotFoundException(Exception):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __str__(self):
        return f"{self.field} not found"


class DuplicateEntryException(Exception):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __str__(self):
        return f"{self.field} already exists"


# PostgreSQL named constraints
UNIQUE_CONSTRAINT_TO_FIELD = {
    "uq_users_username": "username",
    "uq_users_email": "email",
}

# SQLite column names in error messages
COLUMN_TO_FIELD = {
    "users.username": "username",
    "users.email": "email",
    "username": "username",
    "email": "email",
}


def get_unique_constraint_name(e: IntegrityError) -> str | None:
    """Try to get PostgreSQL constraint name."""
    orig = e.orig

    name = getattr(orig, "constraint_name", None)
    if name:
        return name

    cause = getattr(orig, "__cause__", None)
    name = getattr(cause, "constraint_name", None) if cause else None
    if name:
        return name

    return None


def get_field_from_sqlite_error(e: IntegrityError) -> str | None:
    """Extract field name from SQLite error message.

    SQLite format: "UNIQUE constraint failed: users.username"
    """
    error_message = str(e.orig).lower()

    for column, field in COLUMN_TO_FIELD.items():
        if column in error_message:
            return field

    return None


def raise_duplicate_from_integrity_error(
    e: IntegrityError, values: Mapping[str, str | None]
):
    """Convert IntegrityError to DuplicateEntryException.

    Supports both PostgreSQL (named constraints) and SQLite (error message).
    """
    field = None

    # Method 1: PostgreSQL named constraints
    constraint = get_unique_constraint_name(e)
    if constraint:
        field = UNIQUE_CONSTRAINT_TO_FIELD.get(constraint)

    # Method 2: SQLite error message parsing (fallback)
    if not field:
        field = get_field_from_sqlite_error(e)

    # Raise custom exception if we identified the field
    if field:
        raise DuplicateEntryException(field, values.get(field)) from e
