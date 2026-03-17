import base64
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.schemas.cursor import CursorPayload


# clean user info
def parse_user_info(data: dict) -> dict[str, str]:
    for key, val in data.items():
        if key in ["first_name", "last_name"]:
            data[key] = data[key].strip().title()

        if key in ["email", "username"]:
            data[key] = data[key].strip().lower()

    return data


def encode_cursor(date_created: datetime, item_id: UUID):
    payload = CursorPayload(date_created=date_created, item_id=item_id)

    raw_json = payload.model_dump_json().encode()
    token = base64.urlsafe_b64encode(raw_json).decode().rstrip("=")

    return token


def decode_cursor(cursor: str):
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(cursor + padding)

        payload = CursorPayload.model_validate_json(raw)

        return payload

    except (ValidationError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor"
        )
