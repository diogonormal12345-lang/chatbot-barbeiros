import json
from datetime import date as date_cls, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from anthropic import Anthropic, beta_tool

from app.calendar_service import create_appointment as calendar_create
from app.calendar_service import list_free_slots
from app.config import settings
from app.models import AppointmentRequest

BUSINESS_FILE = Path(__file__).resolve().parent.parent / "data" / "business.json"
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _load_business() -> dict:
    return json.loads(BUSINESS_FILE.read_text(encoding="utf-8"))


def _hours_for(d: date_cls, business: dict) -> dict | None:
    return business["hours"][WEEKDAYS[d.weekday()]]


def _format_services(business: dict) -> str:
    lines = []
    for category, items in business["services"].items():
        lines.append(f"\n{category}:")
        for name, price in items.items():
            lines.append(f"  - {name}: {price}€")
    return "\n".join(lines)


def _format_hours(business: dict) -> str:
    pt = {"monday": "Segunda", "tuesday": "Terça", "wednesday": "Quarta",
          "thursday": "Quinta", "friday": "Sexta", "saturday": "Sábado", "sunday": "Domingo"}
    lines = []
    for day, label in pt.items():
        h = business["hours"][day]
        if h is None:
            lines.append(f"  - {label}: fechado")
        else:
            lines.append(f"  - {label}: {h['open']}–{h['close']}")
    return "\n".join(lines)


def _date_reference(today: date_cls, days: int = 14) -> str:
    pt_days = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
               "sexta-feira", "sábado", "domingo"]
    pt_months = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    lines = []
    for i in range(days):
        d = today + timedelta(days=i)
        label = "HOJE" if i == 0 else ("AMANHÃ" if i == 1 else "")
        lines.append(
            f"  - {d.isoformat()} = {pt_days[d.weekday()]}, {d.day} de {pt_months[d.month - 1]} {label}".rstrip()
        )
    return "\n".join(lines)


def _build_system_prompt() -> str:
    b = _load_business()
    today = datetime.now(ZoneInfo(settings.business_timezone)).date()
    return f"""És o(a) recepcionista virtual da {b['name']}, uma barbearia em Leiria, Portugal.

CALENDÁRIO DE REFERÊNCIA — usa SEMPRE estas datas (não calcules de cabeça):
{_date_reference(today)}


INFORMAÇÃO DO NEGÓCIO (em português — adapta ao idioma do cliente quando responderes):
- Morada: {b['address']}
- Telefone: {b['phone']}
- Email: {b['email']}
- Barbeiros: {', '.join(b['barbers'])}

HORÁRIO DE FUNCIONAMENTO:
{_format_hours(b)}

SERVIÇOS E PREÇOS:
{_format_services(b)}

REGRAS DE COMPORTAMENTO:
1. **Idioma**: Detecta o idioma em que o cliente escreve a PRIMEIRA mensagem — qualquer idioma (português, inglês, espanhol, francês, italiano, alemão, ucraniano, romeno, etc.) — e responde SEMPRE nesse idioma durante toda a conversa, mesmo que o cliente alterne. Se não conseguires identificar o idioma, usa português europeu. Traduz os nomes dos serviços para o idioma do cliente sempre que possível.
2. **Tom e formatação**: Simpático, profissional e breve. Cumprimenta no início. Usa emojis com moderação para tornar a conversa mais visual e calorosa — bons exemplos: 💈 (barbearia), ✂️ (corte), 🧔 (barba), 📅 (marcação/dia), ⏰ (horário), 📍 (morada), 📞 (telefone), ✅ (confirmação). Um emoji por linha/secção é o suficiente — não exageres.
   IMPORTANTE: NÃO uses markdown. Nada de `**negrito**`, `#cabeçalhos`, nem listas com `-` ou `*` no início da linha. O widget mostra texto plano e os asteriscos apareceriam literalmente. Para destacar categorias usa emojis (ex: "✂️ Cortes: Degradee 15€, Tradicional curto 13€...") em vez de negrito. Para listar usa frases corridas separadas por vírgulas, ou parágrafos simples — nunca bullets.
3. **Vocabulário**: Esta é uma BARBEARIA, não uma clínica. NUNCA uses a palavra "consulta" — usa "marcação", "corte", "serviço", "appointment" (em inglês), "cita" (em espanhol), "rendez-vous" (em francês), etc. conforme o idioma.
4. **Sugere combos quando relevante**: se o cliente quiser corte + barba, propõe o combo apropriado (mais barato que separado).
5. **Marcações** — fluxo OBRIGATÓRIO em duas fases:
   **Fase A (recolha)**: Pede ao longo da conversa (não tudo de uma vez): serviço, dia, hora, nome completo, e número de telefone (necessário para o barbeiro contactar caso seja preciso). NÃO peças email.
   **Fase B (verificação + confirmação)**: Quando tiveres todos os dados:
   1. Chama `check_availability` para verificar o dia.
   2. Se o slot pedido está OCUPADO: informa e propõe alternativas livres próximas; volta à fase A.
   3. Se o slot está LIVRE: NÃO chames `create_appointment` ainda. Em vez disso, mostra um resumo ao cliente ("Vou marcar X para Y às Z em nome de W, telefone V. Confirma?") e ESPERA que ele responda explicitamente "sim" / "yes" / "sí" / "oui" ou equivalente no idioma da conversa.
   4. Só depois de receberes essa confirmação explícita é que chamas `create_appointment`.
   5. Após `create_appointment` ter sucesso, comunica a confirmação ao cliente — explica que o barbeiro tem o telefone para o contactar em caso de necessidade.
   Nunca chames `create_appointment` baseado em assumir consentimento — o cliente tem de confirmar explicitamente.
6. **Domingo fechado**: se o cliente pedir para domingo, recusa e propõe segunda.
7. **Datas**: usa o CALENDÁRIO DE REFERÊNCIA acima — NUNCA calcules dias da semana ou datas de cabeça. Quando o cliente disser "amanhã", "próxima quarta", etc., procura na tabela acima a linha que corresponde e usa essa data ISO. Antes de propor uma data ao cliente verifica que o dia da semana que dizes corresponde mesmo à data ISO da tabela.
8. **Não inventes preços nem serviços** que não estejam na lista. Se perguntarem por algo que não há, diz que não fazemos esse serviço e oferece alternativas.
9. **Não confirmes marcações** sem usar a ferramenta `create_appointment` — só está confirmado quando recebes resposta de sucesso.
"""


@beta_tool
def check_availability(date: str) -> str:
    """Verifica os horários livres num dia específico da barbearia.

    Args:
        date: Data no formato ISO YYYY-MM-DD (ex: 2026-05-05).

    Returns:
        Lista de horários livres em formato HH:MM, ou mensagem de erro se a barbearia estiver fechada nesse dia ou se a data for inválida/passada.
    """
    business = _load_business()
    tz = ZoneInfo(settings.business_timezone)

    try:
        target = date_cls.fromisoformat(date)
    except ValueError:
        return f"Erro: data '{date}' inválida. Usa o formato YYYY-MM-DD."

    today = datetime.now(tz).date()
    if target < today:
        return f"Erro: a data {date} já passou."

    hours = _hours_for(target, business)
    if hours is None:
        return f"A barbearia está fechada em {date} (domingo)."

    open_h = int(hours["open"].split(":")[0])
    close_h = int(hours["close"].split(":")[0])
    day_dt = datetime.combine(target, datetime.min.time())
    slots = list_free_slots(day_dt, slot_minutes=30, work_start=open_h, work_end=close_h)

    if not slots:
        return f"Não há horários livres em {date}."

    formatted = [s.strftime("%H:%M") for s in slots]
    return f"Horários livres em {date} ({hours['open']}–{hours['close']}): {', '.join(formatted)}"


@beta_tool
def create_appointment(name: str, phone: str, datetime_iso: str, service: str) -> str:
    """Cria uma marcação confirmada no Google Calendar do barbeiro com o telefone do cliente para contacto.

    Só chamar depois de o cliente ter confirmado os dados E de check_availability ter mostrado que o slot está livre.

    Args:
        name: Nome completo do cliente.
        phone: Número de telefone do cliente (com indicativo se possível, ex: +351 912 345 678).
        datetime_iso: Data e hora ISO (ex: 2026-05-05T14:30:00).
        service: Nome exato do serviço da lista (ex: 'Degradee', 'Combo: Degradee + Barba Design').

    Returns:
        Confirmação com event_id, ou mensagem de erro.
    """
    business = _load_business()
    tz = ZoneInfo(settings.business_timezone)

    try:
        start = datetime.fromisoformat(datetime_iso)
        if start.tzinfo is None:
            start = start.replace(tzinfo=tz)
    except ValueError:
        return f"Erro: datetime '{datetime_iso}' inválido."

    duration = business.get("default_service_duration_minutes", 30)
    req = AppointmentRequest(
        name=name,
        phone=phone,
        service=service,
        start=start,
        duration_minutes=duration,
    )
    try:
        resp = calendar_create(req)
    except Exception as e:
        return f"Erro ao criar marcação: {e}"

    return (
        f"Marcação confirmada. event_id={resp.event_id}, "
        f"início={resp.start.isoformat()}"
    )


def run_chat(history: list[dict], user_message: str) -> str:
    """Run one chat turn with full conversation history. Returns the assistant text reply."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    messages = [*history, {"role": "user", "content": user_message}]

    runner = client.beta.messages.tool_runner(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=_build_system_prompt(),
        tools=[check_availability, create_appointment],
        messages=messages,
    )

    last_text = ""
    for message in runner:
        text_parts = [b.text for b in message.content if b.type == "text"]
        if text_parts:
            last_text = "\n".join(text_parts)
    return last_text or "Desculpe, ocorreu um problema. Pode repetir?"
