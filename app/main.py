from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.calendar_service import create_appointment, list_free_slots
from app.chat import handle_message
from app.config import settings
from app.models import (
    AppointmentRequest,
    AppointmentResponse,
    ChatRequest,
    ChatResponse,
)

app = FastAPI(title=f"Chatbot — {settings.business_name}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/widget", StaticFiles(directory=STATIC_DIR, html=True), name="widget")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "business": settings.business_name}


@app.get("/widget-config")
def widget_config() -> dict:
    return {
        "business_name": settings.business_name,
        "whatsapp": settings.business_whatsapp,
        "phone": settings.business_phone,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return handle_message(req)


@app.get("/availability")
def availability(date: str) -> dict:
    try:
        day = datetime.fromisoformat(date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Data inválida: {e}")
    slots = list_free_slots(day)
    return {"date": date, "slots": [s.isoformat() for s in slots]}


@app.post("/appointments", response_model=AppointmentResponse)
def book_appointment(req: AppointmentRequest) -> AppointmentResponse:
    try:
        return create_appointment(req)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao marcar consulta: {e}")
