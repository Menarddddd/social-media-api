from typing import Mapping

from sqlalchemy.exc import IntegrityError


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


UNIQUE_CONSTRAINT_TO_FIELD = {
    "uq_users_username": "username",
    "uq_users_email": "email",
}


def get_unique_constraint_name(e: IntegrityError) -> str | None:
    orig = e.orig

    name = getattr(orig, "constraint_name", None)
    if name:
        return name

    cause = getattr(orig, "__cause__", None)
    name = getattr(cause, "constraint_name", None) if cause else None
    if name:
        return name

    return None


def raise_duplicate_from_integrity_error(
    e: IntegrityError, values: Mapping[str, str | None]
):
    constraint = get_unique_constraint_name(e)
    if constraint is None:
        return

    field = UNIQUE_CONSTRAINT_TO_FIELD.get(constraint)

    if field:
        raise DuplicateEntryException(field, values.get(field)) from e
