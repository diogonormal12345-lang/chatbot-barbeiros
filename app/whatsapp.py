from collections import defaultdict

from fastapi import Form, Request, Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from app.agent import run_chat
from app.config import settings

# Histórico de conversa por número de telefone (em memória)
_history: dict[str, list[dict]] = defaultdict(list)


def _twiml(text: str) -> Response:
    resp = MessagingResponse()
    resp.message(text)
    return Response(content=str(resp), media_type="application/xml")


async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
) -> Response:
    # Valida que o pedido vem mesmo da Twilio
    if settings.twilio_auth_token:
        validator = RequestValidator(settings.twilio_auth_token)
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        form_data = dict(await request.form())
        if not validator.validate(url, form_data, signature):
            return Response(content="Forbidden", status_code=403)

    phone = From  # ex: "whatsapp:+351912345678"
    message = Body.strip()

    if not message:
        return _twiml("Não percebi. Podes repetir?")

    history = _history[phone]

    try:
        reply = run_chat(history, message)
    except Exception:
        return _twiml("Ocorreu um erro. Por favor tenta novamente.")

    # Actualiza o histórico (mantém últimas 20 mensagens)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    _history[phone] = history[-20:]

    return _twiml(reply)
