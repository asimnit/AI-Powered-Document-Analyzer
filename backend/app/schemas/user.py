"""
User Schemas (Pydantic Models)

Define data structures for API requests and responses.
- Request validation: Ensure incoming data is correct
- Response serialization: Format data sent to frontend
- Type safety: TypeScript-like types for Python
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """
    Base User Schema
    Shared properties across different user schemas
    """
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema for user registration
    Used when creating a new user
    """
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """
    Schema for user login
    Can login with either email or username
    """
    username: str
    password: str


class UserUpdate(BaseModel):
    """
    Schema for updating user profile
    All fields are optional
    """
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """
    Schema for user response (sent to frontend)
    Notice: Does NOT include password!
    """
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        """Pydantic config"""
        from_attributes = True  # Allow ORM models to be converted


class Token(BaseModel):
    """
    Schema for JWT token response
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Schema for data stored in JWT token
    """
    user_id: Optional[int] = None
