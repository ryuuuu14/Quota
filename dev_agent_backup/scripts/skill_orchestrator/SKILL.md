---
name: skill-auto-orchestrator
description: "Meta-skill. Auto-selects best local skill + switches model tier based on task complexity. Runs skill_selector.py, interprets output, invokes chosen skill. No human interview needed."
risk: safe
source: local
tags: "orchestration, meta-skill, auto-select, model-switching"
---

# skill-auto-orchestrator

## Overview

Auto-selects appropriate local skill + optimal model tier for any task.
Uses TF-IDF scoring over indexed local skills (~1450 skills).
No interview. No human input needed. Fully programmatic.

## When to Use

- Any task where you need to pick the right skill automatically
- Multi-agent pipelines where each agent needs correct skill + model
- When user says "use best skill for this" or "auto-select"
- When building agent orchestrators that need self-directed skill selection

## Model Tiers

| Tier | Model | Use When |
|------|-------|----------|
| 1 | Gemini 3.5 Flash | Simple: single-file edit, CSS tweak, rename, format, comment |
| 2 | Claude Sonnet 4.6 | Medium: feature dev, multi-file, debug, API integration |
| 3 | Claude Opus 4.6 (Thinking) | Complex: architecture, multi-agent, research, full-system design |

### Tier Signals

**Tier 3 (complex):** architect, orchestrat, multi-agent, distributed, security audit,
penetration, from scratch, full refactor, research, strategy, optimize performance,
concurrent, langgraph, crewai, autonomous agent, rag pipeline, migrate entire,
schema design, compliance, scalab, system design, full stack

**Tier 1 (simple):** fix typo, rename variable, add comment, format, css color,
change label, minor, tweak, adjust, small fix, single file, one line, typo, lint

**Default:** Tier 2 (no strong signals either way)

## Instructions

### Step 1 — Run the selector

```powershell
python f:\annd\Quota\scripts\skill_orchestrator\skill_selector.py "TASK_DESCRIPTION"
```

Or with rebuild (after new skills installed):
```powershell
python f:\annd\Quota\scripts\skill_orchestrator\skill_selector.py "TASK" --rebuild
```

Or request top 5:
```powershell
python f:\annd\Quota\scripts\skill_orchestrator\skill_selector.py "TASK" --top 5
```

### Step 2 — Interpret output

Output JSON structure:
```json
{
  "task": "...",
  "complexity_tier": 2,
  "complexity_reason": "...",
  "recommended_model": {
    "tier": 2,
    "name": "Claude Sonnet 4.5",
    "setting": "Claude Sonnet 4.6",
    "desc": "..."
  },
  "recommended_skills": [
    {
      "name": "skill-name",
      "dir": "skill-dir-name",
      "description": "...",
      "score": 0.842,
      "invoke": "@[/skill-dir-name]"
    }
  ],
  "usage": {
    "primary": "@[/primary-skill]",
    "secondary": ["@[/secondary-skill]"]
  }
}
```

### Step 3 — Switch model (if needed)

Tell user: "Switching to [recommended_model.name] for this task (Tier [tier])."
If in Antigravity UI: user changes Model Selection setting to `recommended_model.setting`.

### Step 4 — Read and apply selected skill

```
Read SKILL.md at:
  C:\Users\ADMIN\.gemini\antigravity\skills\[dir]\SKILL.md
```

Then follow that skill's instructions for the task.

### Step 5 — Chain secondary skills if needed

If primary skill handles only part of task, apply secondary skills in sequence.
Always re-assess complexity before each sub-task.

## Complexity Assessment (Manual Fallback)

If selector script unavailable, assess manually:

1. Count Tier 3 signals in task → ≥1 = Tier 3
2. Count Tier 1 signals + task word count < 15 → = Tier 1
3. Else → Tier 2

## Re-indexing

Run when new skills installed:
```powershell
python f:\annd\Quota\scripts\skill_orchestrator\build_skill_index.py
```

Index location: `f:\annd\Quota\scripts\skill_orchestrator\skill_index.json`

## Files

| File | Purpose |
|------|---------|
| `build_skill_index.py` | Scans all SKILL.md, writes JSON index |
| `skill_selector.py` | TF-IDF ranker + complexity assessor |
| `skill_index.json` | Cached index (auto-built on first run) |

## Limitations

- Skill selection is keyword/TF-IDF based — not semantic LLM reasoning
- Model switching is heuristic, not guaranteed optimal
- Index must be rebuilt after new skill installs (`--rebuild`)
- Cannot write SKILL.md to C: if disk full — keep this file on F: and symlink or copy when space available
