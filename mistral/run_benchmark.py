import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import httpx
from shared.config import require_api_key
from shared.filter import gate_and_write
from shared.provider import run_provider_benchmark

MODELS_URL = "https://api.mistral.ai/v1/models"
OUTPUT_PATH = "mistral/data/models.txt"
SNAPSHOT_PATH = "mistral/data/endpoint_snapshot.json"

EXCLUDE_TERMS = ["embed", "fim", "ocr", "moderation", "tts", "stt", "realtime",
    "transcribe", "voxtral", "open-mistral-nemo"]
SMALL_MODEL_PATTERNS = ["-1b-", "-1b.", "-1.2b-", "-1.3b-", "-2b-", "-2b."]


def fetch_chat_models() -> list[str]:
    key = require_api_key("mistral", "MISTRAL_API_KEY")
    resp = httpx.get(MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    return sorted(set(
        m["id"] for m in resp.json().get("data", [])
        if m.get("capabilities", {}).get("completion_chat", False)
    ))


def name_filter(mid: str) -> bool:
    lower = mid.lower()
    if any(t in lower for t in EXCLUDE_TERMS):
        return False
    if any(p in lower for p in SMALL_MODEL_PATTERNS):
        return False
    return True


if __name__ == "__main__":
    gate_and_write("Mistral", model_ids=fetch_chat_models(),
        output_path=OUTPUT_PATH, snapshot_path=SNAPSHOT_PATH,
        source_url=MODELS_URL, name_filter=name_filter)
    run_provider_benchmark(provider="mistral")
