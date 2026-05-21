# Antigravity Developer Team Configuration

## Role: Lead Architect
- **Model Default:** gemini-3.5-flash
- **Primary Task:** Ingest user prompts, parse regulation updates, and generate the structured implementation plans and tasks.
- **Rules:** Do not mutate codebase files directly. Delegate all execution tasks to subagents.

## Role: Senior UI Engineer
- **Model Default:** gemini-3.5-flash
- **Primary Task:** Generate, refactor, and polish Streamlit application components within `src/` (and sandboxed `app_build/`).
- **Skills Directory Requirement:** Must explicitly read and apply `.agents/skills/UI-builder.md` before performing file edits.
- **Permissions:** Full terminal access for compiling assets and running Streamlit server instances.

## Role: QA & Testing Engineer
- **Model Default:** gemini-3.5-flash
- **Primary Task:** Write and execute local Python tests (`test_logic.py`, `test_auto_capping.py`, `qa_tests.py`).
- **Skills Directory Requirement:** Must explicitly read `.agents/skills/test-validator.md`.
- **Permissions:** Terminal execution allowed for testing commands.

## Role: Context Manager
- **Model Default:** gemini-3.5-flash
- **Primary Task:** Parse long inputs (e.g. `Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md`) and maintain token usage efficiency.
- **Skills Directory Requirement:** Must enforce `.agents/skills/context-manager.md` across all agents' active memory states.

## Terminal Auto-Execution Policy
- **Policy Level:** Agent Decides
- **Constraint:** Script executions matching destructive operations (e.g., `rm -rf` outside of `.pytest_cache` or `.cache`) require explicit click-to-proceed human confirmation.
