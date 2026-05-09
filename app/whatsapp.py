from collections import defaultdict

from fastapi import Response
from twilio.twiml.messaging_response import MessagingResponse

from app.agent import run_chat

# Histórico de conversa por número de telefone (em memória)
_history: dict[str, list[dict]] = defaultdict(list)


def _twiml(text: str) -> Response:
    resp = MessagingResponse()
    resp.message(text)
    return Response(content=str(resp), media_type="application/xml")


async def whatsapp_webhook(phone: str, message: str) -> Response:
    message = message.strip()

    if not message:
        return _twiml("Não percebi. Podes repetir?")

    history = _history[phone]

    try:
        reply = run_chat(history, message)
    except Exception:
        return _twiml("Ocorreu um erro. Por favor tenta novamente.")

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    _history[phone] = history[-20:]

    return _twiml(reply)
