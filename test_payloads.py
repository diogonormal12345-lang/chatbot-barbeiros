"""Quick smoke tests for /chat — uses requests so encoding stays UTF-8."""
import requests

BASE = "http://127.0.0.1:8000"

cases = [
    ("FAQ horário", "Qual é o horário de funcionamento?"),
    ("FAQ seguros", "Aceitam Médis?"),
    ("FAQ morada", "Onde ficam localizados?"),
    ("FAQ preço", "Quanto custa uma primeira consulta?"),
    ("Intenção marcação", "Queria marcar uma consulta para a próxima semana"),
    ("Fora do FAQ", "Tratam de problemas dermatológicos?"),
    ("Cumprimento", "Olá, bom dia"),
]

for label, msg in cases:
    r = requests.post(f"{BASE}/chat", json={"message": msg, "history": []})
    print(f"\n--- {label} ---")
    print(f"User : {msg}")
    print(f"Bot  : {r.json().get('reply', r.text)}")
