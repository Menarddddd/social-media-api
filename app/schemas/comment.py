from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    id: UUID
    first_name: str
    last_name: str


class PostPublic(BaseModel):
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
    id: UUID
    post: PostPublic


class CommentLoadedAllResponse(CommentBase):
    id: UUID
    author: UserPublic
    post: PostPublic


class CommentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
