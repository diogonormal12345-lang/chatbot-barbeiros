import json
import re
from pathlib import Path
from rapidfuzz import fuzz

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "faq.json"
MATCH_THRESHOLD = 86


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()


class FAQEngine:
    def __init__(self, data_file: Path = DATA_FILE):
        self.data_file = data_file
        self.entries: list[dict] = []
        self.reload()

    def reload(self) -> None:
        if not self.data_file.exists():
            self.entries = []
            return
        with self.data_file.open(encoding="utf-8") as f:
            self.entries = json.load(f)

    def search(self, query: str) -> dict | None:
        if not self.entries:
            return None
        q = _normalize(query)
        best_score = 0.0
        best_idx = -1
        for i, entry in enumerate(self.entries):
            for variant in [entry["question"], *entry.get("aliases", [])]:
                score = fuzz.WRatio(q, _normalize(variant))
                if score > best_score:
                    best_score, best_idx = score, i
        if best_idx < 0 or best_score < MATCH_THRESHOLD:
            return None
        return self.entries[best_idx]


faq_engine = FAQEngine()
