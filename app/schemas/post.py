from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class UserPublic(BaseModel):
    id: UUID
    first_name: str
    last_name: str


class CommentPublic(BaseModel):
    message: str
    date_created: datetime
    author: UserPublic


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    id: UUID
    date_created: datetime


class ProfileResponse(PostBase):
    comments: list[CommentPublic]


class FeedResponse(PostBase):
    author: UserPublic
    comments: list[CommentPublic]


class PostUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    content: str | None = None
