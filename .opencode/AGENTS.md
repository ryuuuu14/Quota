# AGENTS.md — Project Memory Log

## Project
Vietnamese university teacher workload management system (Streamlit + LangGraph + SQLite).
Tracks Giảng dạy, Hoạt động chuyên môn, Bồi dưỡng, NCKH, and Chấp hành Nhiệm vụ khác.

## Tech Stack
- **UI**: Streamlit (multi-page: Dashboard, Teacher, Activity, Settings)
- **State engine**: LangGraph (design pipeline, debug pipeline)
- **DB**: SQLite (`data/database.sqlite`, absolute path from project root)
- **Tests**: Python unittest-style, direct `python src/test_*.py` (pytest broken — trio env issue)
- **Chrome**: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- **Design**: Stitch MCP with local mock fallback; Gemini Vision tier skipped (no `GOOGLE_API_KEY`)

## Key Config
- `DB_PATH`: resolved absolute from `database.py`'s `__file__` → `{PROJECT_ROOT}/data/database.sqlite`
- Override: `os.environ['DB_PATH']` for testing (temp DB)
- `GC_CATEGORIES = {'Giảng dạy', 'Hoạt động chuyên môn', 'Bồi dưỡng'}`
- `nvk_dict = {'Hoạt động chuyên môn', 'Bồi dưỡng'}` (for "Kế hoạch khác" column)
- "Chấp hành Nhiệm vụ khác" is NOT in GC — free-form, no conversion rate

## Seed Status (run `python src/seed_full.py`)
- 113 activity types: 13 Giảng dạy, 52 Hoạt động chuyên môn, 4 Bồi dưỡng, 33 NCKH, 10 NCKH-Hướng dẫn thi đấu, 1 CHNVK
- 51 reduction rules (NCKH values verified via 5-agent swarm consensus)
- 4 titles (GS/PGS, GVC, GV, TG) × 3 fields (TN, XH, NCKH) = 12 base norms
- 4 departments, 1 timeframe (Aug 4 2025 – Jun 5 2026)
- Uses UPSERT — existing rows get updated on re-seed

## Key Decisions
1. **DB_PATH**: Absolute from `__file__`, no silent fallback. Env var overrides.
2. **Pipeline files**: `pipeline.py` (design/Stitch) vs `debug_pipeline.py` (test/Playwright). Separate lifecycle stages.
3. **Debug pipeline fix**: `wait_until="load"` not `"networkidle"` (Streamlit WebSockets prevent idle).
4. **NVK rename**: "Nhiệm vụ khác"→"Hoạt động chuyên môn". True catch-all = "Chấp hành Nhiệm vụ khác".
5. **Week calculation**: System counts actual working days, not idealized 44 weeks. Current TF = 43.80 working weeks.
6. **Test tolerances**: Base metrics ±3% working-day tolerance; reduction ratios ±0.02; direct reductions ±0.15.

## Pipeline
### Design Pipeline (`src/pipeline.py`)
Editor → Validator (hybrid: string + regex + BS4) → Critic (hybrid: local + Gemini Vision) → Router

### Debug Pipeline (`src/debug_pipeline.py`)
Sandbox Runner (Playwright) → Telemetry Critic (console + net + a11y) → Router. Runs in ~4.6s.

## Test Status
| Suite | Status | Run command |
|-------|--------|-------------|
| Compliance (Điều 6-12) | 70/70 ✅ | `python src/test_compliance.py` |
| QA integration | All ✅ | `python qa_tests.py` |
| Teacher integration | 8/8 ✅ | `python src/test_teacher_integration.py` |

## Important Calculations
- `calculate_t04_weeks(start, end)`: counts weekday (Mon-Fri) / 5 between two dates
- Norm reduction formula: `base_gc × role_pct × seg_weeks / 44.0`
- Event reduction: `segment_norm × event_weeks / seg_weeks × reduction_pct`
- Bu trừ: GC surplus → NCKH; NCKH surplus → GC (Điều 12)
- NCKH for GV nữ nuôi con 12-36 tháng: 0% reduction (Điều 11.4)

## Regulation Derived Values
- Lê Văn D: dinh_muc≈178.8, giam=47.1 (system: 178.05, 47.09)
- Bùi Thị X: dinh_muc≈269.8, giam≈119.1 (system: 267.23, 120.92)
- GV Bình Thường: base=250, actual=248.86 (43.80/44 weeks)

## Edge Cases
- Nuôi con reduction: only applicable during thai sản or within 12 months of childbirth
- Trưng tập ≥10 tháng: treated as role change (Điều 10.4)
- Day rounding: 5 days = 1 week, <5 days kept as fraction (Điều 10.1.b)
- Multiple reductions stack multiplicatively within a segment

## Agent Conventions
- Seed script = `python src/seed_full.py` (single entry point)
- All test files in `src/` or root, run standalone with `python -X utf8`
- No `pytest` — broken (trio env issue), use direct `python` invocation
- Activity log data: insert directly into SQLite (see `test_teacher_integration.py` for pattern)
- Teacher records: insert into `teachers` + `teacher_titles` + `teacher_reductions` tables

## URLs
- Source regulation: `Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md` (in project root)
