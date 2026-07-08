"""
Fetches the Artificial Analysis Intelligence Index for open-weights models and
writes _data/intelligence.csv (name,intelligence) using the raw AA index value.

This is a MANUAL tool — run it by hand, not in CI:

    python3 fetch_intelligence.py

The "name" column uses the format vendor/slug (e.g. "deepseek/deepseek-r1").
"""

import csv
import re
import urllib.request

LEADERBOARD_URL = "https://artificialanalysis.ai/leaderboards/models"
OUTPUT_PATH = "_data/intelligence.csv"

_MODELS_ARRAY_RE = re.compile(r'\\?"models\\?":\s*\[')
_FIELD_RE = lambda k: re.compile(r'\\?"' + k + r'\\?":\s*\\?"([^"\\]+)\\?"')
_INDEX_RE = re.compile(r'\\?"intelligenceIndex\\?":\s*(-?\d+(?:\.\d+)?)')


def _extract_pairs(html: str) -> list[tuple[str, float]]:
    pairs: list[tuple[str, float]] = []
    for arr in _MODELS_ARRAY_RE.finditer(html):
        start = arr.end()
        if "intelligenceIndex" not in html[start : start + 5000]:
            continue
        pos = start
        while pos < len(html):
            obj_start = html.find("{", pos)
            if obj_start < 0:
                break
            depth, i = 1, obj_start + 1
            while i < len(html) and depth:
                if html[i] == "{":
                    depth += 1
                elif html[i] == "}":
                    depth -= 1
                i += 1
            if depth == 0:
                obj = html[obj_start:i]
                cm = _FIELD_RE("modelCreatorSlug").search(obj)
                sm = _FIELD_RE("slug").search(obj)
                im = _INDEX_RE.search(obj)
                if cm and sm and im:
                    pairs.append((f"{cm.group(1)}/{sm.group(1)}", float(im.group(1))))
            pos = i
    return pairs


def main() -> None:
    print(f"Fetching {LEADERBOARD_URL} ...")
    req = urllib.request.Request(LEADERBOARD_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode()

    pairs = _extract_pairs(html)
    if not pairs:
        raise SystemExit("No (name, intelligenceIndex) pairs found on the page.")

    best: dict[str, float] = {}
    for name, score in pairs:
        if score > best.get(name, float("-inf")):
            best[name] = score

    rows = sorted(best.items())
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "intelligence"])
        for name, score in rows:
            writer.writerow([name, f"{score:.1f}"])

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
