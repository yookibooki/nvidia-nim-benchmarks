"""
Generates index.html from tps.csv data.
Only includes models actually benchmarked on NVIDIA NIM.
Outputs a self-contained HTML file with dark mode and sortable columns.
"""

import csv

TPS_PATH = "_data/tps.csv"
INTELLIGENCE_PATH = "_data/intelligence.csv"
OUTPUT_PATH = "index.html"

# Mapping from NIM API model names to intelligence.csv names
NIM_TO_INTELLIGENCE = {
    "nvidia/nemotron-3-nano-30b-a3b": "nvidia/nvidia-nemotron-3-nano-30b-a3b",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": "nvidia/nemotron-3-nano-omni-30b-a3b",
    "stepfun-ai/step-3.5-flash": "stepfun/step-3-5-flash",
    "stepfun-ai/step-3.7-flash": "stepfun/step-3-7-flash",
    "mistralai/mistral-small-4-119b-2603": "mistral/mistral-small-4",
    "nvidia/nemotron-3-ultra-550b-a55b": "nvidia/nvidia-nemotron-3-ultra-550b-a55b",
    "sarvamai/sarvam-m": "sarvam/sarvam-m-reasoning",
    "google/diffusiongemma-26b-a4b-it": "google/diffusiongemma-26b-a4b",
    "minimaxai/minimax-m2.7": "minimax/minimax-m2-7",
    "abacusai/dracarys-llama-3.1-70b-instruct": None,  # Not in intelligence.csv
    "bytedance/seed-oss-36b-instruct": "bytedance_seed/seed-oss-36b-instruct",
    "deepseek-ai/deepseek-v4-flash": "deepseek/deepseek-v4-flash",
    "deepseek-ai/deepseek-v4-pro": "deepseek/deepseek-v4-pro",
    "google/gemma-2-2b-it": None,  # Not in intelligence.csv
    "google/gemma-3n-e2b-it": "google/gemma-3n-e2b",
    "google/gemma-3n-e4b-it": "google/gemma-3n-e4b",
    "google/gemma-4-31b-it": "google/gemma-4-31b",
    "meta/llama-3.1-70b-instruct": "meta/llama-3-1-instruct-70b",
    "meta/llama-3.1-8b-instruct": "meta/llama-3-1-instruct-8b",
    "meta/llama-3.2-1b-instruct": "meta/llama-3-2-instruct-1b",
    "meta/llama-3.2-3b-instruct": "meta/llama-3-2-instruct-3b",
    "meta/llama-3.3-70b-instruct": "meta/llama-3-3-instruct-70b",
    "meta/llama-4-maverick-17b-128e-instruct": "meta/llama-4-maverick",
    "microsoft/phi-4-mini-instruct": "azure/phi-4-mini",
    "minimaxai/minimax-m3": "minimax/minimax-m3",
    "mistralai/ministral-14b-instruct-2512": "mistral/ministral-3-14b",
    "mistralai/mistral-large-3-675b-instruct-2512": "mistral/mistral-large-3",
    "mistralai/mistral-medium-3.5-128b": "mistral/mistral-medium-3-5",
    "mistralai/mistral-nemotron": None,  # Not in intelligence.csv
    "mistralai/mixtral-8x7b-instruct-v0.1": "mistral/mixtral-8x7b-instruct",
    "moonshotai/kimi-k2.6": "kimi/kimi-k2-6",
    "nvidia/llama-3.1-nemotron-nano-8b-v1": "nvidia/llama-3-1-nemotron-nano-4b-reasoning",
    "nvidia/llama-3.3-nemotron-super-49b-v1": "nvidia/llama-3-3-nemotron-super-49b",
    "nvidia/llama-3.3-nemotron-super-49b-v1.5": "nvidia/llama-nemotron-super-49b-v1-5",
    "nvidia/nemotron-3-super-120b-a12b": "nvidia/nvidia-nemotron-3-super-120b-a12b",
    "nvidia/nemotron-mini-4b-instruct": "nvidia/nvidia-nemotron-3-nano-4b",
    "qwen/qwen3-next-80b-a3b-instruct": "alibaba/qwen3-next-80b-a3b-instruct",
    "qwen/qwen3.5-122b-a10b": "alibaba/qwen3-5-122b-a10b",
    "qwen/qwen3.5-397b-a17b": "alibaba/qwen3-5-397b-a17b",
    "stockmark/stockmark-2-100b-instruct": None,  # Not in intelligence.csv
    "upstage/solar-10.7b-instruct": "upstage/solar-mini",
    "z-ai/glm-5.2": "zai/glm-5-2",
}


def main():
    # Read intelligence.csv for lookup
    intelligence = {}
    with open(INTELLIGENCE_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            intelligence[row["name"]] = row["intelligence"]

    # Read tps.csv - these are the only NIM-hosted models
    models = []
    with open(TPS_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            models.append(row)

    # Sort by intelligence index descending (highest first)
    def sort_key(row):
        intel_name = NIM_TO_INTELLIGENCE.get(row["name"], row["name"])
        val = intelligence.get(intel_name, "0") if intel_name else "0"
        try:
            return -float(val)
        except (ValueError, TypeError):
            return 0

    models.sort(key=sort_key)

    # Build table rows
    rows_html = []
    for row in models:
        name = row["name"]
        # Use mapping to find intelligence score
        intel_name = NIM_TO_INTELLIGENCE.get(name, name)
        intel = intelligence.get(intel_name, "-") if intel_name else "-"
        ttft_raw = row["ttft"]
        tps_raw = row["tps"]

        # Format intelligence
        try:
            intel_fmt = f"{float(intel):.2f}"
        except (ValueError, TypeError):
            intel_fmt = "-"

        # Convert TTFT from ms to seconds
        if ttft_raw == "-":
            ttft_fmt = "-"
        else:
            try:
                ttft_fmt = f"{float(ttft_raw) / 1000:.2f}"
            except (ValueError, TypeError):
                ttft_fmt = "-"

        # Format TPS
        if tps_raw == "-":
            tps_fmt = "-"
        else:
            try:
                tps_fmt = f"{float(tps_raw):.2f}"
            except (ValueError, TypeError):
                tps_fmt = "-"

        rows_html.append(
            f"<tr><td>{name}</td><td>{intel_fmt}</td><td>{ttft_fmt}</td><td>{tps_fmt}</td></tr>"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NVIDIA NIM Models Benchmarks</title>
<style>
body {{ background: #1a1a1a; color: #e0e0e0; font-family: system-ui, sans-serif; margin: 0; padding: 2rem; overflow-x: hidden; }}
h1 {{ text-align: center; margin-bottom: 1.5rem; }}
table {{ border-collapse: collapse; width: auto; margin: 0 auto; }}
th, td {{ padding: 0.4rem 0.6rem; text-align: left; border-bottom: 1px solid #333; }}
th:first-child, td:first-child {{ white-space: normal; min-width: 200px; text-align: right; }}
th:not(:first-child), td:not(:first-child) {{ white-space: nowrap; text-align: center; }}
th {{ background: #2a2a2a; }}
tr:hover {{ background: #252525; }}
a {{ color: #4fc3f7; }}
th {{ cursor: pointer; user-select: none; }}
th .arrow {{ display: inline-block; margin-left: 0.3rem; font-size: 0.5rem; opacity: 0.4; transition: opacity 0.2s; vertical-align: middle; line-height: 1; }}
th:hover .arrow, th.active .arrow {{ opacity: 1; }}
th .arrow::before {{ content: '\\25B2'; }}
th .arrow::after {{ content: '\\25BC'; }}
th.asc .arrow::before, th.desc .arrow::after {{ opacity: 1; }}
th.asc .arrow::after, th.desc .arrow::before {{ opacity: 0.2; }}
</style>
</head>
<body>
<h1>NVIDIA NIM Models Benchmarks</h1>
<table>
<thead>
<tr><th>Model <span class="arrow"></span></th><th>Index <span class="arrow"></span></th><th>TTFT (s) <span class="arrow"></span></th><th>TPS <span class="arrow"></span></th></tr>
</thead>
<tbody>
{chr(10).join(rows_html)}
</tbody>
</table>
<p style="text-align:center;margin-top:1rem;"><a href="https://yookibooki.github.io/nvidia-nim-benchmarks">Results published at yookibooki.github.io/nvidia-nim-benchmarks</a></p>
<script>
document.querySelectorAll('th').forEach((th, col) => {{
  th.addEventListener('click', () => {{
    const tbody = document.querySelector('tbody');
    const rows = [...tbody.querySelectorAll('tr')];
    const asc = th.dataset.asc = th.dataset.asc === '1' ? '0' : '1';
    document.querySelectorAll('th').forEach(h => {{ h.classList.remove('asc', 'desc'); }});
    th.classList.add(asc == 1 ? 'asc' : 'desc');
    rows.sort((a, b) => {{
      const va = a.children[col].textContent.trim();
      const vb = b.children[col].textContent.trim();
      const na = parseFloat(va), nb = parseFloat(vb);
      const cmp = (isNaN(na) || isNaN(nb)) ? va.localeCompare(vb) : na - nb;
      return asc == 1 ? cmp : -cmp;
    }});
    rows.forEach(r => tbody.appendChild(r));
  }});
}});
</script>
</body>
</html>"""

    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    print(f"Wrote {len(models)} NIM-hosted models to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
