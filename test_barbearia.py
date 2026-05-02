"""Smoke tests for the Barbearia chatbot — language detection, FAQ, combos, booking."""
import json
import requests

BASE = "http://127.0.0.1:8000"


def chat(history, message, label):
    print(f"\n--- {label} ---")
    print(f"USER: {message}")
    r = requests.post(f"{BASE}/chat", json={"message": message, "history": history})
    reply = r.json().get("reply", r.text)
    print(f"BOT : {reply}")
    return [*history, {"role": "user", "content": message},
                       {"role": "assistant", "content": reply}]


print("=" * 60)
print("TESTE 1: Idioma PT — pergunta sobre serviços")
print("=" * 60)
h = []
h = chat(h, "Olá, bom dia!", "PT greeting")
h = chat(h, "Quanto custa um degradê?", "PT preço serviço")

print("\n" + "=" * 60)
print("TESTE 2: Idioma EN — sugestão de combo")
print("=" * 60)
h = []
h = chat(h, "Hi! How much is a haircut and beard?", "EN combo question")

print("\n" + "=" * 60)
print("TESTE 3: Idioma ES — horário e domingo")
print("=" * 60)
h = []
h = chat(h, "Hola, ¿abren los domingos?", "ES Sunday question")

print("\n" + "=" * 60)
print("TESTE 4: Idioma FR — informação geral")
print("=" * 60)
h = []
h = chat(h, "Bonjour, où vous trouvez-vous?", "FR location question")

print("\n" + "=" * 60)
print("TESTE 5: Booking flow end-to-end (PT)")
print("=" * 60)
h = []
h = chat(h, "Olá, queria marcar uma consulta", "PT start booking")
h = chat(h, "Quero um Degradee na próxima quarta-feira às 11h", "PT specify service+time")
h = chat(h, "Sou o João Silva, email: diogonormal12345@gmail.com", "PT name+email")
h = chat(h, "Sim, confirmo", "PT confirm")
