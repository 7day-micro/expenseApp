from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import uuid
from datetime import datetime
import re


# Data required for user registration (Signup) with strict validation
class UserCreateSchema(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Username must be between 3 and 30 characters",
    )
    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters long"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # REGEX: Minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 number, and 1 special character
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#_])\S{8,}$"
        if not re.match(pattern, v):
            raise ValueError(
                "Password must contain at least: one uppercase letter, one lowercase letter, one number, and one special character (@$!%*?&#_)"
            )
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        # REGEX: Only letters, numbers, and underscores. No spaces or special symbols.
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores (_)"
            )
        return v

    model_config = ConfigDict(
        {
            "from_attributes": True,
            "extra": "forbid",
        }
    )


class UserResponseSchema(BaseModel):
    uid: uuid.UUID
    username: str
    email: EmailStr
    is_verified: bool
    role: str  # role
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        {
            "from_attributes": True,
            "extra": "forbid",
        }
    )


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


# JWT Token schema
class TokenSchema(BaseModel):
    access_token: str
    token_type: str


# Token data extraction
class TokenDataSchema(BaseModel):
    user_id: str | None = None
