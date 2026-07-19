import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import httpx
from shared.config import require_api_key
from shared.filter import gate_and_write
from shared.provider import run_provider_benchmark

MODELS_URL = "https://opencode.ai/zen/v1/models"
OUTPUT_PATH = "opencode/data/models.txt"
SNAPSHOT_PATH = "opencode/data/endpoint_snapshot.json"

EXCLUDE_TERMS = ["embed", "rerank", "moderation", "tts", "stt", "whisper", "dall-e",
    "stable-diffusion", "midjourney", "content-safety", "safety", "guard",
    "lyria", "clip", "audio", "music"]


def fetch_models() -> list[str]:
    key = require_api_key("opencode", "OPENCODE_API_KEY")
    resp = httpx.get(MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("data", [])]


def name_filter(mid: str) -> bool:
    lower = mid.lower()
    if any(t in lower for t in EXCLUDE_TERMS):
        return False
    return lower.endswith("-free") or "big-pickle" in lower


if __name__ == "__main__":
    gate_and_write("OpenCode", model_ids=fetch_models(),
        output_path=OUTPUT_PATH, snapshot_path=SNAPSHOT_PATH,
        source_url=MODELS_URL, name_filter=name_filter)
    run_provider_benchmark(provider="opencode")
