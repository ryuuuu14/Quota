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

## Seed Status (run `python src/seed_teachers.py`)
- 113 activity types: 13 Giảng dạy, 52 Hoạt động chuyên môn, 4 Bồi dưỡng, 33 NCKH, 10 NCKH-Hướng dẫn thi đấu, 1 CHNVK
- 51 reduction rules (NCKH values verified via 5-agent swarm consensus)
- 4 titles (GS/PGS, GVC, GV, TG) × 3 fields (TN, XH, NCKH) = 12 base norms
- 4 departments, 1 timeframe (Aug 4 2025 – Jun 5 2026)
- 29 police ranks (Bảng 6+7 NĐ 204/2004/NĐ-CP)
- 8 teachers: 6 TEACHER + 1 GUEST + 1 STAFF, each with police rank + coefficient
- Uses UPSERT — existing rows get updated on re-seed

## Key Decisions
1. **DB_PATH**: Absolute from `__file__`, no silent fallback. Env var overrides.
2. **Auth redirect**: `st.switch_page()` replaces `st.warning()` + `st.page_link()` for unauthorized access. Page guard now does full redirect to login page. `st.stop()` prevents any content from rendering after redirect.
3. **Auth gate pattern**: `app.py` (Trang chủ) has a root auth gate, but every protected page also has its own `require_role()` because Streamlit pages load independently (bypassing `app.py`). Dashboard, Teacher, and Activity pages require `["admin", "head_dept"]`; Settings, Payroll, Approval require specific roles.
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

### Dev Pipeline (`src/dev_pipeline/`) — NEW
LangGraph build → test → validate loop with 3 human-in-loop checkpoints.
Used for automating dev tasks: generates plan, writes code, runs tests, reviews quality.

**Usage:**
```
python -m src.dev_pipeline "Add Excel bulk upload with 3 columns"
python -m src.dev_pipeline --iterations 5 "Fix calculations.py regression"
python -m src.dev_pipeline --interactive
```

**Graph flow:**
[Plan] → interrupt (human approves/rejects plan)
  → [Build] → implements code
  → [Test] → runs test_compliance.py + test_teacher_integration.py → interrupt
  → [Validate] → code quality review → interrupt (human approves/rejects)
  → END

**Checkpoints:** Plan, Test results, Validation — each pauses for human input.
- 'approve' → continue
- 'abort' → cancel
- <any text> → retry with feedback

**Agent:**
- Uses Gemini (genai.Client) if available; mock fallback for offline dev.
- Each agent has app-specific context (DB schema, code conventions, test patterns).
- Build agent has file read/write/edit tools.
- Test agent runs both test suites, parses pass/fail counts.
- Validate agent reviews code quality against project conventions.

## Salary Reform (Police Rank-Based)
- `total_12m_salary` replaced by coefficient × base_salary × 12 computation
- **`police_ranks` table**: 29 ranks from NĐ 204/2004/NĐ-CP Bảng 6+7
- **`salary_coefficient`** column on teachers (source of truth for pay)
- **`police_rank_id`** FK to police_ranks (auto-fills coefficient on selection)
- **`base_salary`** setting in DB: 2,340,000 VND (NĐ 73/2024/NĐ-CP), updatable
- Fallback: if `salary_coefficient` is NULL, uses stored `total_12m_salary`
- GUEST pay unchanged (still TT11 per-session rates)
- Teacher create/edit forms: police_rank selectbox → auto-compute preview
- Seed teachers: each has realistic police rank (Thiếu úy→Đại tá, Đại úy→Đại tướng)

## Bù Định Mức (Dashboard)
- Radio selector: "Cá nhân (GC ↔ NCKH)" / "Tập thể (theo Đơn vị)" / "Không bù"
- Individual: auto-compensation between GC and NCKH per teacher (Điều 12)
- Department: sharing surplus hours within same unit (Điều 12.3)
- No compensation: raw metrics display

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
- Salary: `total_12m = salary_coefficient × base_salary × 12` (NĐ 204/2004/NĐ-CP)
- Hourly rate: `(total_12m / standard_hours) × (44/52)` per TT21/2025
- Base pay: `hourly_rate × min(actual_hours, standard_hours)`
- Overtime: `hourly_rate × capped_overtime` (max 100h or 100% standard)

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

---
## Multi-Agent Architect — Review Loop

### Architecture
`task` tool-based subagent delegation with 4 roles:

| Role | Implementation | Responsibility |
|------|---------------|----------------|
| **Orchestrator** | Main agent (me) | Decompose, delegate, route feedback, update memory |
| **Implementer** | `task` subagent (general) | Write code for one task. Self-review before report. |
| **Reviewer** | `task` subagent (general) | Two-stage: spec compliance → code quality |
| **Tester** | `task` subagent (explore/general) | Run test commands, parse results |

### The Loop
```
Orchestrator → Plan → [FOR each task: Implement → Spec Review → Code Review → Fix → Test] → Merge → Update AGENTS.md
```

### Quality Gates
1. Spec review must pass (no missing/extra features)
2. Code quality review: no Critical issues
3. All tests pass
4. Orchestrator reviews final diff for consistency

### Skills
- **`.opencode/skills/review-loop/SKILL.md`** — Full workflow definition with prompt templates
- **`.opencode/agents/orchestrator.md`** — Orchestrator agent definition
- **`docs/plans/<feature>-plan.md`** — Feature plans with decomposed tasks
- **`docs/plans/task.md`** — Live task tracker

### Current Feature: Auth Portal — COMPLETED ✅
Full-screen login portal with st.switch_page() redirect.
- Plan: `docs/plans/auth-portal-plan.md`
- Status: 6/6 tasks done
- Files changed:
  - `requirements.txt`: `streamlit>=1.36.0` (upgraded from 1.32.2)
  - `src/pages/8_DangNhap.py`: Full-screen portal, hides sidebar via CSS, `st.switch_page("app.py")` on login, `st.switch_page("pages/8_DangNhap.py")` on logout
  - `src/auth.py`: `require_role()` redirects via `st.switch_page()` + `st.stop()`
  - `src/app.py`: Root auth gate before `render_sidebar()`
  - `src/components.py`: Logout button in sidebar
  - `src/pages/1_Dashboard.py`: Added `require_role(["admin", "head_dept"])`
  - `src/pages/2_QuanLyCanBo.py`: Added `require_role(["admin", "head_dept"])`
  - `src/pages/3_NhatKyHoatDong.py`: Added `require_role(["admin", "head_dept"])`
- Tests: 85/85 pass across 6 test suites

---
## Understand Anything — Knowledge Graph Tool
- Installed: `Lum1104/Understand-Anything` (MIT, ~21k+ stars)
- Location: `~\.understand-anything\repo\`
- Skills (auto-discovered from `~\.agents\skills\`):
  `/understand`, `/understand-dashboard`, `/understand-chat`
  `/understand-diff`, `/understand-explain`, `/understand-onboard`
  `/understand-domain`, `/understand-knowledge`
- Plugin root: `~\.understand-anything-plugin` (junction → repo plugin dir)
- Must restart opencode after install for skills to load
- Only works on repos with a `.git` directory
- After `/understand`, graph saved to `.understand-anything/knowledge-graph.json`
- To update: re-run install steps or `git pull`

---
## Pending: Template Restructure — Bulk Import  → 17-column format
**Context:** The bulk import template is being restructured from 11 columns to 17 columns to match the actual teaching schedule format used by the university.

### New Template Columns (B→R, A blank)

| Col | Header | Source | Editable |
|-----|--------|--------|----------|
| B | STT | auto 1,2,3… | Locked |
| C | Mã GV | DB (`teachers.id`) | Locked |
| D | Họ lót | DB (`teachers.name` split: last space = Tên) | Locked |
| E | Tên | DB | Locked |
| F | Chức danh | DB (teacher_role_history TITLE) | Locked |
| G | Đơn vị | DB (teacher_role_history DEPARTMENT) | Locked |
| H | Mã môn | User input | Editable |
| I | Tên môn | User input | Editable |
| J | Loại | Dropdown (ALLOWED_LOAI) | Editable |
| K | Nhóm | User input | Editable |
| L | Mã lớp | User input | Editable |
| M | Sỉ số | User input (numeric) | Editable |
| N | TKB | User input (text) | Editable |
| O | Tiết quy đổi | User input (numeric) | Editable |
| P | Hệ số tín chỉ | User input (numeric) | Editable |
| Q | Hệ số lớp đông | Calculated (trống, khóa) | Locked |
| R | Tiết thực dạy | Calculated (trống, khóa) | Locked |

### Files to change
| File | Changes |
|------|---------|
| `src/database.py` | ALTER TABLE `bulk_teaching_assignments` ADD `ma_mon`, `ma_lop`, `tkb`; DROP `ghi_chu` (or keep for compat) |
| `src/bulk_import/templates.py` | Rewrite headers (B→R, A blank), split `name`→họ lót/tên, STT auto-gen, merge A1:R1, A2:R2 |
| `src/bulk_import/validator.py` | 17 expected headers, map columns accordingly, validate optional fields |
| `src/bulk_import/calculator.py` | No change needed (uses loai, si_so, tiet_quy_doi, he_so_tin_chi) |
| `src/bulk_import/importer.py` | INSERT add `ma_mon`, `ma_lop`, `tkb`; remove `ghi_chu` |
| `src/pages/5_NhapDuLieu.py` | Raw preview + calculated table columns match new layout |
| `test_bulk_import.py` | Update template + full flow tests |

### User decisions
- **Mã môn**: Subject code from import file, store in DB for reference
- **TKB**: Stored but not used in calculation
- **Hệ số lớp đông / Tiết thực dạy**: Show as locked empty columns in template AND in calculated results
- **Họ lót / Tên**: Split `teachers.name` at last space
- **Ghi chú**: User said to remove it (not in their column list; confirmed via question)
