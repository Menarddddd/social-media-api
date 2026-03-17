from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cursor import CursorPageInfo


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class PostPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    author: UserPublic


class CommentBase(BaseModel):
    message: str = Field(min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class CommentLoadedResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post: PostPublic


class CommentLoadedAllResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author: UserPublic
    post: PostPublic


class CommentPageResponse(BaseModel):
    items: list[CommentLoadedAllResponse]
    page_info: CursorPageInfo


class CommentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
