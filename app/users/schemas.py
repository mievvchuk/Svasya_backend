from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.common.enums import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreateStaffRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    role: UserRole = Field(description="Must be 'admin' or 'manager'")


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    phone: str
    role: UserRole
    is_active: bool = True
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ManagerContactResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
