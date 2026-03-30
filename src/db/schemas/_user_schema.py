from pydantic import BaseModel
from datetime import datetime


class UserSchema(BaseModel):
    id: int
    email: str

    created_at: datetime
    updated_at: datetime

    class Meta:
        from_attributes = True


class UserCreateSchema(BaseModel):
    email: str
    password: str
