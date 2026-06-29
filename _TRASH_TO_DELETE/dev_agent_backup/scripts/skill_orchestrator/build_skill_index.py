#!/usr/bin/env python3
"""
build_skill_index.py — Scan all local Antigravity skills and build a JSON index.

Usage:
    python f:/annd/Quota/scripts/skill_orchestrator/build_skill_index.py

Output: f:/annd/Quota/scripts/skill_orchestrator/skill_index.json
"""

import json
import re
import sys
from pathlib import Path

SKILLS_DIR = Path(r"C:\Users\ADMIN\.gemini\antigravity\skills")
INDEX_FILE = Path(r"f:\annd\Quota\scripts\skill_orchestrator\skill_index.json")


def extract_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter between --- delimiters."""
    meta = {}
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        return meta
    for line in fm_match.group(1).splitlines():
        kv = line.split(":", 1)
        if len(kv) == 2:
            key = kv[0].strip()
            val = kv[1].strip().strip('"').strip("'")
            meta[key] = val
    return meta


def extract_when_to_use(text: str) -> str:
    """Extract 'When to Use' / Overview section."""
    patterns = [
        r"#+\s*When to Use\s*\n(.*?)(?=\n#+|\Z)",
        r"#+\s*Use When\s*\n(.*?)(?=\n#+|\Z)",
        r"#+\s*Overview\s*\n(.*?)(?=\n#+|\Z)",
        r"#+\s*Goal\s*\n(.*?)(?=\n#+|\Z)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            content = m.group(1).strip()
            content = re.sub(r"[#*`>\-]", " ", content)
            content = re.sub(r"\s+", " ", content)
            return content[:400]
    # Fallback: body after frontmatter
    body = re.sub(r"^---.*?---\s*\n", "", text, flags=re.DOTALL)
    body = re.sub(r"[#*`>\-]", " ", body)
    body = re.sub(r"\s+", " ", body)
    return body[:300]


def extract_tags(meta: dict, text: str) -> list:
    raw = meta.get("tags", meta.get("category", ""))
    tags = re.findall(r'[\w\-]+', raw)

    tech_keywords = [
        "python", "javascript", "typescript", "react", "nextjs", "node",
        "css", "html", "sql", "postgres", "sqlite", "docker", "aws", "azure",
        "gcp", "security", "auth", "api", "ui", "ux", "testing", "devops",
        "llm", "ai", "agent", "streamlit", "fastapi", "django", "flask",
        "rust", "go", "java", "dotnet", "swift", "kotlin", "flutter",
        "git", "github", "ci", "cd", "terraform", "kubernetes", "redis",
        "graphql", "rest", "websocket", "oauth", "jwt", "email", "seo",
        "analytics", "marketing", "billing", "stripe", "supabase", "firebase",
        "langchain", "langgraph", "crewai", "rag", "embedding", "vector",
        "debug", "refactor", "migrate", "deploy", "monitor", "log", "trace",
        "orchestrat", "pipeline", "workflow", "skill", "planning",
        "architecture", "design", "component", "layout", "animation",
    ]
    lower_text = text.lower()
    for kw in tech_keywords:
        if kw in lower_text and kw not in tags:
            tags.append(kw)

    return list(set(tags))[:20]


def classify_complexity(text: str) -> str:
    """Returns: low | medium | high"""
    high_signals = [
        "architect", "orchestrat", "multi-agent", "distributed", "pipeline",
        "security audit", "penetration", "refactor entire", "full system",
        "research", "strategy", "from scratch", "optimize performance",
        "migrate", "schema design", "concurrent", "langgraph", "crewai",
        "multi-step", "autonomous", "complex",
    ]
    low_signals = [
        "simple", "quick fix", "rename", "comment", "format", "style",
        "color", "label", "text", "import", "lint", "typo", "minor",
        "small", "adjust", "tweak", "single file",
    ]
    lower = text.lower()
    high_count = sum(1 for s in high_signals if s in lower)
    low_count = sum(1 for s in low_signals if s in lower)

    if high_count >= 2:
        return "high"
    elif low_count >= 2:
        return "low"
    return "medium"


def build_index():
    if not SKILLS_DIR.exists():
        print(f"ERROR: Skills dir not found: {SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)

    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    total = len(skill_dirs)
    print(f"Scanning {total} skill directories...", flush=True)

    skills = []
    skipped = 0

    for i, skill_dir in enumerate(sorted(skill_dirs)):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            skipped += 1
            continue

        try:
            text = skill_md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            skipped += 1
            continue

        meta = extract_frontmatter(text)
        name = meta.get("name", skill_dir.name)
        description = meta.get("description", "")
        when_to_use = extract_when_to_use(text)
        tags = extract_tags(meta, text)
        complexity = classify_complexity(text)
        risk = meta.get("risk", "safe")

        corpus = f"{name} {description} {when_to_use} {' '.join(tags)}".lower()

        skills.append({
            "name": name,
            "dir": skill_dir.name,
            "description": description,
            "when_to_use": when_to_use[:200],
            "tags": tags,
            "complexity": complexity,
            "risk": risk,
            "corpus": corpus,
        })

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{total} scanned...", flush=True)

    index = {
        "version": 1,
        "total_skills": len(skills),
        "skills": skills,
    }

    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone. Indexed {len(skills)} skills ({skipped} skipped — no SKILL.md).")
    print(f"Index: {INDEX_FILE}")
    return index


if __name__ == "__main__":
    build_index()
