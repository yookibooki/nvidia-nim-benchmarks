# llm-benchmarks

Auto leaderboard: https://yookibooki.github.io/llm-benchmarks
Benchmarks LLM providers for tokens-per-second (TPS) + latency, then merges each
model's Artificial Analysis (AA) intelligence score and renders a static
leaderboard (`index.html`). Driven daily by GitHub Actions.

> Run scripts with `python3 path/to/script.py` (deps: `httpx`, `openai`,
> `python-dotenv`). Each provider script adds the repo root to `sys.path` so
> `import shared.*` works.

## Tree

```
AGENTS.md, gen_html.py, index.html, LICENSE, .gitignore, .nojekyll
data/aa_raw.json, data/tps.csv              (shared - merged leaderboard)
shared/                                     (shared Python package)
  benchmark.py                              (streaming TPS/latency measurement)
  config.py                                 (repo root + API key helper)
  csv_utils.py                              (read/write/merge benchmark CSVs)
  filter.py                                 (snapshot-gated model filtering)
  matcher.py                                (merge AA intelligence into tps.csv)
  provider.py                               (PROVIDERS registry + run harness)
  snapshot.py                               (endpoint catalog snapshot/hash)
nvidia/ openrouter/ google/ mistral/ opencode/ nous/   (one per provider)
.github/workflows/daily.yml
```

## Provider structure

Each provider directory contains three thin scripts plus its own `data/`:

- `filter_models.py` — fetches the available models, applies provider-specific
  excludes, and writes `data/models.txt`. Uses a `data/endpoint_snapshot.json`
  hash gate so unchanged catalogs are skipped.
- `run_benchmark.py` — a one-line wrapper calling
  `shared.provider.run_provider_benchmark(provider="...")`, which reads
  `data/models.txt`, benchmarks each model, and writes `data/tps.csv`.
- `tps-aa_matcher.py` — calls `shared.matcher.match_provider(...)` to fill the
  `Intelligence` column of `data/tps.csv` from `data/aa_raw.json`. Each provider
  supplies its own `normalize_slug`, `MANUAL_OVERRIDES`, `MANUAL_INTELLIGENCE`,
  and (for namespaced providers) `expected_creator`.
- `data/` — provider-local state: `models.txt`, `tps.csv`, `endpoint_snapshot.json`.

## Provider registry

All providers are registered once in `shared/provider.py` (`PROVIDERS` dict),
keyed by directory name, each with `base_url`, `api_env_var`, and `api_kind`
(`"chat"` or `"responses"`). `gen_html.py` imports this registry to know which
provider data dirs to merge. **Adding a provider requires updating `PROVIDERS`
there** — it is no longer configured in `gen_html.py`.

## Adding a new provider

1. Create `new-provider/` with `filter_models.py`, `run_benchmark.py`,
   `tps-aa_matcher.py` (copy an existing provider and adapt the filter/matcher).
2. Register it in `PROVIDERS` in `shared/provider.py` (base_url, api_env_var,
   api_kind).
3. Add the `API_ENV_VAR` secret to the repo and to the `env:` block in
   `.github/workflows/daily.yml`.
4. Add the provider directory name to the `for prov in ...` loop in each step
   of the `benchmark` job in `.github/workflows/daily.yml`.

## Pipeline (daily.yml)

1. Cron trigger (daily at 17:00 UTC) or manual `workflow_dispatch`.
   Concurrency group `daily-benchmark` cancels in-progress runs.
2. A single runner runs all 6 providers **in parallel** (background processes
   per provider, joined with `wait`). Each provider goes through
   filter→benchmark→match in its own step — all providers filter concurrently,
   then all benchmark concurrently, then all match concurrently. Within each
   provider, models are benchmarked sequentially (one at a time).
   A failing provider does **not** block the others — each `python3`
   invocation is guarded with `|| echo "WARNING: ..."`.
3. After all providers complete, `gen_html.py` merges every `data/tps.csv`
   into `data/tps.csv`, renders `index.html`, commits, and deploys.

## Shared data

- `data/aa_raw.json` — Artificial Analysis model list with intelligence index
  and creator slugs; source for the `Intelligence` column (shared by all
  providers).
- `data/tps.csv` — merged leaderboard: columns
  `Model, Provider, Intelligence, Latency, TPS` (`-` = no value).

## How benchmarking works (`shared/benchmark.py`)

For each model it streams a fixed known prompt and measures:
- **Latency** — seconds to first token.
- **TPS** — chars generated ÷ streaming duration (characters per second).
  Hard timeout 8s, total timeout 40s (SIGALRM guarded). Failures are recorded
  with an error reason per model.

## Fetch AA data

```bash
curl -H "x-api-key: $AA_API_KEY" https://artificialanalysis.ai/api/v2/data/llms/models -o data/aa_raw.json
```

`shared/matcher.py` reads `data/aa_raw.json` → `["data"]`, indexes by `slug`,
keeps the highest `artificial_analysis_intelligence_index`, and matches each
`Model` via slug normalization, `MANUAL_OVERRIDES`, or `MANUAL_INTELLIGENCE`,
optionally verifying the AA `creator` slug.

## Conventions

- API keys come from environment variables / repo secrets (`NVIDIA_API_KEY`,
  `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `MISTRAL_API_KEY`, `OPENCODE_API_KEY`,
  `NOUS_API_KEY`) — there are no per-provider `.env` files in the repo.
- Provider scripts self-register on `sys.path` (`sys.path.insert(0, repo_root)`)
  before importing `shared`.
- Keep `shared/` provider-agnostic; provider-specific logic (excludes,
  normalization, overrides) belongs in each provider's scripts.
