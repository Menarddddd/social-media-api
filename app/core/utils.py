import base64
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from uuid import UUID

from arq import ArqRedis
from fastapi import HTTPException, status
from pydantic import ValidationError
import resend

from app.core.settings import settings
from app.schemas.cursor import CursorPayload


_recovery_attempts: dict[str, list[datetime]] = defaultdict(list)
logger = logging.getLogger(__name__)


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


async def _send_recovery_email_task(email: str, token: str, username: str):
    """Background task to send recovery email."""
    try:
        await send_recovery_email(email, token)
        logger.info(f"Recovery email sent to: {username}")
    except Exception as e:
        logger.error(f"Failed to send recovery email to {username}: {e}")


# Using asyncio right now so currently not in use
# async def check_rate_limit(
#     redis: ArqRedis, key: str, max_attempts: int, window_seconds: int
# ):
#     current = await redis.get(key)

#     if current is None:
#         await redis.setex(key, window_seconds, 1)
#         return True

#     if int(current) >= max_attempts:
#         return False

#     await redis.incr(key)
#     return True


# Current in use
def check_rate_limit_memory(
    email: str, max_attempts: int = 3, window_seconds: int = 900
):
    """Rate limiter"""
    now = datetime.now()
    window_start = now - timedelta(seconds=window_seconds)

    # Clean old attempts
    _recovery_attempts[email] = [
        t for t in _recovery_attempts[email] if t > window_start
    ]

    # Check limit
    if len(_recovery_attempts[email]) >= max_attempts:
        return False

    # Record attempt
    _recovery_attempts[email].append(now)
    return True
