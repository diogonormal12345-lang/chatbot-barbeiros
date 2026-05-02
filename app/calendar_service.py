import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import settings
from app.models import AppointmentRequest, AppointmentResponse

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _load_credentials() -> Credentials:
    """Load Google credentials. Production: env var GOOGLE_TOKEN_JSON. Local dev: token.json file."""
    token_env = os.environ.get("GOOGLE_TOKEN_JSON")
    token_path = Path(settings.google_token_file)
    creds_path = Path(settings.google_credentials_file)
    creds: Credentials | None = None

    if token_env:
        creds = Credentials.from_authorized_user_info(json.loads(token_env), SCOPES)
    elif token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        if not token_env:
            token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    if not creds_path.exists():
        raise RuntimeError(
            "Sem credenciais Google. Em produção: define GOOGLE_TOKEN_JSON com o conteúdo "
            "de token.json. Localmente: descarrega credentials.json e corre o fluxo OAuth uma vez."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _service():
    return build("calendar", "v3", credentials=_load_credentials(), cache_discovery=False)


def list_free_slots(day: datetime, slot_minutes: int = 30,
                    work_start: int = 9, work_end: int = 18) -> list[datetime]:
    tz = ZoneInfo(settings.business_timezone)
    day_start = day.replace(hour=work_start, minute=0, second=0, microsecond=0, tzinfo=tz)
    day_end = day.replace(hour=work_end, minute=0, second=0, microsecond=0, tzinfo=tz)

    body = {
        "timeMin": day_start.isoformat(),
        "timeMax": day_end.isoformat(),
        "items": [{"id": settings.google_calendar_id}],
    }
    busy = _service().freebusy().query(body=body).execute()
    busy_periods = busy["calendars"][settings.google_calendar_id].get("busy", [])

    slots: list[datetime] = []
    cursor = day_start
    while cursor + timedelta(minutes=slot_minutes) <= day_end:
        slot_end = cursor + timedelta(minutes=slot_minutes)
        overlaps = any(
            datetime.fromisoformat(b["start"]) < slot_end
            and datetime.fromisoformat(b["end"]) > cursor
            for b in busy_periods
        )
        if not overlaps:
            slots.append(cursor)
        cursor += timedelta(minutes=slot_minutes)
    return slots


def create_appointment(req: AppointmentRequest) -> AppointmentResponse:
    tz = ZoneInfo(settings.business_timezone)
    start = req.start if req.start.tzinfo else req.start.replace(tzinfo=tz)
    end = start + timedelta(minutes=req.duration_minutes)

    description_lines = [
        f"Cliente: {req.name}",
        f"Telefone: {req.phone}",
    ]
    if req.service:
        description_lines.append(f"Serviço: {req.service}")
    if req.notes:
        description_lines.append(req.notes)

    summary = f"{req.name} — {req.service}" if req.service else req.name

    event = {
        "summary": summary,
        "description": "\n".join(description_lines),
        "start": {"dateTime": start.isoformat(), "timeZone": settings.business_timezone},
        "end": {"dateTime": end.isoformat(), "timeZone": settings.business_timezone},
        "reminders": {"useDefault": True},
    }
    if req.email:
        event["attendees"] = [{"email": req.email}]

    created = _service().events().insert(
        calendarId=settings.google_calendar_id,
        body=event,
        sendUpdates="all" if req.email else "none",
    ).execute()

    return AppointmentResponse(
        event_id=created["id"],
        start=start,
        end=end,
        html_link=created.get("htmlLink", ""),
    )
