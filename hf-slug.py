#!/usr/bin/env python3
"""
Validate NIM model names against intelligence.csv using fuzzy matching.
Use when adding new models to find potential matches.

Usage:
  python hf-slug.py <nim_model_name>
  python hf-slug.py --validate  # validate all models in models.txt
"""
import csv
import re
import sys
from difflib import SequenceMatcher

INTELLIGENCE_PATH = "_data/intelligence.csv"
MODELS_PATH = "_data/models.txt"

ORG_ALIASES = {
    "stepfun-ai": "stepfun",
    "mistralai": "mistral",
    "minimaxai": "minimax",
    "moonshotai": "kimi",
    "bytedance": "bytedance_seed",
    "microsoft": "azure",
    "qwen": "alibaba",
    "z-ai": "zai",
    "sarvamai": "sarvam",
}

CONFIDENCE_THRESHOLD = 0.7


def normalize(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def map_org(nim_org):
    return ORG_ALIASES.get(nim_org, nim_org)


def score_match(query, model_id):
    q_org, q_model = query.split("/", 1) if "/" in query else ("", query)
    m_org, m_model = model_id.split("/", 1) if "/" in model_id else ("", model_id)

    q_org_mapped = map_org(q_org)
    org_bonus = 0.15 if q_org_mapped == m_org else 0.0

    q_norm = normalize(q_model)
    m_norm = normalize(m_model)
    model_score = SequenceMatcher(None, q_norm, m_norm).ratio()

    return min(model_score + org_bonus, 1.0)


def load_intelligence():
    names = []
    with open(INTELLIGENCE_PATH) as f:
        for row in csv.DictReader(f):
            names.append(row["name"])
    return names


def find_candidates(nim_name, intelligence_names, top_k=5):
    scored = [(score_match(nim_name, name), name) for name in intelligence_names]
    scored.sort(reverse=True)
    return scored[:top_k]


def validate_single(nim_name):
    intelligence_names = load_intelligence()
    candidates = find_candidates(nim_name, intelligence_names)

    print(f"\nTop candidates for: {nim_name}")
    print("-" * 70)
    for score, name in candidates:
        flag = " <-- HIGH" if score >= CONFIDENCE_THRESHOLD else ""
        print(f"  {score:.2f}  {name}{flag}")
    print()


def validate_all():
    intelligence_names = load_intelligence()

    with open(MODELS_PATH) as f:
        models = [line.strip() for line in f if line.strip()]

    print(f"{'NIM Model':<50} {'Best Match':<50} {'Score':>6}")
    print("-" * 108)

    for model in models:
        candidates = find_candidates(model, intelligence_names, top_k=1)
        best_score, best_id = candidates[0]
        flag = "" if best_score >= CONFIDENCE_THRESHOLD else " <-- REVIEW"
        print(f"{model:<50} {best_id:<50} {best_score:>6.2f}{flag}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        print(__doc__)
        sys.exit(0)
    elif sys.argv[1] == "--validate":
        validate_all()
    else:
        validate_single(sys.argv[1])
