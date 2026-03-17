from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CursorPageInfo(BaseModel):
    next_cursor: str | None = None
    has_next_page: bool


class CursorPayload(BaseModel):
    date_created: datetime
    item_id: UUID
