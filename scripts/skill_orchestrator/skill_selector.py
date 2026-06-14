#!/usr/bin/env python3
"""
skill_selector.py — Given a task description, select the best skill + model.

Usage:
    python skill_selector.py "your task description here"
    python skill_selector.py "your task" --top 5
    python skill_selector.py --rebuild    # rebuild index first

Output (JSON):
    {
      "task": "...",
      "complexity_tier": 1|2|3,
      "recommended_model": {...},
      "recommended_skills": [...],
      "reasoning": "..."
    }
"""

import json
import math
import re
import sys
import subprocess
from pathlib import Path
from collections import Counter

INDEX_FILE = Path(r"f:\annd\Quota\scripts\skill_orchestrator\skill_index.json")
BUILD_SCRIPT = Path(r"f:\annd\Quota\scripts\skill_orchestrator\build_skill_index.py")

# ── Model tiers ──────────────────────────────────────────────────────────────
MODELS = {
    1: {
        "tier": 1,
        "name": "Gemini 3.5 Flash",
        "setting": "Gemini 3.5 Flash (Medium)",
        "desc": "Fast & cheap. Simple edits, CSS tweaks, single-file fixes, formatting.",
        "token_budget": "low",
    },
    2: {
        "tier": 2,
        "name": "Claude Sonnet 4.5",
        "setting": "Claude Sonnet 4.6",
        "desc": "Balanced. Feature dev, multi-file refactor, debugging, API integration.",
        "token_budget": "medium",
    },
    3: {
        "tier": 3,
        "name": "Claude Opus 4.5 (Thinking)",
        "setting": "Claude Opus 4.6 (Thinking)",
        "desc": "Max power + reasoning. Architecture, research, complex multi-agent systems.",
        "token_budget": "high",
    },
}

# ── Complexity signal words ───────────────────────────────────────────────────
TIER3_SIGNALS = [
    "architect", "design system", "orchestrat", "multi-agent", "distributed",
    "security audit", "penetration test", "from scratch", "full refactor",
    "research", "strategy", "optimize performance", "concurrent", "langgraph",
    "crewai", "autonomous agent", "rag pipeline", "migrate entire", "schema",
    "compliance", "production", "scalab", "review entire", "system design",
    "authentication system", "billing", "full stack", "all pages",
]

TIER1_SIGNALS = [
    "fix typo", "rename variable", "add comment", "format", "css color",
    "change label", "update text", "add import", "remove line", "indent",
    "simple", "quick", "minor", "tweak", "adjust color", "small fix",
    "change button", "update string", "fix spacing", "single file",
    "one line", "typo", "lint", "whitespace",
]


def assess_complexity(task: str) -> tuple[int, str]:
    """Return (tier 1|2|3, reasoning_snippet)."""
    lower = task.lower()

    t3_hits = [s for s in TIER3_SIGNALS if s in lower]
    t1_hits = [s for s in TIER1_SIGNALS if s in lower]
    word_count = len(task.split())

    # Long task descriptions usually = complex
    if word_count > 60 or len(t3_hits) >= 2:
        return 3, f"High complexity signals: {t3_hits[:3] or ['long description']}"
    if len(t3_hits) == 1:
        return 3, f"Complex signal found: {t3_hits}"
    if len(t1_hits) >= 2 and word_count < 20:
        return 1, f"Simple signals: {t1_hits[:3]}"
    if len(t1_hits) >= 1 and word_count < 15:
        return 1, f"Simple signal: {t1_hits}"
    return 2, "Medium complexity — no strong signals either way"


def tokenize(text: str) -> Counter:
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    # Remove common stop words
    stops = {
        "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
        "of", "and", "or", "but", "not", "this", "that", "with", "be",
        "use", "used", "when", "how", "what", "you", "your", "can", "will",
        "are", "have", "has", "do", "does", "from", "as", "by", "if",
        "should", "would", "could", "may", "more", "any", "all", "some",
    }
    return Counter(w for w in words if w not in stops)


def tf_idf_score(task_tokens: Counter, skill_corpus: str, idf: dict) -> float:
    """Compute TF-IDF cosine-ish similarity between task and skill corpus."""
    corpus_tokens = tokenize(skill_corpus)
    if not corpus_tokens:
        return 0.0

    score = 0.0
    corpus_total = sum(corpus_tokens.values())

    for word, task_count in task_tokens.items():
        if word in corpus_tokens:
            # TF in corpus
            tf = corpus_tokens[word] / corpus_total
            # IDF boost for rare terms
            idf_val = idf.get(word, 1.0)
            score += task_count * tf * idf_val

    return score


def build_idf(skills: list) -> dict:
    """Build IDF table from all skill corpora."""
    doc_count = len(skills)
    df = Counter()
    for skill in skills:
        words = set(tokenize(skill["corpus"]).keys())
        for w in words:
            df[w] += 1
    idf = {}
    for word, count in df.items():
        idf[word] = math.log((doc_count + 1) / (count + 1)) + 1
    return idf


def load_index() -> dict:
    if not INDEX_FILE.exists():
        print("Index not found. Building now...", flush=True)
        subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=True)
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def select_skills(task: str, top_k: int = 3, rebuild: bool = False) -> dict:
    if rebuild:
        subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=True)

    index = load_index()
    skills = index["skills"]

    task_tokens = tokenize(task)
    idf = build_idf(skills)

    # Score all skills
    scored = []
    for skill in skills:
        score = tf_idf_score(task_tokens, skill["corpus"], idf)
        # Bonus for tag overlap
        task_words = set(task_tokens.keys())
        tag_overlap = len(task_words & set(skill["tags"]))
        score += tag_overlap * 0.5
        scored.append((score, skill))

    scored.sort(key=lambda x: -x[0])
    top_skills = scored[:top_k]

    tier, complexity_reason = assess_complexity(task)
    model = MODELS[tier]

    recommendations = []
    for score, skill in top_skills:
        recommendations.append({
            "name": skill["name"],
            "dir": skill["dir"],
            "description": skill["description"],
            "when_to_use": skill["when_to_use"],
            "tags": skill["tags"][:8],
            "complexity": skill["complexity"],
            "score": round(score, 4),
            "invoke": f"@[/{skill['dir']}]",
        })

    return {
        "task": task,
        "complexity_tier": tier,
        "complexity_reason": complexity_reason,
        "recommended_model": model,
        "recommended_skills": recommendations,
        "usage": {
            "primary": recommendations[0]["invoke"] if recommendations else "",
            "secondary": [r["invoke"] for r in recommendations[1:]],
        },
        "reasoning": (
            f"Task complexity: Tier {tier} ({model['name']}). "
            f"{complexity_reason}. "
            f"Top skill: '{recommendations[0]['name']}' "
            f"(score {recommendations[0]['score']})."
            if recommendations else "No skills matched."
        ),
    }


def main():
    args = sys.argv[1:]

    if not args or "--help" in args:
        print(__doc__)
        sys.exit(0)

    rebuild = "--rebuild" in args
    args = [a for a in args if not a.startswith("--rebuild")]

    top_k = 3
    if "--top" in args:
        idx = args.index("--top")
        top_k = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    if not args:
        print("ERROR: Provide a task description.", file=sys.stderr)
        sys.exit(1)

    task = " ".join(args)
    result = select_skills(task, top_k=top_k, rebuild=rebuild)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
