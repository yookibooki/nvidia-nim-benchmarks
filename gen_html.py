import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from shared.csv_utils import merge_provider_csvs
from shared.provider import PROVIDERS

PROVIDER_NAMES = list(PROVIDERS)

MERGED_PATH = "data/tps.csv"
html_path = Path("index.html")

merge_provider_csvs(PROVIDER_NAMES, MERGED_PATH)

if not Path(MERGED_PATH).exists():
    print(f"[error] {MERGED_PATH} not found, skipping HTML generation", file=sys.stderr)
    sys.exit(1)

with open(MERGED_PATH) as f:
    all_rows = list(csv.DictReader(f))

if not all_rows:
    print(f"[error] {MERGED_PATH} is empty, skipping HTML generation", file=sys.stderr)
    sys.exit(1)

rows = sorted(
    all_rows,
    key=lambda r: (
        0 if r.get("Intelligence") not in ("", "-", None) else 1,
        -(int(r["Intelligence"])) if r.get("Intelligence") not in ("", "-", None) else 0,
        r.get("Provider", ""),
        r.get("Model", ""),
    ),
)


def fmt(v):
    if v == "-":
        return "-"
    return str(int(v))


rows_html = ""
for r in rows:
    latency = r["Latency"]
    if latency != "-":
        latency = str(int(latency))
    provider = r.get("Provider", "")
    rows_html += f"<tr><td>{r['Model']}</td><td>{provider}</td><td>{r['Intelligence']}</td><td>{latency}</td><td>{fmt(r['TPS'])}</td></tr>\n"

html_path.write_text(f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>LLM Benchmarks Leaderboard</title>
<style>
body {{ background: #1a1a1a; color: #e0e0e0; font-family: system-ui, sans-serif; margin: 0; padding: 2rem; }}
h1 {{ text-align: center; }}
.updated {{ text-align: center; color: #888; font-size: .9rem; margin-top: -.5rem; }}
table {{ border-collapse: collapse; margin: 1rem auto; }}
th, td {{ padding: .4rem .6rem; border-bottom: 1px solid #333; }}
th:first-child, td:first-child {{ text-align: right; }}
th:not(:first-child), td:not(:first-child) {{ white-space: nowrap; text-align: center; }}
th {{ background: #2a2a2a; cursor: pointer; }}
.provider {{ font-size: .75rem; padding: .1rem .3rem; border-radius: 3px; }}
.provider-nvidia {{ background: #76b900; color: #000; }}
.provider-openrouter {{ background: #ff6b35; color: #000; }}
.provider-google {{ background: #4285f4; color: #fff; }}
.provider-mistral {{ background: #ff7000; color: #000; }}
.provider-opencode {{ background: #3498db; color: #fff; }}
.provider-nous {{ background: #e74c3c; color: #fff; }}
</style>
</head>
<body>
<h1>LLM Benchmarks Leaderboard</h1>
<p class="updated" data-iso="{datetime.now(timezone.utc).isoformat()}"></p>
<table>
<tr><th>Model</th><th>Provider</th><th>Intelligence</th><th>Latency</th><th>TPS</th></tr>
{rows_html}</table>
<script>
function fmtAgo(secs) {{
  const m = Math.floor(secs / 60);
  if (m < 60) return m + ' minute' + (m === 1 ? '' : 's') + ' ago';
  const h = Math.floor(m / 60);
  if (h < 24) return h + ' hour' + (h === 1 ? '' : 's') + ' ago';
  const d = Math.floor(h / 24);
  return d + ' day' + (d === 1 ? '' : 's') + ' ago';
}}
const el = document.querySelector('.updated');
const then = new Date(el.dataset.iso);
function tick() {{
  const secs = (Date.now() - then.getTime()) / 1000;
  el.textContent = 'Updated ' + fmtAgo(secs);
}}
tick();
setInterval(tick, 60000);
document.querySelectorAll('th').forEach((th, col) => {{
  th.addEventListener('click', () => {{
    const rows = [...document.querySelectorAll('tr')].slice(1);
    const asc = th.dataset.asc = th.dataset.asc === '1' ? '0' : '1';
    document.querySelectorAll('th').forEach(h => h.classList.remove('asc', 'desc'));
    th.classList.add(asc == 1 ? 'asc' : 'desc');
    rows.sort((a, b) => {{
      const va = a.children[col].textContent.trim();
      const vb = b.children[col].textContent.trim();
      const na = parseFloat(va), nb = parseFloat(vb);
      const cmp = (isNaN(na) || isNaN(nb)) ? va.localeCompare(vb) : na - nb;
      return asc == 1 ? cmp : -cmp;
    }});
    rows.forEach(r => r.parentNode.appendChild(r));
  }});
}});
</script>
</body>
</html>
""")
