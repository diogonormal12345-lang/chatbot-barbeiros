"""Verify date calculations after adding calendar reference."""
import requests

BASE = "http://127.0.0.1:8000"

# wait
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
    return [*history, {"role": "user", "content": message},
                       {"role": "assistant", "content": reply}]


print("=" * 60)
print("Date math test — today is Sat 2026-05-02")
print("=" * 60)
print("Expected: amanha=domingo (closed); proxima quarta=2026-05-06")

h = []
h = chat(h, "Queria marcar para amanhã às 14h", "amanhã (deve recusar — domingo)")

h = []
h = chat(h, "Queria um Degradee na próxima quarta-feira às 16h", "próxima quarta (deve dar 2026-05-06)")
h = chat(h, "Sou o Ana Pereira, ana@example.com", "dados")
# Don't actually book — just check if it proposes the right date in the confirmation question
