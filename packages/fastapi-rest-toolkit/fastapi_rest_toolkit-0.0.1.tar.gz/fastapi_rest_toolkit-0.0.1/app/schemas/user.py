from pydantic import EmailStr
from app.schemas import BaseSchema


class UserRead(BaseSchema):
    id: int
    email: EmailStr
    name: str
    is_admin: bool


class UserCreate(BaseSchema):
    email: EmailStr
    name: str
    is_admin: bool = False


class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    name: str | None = None
    is_admin: bool | None = None
