"""Re-test booking flow with explicit confirmation step."""
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


# Wait for server
for _ in range(10):
    try:
        if requests.get(f"{BASE}/health", timeout=2).status_code == 200:
            break
    except Exception:
        pass

print("=" * 60)
print("Booking flow with explicit confirmation (slot livre: Wed 15:00)")
print("=" * 60)
h = []
h = chat(h, "Olá, queria marcar um Degradee", "1: ask service")
h = chat(h, "Para a próxima quarta-feira às 15h", "2: specify time")
h = chat(h, "Sou o Pedro Costa, email pedro.test@example.com", "3: provide name+email")
h = chat(h, "Sim, confirmo a marcação", "4: explicit yes")
