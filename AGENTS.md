# nvidia-nim-benchmarks
Auto leaderboard: https://yookibooki.github.io/nvidia-nim-benchmarks
Benchmarks NIM chat models for TPS, renders static leaderboard. Runs via GH Actions.

## Tree
```
AGENTS.md, filter_models.py, run_benchmark.py, generate_index.py, index.html, _config.yml, pyproject.toml, LICENSE, .gitignore
_data/{endpoint_snapshot.json, intelligence.csv, models.txt, tps.csv}
.github/workflows/daily.yml
```

## Pipeline (daily.yml)
1. Cron trigger.
2. Diff `_data/endpoint_snapshot.json` hash vs live `integrate.api.nvidia.com/v1/models`.
3. Match → `run_benchmark.py` (existing `models.txt`).
4. Diff → `filter_models.py` → new `models.txt` → `run_benchmark.py`.
5. `run_benchmark.py` → `_data/tps.csv`.
6. `generate_index.py` → `index.html` from `tps.csv` + `intelligence.csv`.
7. Commit changed files; push triggers Pages rebuild.
