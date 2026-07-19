import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import httpx
from shared.config import require_api_key
from shared.filter import gate_and_write
from shared.provider import run_provider_benchmark

MODELS_URL = "https://inference-api.nousresearch.com/v1/models"
OUTPUT_PATH = "nous/data/models.txt"
SNAPSHOT_PATH = "nous/data/endpoint_snapshot.json"

EXCLUDE_TERMS = ["embed", "rerank", "moderation", "tts", "stt", "whisper", "dall-e",
    "stable-diffusion", "midjourney", "content-safety", "safety", "guard",
    "lyria", "clip", "audio", "music", "safeguard"]


def fetch_models() -> list[str]:
    key = require_api_key("nous", "NOUS_API_KEY")
    resp = httpx.get(MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("data", [])]


def name_filter(mid: str) -> bool:
    if not mid.endswith(":free"):
        return False
    lower = mid.lower()
    return not any(t in lower for t in EXCLUDE_TERMS)


if __name__ == "__main__":
    gate_and_write("Nous", model_ids=fetch_models(),
        output_path=OUTPUT_PATH, snapshot_path=SNAPSHOT_PATH,
        source_url=MODELS_URL, name_filter=name_filter)
    run_provider_benchmark(provider="nous")
