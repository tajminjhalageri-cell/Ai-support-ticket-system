from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TicketStatus = Literal["open", "in_progress", "resolved", "closed"]
TicketPriority = Literal["low", "medium", "high", "critical"]


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    status: TicketStatus = "open"
    priority: TicketPriority = "medium"

    model_config = ConfigDict(extra="forbid")


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_update_fields(self) -> "TicketUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Updated fields cannot be null")
        return self


class TicketRead(BaseModel):
    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketList(BaseModel):
    items: list[TicketRead]
    total: int
    skip: int
    limit: int
