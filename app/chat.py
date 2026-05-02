from app.agent import run_chat
from app.config import settings
from app.faq import faq_engine
from app.models import ChatRequest, ChatResponse


def handle_message(req: ChatRequest) -> ChatResponse:
    # Static FAQ short-circuit — only on the first turn, so we don't break a booking flow in progress.
    if not req.history:
        match = faq_engine.search(req.message)
        if match is not None:
            return ChatResponse(reply=match["answer"])

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
