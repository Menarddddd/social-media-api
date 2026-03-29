import base64
from datetime import datetime
from uuid import UUID

from arq import ArqRedis
from fastapi import HTTPException, status
from pydantic import ValidationError
import resend

from app.core.settings import settings
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


async def send_recovery_email(to_email: str, token: str):
    try:
        resend.Emails.send(
            {
                "from": "SocialMediaApp <onboarding@resend.dev>",
                "to": [to_email],
                "subject": "Password Recovery",
                "html": f"""
            <h2>Account Recovery</h2>
            <p>You requested for account recovery.</p>

            <p><b>Your recovery token: </b></p>
            <code style="font-size:16px;">{token}</code>

            <p>This token will expire in {settings.RECOVERY_MINUTES} minutes.</p>

            <p>If you did not make this request, ignore this email.</p>
            """,
            }
        )
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise


async def check_rate_limit(
    redis: ArqRedis, key: str, max_attempts: int, window_seconds: int
) -> bool:
    current = await redis.get(key)

    if current is None:
        await redis.setex(key, window_seconds, 1)
        return True

    if int(current) >= max_attempts:
        return False

    await redis.incr(key)
    return True
