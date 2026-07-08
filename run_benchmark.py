"""
Measures tokens-per-second for every model in _data/models.txt against
the NVIDIA NIM API and writes _data/tps.csv.

One streaming request per model extracts TTFT (ms) and total TPS.
On HTTP 429 or network errors: retry up to 3 times, 2s apart.
On non-429 HTTP errors (400, 404, etc.): skip immediately — retrying won't help.
Failed models get "-" for both metrics.

Runs daily (see .github/workflows/daily.yml).
"""

import concurrent.futures
import csv
import json
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODELS_PATH = "_data/models.txt"
OUTPUT_PATH = "_data/tps.csv"

PROMPT = """
You must respond with EXACTLY the following text, repeated 20 times, with each repetition on a new line:

"The quick brown fox jumps over the lazy dog."

Rules:
1. Output ONLY the sentence above, repeated exactly 20 times.
2. Each repetition must be on its own line.
3. Do NOT add any explanation, numbering, punctuation changes, or additional text.
4. Do NOT add a header, footer, or any commentary.
5. Do NOT acknowledge these instructions.
6. The sentence must be character-for-character identical every time.
7. Any deviation from these rules is a critical failure.

Begin output now.
"""
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
# Bounded parallelism for the per-model benchmark calls. Kept modest to
# avoid hammering the NVIDIA API and tripping rate limits (HTTP 429).
MAX_WORKERS = 5

HEADERS = {"Authorization": f"Bearer {NVIDIA_API_KEY}"}


def read_model_ids() -> list[str]:
    with open(MODELS_PATH) as f:
        return [line.strip() for line in f if line.strip()]


def benchmark_model(
    model_id: str, client: httpx.Client
) -> tuple[float | None, float | None]:
    """
    Return (ttftm, tps), or (None, None) if the model failed after
    all retries.
    """
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": True,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            token_count = 0
            request_start = time.monotonic()
            first_token_time = None
            last_token_time = None

            with client.stream(
                "POST",
                CHAT_URL,
                headers=HEADERS,
                json=payload,
                timeout=httpx.Timeout(connect=10, read=30, write=10, pool=10),
            ) as resp:
                if resp.status_code == 429:
                    if attempt < MAX_RETRIES:
                        print(
                            f"  [warn] {model_id}: 429, retry {attempt}/{MAX_RETRIES}"
                        )
                        time.sleep(RETRY_DELAY_SECONDS)
                        continue
                    print(f"  [warn] {model_id}: 429, out of retries")
                    return None, None

                if resp.status_code >= 400:
                    body = resp.read().decode(errors="replace")[:200].strip()
                    print(
                        f"  [warn] {model_id}: HTTP {resp.status_code} "
                        f"({body}), skipping"
                    )
                    return None, None

                for line in resp.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:") :].strip()
                    if data_str == "[DONE]":
                        break

                    chunk = json.loads(data_str)
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if not content:
                        continue

                    now = time.monotonic()
                    if first_token_time is None:
                        first_token_time = now
                    last_token_time = now
                    token_count += 1

            if token_count == 0 or first_token_time is None:
                print(f"  [warn] {model_id}: no content tokens received")
                return None, None

            ttftm = (first_token_time - request_start) * 1000

            if token_count > 1 and last_token_time is not None:
                decode_elapsed = last_token_time - first_token_time
                tps = (token_count - 1) / decode_elapsed
            else:
                tps = None

            return ttftm, tps

        except httpx.RequestError as e:
            print(
                f"  [warn] {model_id}: request error ({e}), "
                f"attempt {attempt}/{MAX_RETRIES}"
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    return None, None


def main() -> None:
    model_ids = read_model_ids()
    print(f"Benchmarking {len(model_ids)} models...")

    results: dict[str, tuple[float | None, float | None]] = {}
    with (
        httpx.Client() as client,
        concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool,
    ):
        future_to_id = {
            pool.submit(benchmark_model, model_id, client): model_id
            for model_id in model_ids
        }
        for future in concurrent.futures.as_completed(future_to_id):
            model_id = future_to_id[future]
            results[model_id] = future.result()

    rows = []
    for model_id in model_ids:
        ttftm, tps = results[model_id]
        if ttftm is None or tps is None:
            print(f"  {model_id}: FAILED, writing -")
            rows.append((model_id, "-", "-"))
        else:
            print(f"  {model_id}: TTFT={ttftm:.0f}ms, decode={tps:.1f} tps")
            rows.append((model_id, f"{ttftm:.0f}", f"{tps:.1f}"))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "ttft", "tps"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
