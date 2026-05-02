from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)
    session_id: str | None = None


class BookingIntent(BaseModel):
    """Dados extraídos da conversa para marcar uma consulta."""
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    preferred_datetime: datetime | None = None
    notes: str | None = None


class ChatResponse(BaseModel):
    reply: str
    booking: BookingIntent | None = None
    suggested_slots: list[datetime] = Field(default_factory=list)


class AppointmentRequest(BaseModel):
    name: str
    phone: str
    service: str | None = None
    email: EmailStr | None = None
    start: datetime
    duration_minutes: int = 30
    notes: str | None = None


class AppointmentResponse(BaseModel):
    event_id: str
    start: datetime
    end: datetime
    html_link: str
