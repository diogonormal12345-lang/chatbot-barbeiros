"""Test: phone instead of email, any language, no 'consulta' word."""
import re
import requests

BASE = "http://127.0.0.1:8000"

for _ in range(10):
    try:
        if requests.get(f"{BASE}/health", timeout=2).status_code == 200:
            break
    except Exception:
        pass


def chat(history, message, label):
    print(f"\n--- {label} ---")
    print(f"USER: {message}")
    r = requests.post(f"{BASE}/chat", json={"message": message, "history": history})
    reply = r.json().get("reply", r.text)
    print(f"BOT : {reply}")
    if re.search(r"\bconsulta\b", reply, re.IGNORECASE):
        print("!!! REGRESSION: bot used 'consulta' !!!")
    if re.search(r"\bemail\b", reply, re.IGNORECASE):
        print("!!! WARN: bot mentioned email !!!")
    return [*history, {"role": "user", "content": message},
                       {"role": "assistant", "content": reply}]


print("=" * 60)
print("TEST 1: PT booking with phone (Mon 4 mai 16:00)")
print("=" * 60)
h = []
h = chat(h, "Olá, queria marcar um corte", "ask service")
h = chat(h, "Um Tradicional curto na segunda-feira às 16h", "specify time")
h = chat(h, "Sou o Rui Santos, telefone 912345678", "name+phone")
h = chat(h, "Sim, confirmo", "confirm")

print("\n" + "=" * 60)
print("TEST 2: Italiano (idioma fora dos 4 originais)")
print("=" * 60)
h = []
h = chat(h, "Ciao, vorrei prenotare un taglio di capelli", "IT booking")

print("\n" + "=" * 60)
print("TEST 3: Alemão")
print("=" * 60)
h = []
h = chat(h, "Hallo, was kostet ein Haarschnitt?", "DE price question")
