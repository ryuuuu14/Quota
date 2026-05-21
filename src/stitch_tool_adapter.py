"""Adapter for bridging Stitch MCP tool output to the pipeline."""
import json
import os

_RESULTS_FILE = os.path.join(os.path.dirname(__file__), ".stitch_results.json")


def edit_screens_blocking(
    project_id: str, screen_ids: list, prompt: str
) -> str:
    """Reads pre-computed Stitch results cached by the agent."""
    if not os.path.exists(_RESULTS_FILE):
        return f"# ADAPTER_NO_RESULTS: run Stitch tools first to populate cache"

    with open(_RESULTS_FILE, encoding="utf-8") as f:
        results = json.load(f)

    key = f"{project_id}:{','.join(sorted(screen_ids))}:{prompt}"
    if key in results:
        return results[key]

    # fallback: match on project+screen ignoring prompt
    prefix = f"{project_id}:{','.join(sorted(screen_ids))}:"
    for k, v in results.items():
        if k.startswith(prefix):
            return v

    return f"# ADAPTER_NO_MATCH: no cached result for {key}"


def cache_stitch_result(
    project_id: str, screen_ids: list, prompt: str, html: str
):
    """Saves a Stitch result for the pipeline to consume."""
    results = {}
    if os.path.exists(_RESULTS_FILE):
        with open(_RESULTS_FILE, encoding="utf-8") as f:
            results = json.load(f)

    key = f"{project_id}:{','.join(sorted(screen_ids))}:{prompt}"
    results[key] = html
    with open(_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
