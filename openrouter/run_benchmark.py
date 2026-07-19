import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import httpx
from shared.config import require_api_key
from shared.filter import gate_and_write
from shared.provider import run_provider_benchmark

MODELS_URL = "https://openrouter.ai/api/v1/models"
OUTPUT_PATH = "openrouter/data/models.txt"
SNAPSHOT_PATH = "openrouter/data/endpoint_snapshot.json"

EXCLUDE_TERMS = [
    "embed", "rerank", "moderation", "openrouter/free", "tts", "stt",
    "whisper", "dall-e", "stable-diffusion", "midjourney", "content-safety",
    "safety", "guard", "lyria", "clip", "audio", "music",
]
SMALL_MODEL_PATTERNS = ["-1b-", "-1b.", "-1.2b-", "-1.3b-", "-2b-", "-2b."]


def fetch_free_models() -> list[str]:
    key = require_api_key("openrouter", "OPENROUTER_API_KEY")
    resp = httpx.get(MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    free = []
    for m in resp.json().get("data", []):
        p = m.get("pricing", {})
        if float(p.get("prompt", "1") or "1") == 0 and float(p.get("completion", "1") or "1") == 0:
            mods = m.get("architecture", {}).get("output_modalities", [])
            if "text" in mods or not mods:
                free.append(m["id"])
    return sorted(free)


def name_filter(mid: str) -> bool:
    lower = mid.lower()
    if any(t in lower for t in EXCLUDE_TERMS):
        return False
    if any(p in lower for p in SMALL_MODEL_PATTERNS):
        return False
    return True


if __name__ == "__main__":
    gate_and_write("OpenRouter",
        model_ids=fetch_free_models(),
        output_path=OUTPUT_PATH, snapshot_path=SNAPSHOT_PATH,
        source_url=MODELS_URL, name_filter=name_filter)
    run_provider_benchmark(provider="openrouter")
