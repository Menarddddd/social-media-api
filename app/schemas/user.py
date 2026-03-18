from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator

from app.exceptions.exception import BadRequestException
from app.schemas.cursor import CursorPageInfo


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class UserDeletion(BaseModel):
    password: str
    reason: str | None = Field(default=None, max_length=200)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_password(self):
        if self.current_password == self.new_password:
            raise BadRequestException(
                "New password must be different from your current password"
            )

        return self


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=7, max_length=200)
    email: EmailStr = Field(min_length=7, max_length=200)


class UserCreate(UserBase):
    password: str = Field(min_length=7, max_length=200)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    email: str | None = None


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


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message: str
    post: PostPublic


class ActivityListPageInfo(BaseModel):
    posts_next_cursor: str | None = None
    posts_next_page: bool
    comments_next_cursor: str | None = None
    comments_next_page: bool


class UserActivity(BaseModel):
    posts: list[PostPublic]
    comments: list[CommentPublic]
    page_info: ActivityListPageInfo


# ADMIN
class AdminDelete(BaseModel):
    reason: str = Field(min_length=1, max_length=200)
