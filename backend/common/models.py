"""
Models for the FastAPI application, including Pydantic schemas for request and response validation.
"""
from datetime import datetime
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Schemas for client management
# ---------------------------------------------------------------------------
#pylint:disable=missing-class-docstring
class ClientCreate(BaseModel):
    name: str
    address: str | None = None
    contact_number: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    contact_number: str | None = None


class ClientOut(BaseModel):
    id: int
    owner_username: str
    name: str
    address: str | None
    contact_number: str | None
    created_at: datetime
    last_edited_at: datetime
    last_accessed_at: datetime | None


class StatsOut(BaseModel):
    total: int
    last_edited: ClientOut | None
    last_accessed: ClientOut | None


# ---------------------------------------------------------------------------
# Pydantic schemas for login and user management
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class NewUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"   # 'admin' | 'user'
