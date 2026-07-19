import csv
import os
import sys
import time
from openai import OpenAI
from shared.benchmark import benchmark
from shared.config import require_api_key
from shared.csv_utils import write_benchmark_csv

PROVIDERS: dict[str, dict] = {
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_env_var": "NVIDIA_API_KEY",
        "api_kind": "chat",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_env_var": "OPENROUTER_API_KEY",
        "api_kind": "chat",
        "default_headers": {"HTTP-Referer": "https://github.com/nvidia-nim-benchmarks"},
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_env_var": "GOOGLE_API_KEY",
        "api_kind": "chat",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "api_env_var": "MISTRAL_API_KEY",
        "api_kind": "chat",
    },
    "opencode": {
        "base_url": "https://opencode.ai/zen/v1",
        "api_env_var": "OPENCODE_API_KEY",
        "api_kind": "chat",
    },
    "nous": {
        "base_url": "https://inference-api.nousresearch.com/v1",
        "api_env_var": "NOUS_API_KEY",
        "api_kind": "chat",
    },
}


def load_model_ids(models_path: str) -> list[str]:
    if not os.path.exists(models_path):
        sys.exit(f"Can't find the model list at '{models_path}'. Run filter_models.py first.")
    with open(models_path) as f:
        ids = [line.strip() for line in f if line.strip()]
    if not ids:
        sys.exit(f"'{models_path}' exists but has no model names in it.")
    return ids


def _load_intelligence(output_path: str) -> dict[str, str]:
    if not os.path.exists(output_path):
        return {}
    with open(output_path, newline="") as f:
        return {
            r["Model"]: r["Intelligence"]
            for r in csv.DictReader(f)
            if r.get("Intelligence") not in ("", "-", None)
        }


def run_provider_benchmark(*, provider: str) -> None:
    cfg = PROVIDERS.get(provider)
    if cfg is None:
        sys.exit(f"Unknown provider '{provider}'. Add it to shared.provider.PROVIDERS.")
    if cfg["api_kind"] not in ("chat", "responses"):
        sys.exit(f"Provider '{provider}' has invalid api_kind '{cfg['api_kind']}'.")

    models_path = f"{provider}/data/models.txt"
    output_path = f"{provider}/data/tps.csv"

    key = require_api_key(provider, cfg["api_env_var"])
    client_kwargs = {
        "base_url": cfg["base_url"],
        "api_key": key,
        "timeout": 60.0,
        "max_retries": 0,
        "default_headers": cfg.get("default_headers") or {},
    }
    client = OpenAI(**client_kwargs)
    model_ids = load_model_ids(models_path)

    print(f"Starting benchmark for {len(model_ids)} models...", flush=True)

    results = []
    for model_id in model_ids:
        result = benchmark(model_id=model_id, client=client, provider=provider, api_kind=cfg["api_kind"])
        results.append(result)

    write_benchmark_csv(output_path, results, _load_intelligence(output_path))
    print(f"\nCompleted. Wrote results to {output_path}")
