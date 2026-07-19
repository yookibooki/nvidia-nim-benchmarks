import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.matcher import match_provider

def normalize_slug(slug: str) -> str:
    s = slug.lower()
    s = s.removesuffix("-it")
    s = s.replace(".", "-")
    if s.startswith("gemini-") and "-preview" not in s and "-pro-" not in s:
        s = s + "-preview"
    return s

MANUAL_OVERRIDES: dict[str, str] = {
    "gemma-4-26b-a4b-it": "gemma-4-26b-a4b",
    "gemma-4-31b-it": "gemma-4-31b",
    "gemini-3.1-flash-lite": "gemini-3-1-flash-lite-preview",
}

if __name__ == "__main__":
    match_provider(
        "google/data/tps.csv",
        normalize=normalize_slug,
        overrides=MANUAL_OVERRIDES,
    )
