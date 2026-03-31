from email.message import EmailMessage

import aiosmtplib
import base64
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError

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


async def send_recovery_email(to_email: str, token: str, username: str = "User"):
    """Send password recovery email via Gmail SMTP."""
    try:
        message = EmailMessage()
        message["From"] = f"SocialMediaApp <{settings.GMAIL_USERNAME}>"
        message["To"] = to_email
        message["Subject"] = "Password Recovery - SocialMediaApp"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Account Recovery</h2>
                <p>Hi <strong>{username}</strong>,</p>
                <p>You requested to recover your account password.</p>
                
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Your recovery token:</strong></p>
                    <code style="font-size: 18px; color: #4CAF50; font-weight: bold;">{token}</code>
                </div>
                
                <p>⏰ This token will expire in <strong>{settings.RECOVERY_MINUTES} minutes</strong>.</p>
                
                <p>To reset your password, use this token in the password reset form.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px;">
                    If you did not request this, please ignore this email. Your password will remain unchanged.
                </p>
                
                <p style="color: #999; font-size: 12px;">
                    This is an automated message from SocialMediaApp. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

        message.set_content(html_content, subtype="html")

        # Send email
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.GMAIL_USERNAME,
            password=settings.GMAIL_PASSWORD.get_secret_value(),
        )

        logger.info(f"Recovery email sent to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send recovery email to {to_email}: {str(e)}")
        raise


async def _send_recovery_email_task(email: str, token: str, username: str):
    """Background task wrapper for sending recovery email."""
    try:
        await send_recovery_email(email, token, username)
    except Exception as e:
        logger.error(f"Background email task failed: {str(e)}")


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
