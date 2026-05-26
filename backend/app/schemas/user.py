"""
Pydantic schemas for User auth and profile.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(..., examples=["john@company.com"])
    name: str = Field(..., min_length=1, max_length=255, examples=["John Doe"])
    password: str = Field(..., min_length=6, examples=["securepassword"])
    role: str = Field(default="engineer", examples=["engineer", "lead", "manager"])
    tier: int = Field(default=1, ge=1, le=3, examples=[1])


class UserLogin(BaseModel):
    email: str = Field(..., examples=["john@company.com"])
    password: str = Field(..., examples=["securepassword"])


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    tier: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
