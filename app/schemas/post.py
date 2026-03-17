from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.cursor import CursorPageInfo


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    date_created: datetime
    author: UserPublic


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date_created: datetime


class ProfileResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    comments: list[CommentPublic]


class ProfilePostPageResponse(BaseModel):
    items: list[ProfileResponse]
    page_info: CursorPageInfo


class FeedResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date_created: datetime
    author: UserPublic
    comments: list[CommentPublic]


class FeedPageResponse(BaseModel):
    items: list[FeedResponse]
    page_info: CursorPageInfo


class PostUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    content: str | None = None
