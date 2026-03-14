from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class UserDeletion(BaseModel):
    password: str
    reason: str | None = Field(default=None, max_length=200)


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
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    email: str | None = None
