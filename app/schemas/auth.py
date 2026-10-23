"""Auth request/response schemas."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6)


class SignupRequest(LoginRequest):
    pass


class TokenResponse(BaseModel):
    ok: bool = True
    token: str
