from app.agent import run_chat
from app.config import settings
from app.models import ChatRequest, ChatResponse


def handle_message(req: ChatRequest) -> ChatResponse:
    if not settings.anthropic_api_key:
        return ChatResponse(
            reply=(
                f"O assistente da {settings.business_name} está temporariamente indisponível. "
                f"Por favor contacte directamente: {settings.business_phone}."
            )
        )

    history = [{"role": m.role, "content": m.content} for m in req.history]
    reply = run_chat(history, req.message)
    return ChatResponse(reply=reply)
