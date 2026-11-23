"""
Models for the FastAPI application, including Pydantic schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Schemas for client management
# ---------------------------------------------------------------------------
# pylint: disable=missing-class-docstring


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
    role: str = "user"  # 'admin' | 'user'

class CreateDataEntryPayload(BaseModel):
    """Schema for creating a new data entry (only the core fields required at creation)."""
    number: int
    jwellery_value: float
    description: str


class UpdateDataEntryPayload(BaseModel):
    """Schema for updating an existing data entry."""
    number: Optional[int] = None
    jwellery_value: Optional[float] = None
    description: Optional[str] = None
    final_value: Optional[float] = None


class CompleteDataEntryPayload(BaseModel):
    """Schema for completing a data entry — sets date_completed and final_value."""
    final_value: float


class GetClientDataEntryResponse(BaseModel):
    """Schema for a data entry response."""
    id: int
    client_id: int
    number: int
    jwellery_value: float
    description: Optional[str] = ""
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    final_value: Optional[float] = None
