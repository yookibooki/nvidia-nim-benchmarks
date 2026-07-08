"""
Pulls the live model list from NVIDIA NIM, drops known non-chat model
families by name, probes survivors with a minimal request, and writes
the survivors to _data/models.txt (one id per line, no header).

Also writes _data/endpoint_snapshot.json containing a hash of the full
live catalog, so daily.yml can detect when the catalog changed and only
re-run this filter then.

Runs weekly via .github/workflows/filter-models.yml, and is also invoked
automatically by daily.yml when the catalog hash changes.
"""

import hashlib
import json
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODELS_URL = f"{BASE_URL}/models"
CHAT_URL = f"{BASE_URL}/chat/completions"
OUTPUT_PATH = "_data/models.txt"
SNAPSHOT_PATH = "_data/endpoint_snapshot.json"

EXCLUDE_TERMS = [
    "embed",
    "image",
    "vision",
    "video",
    "audio",
    "moderation",
    "rerank",
    "guard",
    "clip",
    "parse",
    "retriever",
    "deplot",
    "diffusion",
    "kosmos",
    "neva",
    "vila",
    "pii",
    "reward",
    "safety",
    "content-safety",
    "ising",
    "bge",
    "fuyu",
    "multimodal",
    "translate",
    "cosmos",
]

HEADERS = {"Authorization": f"Bearer {NVIDIA_API_KEY}"}


def model_list_hash(model_ids: list[str]) -> str:
    """Stable hash of the full live catalog; changes when any model is added/removed."""
    normalized = "\n".join(sorted(model_ids))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def write_snapshot(model_ids: list[str]) -> None:
    """Persist a hash of the live catalog so daily.yml can detect changes."""
    snapshot = {
        "hash": model_list_hash(model_ids),
        "count": len(model_ids),
        "source": MODELS_URL,
    }
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)
        f.write("\n")


def fetch_model_ids() -> list[str]:
    resp = httpx.get(MODELS_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [m["id"] for m in data["data"]]


def name_filter(model_id: str) -> bool:
    """Return True if model_id should be KEPT (does not match exclude terms)."""
    lower = model_id.lower()
    return not any(term in lower for term in EXCLUDE_TERMS)


def probe_model(model_id: str, client: httpx.Client) -> bool:
    """Return True unless the model returns 404."""
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    }
    try:
        resp = client.post(CHAT_URL, headers=HEADERS, json=payload, timeout=30)
    except httpx.RequestError as e:
        print(f"  [warn] {model_id}: request error ({e}), keeping", file=sys.stderr)
        return True

    if resp.status_code == 404:
        return False
    if resp.status_code >= 400:
        print(
            f"  [warn] {model_id}: probe returned {resp.status_code}, keeping",
            file=sys.stderr,
        )
    return True


def main() -> None:
    print("Fetching model list from NVIDIA NIM...")
    all_ids = fetch_model_ids()
    print(f"  {len(all_ids)} models returned")

    write_snapshot(all_ids)
    print(f"  catalog hash={model_list_hash(all_ids)[:12]}")

    name_filtered = [m for m in all_ids if name_filter(m)]
    print(f"  {len(name_filtered)} survive name filter")

    survivors = []
    with httpx.Client() as client:
        for model_id in name_filtered:
            if probe_model(model_id, client):
                survivors.append(model_id)
            else:
                print(f"  dropping {model_id} (404)")

    print(f"  {len(survivors)} survive probe step")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        for model_id in sorted(survivors):
            f.write(f"{model_id}\n")

    print(f"Wrote {len(survivors)} model ids to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
