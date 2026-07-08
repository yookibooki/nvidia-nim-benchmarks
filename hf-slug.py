import csv
import re
from difflib import SequenceMatcher

from huggingface_hub import HfApi

api = HfApi()


def normalize(s):
    # lowercase, strip punctuation/spaces for comparison
    return re.sub(r"[^a-z0-9]", "", s.lower())


def slug_last_part(model_id):
    return model_id.split("/")[-1]


def score_match(query, model_id):
    q = normalize(query)
    m = normalize(slug_last_part(model_id))
    return SequenceMatcher(None, q, m).ratio()


def find_best_slug(name, top_k=5):
    try:
        results = list(api.list_models(search=name, limit=top_k, sort="downloads"))
    except Exception:
        return "", 0.0, []

    if not results:
        return "", 0.0, []

    scored = [(score_match(name, r.id), r.id) for r in results]
    scored.sort(reverse=True)
    best_score, best_id = scored[0]
    return best_id, round(best_score, 2), [s[1] for s in scored]


CONFIDENCE_THRESHOLD = 0.6  # below this, flag for manual review

with open("input.csv") as f_in, open("output.csv", "w", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames + [
        "slug",
        "confidence",
        "needs_review",
        "alt_candidates",
    ]
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        slug, conf, candidates = find_best_slug(row["name"])
        row["slug"] = slug
        row["confidence"] = conf
        row["needs_review"] = "YES" if conf < CONFIDENCE_THRESHOLD else ""
        row["alt_candidates"] = "; ".join(candidates[1:4])  # next best options
        writer.writerow(row)
        print(
            f"{row['name']:35s} -> {slug:45s} (conf={conf}){'  <-- REVIEW' if conf < CONFIDENCE_THRESHOLD else ''}"
        )
