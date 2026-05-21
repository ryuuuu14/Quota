# Bộ nhớ dùng chung (Swarm Shared Memory Log)

File này đóng vai trò là não bộ lưu trữ ngữ cảnh (context) cho các agent.

---

## Debug Session 2026-05-20 (16:39 ICT) — Critical Root Cause Found

### BUG 1 — DB_PATH Mismatch (ROOT CAUSE) — FIXED

**Symptom:** Dashboard showed empty state despite data existing.

**Root Cause:** `app.py` defaulted to `src/database.sqlite` while seeded data lived in `data/database.sqlite`.

**Fix applied (2026-05-20):**
- Changed `app.py` default to `data/database.sqlite` via `os.environ.setdefault('DB_PATH', ...)`
- Removed orphaned `database.sqlite` (root, 0 bytes) and `src/database.sqlite` (empty schema, 86KB)
- Re-verified: `data/database.sqlite` (114KB) has all seeds (112 activity_types, 48 reduction_rules, etc.)
- `src/database.py` fallback respects env var; directory check passes for `data/`

**Status:** FIXED.

---

### BUG 2 — "Kế hoạch khác" / "Nhiệm vụ khác" NOT included in dashboard calculations

**Finding:** The regulation (TT108) has a third quota type: **Kế hoạch khác** (other planned tasks). In the seed data these are labelled category `Nhiệm vụ khác` (NVK prefix). They count toward GC quota under Điều 9.

**Fix verified (2026-05-20):** Already present in current code — `calculations.py` lines 520-536:
```python
GC_CATEGORIES = {'Giảng dạy', 'Nhiệm vụ khác', 'Bồi dưỡng'}
NCKH_CATEGORIES = {'NCKH', 'NCKH - Hướng dẫn thi đấu'}
nvk_dict[tid] = group[group['category'].isin({'Nhiệm vụ khác', 'Bồi dưỡng'})]['calculated_hours'].sum()
```

**Status:** ALREADY FIXED in previous session.

---

### BUG 3 — `converted_hours` always saved as 0.0

**Location:** `src/pages/3_NhatKyHoatDong.py` line 119
```python
0.0, note, tf_options[tf_sel]   # converted_hours hardcoded 0.0
```
The actual calculation is done lazily in `calculations.py` via `calculate_activity_hours()` at query time, so the `converted_hours` column in `activity_logs` is always 0. This is by design (not a bug) but means any query that reads `converted_hours` directly (e.g. reports) will show 0. Calculations recalculate on the fly which is correct.

**Status:** By design — no fix needed unless a raw `converted_hours` report is added.

---

### DB_PATH Design (final, won't regress)

```
database.py DB_PATH = os.environ.get('DB_PATH', os.path.join(PROJECT_ROOT, 'data', 'database.sqlite'))
                      ↑ env override                 ↑ always absolute, computed from __file__
```

- `PROJECT_ROOT` = `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` = `F:\annd\dhannd\annd`
- If `data/` dir doesn't exist → `os.makedirs()` creates it
- No fallback to `src/database.sqlite` anywhere in the project
- `seed_reductions.py` and `test_compliance.py` both import `get_connection()` / `DB_PATH` from `database`
- `app.py` calls `os.environ.setdefault('DB_PATH', ...)` before importing `database` (belt + suspenders)

## Architecture Reference (confirmed working as of this session)

| File | Role |
|------|------|
| `src/database.py` | Schema + `init_db()` + `seed_initial_data()`. Column is `base_conversion_rate` (not `conversion_rate`) |
| `src/calculations.py` | All quota math. `calculate_teacher_metrics()` is the main function. `calculate_activity_hours()` applies multipliers per Điều 8 |
| `src/seed_activities.py` | Seeds all activity types. Run once: `python src/seed_activities.py` |
| `src/seed_reductions.py` | Seeds reduction rules. Run once: `python src/seed_reductions.py` |
| `src/pages/1_Dashboard.py` | Reads from `calculate_teacher_metrics()`. Calls `get_conversion_limits()` for Điều 12 suggestions |
| `src/pages/3_NhatKyHoatDong.py` | Inserts into `activity_logs`. `converted_hours` stored as 0.0 (recalculated at read time) |
| `data/database.sqlite` | **Active DB path** — 114KB, fully seeded (112 act_types, 48 reductions) |
| ~~`src/database.sqlite`~~ | **REMOVED** — orphaned empty schema |

### Next Actions (in order)

1. ~~Fix DB_PATH~~ **DONE**
2. ~~Fix calculations.py~~ **DONE** (already fixed)
3. ~~Verify: debug_pipeline.py~~ **DONE** — passed in 4.5s, 0 console/net errors
4. Add NVK summary row to Dashboard KPI section (optional enhancement)

### Bug DB_PATH — FINAL FIX (2026-05-20)

**Root cause:** `database.py` silently fell back to `src/database.sqlite` when `data/` dir didn't exist or `DB_PATH` was a relative path resolved from wrong CWD.

**Fix applied:**
- `database.py`: removed dangerous fallback. Always resolves `data/database.sqlite` as absolute path from `__file__` (project root). Creates `data/` dir if missing.
- `test_compliance.py`: was hardcoded to `src/database.sqlite` → now imports `DB_PATH` from `database` module.
- `seed_reductions.py`: was using raw `sqlite3.connect(DB_PATH)` with ambiguous fallback → now uses `get_connection()` from `database`.
- Created `seed_full.py` (gộp `seed_activities` + `seed_reductions` + `seed_initial_data`).

**Will NOT happen again because:** No code in the project references `src/database.sqlite` anymore. All DB access goes through `database.get_connection()` which uses the absolute project-root path.

### Verification Results (2026-05-20) — FINAL

| Check | Result |
|-------|--------|
| DB_PATH points to `data/database.sqlite` | **OK** (172KB, absolute path) |
| reduction_rules seeded | **48 rows** |
| activity_types seeded | **112 rows** |
| Compliance tests | **70/70 PASSED** |
| All 4 pages load via Playwright | **OK** (no 404s) |
| Console errors | **0** (clean) |
| Network errors | **0** (clean) |
| Debug pipeline verdict | **PASSED** (1 iteration, 4.6s) |


---

## Pipeline Architecture

### 1. Design Pipeline (`src/pipeline.py`)
| Node | Function | Description |
|------|----------|-------------|
| Editor | `run_editor()` | Stitch screen generation (real MCP or mock fallback), cached via `stitch_tool_adapter.py` |
| Validator | `run_validator()` | 3-tier: string match → regex → BeautifulSoup DOM check |
| Critic | `run_critic()` | Console output + Gemini Vision (if `GOOGLE_API_KEY` set) → approve/retry/abort |
| Router | `router_condition()` | Decides: approve (pass) → **terminal**, retry (<3 iterations) → **Editor**, abort → **terminal** |

**Graph:** `Editor → Validator → Critic → Router` (conditional loop back to Editor)

**Entry:**
```python
from pipeline import run_pipeline
result = run_pipeline()
# → {"code": str, "summary": {"iterations": int, "status": str, "logs": list}}
```

### 2. Debug Pipeline (`src/debug_pipeline.py`)
| Node | Function | Description |
|------|----------|-------------|
| Sandbox Runner | `sandbox_runner()` | Playwright + local Chrome → goto Dashboard → click 3 sidebar pages → screenshots |
| Telemetry Critic | `telemetry_critic()` | Hybrid: console log errors → network errors → a11y tree (Streamlit: skip empty tree) |
| Router | `router_condition_debug()` | pass → **terminal**, fail+<3 retries → **Sandbox**, fail+≥3 → **terminal** |

**Graph:** `Sandbox Runner → Telemetry Critic → Router` (conditional loop back to Sandbox)

**Entry:**
```python
python src/run_debug.py
# → {"verdict": str, "test_run_count": int, "console_logs": list, "network_errors": list, "feedback": str}
```

### 3. Stitch Tool Adapter (`src/stitch_tool_adapter.py`)
Bridges Stitch MCP tool output into the pipeline. Caches results (read from file, fallback to mock).

## File Inventory

| File | Size | Role |
|------|------|------|
| `src/app.py` | 3,086 B | Streamlit entry point. Custom MD3 sidebar + welcome page. DB_PATH → `data/database.sqlite` |
| `src/database.py` | ~8 KB | Schema + `init_db()` + `seed_initial_data()`. **Always** resolves to absolute `data/database.sqlite` path. No silent fallback. |
| `src/calculations.py` | 31,518 B | All quota math. `calculate_teacher_metrics()`, `calculate_activity_hours()`, GC/NCKH grouping |
| `src/components.py` | 16,394 B | MD3-themed components: `render_card()`, `render_chip()`, `render_kpi_card()`, `render_status_bar()` |
| `src/pipeline.py` | 9,232 B | Design pipeline: LangGraph Editor → Validator → Critic → Router |
| `src/stitch_tool_adapter.py` | 1,407 B | Stitch MCP result cache bridge |
| `src/debug_pipeline.py` | 9,520 B | Debug pipeline: Playwright Sandbox → Hybrid Critic → Router |
| `src/run_debug.py` | 587 B | Entry point for debug pipeline |
| `src/seed_full.py` | ~600 B | **Single seed script** — combines `seed_initial_data()` + `seed_reductions.run()` + `seed_activities.run()` |
| `src/seed_activities.py` | 11,313 B | Seeds 112 activity types. Called by `seed_full.py` |
| `src/seed_reductions.py` | ~7 KB | Seeds 48 reduction rules. Called by `seed_full.py` |
| `src/test_calculations.py` | 3,637 B | Unit tests for `calculations.py` |
| `src/test_compliance.py` | ~34 KB | Compliance tests (TT108 regulation checks). Uses `DB_PATH` from `database` module. |
| `src/test_ui.py` | 1,831 B | UI smoke tests |

## Run Commands

```bash
# Terminal 1 — Streamlit app
streamlit run src/app.py

# Terminal 2 — Debug pipeline
python src/run_debug.py

# Terminal 3 — Design pipeline (Stitch)
python -c "from pipeline import run_pipeline; print(run_pipeline())"

# Seed database (idempotent) — single script
python src/seed_full.py    # → 48 reductions, 112 activity_types

# Compliance tests (70 tests, must be 0 failures)
python src/test_compliance.py
```

## Pipeline Test Results (2026-05-20)

| Pipeline | Iterations | Time | Verdict |
|----------|-----------|------|---------|
| Design (Stitch mock) | 2 | ~0.5s | approved |
| Design (Stitch adapter) | 1 | ~0.3s | approved |
| Debug (Playwright) | 1 | 4.5s | passed |

---

## Lịch sử Lỗi (Error Logs)
### 1. OCR (Research Agent)
- `tesseract_setup.exe /SILENT` thất bại (thiếu Tesseract trong PATH hoặc AppData).
- Dùng `PyMuPDF` (`extract_pdf.py`) xuất ra 0 ký tự vì PDF là dạng ảnh (scanned).
- Cài đặt `easyocr` qua pip trên Python 3.13 báo lỗi biên dịch Rust (`python-bidi`).
- **Hậu quả**: File `quy_dinh_ocr.md` lỗi và `quy_dinh.txt` trống không.

### 2. Browser QA (QA Agent)
- Chạy Streamlit trên `localhost:8501`.
- UI sập khi truy cập "Ghi nhận hoạt động" và "Cài đặt hệ thống".
- Lỗi: `pandas.errors.DatabaseError: Execution failed on sql 'SELECT id, name, category, unit, conversion_rate FROM activity_types': no such column: conversion_rate`
- **Nguyên nhân**: Cột `conversion_rate` đã được đổi tên thành `base_conversion_rate` trong `database.py` (Giai đoạn 2) nhưng UI chưa cập nhật.

=> Tất cả lỗi đã được push trực tiếp lên `implementation_plan.md` cho Planning Agent đánh giá.

### 3. Streamlit Page Reload & HTML Metric Cards (2026-05-21)
- **Symptom 1**: 404 console errors on `_stcore/host-config` and `_stcore/health` when reloading or accessing subpages directly (e.g. `/Dashboard`).
  - **Root Cause**: Known Streamlit 1.32.2 multipage router behavior. When browser loads a subpage path, the frontend requests config endpoints relatively (`/Dashboard/_stcore/host-config`), resulting in a 404.
  - **Resolution**: Harmless Streamlit behavior. The frontend automatically falls back to root paths (`/_stcore/...`), so no changes were needed for the 404 itself.
- **Symptom 2**: `onboarding.js:28 Uncaught (in promise) undefined` and metric cards rendering raw HTML on screen.
  - **Root Cause**: Indentation inside `components.py` `render_metric_card` f-string block triggered markdown code-block parsing when `{delta_html}` was empty. Raw HTML code (`</div>`) was outputted as code block text, corrupting the page's DOM hierarchy, which caused external automation/onboarding JS scripts (like `onboarding.js`) to throw an uncaught undefined promise error when reading the malformed DOM elements.
  - **Fix**: Removed leading indentation from the HTML templates in `components.py` `render_metric_card` to prevent markdown code block formatting.
  - **Verification**: Running `python src/run_debug.py` now runs successfully with 0 console logs, 0 network errors, and clean page layouts. Playwright test selectors in `debug_pipeline.py` were also fixed to select visible custom links (`div[data-testid="stPageLink"] a`) rather than default hidden sidebar nav components.

# Restoration Point
- Date: 2026-05-19 21:19:25
- Location: F:\TEMP\local\opencode\restoration-point-20260519-211925.zip
- Size: 90 MB
- Scope: Full F:\annd\dhannd workspace snapshot

# UI Redesign Knowledge Transfer (2026-05-19)
## Overview
Applied Material Design 3 redesign to Streamlit app using Stitch-generated design system.

## Design System
- **Primary:** `#0056B3` (blue)
- **Surface:** `#f9f9ff` (light), white cards, `#c2c6d4` borders
- **Font:** Inter (via Google Fonts CDN link in app.py)
- **Icons:** Material Symbols Outlined (via Google Fonts CDN)
- **Radius:** 8px (components), 12px (containers), 9999px (chips)
- **Grid:** 8px base, 24px gutters
- **Shadows:** `rgba(0,0,0,0.05)` ambient

## Files Modified
- `src/app.py` — Global CSS with `--md-*` custom properties, custom sidebar nav with Material icons, welcome page
- `src/components.py` — Updated all 4 components to use CSS vars, added `render_chip()`, `render_card()`
- `src/pages/1_Dashboard.py` — KPI cards with icons, conversion cards with chips, section icons
- `src/pages/2_QuanLyCanBo.py` — Section icons, status bar M3 colors, reduction cards with chips
- `src/pages/3_NhatKyHoatDong.py` — Teaching/NCKH section badges with icons
- `src/pages/4_CaiDatHeThong.py` — Tab icons, list cards with chips, holiday amber badges

## Key CSS Custom Properties
Defined in `app.py` `:root`:
```
--md-primary, --md-primary-container, --md-on-primary
--md-surface{,-dim,-container-lowest,-container-low,-container,-container-high,-container-highest}
--md-on-surface, --md-on-surface-variant
--md-outline, --md-outline-variant
--md-error, --md-error-container
--md-green, --md-green-bg, --md-red, --md-red-bg, --md-amber, --md-amber-bg
--radius-sm/md/lg/xl/full
--shadow-card, --shadow-elevated
--font-family: 'Inter', sans-serif
```

## Stitch Project
- Project ID: `16682207781060267797`
- Design System asset: `assets/e8ae041a1de943d2b4b5bb898f6bd031`
- Desktop screens generated: Dashboard, Teacher Management
- Mobile screens: All 4 pages

## Context7 Validation
- `/streamlit/docs` confirms CSS custom properties approach for theming
- Streamlit supports `st.markdown(unsafe_allow_html=True)` for custom HTML/CSS
- External fonts via `@font-face` or link tag both valid
- Status badges with conditional styling pattern validated

## Run Command
```bash
streamlit run src/app.py
```

---

## Teacher Record — Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn)

# **QUYẾT ĐỊNH**

**Về việc ban hành Quy định chế độ làm việc đối với nhà giáo giảng dạy của Trường Đại học An ninh nhân dân**  
**HIỆU TRƯỞNG TRƯỜNG ĐẠI HỌC AN NINH NHÂN DÂN**  
Căn cứ Quyết định số 7087/QĐ-BCA ngày 15 tháng 8 năm 2025 của Bộ trưởng Bộ Công an quy định chức năng, nhiệm vụ, quyền hạn và tổ chức bộ máy của Trường Đại học An ninh nhân dân;  
Căn cứ Quyết định số 8445/QĐ-BCA ngày 18 tháng năm 2024 của Bộ trưởng Bộ Công an về tổ chức bộ máy của Trường Đại học An ninh nhân dân;  
Căn cứ Thông tư số 108/2025/TT-BCA ngày 20 tháng 11 năm 2025 của Bộ trưởng Bộ Công an quy định chế độ làm việc đối với nhà giáo giảng dạy ở các học viện, trường Công an nhân dân;  
Căn cứ Hướng dẫn số 08/HD-X02-P3 ngày 05 tháng 01 năm 2026 của Cục Đào tạo về thực hiện Thông tư số 108/2025/TT-BCA ngày 20 tháng 11 năm 2025 của Bộ trưởng Bộ Công an quy định chế độ làm việc đối với nhà giáo giảng dạy ở các học viện, trường Công an nhân dân;  
Căn cứ Công văn số 668/X02-P3 ngày 12 tháng 02 năm 2026 của Cục Đào tạo về việc thống nhất một số nội dung về chế độ làm việc đối với nhà giáo của các trường Công an nhân dân;  
Theo đề nghị của đồng chí Trưởng phòng Phòng Chính trị.

## **QUYẾT ĐỊNH:**

**Điều 1.** Ban hành kèm theo Quyết định này Quy định chế độ làm việc đối với nhà giáo giảng dạy của Trường Đại học An ninh nhân dân.  
**Điều 2.** Quyết định này có hiệu lực kể từ ngày ký.  
**Điều 3.** Các đồng chí Trưởng phòng Phòng Chính trị, Thủ trưởng các đơn vị thuộc Trường Đại học An ninh nhân dân; các đơn vị, tổ chức, cá nhân có liên quan chịu trách nhiệm thi hành Quyết định này.  
**Nơi nhận:**  
- Như Điều 3 (để thực hiện);  
- Cục Đào tạo (để phối hợp);  
- Lưu: VT, P2.  
**HIỆU TRƯỞNG**

**Thiếu tướng Trần Văn Tuấn**

# **QUY ĐỊNH**

**Chế độ làm việc đối với nhà giáo giảng dạy của Trường Đại học An ninh nhân dân**  
*(Ban hành kèm theo Quyết định số 300/QĐ-T04-P2 ngày 16/3/2026 của Hiệu trưởng Trường Đại học An ninh nhân dân)*

## **Chương I**

QUY ĐỊNH CHUNG

### **Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng**

1. Văn bản này quy định về định mức thời gian làm việc, giờ chuẩn giảng dạy và giờ nghiên cứu khoa học; quy đổi, miễn, giảm, bù giờ chuẩn giảng dạy và giờ nghiên cứu khoa học; quản lý và thực hiện chế độ làm việc của nhà giáo thuộc biên chế của Trường Đại học An ninh nhân dân (Viết tắt là ANND).  
2. Văn bản này áp dụng đối với nhà giáo được bổ nhiệm chức danh giảng viên; các đơn vị thuộc Trường Đại học ANND; cơ quan, đơn vị, tổ chức, cá nhân có liên quan.

### **Điều 2. Giải thích từ ngữ**

Trong Quy định này, các từ ngữ dưới đây được hiểu như sau:  
1. Nhà giáo là sĩ quan Công an nhân dân làm nhiệm vụ giảng dạy, giáo dục trong Trường Đại học ANND, được bổ nhiệm chức danh giảng dạy theo quy định của Nhà nước và của Bộ Công an.  
2. Giờ hành chính là đơn vị tính thời gian làm việc theo chế độ tuần làm việc 40 giờ được quy định trong Bộ luật Lao động (01 giờ hành chính bằng 60 phút).  
3. Định mức thời gian làm việc là số giờ hành chính trong tổng thời gian làm việc của một năm học được phân chia theo chức danh giảng viên của nhà giáo để thực hiện nhiệm vụ giảng dạy, nghiên cứu khoa học và các nhiệm vụ: Sinh hoạt chuyên môn; học tập, bồi dưỡng nâng cao trình độ; theo quy định đối với sĩ quan Công an nhân dân (Sau đây gọi chung là nhiệm vụ khác).  
4. Giờ chuẩn giảng dạy là đơn vị thời gian quy đổi từ số giờ lao động cần thiết để hoàn thành một công việc nhất định thuộc nhiệm vụ của nhà giáo tương đương với một tiết (Giờ) giảng lý thuyết trực tiếp trên lớp hoặc trực tuyến, bao gồm thời gian lao động cần thiết trước, trong và sau tiết (Giờ) giảng; thời gian giảng dạy trong kế hoạch đào tạo được tính bằng giờ chuẩn, 01 giờ chuẩn được tính bằng 03 giờ hành chính (Sau đây viết gọn là giờ chuẩn).  
5. Định mức giờ chuẩn là số giờ chuẩn tối thiểu của nhà giáo phải thực hiện nhiệm vụ giảng dạy trong một năm học.  
6. Định mức giờ nghiên cứu khoa học là số giờ hành chính tối thiểu của một nhà giáo phải thực hiện nhiệm vụ nghiên cứu khoa học trong một năm học.  
7. Chức danh giảng viên là cách gọi chung của các chức danh giảng dạy trình độ đại học trở lên ở Trường Đại học ANND, gồm: Giáo sư, Phó Giáo sư, Giảng viên chính, Giảng viên, Trợ giảng.

### **Điều 3. Nguyên tắc chung**

1. Việc phân công nhà giáo thực hiện chế độ làm việc quy định tại Quy định này trên cơ sở thực tế đội ngũ nhà giáo, chỉ tiêu đào tạo, bồi dưỡng và nhiệm vụ giáo dục, đào tạo của Trường Đại học ANND theo từng năm học.  
2. Kết quả thực hiện định mức thời gian làm việc là căn cứ để đánh giá, xếp loại cán bộ, bình xét danh hiệu thi đua và thực hiện chế độ, chính sách đối với nhà giáo trong năm học.  
3. Nhà giáo giảng dạy nhiều trình độ đào tạo áp dụng định mức giờ chuẩn đối với chức danh giảng dạy đã được bổ nhiệm.  
4. Nhà giáo kiêm nhiệm nhiều chức vụ, công việc được áp dụng định mức giờ chuẩn thấp nhất trong các chức vụ hoặc công việc kiêm nhiệm.  
5. Định mức giờ chuẩn áp dụng đối với chức vụ, chức danh giảng dạy mới được bổ nhiệm tính từ ngày quyết định bổ nhiệm chức vụ, chức danh giảng dạy mới có hiệu lực thi hành.  
6. Số giờ chuẩn quy đổi từ hoạt động giảng trực tiếp trên lớp hoặc trực tuyến (Sau đây viết gọn là hoạt động giảng trên lớp) của nhà giáo được bổ nhiệm chức danh giảng viên phải bảo đảm tối thiểu 50% định mức giờ chuẩn quy định.  
7. Hoạt động, sản phẩm khoa học được quy đổi ra giờ nghiên cứu khoa học và được thanh toán thù lao theo quy định hiện hành của Nhà nước và của Bộ Công an đối với từng hoạt động, sản phẩm khoa học; việc quy đổi thực hiện theo năm học và không được bù trừ giữa các năm học.

## **Chương II**

THỜI GIAN LÀM VIỆC, GIỜ CHUẨN GIẢNG DẠY VÀ GIỜ NGHIÊN CỨU KHOA HỌC

### **Điều 4. Thời gian làm việc, thời gian nghỉ**

1. Thời gian làm việc của nhà giáo ở Trường Đại học ANND theo chế độ tuần làm việc 40 giờ (Giờ hành chính) và được xác định theo năm học. Tổng thời gian làm việc của nhà giáo trong một năm học là: 44 tuần x 40 giờ = 1.760 giờ.  
2. Thời gian nghỉ trong một năm học của nhà giáo là 08 tuần; trong đó:  
a) Thời gian nghỉ hè và nghỉ tết Âm lịch của nhà giáo công tác ở đơn vị có chức năng giảng dạy là 07 tuần, thay cho nghỉ phép hằng năm. Trường hợp nhà giáo không được bố trí thời gian nghỉ hè trong năm học thì được thực hiện chế độ nghỉ phép theo quy định tại Thông tư số 96/2025/TT-BCA ngày 06 tháng 10 năm 2025 của Bộ trưởng Bộ Công an quy định chế độ nghỉ hằng năm trong Công an nhân dân (Gọi tắt là Thông tư số 96);  
b) Thời gian nghỉ của nhà giáo công tác ở phòng, trung tâm thực hiện theo quy định tại Thông tư số 96;  
c) Thời gian nghỉ ngày lễ, nghỉ tết Dương lịch, nghỉ ngày Truyền thống Công an nhân dân, nghỉ việc riêng, nghỉ không lương của nhà giáo thực hiện theo quy định tại Thông tư số 96;

### **Điều 5. Định mức thời gian làm việc đối với nhà giáo được bổ nhiệm chức danh giảng viên**

Đơn vị tính: Giờ hành chính

| Chức danh | Giảng dạy | Nghiên cứu khoa học | Nhiệm vụ khác |
| ----- | :---: | :---: | :---: |
| Giáo sư, Phó Giáo sư | 930 - 990 | 600 | 170 - 230 |
| Giảng viên chính | 840 - 900 | 600 | 260 - 320 |
| Giảng viên | 750 - 810 | 600 | 350 - 410 |
| Trợ giảng | 600 - 720 | 300 | 740 - 860 |

### **Điều 6. Định mức giờ chuẩn**

1. Định mức giờ chuẩn được quy đổi từ thời gian thực hiện nhiệm vụ giảng dạy của chức danh giảng viên giảng dạy các học phần, môn học khoa học tự nhiên, kỹ thuật, ngoại ngữ, tin học và nhà giáo giảng dạy thực hành như sau:  
Đơn vị tính: Giờ chuẩn

| Giáo sư, Phó Giáo sư | Giảng viên chính | Giảng viên | Trợ giảng |
| :---: | :---: | :---: | :---: |
| 330 | 300 | 270 | 240 |

2. Định mức giờ chuẩn được quy đổi từ thời gian thực hiện nhiệm vụ giảng dạy của chức danh giảng viên giảng dạy các học phần, môn học chính trị, pháp luật, nghiệp vụ như sau:  
Đơn vị tính: Giờ chuẩn

| Giáo sư, Phó Giáo sư | Giảng viên chính | Giảng viên | Trợ giảng |
| :---: | :---: | :---: | :---: |
| 310 | 280 | 250 | 200 |

### **Điều 7. Định mức giờ chuẩn đối với nhà giáo được bổ nhiệm chức vụ lãnh đạo; kiêm nhiệm công tác quản lý, đảng, đoàn thể; công tác tại phòng, trung tâm**

1. Nhà giáo được bổ nhiệm chức vụ lãnh đạo, quản lý; kiêm nhiệm công tác quản lý, đảng, đoàn thể; công tác tại phòng, trung tâm thực hiện định mức giờ chuẩn tối thiểu theo tỉ lệ phần trăm (%) định mức giờ chuẩn quy định tại Điều 6 Quy định này, cụ thể như sau:

| TT | Chức vụ / Nhiệm vụ kiêm nhiệm | Tỉ lệ |
| :---: | ----- | :---: |
| 1. | Hiệu trưởng | 10% |
| 2. | Phó Bí thư Đảng ủy Trường | 15% |
| 3. | Phó Hiệu trưởng | 20% |
| 4. | Trưởng phòng và tương đương | 25% |
| 5. | Phó Trưởng phòng và tương đương | 30% |
| 6. | Trưởng khoa | 60% |
| 7. | Phó Trưởng khoa | 70% |
| 8. | Công tác tại phòng, trung tâm không giữ chức vụ lãnh đạo | 40% |

2. Ngoài những trường hợp được quy định tại khoản 1, Điều 7 của Quy định này, Hiệu trưởng quy định các trường hợp sau thực hiện định mức giờ chuẩn tối thiểu theo tỉ lệ phần trăm (%) định mức giờ chuẩn quy định của Điều 6 Quy định này, cụ thể như sau:

| TT | Chức vụ / Nhiệm vụ kiêm nhiệm | Đơn vị giảng dạy | Phòng, Trung tâm |
| :---: | ----- | :---: | ----- |
| 1. | Ủy viên Ủy ban kiểm tra Đảng ủy Trường | 85% | 35% |
| 2. | Cấp ủy chi bộ hoặc Đảng bộ cơ sở | 85% | 35% |
| 3. | Phó Chủ nhiệm chuyên trách Ủy ban kiểm tra đảng bộ Cơ sở | 85% | 35% |
| 4. | Ủy viên chuyên trách Ủy ban kiểm tra đảng bộ cơ sở | 90% | 37% |
| 5. | Bí thư Đoàn Thanh niên Trường | 80% | 30% |
| 6. | Phó Bí thư Đoàn Thanh niên Trường | 90% | 35% |
| 7. | Ủy viên Ban chấp hành Đoàn Thanh niên Trường | 95% | 37% |
| 8. | Chủ tịch Hội Phụ nữ Trường | 80% | 30% |
| 9. | Phó Chủ tịch Hội Phụ nữ Trường | 90% | 35% |
| 10. | Ủy viên Ban chấp hành Hội Phụ nữ Trường | 95% | 37% |
| 11. | Đội trưởng | 32% |  |
| 12. | Phó Đội trưởng | 36% |  |
| 13. | Tham gia Ban Chủ nhiệm câu lạc bộ học tập | 90% | 37% |
| 14. | Giáo vụ (thực hiện công tác giáo vụ, nhiệm vụ tổng hợp, công tác đảng)¹ | 80% |  |
| 15. | Quản lý phòng học thực hành, phòng thí nghiệm; quản lý kho vũ khí, công cụ hỗ trợ, vật liệu nổ, trường bắn, phòng bắn điện tử và các loại phòng chuyên dụng khác theo quy định² | 85% | 35% |

*¹ Định mức giờ chuẩn tối thiểu của nhà giáo kiêm nhiệm nhiệm vụ giáo vụ được áp dụng cho 01 nhà giáo tại 01 đơn vị giảng dạy. Căn cứ điều kiện thực tiễn tại từng đơn vị giảng dạy có thể bố trí số lượng nhà giáo thực hiện nhiệm vụ giáo vụ tại mỗi đơn vị giảng dạy nhiều hơn 01 người; trong trường hợp này, mỗi nhà giáo được giảm định mức với số giờ chuẩn được chia đều từ tổng số giờ chuẩn được giảm tương ứng tối đa 20% định mức giờ chuẩn của chức danh Giảng viên.*  
*² Định mức giờ chuẩn tối thiểu của nhà giáo kiêm nhiệm quản lý phòng học thực hành, phòng chuyên dụng được áp dụng cho 01 nhà giáo đối với 01 phòng học. Căn cứ điều kiện thực tiễn đối với từng loại phòng học, nhà trường có thể bố trí số lượng nhà giáo thực hiện nhiệm vụ quản lý phòng học nhiều hơn 01 người; trong trường hợp này, mỗi nhà giáo được giảm định mức với số giờ chuẩn được chia đều từ tổng số giờ chuẩn được giảm tương ứng tối đa 15% định mức giờ chuẩn của chức danh Giảng viên tại đơn vị giảng dạy đó.*

### **Điều 8. Quy đổi hoạt động chuyên môn ra giờ chuẩn**

1. Hoạt động giảng trên lớp:  
a) Đào tạo trình độ đại học:  
- Một tiết giảng lý thuyết trên lớp được tính: Cho tối đa 40 học viên là 50 phút được tính bằng 1,0 giờ chuẩn; 1,2 giờ chuẩn đối với lớp học có từ 41 đến 60 học viên; 1,4 giờ chuẩn đối với lớp học có từ 61 đến 80 học viên; 1,5 giờ chuẩn đối với lớp học có trên 80 học viên.  
Đối với tiết giảng trên lớp các học phần Ngoại ngữ, Công nghệ thông tin, Kỹ thuật hình sự được tính: 1,0 giờ chuẩn đối với lớp có tối đa 25 học viên; 1,2 giờ chuẩn đối với lớp học có từ 26 đến 40 học viên; 1,4 giờ chuẩn đối với lớp học có từ 41 đến 60 học viên; 1,5 giờ chuẩn đối với lớp học có trên 60 học viên.  
- Một tiết giảng lý thuyết kết hợp làm mẫu, hạ khoa mục hoặc giảng thực hành ở thao trường, bãi tập cho tối đa 40 học viên là 50 phút được tính bằng 1,0 giờ chuẩn; 1,2 giờ chuẩn đối với lớp học có từ 41 đến 55 học viên; 1,4 giờ chuẩn đối với lớp học có từ 56 đến 70 học viên; 1,5 giờ chuẩn đối với lớp học có trên 70 học viên.  
Căn cứ thực tiễn từng học phần có bố trí hình thức tổ chức dạy học thực hành, đơn vị giảng dạy có thể phân công nhiều hơn 01 nhà giáo lên lớp, trong trường hợp này, một tiết giảng được tính 0,7 giờ chuẩn đối với mỗi nhà giáo, trong đó bố trí: Tối đa 02 nhà giáo với lớp học có từ 40 học viên trở xuống; tối đa 03 nhà giáo đối với lớp học có từ 41 đến 60 học viên; tối đa 04 nhà giáo đối với lớp học có trên 60 học viên.  
- Một tiết giảng trên lớp với các hình thức tổ chức dạy học khác (Xêmina, thảo luận, bài tập,...) được tính quy đổi hệ số tương đương một tiết giảng lý thuyết trên lớp.  
b) Đào tạo trình độ thạc sĩ: Một tiết giảng chuyên đề, lý thuyết trên lớp cho tối đa 50 học viên được tính bằng 1,3 giờ chuẩn; lớp trên 50 học viên được tính bằng 1,5 giờ chuẩn.  
c) Đào tạo trình độ tiến sĩ: Một tiết giảng chuyên đề, lý thuyết trên lớp được tính bằng 2,0 giờ chuẩn.  
d) Đào tạo trình độ trung cấp lý luận chính trị: Một tiết giảng lý thuyết, thảo luận trên lớp cho lớp tối đa 50 học viên được tính bằng 1,0 giờ chuẩn; lớp trên 50 học viên được tính bằng 1,2 giờ chuẩn.  
đ) Đào tạo trình độ cao cấp lý luận chính trị: Một tiết giảng lý thuyết, thảo luận trên lớp được tính bằng 1,3 giờ chuẩn cho lớp tối đa 50 học viên, được tính bằng 1,5 giờ chuẩn cho lớp trên 50 học viên.  
e) Lớp bồi dưỡng: Một tiết giảng chuyên đề, lý thuyết trên lớp được tính:

* Hệ số 1,0 giờ chuẩn đối với lớp bồi dưỡng: Chỉ huy cấp đội; chức danh ngạch sơ cấp; nội dung bồi dưỡng trình độ cơ bản.  
* Hệ số 1,3 giờ chuẩn đối với lớp bồi dưỡng: Trưởng Công an xã, Phó Trưởng Công an xã.  
* Hệ số 1,5 giờ chuẩn đối với lớp bồi dưỡng: Lãnh đạo cấp phòng; chức danh ngạch trung cấp; nội dung bồi dưỡng nghiệp vụ chuyên sâu.  
* Hệ số 2,0 giờ chuẩn đối với lớp bồi dưỡng: Lãnh đạo cấp Cục; chức danh ngạch cao cấp; nội dung bồi dưỡng chuyên gia.

g) Một tiết giảng trên lớp tiếng nước ngoài đối với môn học không phải là môn ngoại ngữ được tính 1,5 giờ chuẩn đối với lớp học có 40 học viên; 1,7 giờ chuẩn đối với lớp học có từ 41 đến 60 học viên; 2,0 giờ chuẩn đối với lớp học có trên 60 học viên.  
2. Hướng dẫn trực tiếp học viên thực tập tốt nghiệp, đi tham quan, thực tế được tính bằng 2,5 giờ chuẩn/01 ngày/01 nhà giáo.  
3. Thực hiện bài dạy giỏi, tham gia hội thi dạy giỏi:  
a) Đạt bài dạy giỏi cấp khoa được tính 10 giờ chuẩn.  
b) Đạt bài dạy giỏi cấp trường được tính 15 giờ chuẩn.  
c) Đạt bài dạy giỏi cấp bộ được tính 20 giờ chuẩn.  
4. Tham gia hội đồng, hội thi đánh giá hoạt động dạy giỏi:  
a) Cấp khoa được tính bằng 2,0 giờ chuẩn/01 buổi/01 thành viên.  
b) Cấp trường được tính bằng 3,0 giờ chuẩn/01 buổi/01 thành viên.  
c) Cấp bộ được tính bằng 5,0 giờ chuẩn/01 buổi/01 thành viên.  
5. Tham gia Hội đồng xét danh hiệu dạy giỏi:  
a) Cấp trường: Thẩm định hồ sơ ứng viên được tính 1,0 giờ chuẩn/01 hồ sơ; họp thảo luận, đánh giá, bỏ phiếu tín nhiệm được tính bằng 3,0 giờ chuẩn/01 buổi/01 thành viên.  
b) Cấp bộ: Thẩm định hồ sơ ứng viên được tính 2,0 giờ chuẩn/01 hồ sơ; họp thảo luận, đánh giá, bỏ phiếu tín nhiệm được tính bằng 5,0 giờ chuẩn/01 buổi/01 thành viên.  
6. Tham gia Hội đồng xét chức danh nhà giáo (Các chức danh giảng dạy theo quy định của Bộ Công an):  
a) Cấp trường: Thẩm định hồ sơ ứng viên được tính 2,0 giờ chuẩn/01 hồ sơ; họp thảo luận, đánh giá, bỏ phiếu tín nhiệm được tính bằng 3,0 giờ chuẩn/01 buổi/01 thành viên.  
b) Cấp bộ: Thẩm định hồ sơ ứng viên được tính 3,0 giờ chuẩn/01 hồ sơ; họp thảo luận, đánh giá, bỏ phiếu tín nhiệm được tính bằng 5,0 giờ chuẩn/01 buổi/01 thành viên.  
7. Nhà giáo thực hiện các hoạt động chuyên môn được trả thù lao theo quy định của pháp luật thì không được quy đổi ra giờ chuẩn nhưng được xem xét tính vào tổng định mức giờ chuẩn để đánh giá hoàn thành nhiệm vụ đối với nhà giáo không vượt định mức giờ chuẩn trong năm học.  
8. Quy đổi ra giờ chuẩn các hoạt động: Soạn đề thi, coi thi, chấm thi kết thúc học phần, môn học; soạn đề thi, coi thi, chấm thi tốt nghiệp; hướng dẫn chuyên đề, khóa luận, luận văn, đề án, luận án; chấm chuyên đề, khóa luận, luận văn, đề án; các hoạt động chuyên môn khác:  
a) Biên soạn đề thi:  
- Biên soạn đề thi kết thúc học phần/môn học có đáp án được tính 1,0 giờ chuẩn đối với 01 đề thi tự luận hoặc 08 đề thi vấn đáp, thực hành hoặc 10 đề thi trắc nghiệm.  
- Biên soạn đề thi tốt nghiệp, tuyển sinh, thi học sinh giỏi, thi kiểm tra hiểu biết nhà giáo thực hiện hoạt động dạy giỏi có đáp án được tính: 2,0 giờ chuẩn đối với 01 đề thi tự luận; 1,0 giờ chuẩn đối với 04 đề thi vấn đáp, thực hành hoặc 05 đề thi trắc nghiệm.  
b) Coi thi:  
- Coi thi kết thúc học phần/môn học được tính 1,0 giờ chuẩn/01 buổi coi thi/01 nhà giáo; coi thi tốt nghiệp, tuyển sinh, thi học sinh giỏi, thi kiểm tra hiểu biết nhà giáo thực hiện hoạt động dạy giỏi được tính 1,5 giờ chuẩn/01 buổi coi thi/01 nhà giáo.  
- Nhà giáo phục vụ kỹ thuật thi kết thúc học phần/môn học hình thức thực hành trên máy tính được tính 1,0 giờ chuẩn/01 buổi coi thi/01 nhà giáo. Trường hợp nếu nhà giáo được phân công quản lý phòng thực hành máy tính phục vụ kỹ thuật tại buổi thi thì không được tính quy đổi thành giờ chuẩn. Căn cứ quy mô tổ chức lớp thi hình thức thực hành trên máy tính, Hiệu trưởng quyết định số lượng nhà giáo phục vụ kỹ thuật đảm bảo phù hợp.  
- Các thành viên và thư ký hội đồng thi tốt nghiệp, tuyển sinh, thi học sinh giỏi được tính 2,0 giờ chuẩn/01 buổi họp/01 nhà giáo. Tùy theo yêu cầu đối với khóa tốt nghiệp, tuyển sinh, thi học sinh giỏi, Hiệu trưởng quyết định số buổi họp đảm bảo phù hợp.  
c) Chấm thi (Chấm 02 vòng độc lập):  
- Làm phách bài thi được tính 1,0 giờ chuẩn đối với 50 bài thi tự luận.  
- Chấm thi kết thúc học phần/môn học được tính 1,0 giờ chuẩn đối với 08 bài thi tự luận hoặc 10 bài thi (Học viên) vấn đáp, thực hành hoặc 20 bài thi trắc nghiệm. Chấm tiểu luận (Thay cho thi kết thúc học phần/môn học) được tính 1,0 giờ chuẩn/01 tiểu luận.  
- Chấm thi tốt nghiệp, tuyển sinh, thi học sinh giỏi, thi kiểm tra hiểu biết nhà giáo thực hiện hoạt động dạy giỏi được tính 1,0 giờ chuẩn đối với 06 bài thi tự luận hoặc 06 bài thi (Học viên) vấn đáp, thực hành hoặc 12 bài thi trắc nghiệm.  
- Chấm báo cáo kết quả thực tập tốt nghiệp, báo cáo thực tế, thực hành chính trị được tính 1,0 giờ chuẩn/01 báo cáo/01 nhà giáo.  
d) Khóa luận, đồ án tốt nghiệp đại học (Sau đây gọi chung là khóa luận):  
- Tham gia Hội đồng duyệt tên đề tài: Chủ tịch Hội đồng được tính 1,0 giờ chuẩn/01 khóa luận; các thành viên khác được tính 0,7 giờ chuẩn/01 khóa luận/01 thành viên.  
- Hướng dẫn bảo vệ đạt yêu cầu được tính: 15 giờ chuẩn/01 khóa luận; 20 giờ chuẩn/01 khóa luận đối với trường hợp học viên là người nước ngoài hoặc khóa luận được viết bằng tiếng nước ngoài.  
- Đọc, nhận xét được tính: 3,0 giờ chuẩn/01 khóa luận/01 nhà giáo; 4,0 giờ chuẩn/01 khóa luận/01 nhà giáo đối với khóa luận được viết bằng tiếng nước ngoài.  
- Chấm bảo vệ:

* + Chủ tịch Hội đồng được tính: 3,0 giờ chuẩn/01 khóa luận; 5,0 giờ chuẩn/01 khóa luận đối với khóa luận được viết bằng tiếng nước ngoài.  
* + Các thành viên khác được tính: 2,0 giờ chuẩn/01 khóa luận/01 thành viên; 4,0 giờ chuẩn/01 khóa luận/01 thành viên đối với khóa luận được viết bằng tiếng nước ngoài.

đ) Khóa luận tốt nghiệp đào tạo trung cấp, cao cấp lý luận chính trị  
- Hướng dẫn bảo vệ đạt yêu cầu được tính 15 giờ chuẩn/01 khóa luận.  
- Đọc, nhận xét được tính 3,0 giờ chuẩn/01 khóa luận/01 nhà giáo.  
- Chấm bảo vệ: Chủ tịch Hội đồng được tính 3,0 giờ chuẩn/01 khóa luận; các thành viên khác được tính 2,0 giờ chuẩn/01 khóa luận/01 thành viên.  
e) Luận văn, đề án tốt nghiệp thạc sĩ (Sau đây gọi chung là luận văn):  
- Tham gia Hội đồng duyệt tên đề tài và đề cương: Chủ tịch Hội đồng được tính 1,5 giờ chuẩn/01 luận văn; các thành viên khác được tính 1,0 giờ chuẩn/01 luận văn/01 thành viên.  
- Hướng dẫn bảo vệ đạt yêu cầu được tính: 30 giờ chuẩn/01 luận văn; 40 giờ chuẩn/01 luận văn đối với trường hợp học viên là người nước ngoài.  
- Đọc, nhận xét: Phản biện được tính 6,0 giờ chuẩn/01 luận văn; các thành viên khác được tính 3,0 giờ chuẩn/01 luận văn/01 thành viên.  
- Chấm bảo vệ: Chủ tịch, phản biện, thư ký Hội đồng được tính 4,0 giờ chuẩn/01 luận văn/01 nhà giáo; các thành viên khác được tính 3,0 giờ chuẩn/01 luận văn/01 thành viên.  
g) Luận án tiến sĩ  
- Tham gia Hội đồng duyệt tên đề tài và đề cương luận án, tiểu luận tổng quan, chuyên đề tiến sĩ: Chủ tịch Hội đồng được tính 2,0 giờ chuẩn/01 luận án; các thành viên khác được tính 1,5 giờ chuẩn/01 luận án/01 thành viên.  
- Hướng dẫn nghiên cứu sinh làm luận án tiến sĩ được tính tối đa 200 giờ chuẩn/01 luận án. Cách tính số giờ chuẩn đối với nhà giáo hướng dẫn thực hiện như sau:

* + Trường hợp nghiên cứu sinh làm luận án tiến sĩ trong 04 năm học (Không bao gồm thời gian gia hạn): 50 giờ chuẩn/01 năm học.  
* + Trường hợp nghiên cứu sinh làm luận án tiến sĩ trong 03 năm học: 50 giờ chuẩn/01 năm học trong hai năm học đầu và 100 giờ chuẩn tại năm học thứ ba.  
* + Trường hợp nghiên cứu sinh làm luận án tiến sĩ trong 02 năm học: 50 giờ chuẩn tại năm học đầu tiên và 150 giờ chuẩn tại năm học thứ hai.

Nếu nghiên cứu sinh có 02 nhà giáo hướng dẫn thì hướng dẫn chính được tính 2/3 số giờ chuẩn, hướng dẫn phụ được tính 1/3 số giờ chuẩn trong mỗi năm học.  
- Chấm các chuyên đề luận án tiến sĩ được tính 3,0 giờ chuẩn/01 chuyên đề/01 thành viên.  
- Hội thảo luận án các cấp: Chủ tịch, thư ký Hội đồng được tính 7,0 giờ chuẩn/01 luận án/01 nhà giáo; các thành viên khác được tính 5,0 giờ chuẩn/01 luận án/01 thành viên.  
- Đọc, nhận xét luận án: Phản biện được tính 10 giờ chuẩn/01 luận án; các thành viên khác được tính 5,0 giờ chuẩn/01 luận án/01 thành viên.  
- Chấm bảo vệ luận án cấp cơ sở: Chủ tịch, phản biện, thư ký Hội đồng được tính 10 giờ chuẩn/01 luận án/01 nhà giáo; các thành viên khác được tính 6,0 giờ chuẩn/01 luận án/01 thành viên.  
- Chấm bảo vệ luận án cấp trường: Chủ tịch, phản biện, thư ký Hội đồng được tính 12 giờ chuẩn/01 luận án/01 nhà giáo; các thành viên khác được tính 8,0 giờ chuẩn/01 luận án/01 thành viên.  
i) Chỉ huy, hướng dẫn bắn đạn thật, ném lựu đạn thật: Đối với lớp học có từ 50 học viên trở xuống được tính bố trí tối đa 01 chỉ huy, 02 hướng dẫn; đối với lớp học có trên 50 học viên được bố trí tính tối đa 01 chỉ huy, 03 hướng dẫn.

* - Trong giờ hành chính: Chỉ huy 01 tiết được tính 1,0 giờ chuẩn; hướng dẫn, phục vụ 01 tiết được tính 0,7 giờ chuẩn/01 nhà giáo.  
* - Ngoài giờ hành chính: Chỉ huy 01 tiết được tính 1,5 giờ chuẩn; hướng dẫn, phục vụ 01 tiết được tính 1,0 giờ chuẩn/01 nhà giáo.

k) Tham gia kiểm tra, hướng dẫn, huấn luyện thể dục thể thao theo kế hoạch hội thi, hội thao cấp trường  
- Kiểm tra tiêu chuẩn rèn luyện thể lực, tổ chức hội thao toàn trường, tổ chức thi đấu các môn trong hội thao được tính 2,0 giờ chuẩn/01 buổi/01 nhà giáo.  
- Tham gia trọng tài thi đấu các trận đấu các môn thể dục thể thao:

* + Trọng tài chính được tính: 2,0 giờ chuẩn/01 trận đấu bóng đá, bóng rổ; 1,0 giờ chuẩn/01 trận đấu bóng chuyền; 0,7 giờ chuẩn/01 trận đấu bóng bàn, cầu lông.  
* + Trọng tài phụ, thư ký được tính: 1,5 giờ chuẩn/01 trận đấu bóng đá, bóng rổ/01 nhà giáo; 0,7 giờ chuẩn/01 trận đấu bóng chuyền/01 nhà giáo; 0,5 giờ chuẩn/01 trận đấu bóng bàn, cầu lông/01 nhà giáo.  
* + Trọng tài các môn điền kinh, bơi lội, thể dục dụng cụ được tính 2,0 giờ chuẩn/01 buổi/01 nhà giáo.

l) Tham gia Hội đồng

* - Hội đồng duyệt, tuyển nhà giáo được tính 2,0 giờ chuẩn/01 buổi/01 người dự tuyển/01 thành viên.  
* - Hội đồng duyệt giảng tập sự, người đăng ký thỉnh giảng được tính 3,0 giờ chuẩn/01 buổi/01 người duyệt giảng/01 thành viên.  
* - Hội đồng giáo sư cơ sở: Thẩm định hồ sơ ứng viên được tính 1,5 giờ chuẩn/01 buổi/01 thành viên; thảo luận, đánh giá, bỏ phiếu được tính 2,0 giờ chuẩn/01 buổi/01 thành viên.  
* - Hội đồng giáo sư ngành: Thẩm định hồ sơ ứng viên được tính 2,0 giờ chuẩn/01 buổi/01 thành viên; thảo luận, đánh giá, bỏ phiếu được tính 3,0 giờ chuẩn/01 buổi/01 thành viên.  
* - Hội đồng giáo sư nhà nước: Được tính 1,0 giờ chuẩn/01 buổi/01 thành viên.  
* - Hội đồng xét tặng danh hiệu "Nhà giáo nhân dân", "Nhà giáo ưu tú" cấp trường: Thẩm định hồ sơ ứng viên được tính 1,5 giờ chuẩn/01 buổi/01 thành viên; thảo luận, đánh giá, bỏ phiếu được tính 2,0 giờ chuẩn/01 buổi/01 thành viên.  
* - Hội đồng xét tặng danh hiệu "Nhà giáo nhân dân". "Nhà giáo ưu tú" cấp bộ: Thẩm định hồ sơ ứng viên được tính 2,0 giờ chuẩn/01 buổi/01 thành viên; thảo luận, đánh giá, bỏ phiếu được tính 3,0 giờ chuẩn/01 buổi/01 thành viên.  
* - Hội đồng bồi dưỡng giảng viên tham gia hội thi dạy giỏi cấp bộ: Được tính 2,0 giờ chuẩn/01 buổi/01 thành viên.  
* - Hội đồng bồi dưỡng giảng viên tham gia hội thi dạy giỏi cấp trường: Được tính 1,0 giờ chuẩn/01 buổi/01 thành viên.

Hiệu trưởng quyết định số buổi họp của từng Hội đồng thuộc thẩm quyền quản lý đảm bảo phù hợp.

### **Điều 9. Quy đổi hoạt động, sản phẩm ra giờ nghiên cứu khoa học**

1. Đề tài, chuyên đề khoa học được nghiệm thu, đánh giá từ đạt trở lên:  
a) Một đề tài cấp quốc gia được tính bằng 3.600 giờ hành chính chia đều cho 03 năm học, năm học đầu tiên tính theo thời điểm ký hợp đồng nghiên cứu, năm học thứ hai liền kề năm học đầu tiên, năm học thứ ba tính theo thời điểm được thanh lý hợp đồng nghiên cứu.  
b) Một đề tài cấp bộ, cấp tỉnh được tính bằng 2.400 giờ hành chính chia đều cho 02 năm học, năm học đầu tiên tính theo thời điểm ký hợp đồng nghiên cứu, năm học thứ hai tính theo thời điểm được thanh lý hợp đồng nghiên cứu.  
c) Một đề tài cấp cơ sở được tính bằng 1.200 giờ hành chính ở thời điểm được thanh lý hợp đồng nghiên cứu.  
d) Một chuyên đề khoa học cấp trường được tính bằng 600 giờ hành chính ở thời điểm được nghiệm thu.  
2. Một sáng kiến được quy đổi một lần ở thời điểm được công nhận: Cấp quốc gia được tính bằng 1.200 giờ hành chính; cấp bộ, tỉnh được tính bằng 900 giờ hành chính; cấp cơ sở được tính bằng 600 giờ hành chính.  
3. Biên soạn mới giáo trình, sách, tài liệu dạy học, chương trình giáo dục được quy đổi một lần vào thời điểm có quyết định ban hành hoặc đưa vào sử dụng:  
a) Một giáo trình được tính bằng 1.200 giờ hành chính.  
b) Một sách chuyên khảo được phê duyệt sử dụng trong giảng dạy, nghiên cứu được tính bằng 900 giờ hành chính.  
c) Một sách tham khảo được phê duyệt sử dụng trong giảng dạy, nghiên cứu được tính bằng 600 giờ hành chính.  
d) Một sách hướng dẫn học tập; một tài liệu bồi dưỡng, huấn luyện, tập huấn; một chuyên đề chuyên sâu, chuyên đề bồi dưỡng; một đề cương giáo trình; một chương trình đào tạo, bồi dưỡng, huấn luyện được tính bằng 450 giờ hành chính.  
đ) Một báo cáo thực tế; một báo cáo tổng kết vụ án, chuyên án, chuyên đề; một báo cáo tổng kết chuyên đề nghiệp vụ; một tài liệu biên dịch, sưu tầm; một phim giáo khoa; một tập bài giảng; một đề cương bài giảng (Học phần/môn học, chuyên đề); một đề cương chi tiết học phần (Môn học); một hệ thống bài tập, tình huống thảo luận, thực hành; một hệ thống ngân hàng câu hỏi, đề thi và đáp án được tính bằng 300 giờ hành chính.  
e) Giáo trình, sách, tài liệu dạy học, chương trình giáo dục được chỉnh lý hoặc phiên dịch lại nội dung được tính 50% của biên soạn mới.  
g) Sách, tài liệu dạy học được chuyển hóa từ đề tài khoa học đã được nghiệm thu từ đạt trở lên và thanh lý hợp đồng nghiên cứu của chủ biên (hoặc đồng chủ biên) nếu được Hội đồng thẩm định thông qua, đánh giá có sự thay đổi trên 50% nội dung của đề tài khoa học hoặc được chuyển hóa từ công trình khoa học (Luận án tiến sĩ, luận văn thạc sĩ) của chủ biên (Hoặc đồng chủ biên) được tính tương đương biên soạn mới.  
4. Một bài báo khoa học được công bố trên tạp chí được quy đổi một lần vào thời điểm phát hành tạp chí:  
a) Tạp chí khoa học ISI/Scopus hoặc danh mục quốc tế khác do Hội đồng Giáo sư nhà nước công bố được tính bằng 1.000 giờ hành chính.  
b) Tạp chí khoa học trong Danh mục tạp chí được Hội đồng chức danh giảng dạy Bộ Công an tính điểm: Tối đa đến 1,0 điểm được tính bằng 600 giờ hành chính; tối đa đến 0,75 điểm được tính bằng 450 giờ hành chính; tối đa đến 0,5 điểm được tính bằng 300 giờ hành chính; tối đa đến 0,25 điểm được tính bằng 150 giờ hành chính.  
c) Tạp chí khoa học không trong Danh mục tạp chí được Hội đồng chức danh giảng dạy Bộ Công an tính điểm nhưng có mã số ISSN được tính bằng 150 giờ hành chính.  
5. Một báo cáo khoa học được đăng toàn văn trong kỷ yếu được quy đổi một lần vào thời điểm phát hành kỷ yếu:  
a) Kỷ yếu của hội thảo khoa học được xuất bản có mã số chuẩn quốc tế ISBN hoặc có phản biện được tính bằng: 150 giờ hành chính đối với cấp trường; 300 giờ hành chính đối với cấp bộ, tỉnh; 450 giờ hành chính đối với cấp các hiệp hội, liên tỉnh (Vùng); 600 giờ hành chính đối với cấp quốc gia; 900 giờ hành chính đối với cấp quốc tế viết bằng tiếng nước ngoài.  
b) Kỷ yếu của hội thảo khoa học quy định tại điểm a khoản này không có phản biện nhưng có hội đồng biên tập được tính 75% theo từng cấp.  
c) Báo cáo khoa học có trong danh mục của Web of Science và Scopus được tính tương đương bài báo khoa học quy định tại điểm a khoản 4 Điều này.  
6. Cách tính đối với công trình khoa học có nhiều tác giả:  
a) Đề tài, chuyên đề khoa học: Chủ nhiệm được tính 1/3 số giờ hành chính, số giờ hành chính còn lại được chia đều cho các thành viên kể cả chủ nhiệm.  
b) Bài báo khoa học, báo cáo khoa học, sáng kiến: Tác giả chính được tính 1/3 số giờ hành chính của công trình, số giờ hành chính còn lại được chia theo giá trị đóng góp của mỗi tác giả kể cả tác giả chính. Trường hợp không thể xác định cụ thể giá trị đóng góp của mỗi tác giả thì chia đều cho các tác giả.  
c) Giáo trình, sách, tài liệu dạy học, chương trình giáo dục được biên soạn đảm bảo tiến độ: Chủ biên được tính 1/5 số giờ hành chính của công trình, số giờ hành chính còn lại được chia theo giá trị đóng góp của từng người tham gia biên soạn (Bao gồm cả chủ biên nếu tham gia biên soạn). Trường hợp không thể xác định cụ thể giá trị đóng góp của mỗi người thì chia đều cho từng người tham gia biên soạn; đồng chủ biên thì chia đều cho các thành viên được phân công làm chủ biên.  
7. Các hoạt động, sản phẩm khác được quy đổi ra giờ nghiên cứu khoa học:  
a) Tham gia họp Hội đồng khoa học và đào tạo của trường  
Chủ tịch Hội đồng được tính 15 giờ hành chính/01 buổi họp; các thành viên khác được tính 10 giờ hành chính/01 buổi họp/01 thành viên.  
b) Tham gia Hội đồng hội thảo, thẩm định, nghiệm thu chương trình giáo dục, giáo trình, tài liệu dạy học.

* - Đối với chương trình đào tạo: Chủ tịch, phản biện, thư ký Hội đồng được tính 16 giờ hành chính/01 chương trình/01 nhà giáo; thành viên khác được tính 12 giờ hành chính/01 chương trình/01 thành viên.  
* - Đối với các chương trình giáo dục khác: Chủ tịch, phản biện, thư ký Hội đồng được tính 10 giờ hành chính/01 chương trình/01 nhà giáo; thành viên khác được tính 6,0 giờ hành chính/01 chương trình/01 thành viên.  
* - Đối với giáo trình, sách chuyên khảo:  
  * + Hội đồng duyệt đề cương: Chủ tịch, thư ký Hội đồng được tính 8,0 giờ hành chính/01 giáo trình, sách chuyên khảo/01 nhà giáo; thành viên khác được tính 4,0 giờ hành chính/01 giáo trình, sách chuyên khảo/01 thành viên.  
  * + Hội đồng hội thảo cấp cơ sở: Chủ tịch, thư ký Hội đồng được tính 16 giờ hành chính/01 giáo trình, sách chuyên khảo/01 nhà giáo; thành viên khác được tính 12 giờ hành chính/01 giáo trình, sách chuyên khảo/01 thành viên.  
  * + Hội đồng thẩm định, nghiệm thu cấp trường: Chủ tịch, phản biện, thư ký Hội đồng được tính 24 giờ hành chính/01 giáo trình, sách chuyên khảo/01 nhà giáo; thành viên khác được tính 16 giờ hành chính/01 giáo trình, sách chuyên khảo/01 thành viên.  
* - Đối với các tài liệu dạy học khác:  
  * + Hội đồng duyệt đề cương: Chủ tịch, thư ký Hội đồng được tính 4,0 giờ hành chính/01 tài liệu/01 nhà giáo; thành viên khác được tính 2,0 giờ hành chính/01 tài liệu/01 thành viên.  
  * + Hội đồng hội thảo cấp cơ sở: Chủ tịch, thư ký Hội đồng được tính 8,0 giờ hành chính/01 tài liệu/01 nhà giáo; thành viên khác được tính 4,0 giờ hành chính/01 tài liệu/01 thành viên.  
  * + Hội đồng thẩm định, nghiệm thu cấp trường: Chủ tịch, phản biện, thư ký Hội đồng được tính 16 giờ hành chính/01 tài liệu/01 nhà giáo; thành viên khác được tính 12 giờ hành chính/01 tài liệu/01 thành viên.

c) Hội thảo, tọa đàm khoa học (Sau đây gọi chung là hội thảo) các cấp:

* - Cấp khoa: Chủ trì được tính 15 giờ hành chính/01 hội thảo; thành viên khác được tính 10 giờ hành chính/01 hội thảo/01 thành viên. Ban biên tập kỷ yếu được tính 15 giờ hành chính/01 kỷ yếu, chia đều cho các thành viên.  
* - Cấp trường: Chủ trì được tính 30 giờ hành chính/01 hội thảo; thành viên khác được tính 20 giờ hành chính/01 hội thảo/01 thành viên. Ban biên tập kỷ yếu được tính 20 giờ hành chính/01 kỷ yếu, chia đều cho các thành viên.  
* - Cấp bộ: Chủ trì được tính 60 giờ hành chính/01 hội thảo; thành viên khác được tính 30 giờ hành chính/01 hội thảo/01 thành viên. Ban biên tập kỷ yếu được tính 30 giờ hành chính/01 kỷ yếu, chia đều cho các thành viên.  
* - Cấp các liên hiệp, liên tỉnh (Vùng): Chủ trì được tính 70 giờ hành chính/01 hội thảo; thành viên khác được tính 40 giờ hành chính/01 hội thảo/01 thành viên.  
* - Cấp quốc gia: Chủ trì được tính 80 giờ hành chính/01 hội thảo; thành viên khác được tính 40 giờ hành chính/01 hội thảo/01 thành viên. Ban biên tập kỷ yếu được tính 40 giờ hành chính/01 kỷ yếu, chia đều cho các thành viên.  
* - Cấp quốc tế: Chủ trì được tính 100 giờ hành chính/01 hội thảo; thành viên khác được tính 60 giờ hành chính/01 hội thảo/01 thành viên. Ban biên tập kỷ yếu được tính 60 giờ hành chính/01 kỷ yếu, chia đều cho các thành viên.

d) Hội đồng tư vấn, đánh giá đề tài khoa học, sáng kiến, cải tiến  
- Hội đồng tư vấn xác định nhiệm vụ khoa học và công nghệ: Chủ tịch, thư ký Hội đồng được tính 15 giờ hành chính/01 buổi họp/01 nhà giáo; các thành viên khác được tính 10 giờ hành chính/01 buổi họp/01 thành viên.  
- Đối với đề tài cấp cơ sở:

* + Hội đồng duyệt đề cương chi tiết: Chủ tịch, phản biện, thư ký Hội đồng được tính 8,0 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 5,0 giờ hành chính/01 đề tài/01 thành viên.  
* + Hội đồng tọa đàm, hội thảo: Chủ tịch, thư ký Hội đồng được tính 12 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 8,0 giờ hành chính/01 đề tài/01 thành viên.  
* + Hội đồng đánh giá, nghiệm thu cấp cơ sở: Chủ tịch, phản biện, thư ký Hội đồng được tính 28 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 20 giờ hành chính/01 đề tài/01 thành viên.

- Đối với đề tài cấp tỉnh, bộ:

* + Hội đồng duyệt đề cương chi tiết: Chủ tịch, phản biện, thư ký Hội đồng được tính 12 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 8,0 giờ hành chính/01 đề tài/01 thành viên.  
* + Hội đồng tọa đàm, hội thảo: Chủ tịch, phản biện, thư ký Hội đồng được tính 16 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 12 giờ hành chính/01 đề tài/01 thành viên.  
* + Hội đồng đánh giá, nghiệm thu cấp cơ sở: Chủ tịch, phản biện, thư ký Hội đồng được tính 40 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 32 giờ hành chính/01 đề tài/01 thành viên.

- Đối với đề tài cấp quốc gia:

* + Hội đồng duyệt đề cương chi tiết: Chủ tịch, phản biện, thư ký Hội đồng được tính 16 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 12 giờ hành chính/01 đề tài/01 thành viên.  
* + Hội đồng tọa đàm, hội thảo: Chủ tịch, phản biện, thư ký Hội đồng được tính 24 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 16 giờ hành chính/01 đề tài/01 thành viên.  
* + Hội đồng đánh giá, nghiệm thu cấp cơ sở: Chủ tịch, phản biện, thư ký Hội đồng được tính 56 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 40 giờ hành chính/01 đề tài/01 thành viên.  
* + Hội đồng đánh giá sáng kiến, cải tiến cấp trường: Chủ tịch, phản biện, thư ký Hội đồng được tính 8,0 giờ hành chính/01 đề tài/01 nhà giáo; thành viên khác được tính 6,0 giờ hành chính/01 đề tài/01 thành viên.

đ) Hội đồng đánh giá đề tài, chuyên đề nghiên cứu khoa học (Sau đây gọi chung là đề tài) của học viên.  
- Hội đồng duyệt tên đề tài: Hội đồng cấp khoa được tính 1,0 giờ hành chính/01 đề tài/01 thành viên; Hội đồng cấp trường được tính 1,5 giờ hành chính/01 đề tài/01 thành viên.  
- Hội đồng đánh giá đề tài: Chủ tịch, thư ký Hội đồng được tính 4,0 giờ hành chính/01 đề tài/01 nhà giáo; các thành viên khác được tính 2,0 giờ hành chính/01 đề tài/01 thành viên.  
e) Hướng dẫn học viên nghiên cứu khoa học, tham gia các cuộc thi (Được quy đổi một lần tại thời điểm học viên được công nhận kết quả).

* - Thi cấp trường được tính: 16 giờ hành chính/01 học viên được đánh giá đạt yêu cầu; 20 giờ hành chính/01 học viên đạt giải Khuyến khích; 24 giờ hành chính/01 học viên đạt giải Ba; 32 giờ hành chính/01 học viên đạt giải Nhì; 40 giờ hành chính/01 học viên đạt giải Nhất.  
* - Thi cấp bộ được tính: 32 giờ hành chính/01 học viên được đánh giá đạt yêu cầu; 40 giờ hành chính/01 học viên đạt giải Khuyến khích; 56 giờ hành chính/01 học viên đạt giải đạt Ba; 64 giờ hành chính/01 học viên đạt giải Nhì; 72 giờ hành chính/01 học viên đạt giải Nhất.  
* - Thi cấp quốc gia được tính: 72 giờ hành chính/01 học viên được đánh giá đạt yêu cầu; 80 giờ hành chính/01 học viên đạt giải Khuyến khích; 96 giờ hành chính/01 học viên đạt giải Ba; 104 giờ hành chính/01 học viên đạt giải Nhì; 120 giờ hành chính/01 học viên đạt giải Nhất.  
* - Thi cấp quốc tế được tính: 80 giờ hành chính/01 học viên được đánh giá đạt yêu cầu; 104 giờ hành chính/01 học viên đạt giải Khuyến khích; 128 giờ hành chính/01 học viên đạt giải Ba; 144 giờ hành chính/01 học viên đạt giải Nhì; 160 giờ hành chính/01 học viên đạt giải Nhất.

Trường hợp nhà giáo hướng dẫn nhóm học viên đạt giải thì giờ hành chính được tính quy đổi áp dụng đối với từng thành tích (Giải) đạt được. Trường hợp nhiều nhà giáo tham gia hướng dẫn học viên/nhóm học viên đạt giải thì chia đều số giờ hành chính được tính quy đổi cho từng nhà giáo tham gia hướng dẫn.  
g) Tham gia cuộc thi tìm hiểu các cấp (Được quy đổi một lần tại thời điểm được công nhận kết quả).

* - Đạt giải tại cuộc thi tìm hiểu cấp trường được tính: 300 giờ hành chính/01 giải Nhất; 250 giờ hành chính/01 giải Nhì; 200 giờ hành chính/01 giải Ba; 100 giờ hành chính/01 giải Khuyến khích.  
* - Đạt giải tại cuộc thi tìm hiểu cấp bộ được tính: 450 giờ hành chính/01 giải Nhất; 350 giờ hành chính/01 giải Nhì; 300 giờ hành chính/01 giải Ba; 200 giờ hành chính/01 giải Khuyến khích.

h) Một cải tiến được quy đổi một lần tại thời điểm được công nhận: Cấp trường được tính 300 giờ hành chính, cấp bộ được tính 450 giờ hành chính. Trường hợp nhóm tác giả thực hiện cải tiến được công nhận, chủ nhiệm được tính 1/3 giờ hành chính, số giờ hành chính còn lại được chia đều cho các thành viên kể cả chủ nhiệm.  
i) Một số báo cáo khoa học được đăng toàn văn trong kỷ yếu tọa đàm khoa học cấp trường, kỷ yếu hội thảo, tọa đàm khoa học cấp khoa có phản biện (Hoặc không có phản biện nhưng có hội đồng biên tập) được tính: 40 giờ hành chính/01 bài viết tọa đàm cấp trường; 14 giờ hành chính/01 bài viết hội thảo, tọa đàm cấp khoa.  
k) Một bài viết được đăng tải toàn văn trên trang điện tử của nhà trường (Có thẩm định, biên tập) được tính: 40 giờ hành chính/01 bài viết khoa học; 24 giờ hành chính/01 bài viết thông tin; 12 giờ hành chính/01 bản tin. Ban biên tập trang điện tử của nhà trường được tính: 3,0 hành chính/01 bài viết thông tin; 6,0 giờ hành chính/01 bài viết khoa học (Chia đều cho các thành viên).  
l) Tham gia phản biện, thẩm định, biên tập bài báo khoa học  
- Tham gia phản biện bài báo khoa học được tính: 40 giờ hành chính/01 bài báo tạp chí khoa học ISI/Scopus; 16 giờ hành chính/01 bài báo tạp chính có mã số ISSN trong nước; 24 giờ hành chính/01 bài báo tạp chí có mã số ISSN quốc tế.  
- Thẩm định, phản biện học thuật 01 bài báo tạp chí có chỉ số khoa học được tính 10 giờ hành chính.  
- Biên tập tạp chí khoa học được tính 30 giờ hành chính/01 số tạp chí được phát hành, chia đều cho số người thực hiện biên tập.  
m) Biên tập giáo trình, sách, tài liệu dạy học được tính 20 giờ hành chính/01 loại tài liệu, chia đều cho số người thực hiện biên tập.  
n) Biên soạn mục từ bách khoa thư Công an nhân dân được tính: 80 giờ hành chính/01 mục từ cỡ nhỏ; 120 giờ hành chính/01 mục từ cỡ trung bình; 200 giờ hành chính/01 mục từ cỡ dài; 320 giờ hành chính/01 mục từ cỡ rất dài. Trường hợp nhiều người tham gia biên soạn thì tác giả chính được tính 1/3 giờ hành chính, số giờ hành chính còn lại được chia đều cho các thành viên kể cả tác giả chính.  
o) Xây dựng quy trình đảm bảo chất lượng được công nhận được tính: 40 giờ hành chính/01 quy trình cấp khoa; 80 giờ hành chính/01 quy trình cấp trường. Trường hợp nhiều người tham gia biên soạn thì tác giả chính được tính 1/3 số giờ hành chính, số giờ hành chính còn lại được chia đều cho các thành viên kể cả tác giả chính.

### **Điều 10. Chế độ miễn, giảm định mức giờ chuẩn**

1. Nguyên tắc cách tính giảm định mức giờ chuẩn  
a) Thời gian để tính giảm định mức giờ chuẩn đối với từng trường hợp được xác định thuộc khung thời gian 44 tuần làm việc trong một năm học của nhà giáo (Không bao gồm thời gian nghỉ 08 tuần trong một năm học của nhà giáo).  
b) Việc quy đổi thời gian được tính giảm định mức thống nhất thực hiện theo đơn vị tuần. Trường hợp được tính giảm định mức, nếu số ngày được áp dụng tính không tròn bằng 01 tuần (Chế độ tuần làm việc 40 giờ hành chính, tương đương 05 ngày) thì tính tỉ lệ theo số ngày được tính áp dụng trong tuần đó (05 ngày); nếu số ngày được áp dụng trong tuần vượt quá 05 ngày nhưng vẫn nằm trọn trong 01 tuần theo lịch thì vẫn được tính tròn là 01 tuần.  
c) Trong cùng một khoảng thời gian nhà giáo thuộc nhiều trường hợp được giảm định mức giờ chuẩn thì áp dụng mức giảm định mức giờ chuẩn cao nhất theo quy định.  
d) Số giờ chuẩn giảm định mức được làm tròn đến 01 chữ số thập phân.  
2. Miễn định mức giờ chuẩn đối với nhà giáo đi học tập trung liên tục hoặc thực hiện quyết định trưng tập có thời hạn của cấp có thẩm quyền từ 10 tháng trở lên trong một năm học.  
3. Giảm định mức giờ chuẩn  
a) Nhà giáo có quyết định bổ nhiệm chức danh Trợ giảng được giảm 50% trong 12 tháng và giảm 20% từ tháng thứ 13 đến hết tháng thứ 24 tính từ ngày được bổ nhiệm, cụ thể: Tỷ lệ định mức giờ chuẩn được giảm trong năm học đầu tiên tính từ ngày Quyết định bổ nhiệm chức danh trên của nhà giáo có hiệu lực đến thời điểm kết thúc năm học thống kê, trong các năm học tiếp theo được tính đến thời điểm hết tháng thứ 24 tính từ ngày Quyết định bổ nhiệm chức danh trên có hiệu lực theo các tỉ lệ giảm định mức theo quy định tương ứng với số giờ chuẩn áp dụng trong năm học thống kê.  
Ví dụ: Trong năm học 2025 - 2026, nhà giáo Nguyễn Văn A được bổ nhiệm chức danh Trợ giảng ngày 01/12/2025 (Tuần thứ 18 theo lịch giảng dạy của Trường). Như vậy, nhà giáo Nguyễn Văn A được tính giảm định mức giờ chuẩn các năm học cụ thể như sau:

* - Năm học 2025 - 2026: Số giờ chuẩn (GC) được giảm = 200 GC x 27 (tuần) / 44 (tuần) x 50% = 61,4 GC  
* - Năm học 2026 - 2027: Số giờ chuẩn (GC) được giảm = [200 GC x 17 (tuần) x 50% / 44 (tuần)] + [200 GC x 27 (tuần) x 20% / 44 (tuần)] = 63,2 GC  
* - Năm học 2027 - 2028: Số giờ chuẩn (GC) được giảm = 200 GC x 17 (tuần) x 20% / 44 (tuần) = 15,5 GC

b) Nhà giáo được giảm theo tỉ lệ tương ứng với thời gian: Đi học lớp đào tạo theo hình thức vừa làm vừa học (Không bao gồm thời gian gia hạn đối với đi học nghiên cứu sinh); đi học lớp đào tạo, bồi dưỡng tập trung liên tục từ 20 ngày trở lên (Trừ trường hợp quy định tại khoản 2 Điều này); đi thực tế theo quy định của Bộ Công an (Không bao gồm thời gian đi thực tế kết hợp hướng dẫn học viên thực tập tốt nghiệp, đi thăm quan, thực tế, thực hành chính trị xã hội); thực hiện quyết định trung tập có thời hạn của cấp có thẩm quyền; điều trị bệnh theo kết luận của cơ quan, đơn vị y tế có thẩm quyền; nghỉ không hưởng lương; tạm đình chỉ công tác theo quy định, cụ thể: Trong một năm học, nhà giáo thuộc nhiều trường hợp giảm định mức thì cộng dồn để tính tổng định mức được giảm theo tỉ lệ tương ứng với thời gian áp dụng với từng trường hợp được hưởng (Nếu thuộc nhiều trường hợp trong cùng một thời gian thì chỉ tính giảm tương ứng theo tỉ lệ đối với khoảng thời gian đó).  
Ví dụ: Nhà giáo Trần Văn B có chức danh Giảng viên, trong năm học 2025 - 2026 có quyết định trưng tập có thời hạn cán bộ của X01 từ ngày 01/9/2025 đến ngày 28/12/2025 (16 tuần); đi học lớp bồi dưỡng tập trung liên tục từ ngày 27/10/2025 đến ngày 17/11/2025 (21 ngày = 03 tuần); điều trị bệnh từ ngày 06/4/2026 đến ngày 27/4/2026 (03 tuần). Như vậy, nhà giáo Trần Văn B được tính giảm định mức giờ chuẩn năm học 2025 - 2026 tương ứng với tỷ lệ thời gian được miễn giảm là 19 tuần/44 tuần (Khoảng thời gian đi học lớp bồi dưỡng đã được tính trong khoảng thời gian thực hiện quyết định trưng tập có thời hạn), cụ thể:  
Số giờ chuẩn (GC) được giảm = 260 GC x 19 (tuần) / 44 (tuần) = 112,3 GC  
c) Nhà giáo nữ nghỉ thai sản được giảm tỉ lệ tương ứng thời gian quy định tại Bộ luật Lao động; được giảm 15% trong thời gian nuôi con nhỏ dưới 12 tháng tuổi; được giảm 10% trong thời gian nuôi con nhỏ từ đủ 12 tháng tuổi đến dưới 36 tháng tuổi; thời gian nghỉ thai sản được giảm tỉ lệ tương ứng với thời gian công tác trong năm học thống kê. Trường hợp nếu nhà giáo nữ trở lại làm việc trước khi hết thời gian nghỉ thai sản (Thực hiện về hồ sơ, quy trình theo quy định) thì thời gian được giảm tỉ lệ tương ứng chỉ tính đến thời điểm nhà giáo trở lại làm việc (Thực hiện tương tự cách tính tại điểm a của khoản này).  
Nhà giáo nữ kết thúc thời gian nghỉ thai sản để đi làm trở lại được áp dụng giảm định mức thời gian nuôi con nhỏ đến dưới 36 tháng tuổi (Tính từ ngày nhà giáo nữ sinh con đến tháng thứ 35) theo các tỉ lệ quy định tính từ ngày đi làm trở lại (Thực hiện tương tự cách tính tại Khoản 1 Điều này).  
Ví dụ: Nhà giáo nữ Phạm Thị C có chức danh Giảng viên, trong năm học 2025 - 2026, nhà giáo Phạm Thị C sinh con ngày 08/12/2025, nghỉ thai sản từ ngày 01/12/2025 đến ngày 01/6/2025 (23 tuần, không bao gồm 03 tuần nghỉ Tết Âm lịch). Như vậy, nhà giáo Phạm Thị C được tính giảm định mức giờ chuẩn các năm học cụ thể như sau:

* - Năm học 2025 - 2026: Số giờ chuẩn (GC) được giảm = [260 GC x 23 (tuần) / 44 (tuần)] + [260 GC x 04 (tuần) x 15% / 44 (tuần)] = 143,3 GC  
* - Năm học 2026 - 2027: Số giờ chuẩn (GC) được giảm = [260 GC x 18 (tuần) x 15% / 44 (tuần)] + [260 GC x 26 (tuần) x 10% / 44 (tuần)] = 31,3 GC  
* - Năm học 2027 - 2028: Số GC được giảm = 260 GC x 10% = 26 GC  
* - Năm học 2028 - 2029: Số giờ chuẩn (GC) được giảm = 260 GC x 18 (tuần) x 10% / 44 (tuần) = 10,6 GC

d) Nhà giáo có quyết định của cấp thẩm quyền giao kiêm nhiệm nhiệm vụ tại đơn vị thuộc cơ quan Bộ Công an, Công an tỉnh, thành phố (Sau đây gọi chung là Công an đơn vị, địa phương), Hiệu trưởng Trường Đại học ANND trao đổi, thống nhất với Thủ trưởng Công an đơn vị, địa phương về thời gian làm việc của nhà giáo ở cả hai đơn vị để quyết định tỉ lệ giảm định mức đối với nhà giáo và báo cáo kết quả thực hiện về Cục Đào tạo để quản lý, theo dõi.  
đ) Cách thức áp dụng trong tình huống nhà giáo thuộc nhiều trường hợp được giảm định mức giờ chuẩn trong một năm học theo quy định.  
Trong một năm học, nhà giáo thuộc nhiều trường hợp được miễn giảm định mức giờ chuẩn thì được cộng dồn để tính tổng định mức được giảm và thực hiện theo thứ tự như sau:  
(1) Đối với nhà giáo có sự thay đổi về chức vụ, chức danh giảng dạy trong một năm học thì cần xác định cụ thể định mức giờ chuẩn theo từng chức vụ, chức danh giảng dạy. Nhà giáo thuộc trường hợp được giảm định mức trong thời gian đang đảm nhiệm chức vụ, chức danh giảng dạy nào thì được tính số giờ chuẩn được giảm theo định mức giờ chuẩn của chức vụ, chức danh giảng dạy đó.  
(2) Giảm định mức giờ chuẩn tỉ lệ tương ứng với thời gian đi học, đi thực tế, thực hiện quyết định trưng tập, điều trị bệnh, nghỉ không hưởng lương, tạm đình chỉ công tác, nghỉ thai sản.  
(3) Giảm định mức giờ chuẩn đối với các trường hợp còn lại với tỉ lệ tương ứng theo quy định áp dụng đối với khoảng thời gian còn lại trong năm học nhà giáo làm việc tại đơn vị (Không bao gồm thời gian đã được giảm định mức tại điểm (2) nêu trên).  
Ví dụ 1: Nhà giáo Lê Văn D có chức vụ Phó Trưởng khoa, chức danh Giảng viên chính. Ngày 01/12/2025, nhà giáo Lê Văn D có quyết định bổ nhiệm chức vụ Trưởng khoa. Trong năm học 2025 - 2026, nhà giáo có thời gian đi thực tế từ ngày 04/8/2025 đến ngày 29/9/2025 (08 tuần), có thời gian đi học lớp bồi dưỡng từ ngày 06/4/2026 đến ngày 27/4/2026 (03 tuần). Như vậy, nhà giáo Lê Văn D trong năm 2025 - 2026 được tính giảm định mức như sau:  
Định mức giờ chuẩn (GC) phải thực hiện = [280 GC x 70% x 17 (tuần) / 44 (tuần)] + [280 GC x 60% x 27 (tuần) / 44 (tuần)] = 75,7 GC + 103,1 GC = 178,8 GC  
Số giờ chuẩn (GC) được giảm = [75,7 GC x 08 (tuần) / 17 (tuần)] + [103,1 GC x 03 (tuần) / 27 (tuần)] = 47,1 GC  
Ví dụ 2: Nhà giáo nữ Bùi Thị X có chức danh Giảng viên. Ngày 17/11/2025, nhà giáo được bổ nhiệm chức danh Giảng viên chính. Trong năm học 2025 - 2026, nhà giáo nghỉ thai sản từ ngày 04/8/2025 đến ngày 22/9/2025 (07 tuần), đi học lớp đào tạo hệ vừa làm vừa học từ ngày 06/4/2026 đến ngày 05/7/2026 (13 tuần). Như vậy, nhà giáo Bùi Thị X trong năm học 2025 - 2026 được tính giảm định mức, như sau:  
Định mức giờ chuẩn (GC) phải thực hiện = [260 GC x 15 (tuần) / 44 (tuần)] + [280 GC x 29 (tuần) / 44 (tuần)] = 88,6 GC + 184,5 GC = 273,1 GC  
Số giờ chuẩn (GC) được giảm = [88,6 GC x 07 (tuần) / 15 (tuần)] + [88,6 GC x 15% x 08 (tuần) / 15 (tuần)] + [184,5 GC x 13 (tuần) / 29 (tuần)] + [184,5 GC x 15% x 16 (tuần) / 29 (tuần)] = 146,4 GC  
3. Các trường hợp khác được miễn, giảm định mức giờ chuẩn, cụ thể như sau:  
a) Nhà giáo đang trong thời gian nghiên cứu, xây dựng luận văn, đề án tốt nghiệp thạc sĩ, luận án tiến sĩ (Không bao gồm thời gian học tập trung các học phần trong chương trình đào tạo thạc sĩ, tiến sĩ và thời gian được gia hạn theo quy chế đào tạo) được giảm 15% định mức giờ chuẩn.  
b) Nhà giáo tham gia Tổ tư vấn/Nhóm nghiên cứu phát triển khoa học công nghệ, đổi mới sáng tạo (Tổ tư vấn) của nhà trường được giảm tối đa không quá 15% định mức giờ chuẩn.  
c) Nhà giáo có quyết định của cấp có thẩm quyền (Không bao gồm cấp phòng và tương đương trở xuống) chọn, cử tham gia thành viên các đội tuyển tập luyện, thi đấu tại các hội thi, hội thao từ cấp bộ trở lên hoặc (Và) tham gia các nhiệm vụ cần bố trí làm việc toàn thời gian trong thời gian liên tục từ 20 ngày trở lên được giảm theo tỉ lệ tương ứng với thời gian thực hiện các nhiệm vụ trên.

### **Điều 11. Chế độ miễn, giảm định mức giờ nghiên cứu khoa học**

1. Miễn định mức giờ nghiên cứu khoa học đối với nhà giáo thực hiện quyết định trưng tập có thời hạn của cấp có thẩm quyền từ 10 tháng trở lên trong một năm học.  
2. Giảm định mức giờ nghiên cứu khoa học  
a) Nhà giáo đi đào tạo, bồi dưỡng đối với lớp có tổng thời gian học từ 06 tháng trở lên trong năm học được giảm 50% định mức.  
b) Nhà giáo công tác tại phòng, trung tâm (Không bao gồm nhà giáo được bổ nhiệm chức danh Giáo sư, Phó Giáo sư) được giảm 50% định mức.  
c) Nhà giáo nữ nuôi con nhỏ dưới 12 tháng tuổi có thời gian nghỉ thai sản trong một năm học được giảm 60% định mức; nếu thời gian nghỉ thai sản thuộc hai năm học thì được giảm định mức ở cả hai năm học, mỗi năm học giảm 30% định mức.  
d) Đối với nhà giáo có quyết định của cấp thẩm quyền giao kiêm nhiệm nhiệm vụ tại Công an đơn vị, địa phương thực hiện tương tự quy định tại điểm d Khoản 2 Điều 10 Quy định này.  
3. Các trường hợp khác được miễn, giảm định mức giờ nghiên cứu khoa học:  
a) Nhà giáo nam nuôi con nhỏ trong trường hợp vợ bị chết (Có xác nhận của chính quyền địa phương): Được giảm 15% định mức trong thời gian nuôi con nhỏ dưới 12 tháng tuổi; được giảm 10% định mức trong thời gian nuôi con nhỏ từ đủ 12 tháng tuổi đến dưới 36 tháng tuổi.  
b) Nhà giáo có quyết định trưng tập có thời hạn (Trừ trường hợp trưng tập từ 10 tháng trở lên), luân chuyển có thời hạn đến Công an đơn vị, địa phương của cấp có thẩm quyền, tham gia các nhiệm vụ toàn thời gian theo quyết định hoặc kế hoạch của Bộ Công an có tổng thời gian từ 06 tháng trở lên trong năm học được giảm 50% định mức.

### **Điều 12. Cách tính giảm định mức, bù định mức và vượt định mức**

1. Nhà giáo thuộc nhiều trường hợp giảm định mức thì được cộng dồn để tính tổng định mức được giảm.  
2. Cách tính bù định mức đối với cá nhân nhà giáo  
a) Nhà giáo giảng dạy ở đơn vị giảng dạy được giao ít chỉ tiêu đào tạo, bồi dưỡng hoặc lĩnh vực, ngành, chuyên ngành có ít chỉ tiêu tuyển sinh, sau khi thực hiện quy đổi giờ chuẩn theo quy định tại Điều 8 Quy định này (Phải bao gồm hoạt động giảng trên lớp), nếu không bảo đảm định mức giờ chuẩn theo quy định thì được bù từ giờ nghiên cứu khoa học vượt định mức sang đến đủ định mức theo quy định, quy đổi 03 giờ nghiên cứu khoa học bằng 01 giờ chuẩn.  
b) Nhà giáo không hoàn thành định mức giờ chuẩn nhưng bảo đảm định mức giờ chuẩn quy đổi từ hoạt động giảng trên lớp quy định tại Khoản 6 Điều 3 Quy định này thì được bù từ giờ nghiên cứu khoa học vượt định mức sang đến đủ định mức theo quy định, quy đổi 03 giờ nghiên cứu khoa học bằng 01 giờ chuẩn.  
c) Việc tính bù định mức chỉ áp dụng đối với số giờ quy đổi vượt định mức từ giờ chuẩn thành giờ nghiên cứu khoa học hoặc ngược lại, mức bù tối đa đến đủ định mức đối với số giờ còn thiếu theo quy định.  
d) Nhà giáo hoàn thành tối thiểu 25% định mức giờ nghiên cứu khoa học theo quy định thì được bù từ giờ chuẩn vượt định mức sang đến đủ định mức theo quy định, quy đổi 01 giờ chuẩn bằng 03 giờ nghiên cứu khoa học.  
đ) Riêng đối với trường hợp bù từ giờ chuẩn vượt định mức sang giờ nghiên cứu khoa học thì lấy giờ chuẩn vượt định mức quy đổi từ các hoạt động chuyên môn khác trước, nếu bù chưa đủ thì tiếp tục lấy số giờ chuẩn vượt định mức (Nếu có) quy đổi từ hoạt động giảng trên lớp (Định mức giờ chuẩn hoạt động giảng trên lớp thực hiện theo quy định tại Khoản 6 Điều 3 của Quy định này) để bù đến đủ định mức giờ nghiên cứu khoa học theo quy định.  
3. Cách tính bù định mức đối với đơn vị làm công tác giảng dạy  
- Nguyên tắc áp dụng: Chỉ áp dụng việc bù định mức giờ chuẩn giữa các nhà giáo trong cùng đơn vị giảng dạy; không áp dụng bù định mức giờ nghiên cứu khoa học giữa các nhà giáo hoặc bù định mức quy đổi từ giờ nghiên cứu khoa học vượt định mức của nhà giáo này sang giờ chuẩn còn thiếu định mức của nhà giáo khác trong cùng đơn vị giảng dạy. Tổng số giờ chuẩn chưa hoàn thành định mức của các nhà giáo trong đơn vị giảng dạy được chia đều cho các nhà giáo có số giờ chuẩn vượt định mức để tính bù định mức đến đủ số giờ chuẩn còn thiếu theo quy định (Nếu có).  
- Cách tính: Trường hợp có nhà giáo trong đơn vị không hoàn thành định mức giờ chuẩn thì lấy số giờ chuẩn vượt định mức của các nhà giáo khác trong cùng đơn vị (Nếu có) để bù tối đa đến đủ định mức đối với số giờ chuẩn còn thiếu theo quy định của nhà giáo đó; trong đó thực hiện lấy giờ chuẩn vượt định mức quy đổi từ các hoạt động chuyên môn khác trước, nếu chưa bù đủ thì tiếp tục lấy giờ chuẩn vượt định mức quy đổi từ hoạt động giảng trên lớp của nhà giáo vượt định mức để bù đến đủ định mức của nhà giáo còn thiếu giờ chuẩn.  
Ví dụ: Năm học 2025 - 2026, Khoa X có 02 nhà giáo chưa hoàn thành định mức với tổng 50 giờ chuẩn và có 05 nhà giáo thực hiện vượt định mức giờ chuẩn thì sẽ lấy bù định mức mỗi nhà giáo vượt định mức là 10 giờ chuẩn để bù cho 50 giờ chuẩn còn thiếu (Trường hợp có nhà giáo vượt định mức không đến 10 giờ chuẩn thì vẫn lấy bù hết số giờ chuẩn vượt định mức của nhà giáo đó, số giờ chuẩn cần bù định mức còn lại chia đều cho các nhà giáo có giờ chuẩn vượt định mức còn lại).  
4. Cách tính vượt định mức được xác định theo từng đơn vị làm công tác giảng dạy, cá nhân nhà giáo và theo năm học, cách thức áp dụng như sau:  
a) Cách tính vượt định mức đối với cá nhân nhà giáo  
- Căn cứ kết quả thực hiện định mức thời gian làm việc trong năm học và thực hiện bù định mức theo quy định (Nếu có), nhà giáo có số giờ quy đổi (Giờ chuẩn và giờ nghiên cứu khoa học) cao hơn định mức quy định được xác định là số giờ vượt định mức trong năm học của nhà giáo. Số giờ chuẩn vượt định mức của nhà giáo được sử dụng để bù cho số giờ chuẩn còn thiếu của nhà giáo khác trong cùng đơn vị giảng dạy chưa hoàn thành định mức (Nếu có).  
- Cách tính vượt định mức giờ chuẩn hoạt động giảng trên lớp của nhà giáo: Căn cứ kết quả thực hiện giờ chuẩn quy đổi từ hoạt động giảng trên lớp của nhà giáo và thực hiện bù định mức theo quy định và cách tính tại Khoản 2, 3 Điều này (Nếu có), số giờ chuẩn quy đổi từ hoạt động giảng trên lớp của nhà giáo cao hơn định mức giờ chuẩn hoạt động giảng trên lớp được xác định là số giờ chuẩn vượt định mức hoạt động giảng trên lớp của nhà giáo theo năm học.  
- Hiệu trưởng quyết định hình thức ghi nhận phù hợp đối với nhà giáo thực hiện vượt định mức.  
b) Cách tính vượt định mức đối với đơn vị làm công tác giảng dạy  
- Cách tính: Sau khi tính bù định mức giờ chuẩn của tất cả nhà giáo trong đơn vị (Nếu có), số giờ quy đổi (Giờ chuẩn, giờ nghiên cứu khoa học) còn lại của đơn vị cao hơn tổng định mức quy định của tất cả nhà giáo trong đơn vị là số giờ vượt định mức trong năm học của đơn vị làm công tác giảng dạy.  
- Số giờ chuẩn vượt định mức của từng nhà giáo theo đơn vị được sử dụng để thực hiện chế độ, chính sách cho nhà giáo theo quy định hiện hành của Bộ Công an.

## **Chương III**

TRÁCH NHIỆM CỦA TẬP THỂ, CÁ NHÂN  
TRONG QUẢN LÝ VÀ THỰC HIỆN CHẾ ĐỘ LÀM VIỆC

### **Điều 13. Trách nhiệm của Hiệu trưởng**

1. Chịu trách nhiệm trước Bộ trưởng Bộ Công an trong công tác chỉ đạo, quản lý, tổ chức thực hiện chế độ làm việc của nhà giáo ở Trường Đại học ANND theo đúng quy định của pháp luật.  
2. Kiểm tra, đôn đốc việc quản lý, thực hiện chế độ làm việc của nhà giáo ở Trường Đại học ANND.

### **Điều 14. Trách nhiệm của các đơn vị trong Trường**

1. Phòng Chính trị  
a) Tham mưu giúp Hiệu trưởng thống nhất quản lý, chỉ đạo thực hiện chế độ làm việc của nhà giáo ở các đơn vị trong toàn Trường theo đúng quy định của pháp luật và của Bộ Công an.  
b) Kiểm tra, đôn đốc việc quản lý, thực hiện chế độ của nhà giáo và báo cáo Ban Giám hiệu khi có yêu cầu.  
2. Phòng Quản lý đào tạo và bồi dưỡng nâng cao  
a) Chịu trách nhiệm thẩm định, xác định giờ giảng dạy cho nhà giáo của các đơn vị.  
b) Tổng hợp kết quả về định mức thời gian thực hiện nhiệm vụ của nhà giáo (Thuộc biên chế và thỉnh giảng) trong năm học để báo cáo Hiệu trưởng theo quy định.  
c) Chủ trì thực hiện nhiệm vụ chế độ thông tin báo cáo tại Điều 17 của Quy định này.  
3. Phòng Bảo đảm chất lượng đào tạo: Chịu trách nhiệm thẩm định, xác định việc quy đổi giờ chuẩn các hoạt động: Soạn đề thi, coi thi, chấm thi kết thúc học phần, môn học; soạn đề thi, coi thi, chấm thi tốt nghiệp; hướng dẫn chuyên đề, khóa luận, luận văn, đề án, luận án; chấm chuyên đề, khóa luận, luận văn, đề án; các hoạt động chuyên môn khác.  
4. Phòng Quản lý nghiên cứu khoa học: Chịu trách nhiệm thẩm định, xác nhận cho nhà giáo các đơn vị về quy đổi giờ chuẩn nghiên cứu khoa học đối với các hoạt động: Tham gia thành viên hội đồng khoa học; tổ chức hội thảo, tọa đàm khoa học; hướng dẫn, huấn luyện học viên nghiên cứu khoa học, tham gia các cuộc thi; các hoạt động, sản phẩm khoa học khác (Nếu có) bảo đảm theo quy định.  
5. Phòng Hậu cần: Chịu trách nhiệm hướng dẫn, thẩm định và thanh quyết toán các hồ sơ liên quan đến chế độ làm việc đối với nhà giáo giảng dạy (Nếu có).  
6. Trách nhiệm của các đơn vị giảng dạy và các đơn vị chức năng khác  
Thủ trưởng các đơn vị chịu trách nhiệm trước Hiệu trưởng về công tác quản lý và thực hiện chế độ làm việc của nhà giáo tại đơn vị mình quản lý; đồng thời, có trách nhiệm:  
a) Quản lý, bố trí và sử dụng có hiệu quả đội ngũ nhà giáo tại đơn vị; tạo điều kiện thuận lợi để đội ngũ nhà giáo thực hiện chế độ làm việc và hoàn thành nhiệm vụ được giao; phân công nhà giáo thực hiện không hết giờ định mức của nhiệm vụ khác làm nhiệm vụ giảng dạy hoặc nghiên cứu khoa học.  
b) Tổng hợp, báo cáo kết quả về định mức thời gian thực hiện các nhiệm vụ của nhà giáo (Thuộc biên chế và thỉnh giảng) trong năm học, gửi về Phòng Quản lý đào tạo và bồi dưỡng nâng cao để báo cáo Hiệu trưởng theo quy định.  
c) Quyết định hình thức khen thưởng, động viên phù hợp đối với nhà giáo thực hiện vượt định mức; hình thức xử lý đối với từng trường hợp nhà giáo không hoàn thành định mức thời gian làm việc theo quy định.

### **Điều 15. Trách nhiệm của nhà giáo**

1. Nhà giáo có trách nhiệm thực hiện bảo đảm định mức thời gian làm việc trong năm học được quy định tại Quy định này và nhiệm vụ do Ban Giám hiệu giao trong thời gian nghỉ của năm học.  
2. Nhà giáo công tác ở đơn vị có chức năng giảng dạy thực hiện quy định tại Khoản 1 Điều này; xây dựng kế hoạch thực hiện chế độ làm việc của cá nhân theo phân công thực tế hằng năm, báo cáo Thủ trưởng đơn vị phê duyệt để thực hiện; kịp thời báo cáo những khó khăn, vướng mắc trong thực hiện nhiệm vụ và đề xuất, kiến nghị để đảm bảo thực hiện hoàn thành nhiệm vụ (Nếu có).  
3. Nhà giáo công tác ở phòng, trung tâm thực hiện quy định tại khoản 1 Điều này; xây dựng kế hoạch thực hiện nhiệm vụ giảng dạy, sinh hoạt chuyên môn, nghiên cứu khoa học (Nếu thuộc đối tượng) và nhiệm vụ chuyên môn liên quan đến hoạt động giảng dạy theo phân công thực tế hằng năm của Thủ trưởng đơn vị làm công tác giảng dạy và Thủ trưởng đơn vị quản lý trực tiếp phê duyệt làm căn cứ thực hiện; kịp thời báo cáo những khó khăn, vướng mắc trong thực hiện nhiệm vụ và đề xuất, kiến nghị để đảm bảo thực hiện hoàn thành nhiệm vụ (Nếu có).

### **Điều 16. Trách nhiệm của các đơn vị, tổ chức, cá nhân có liên quan**

Các đơn vị, tổ chức, cá nhân có liên quan có trách nhiệm phối hợp trong công tác quản lý việc thực hiện quy định về chế độ làm việc của nhà giáo.

## **Chương IV**

ĐIỀU KHOẢN THI HÀNH

### **Điều 17. Chế độ thông tin báo cáo**

1. Trường Đại học ANND gửi về Bộ Công an (Qua Cục Đào tạo):  
a) Kế hoạch giảng dạy và học tập (Sau đây viết gọn là lịch giảng dạy) của các khóa học, chương trình và hình thức đào tạo: Chậm nhất sau 30 ngày tính từ ngày nhập học của học viên đối với lịch giảng dạy toàn khóa; trước ngày 31 tháng 8 hằng năm đối với lịch giảng dạy năm học;  
b) Kết quả thực hiện định mức giờ chuẩn, giờ nghiên cứu khoa học của nhà giáo (Thuộc biên chế và thỉnh giảng) và của đơn vị làm công tác giảng dạy trong năm học trước ngày 31 tháng 8 hằng năm.  
2. Việc báo cáo theo quy định tại khoản 1 Điều này thực hiện đến thời điểm sử dụng cơ sở dữ liệu dùng chung.

### **Điều 18. Hiệu lực thi hành**

1. Quy định này có hiệu lực thi hành kể từ ngày 05 tháng 01 năm 2026 (Theo hiệu lực của Thông tư số 108/2025/TT-BCA ngày 20 tháng 11 năm 2025 của Bộ trưởng Bộ Công an quy định chế độ làm việc đối với nhà giáo giảng dạy ở các học viện, trường Công an nhân dân) và áp dụng kể từ năm học 2025 - 2026.  
2. Nhà giáo thuộc đối tượng điều chỉnh tại Quy định này nhưng không thuộc đối tượng điều chỉnh tại Thông tư số 57/2010/TT-BCA ngày 14 tháng 12 năm 2010 của Bộ trưởng Bộ Công an quy định chế độ làm việc của các chức danh giảng dạy, huấn luyện trong các học viện, trường đại học, cao đẳng, trung cấp Công an nhân dân thì áp dụng chế độ làm việc với định mức tỉ lệ theo thời gian tính từ ngày Quy định này có hiệu lực thi hành.  
3. Nhà giáo thuộc đối tượng điều chỉnh tại Quy định này được công nhận Nhà giáo thỉnh giảng theo quy định tại Thông tư số 30/2022/TT-BCA ngày 02 tháng 8 năm 2022 của Bộ trưởng Bộ Công an quy định về Nhà giáo thỉnh giảng, Báo cáo viên tại các trường Công an nhân dân ở thời điểm trước khi Quy định này có hiệu lực thi hành thì Hiệu trưởng ban hành quyết định hủy bỏ công nhận Nhà giáo thỉnh giảng và áp dụng chế độ làm việc với định mức tỉ lệ theo thời gian tính từ ngày Quy định này có hiệu lực thi hành.  
4. Trường hợp các văn bản viện dẫn trong Quy định này được thay thế hoặc sửa đổi, bổ sung thì áp dụng theo văn bản thay thế hoặc sửa đổi, bổ sung.

### **Điều 19. Trách nhiệm thi hành**

1. Phòng Chính trị có trách nhiệm kiểm tra việc thực hiện Quy định này; chủ trì, phối hợp với Phòng Quản lý đào tạo và bồi dưỡng nâng cao theo dõi việc tổ chức thực hiện Quy định này.  
2. Phòng Quản lý đào tạo và bồi dưỡng nâng cao có trách nhiệm phổ biến, quán triệt Quy định này đến toàn thể cán bộ, nhà giáo và tổ chức thực hiện nghiêm túc Quy định này.  
3. Các đơn vị, tổ chức, cá nhân có liên quan có trách nhiệm thực hiện Quy định này.  
4. Trong quá trình tổ chức thực hiện Quy định này, nếu có khó khăn, vướng mắc, các đơn vị báo cáo về Ban Giám hiệu (Qua Phòng Chính trị) để nghiên cứu, giải quyết và có hướng dẫn kịp thời./.

---

## UI Research Session 2026-05-21 — Layout, Information Fields & Data Presentation

### Context
User reported "UI too confusing, navigation flow not clear." Our first pass analyzed navigation/sidebar. User clarified they meant **web layout, information fields, form design, visual hierarchy** — not sidebar routing. Three agents were launched to do deep-dive analysis and research.

### Architecture Overview
- **Stack:** Streamlit (Python), SQLite, custom MD3 CSS theme
- **Pages:** Home (app.py), Dashboard (1), Teacher Mgmt (2), Activity Log (3), Settings (4)
- **UI:** All custom HTML via `st.markdown(unsafe_allow_html=True)` — no external lib
- **Key components:** `render_sidebar()` in `components.py:113`, `render_metric_card()` in `components.py:72`, `render_list_item()` in `4_CaiDatHeThong.py:28`

---

### CRITICAL FIELD ISSUES (data integrity risk)

| # | Issue | File:Line | Severity | Details |
|---|-------|-----------|----------|---------|
| 1 | **Reduction % label contradicts example** | `4_CaiDatHeThong.py:262` | **CRITICAL** | Label: "Nhập % GIẢM TRỪ" — Example: "Hiệu trưởng chỉ phải làm 10% → nhập 90%". If label means "reduce by X%", 90% = do 10%. If example means "remaining X%", 90% = do 90%. Ambiguity will corrupt data. Fix: align label & example to one semantic (recommend: rename to `"% Định mức còn lại"` with example "nhập 10") |
| 2 | **Form field boundary broken** | `3_NhatKyHoatDong.py:26-43` | **HIGH** | Teacher/category/activity/date/timeframe selectors are OUTSIDE `st.form()`. Every category change triggers full page rerun, losing unsaved form input. Fix: move all selectors inside `st.form()` |
| 3 | **Start date defaults to today** | `2_QuanLyCanBo.py:35` | **HIGH** | "Ngày bắt đầu công tác" defaults to `date.today()`. For existing teachers being entered, today is almost always wrong. Silent data error. Fix: no default or default to academic year start |
| 4 | **Delete by raw DB ID** | `3_NhatKyHoatDong.py:155` | **HIGH** | `st.selectbox("Chọn ID nhật ký cần xoá", options=df_logs['id'].tolist())` User sees only numeric IDs [42,43,44...]. Must cross-reference history table. Fix: show `"ID {id}: {teacher} — {activity} ({date})"` |

---

### PAGE 1: Dashboard (`1_Dashboard.py`)

**Metric cards — layout imbalance**
- 5 cards in `st.columns(5)` (line 51). At 1366px laptop width, labels truncate. Labels inconsistent: `"Tổng số nhà giáo"` (7 chars) vs `"Kế hoạch khác (GC)"` (19 chars).
- Acronyms `GC`, `NVK` never explained on this page.
- **Fix:** Group 3+2 rows. Add tooltip/footnote explaining "GC = Giờ chuẩn".

**Conversion suggestions — O(n) scaling**
- `:76-161` — Per-teacher card loop. With 20+ teachers, user must vertically scan all cards to find who needs action.
- `st.warning()` boxes at `:151-156` look like errors but are informational.
- **Fix:** Group by deficiency type (thiếu GC / thiếu NCKH) in an expandable summary with count badges.

**Data table — column overload**
- `st.multiselect` at `:199` defaults to ALL 15+ columns. Horizontally scrolling table, information overload.
- Column names interleave full words and abbreviations: `'Vượt/Thiếu GD'` but `'Đã Giảng dạy (tổng GC)'`
- **Fix:** Default to 5-6 essential columns only. Set `height=400` on `st.dataframe` for virtual scrolling.

**Checkbox orphaned**
- `"Áp dụng Bù định mức Đơn vị"` at `:167` floats between conversion section and data table with no visual bonding to either.
- **Fix:** Move inside data table section heading or use `st.container(border=True)` to group with table.

---

### PAGE 2: Teacher Management (`2_QuanLyCanBo.py`)

**Nested expander hell — WORST LAYOUT OFFENSE**
```
Page
├── Expander: "Thêm mới Hồ sơ" (line 15)
├── Expander: "Xóa Hồ sơ (Khu vực Nguy hiểm)" (line 69) ← BEFORE teacher list!
├── Teacher List table (line 83)
├── Detail header + Status bar (line 110)
│   └── Expander: "Cập nhật Biến động & Xem Lịch sử" (line 170) ← 3rd level
│       ├── Action selectbox (line 172)
│       ├── Form for selected action (line 175-306)
│       │   └── Expander: "Chỉnh sửa số tuần" (line 253) ← 4TH LEVEL
│       ├── History table (line 319)
│       └── Expander: "Quản lý dòng lịch sử (Xóa lỗi)" (line 355)
```
- **Impact:** Timeline update is the #1 primary workflow, buried 3-4 clicks deep.
- **Fix:** Flatten to page-level sections with tabs or conditional rendering. Move history table outside expander.

**Delete positioning wrong**
- "Xóa Hồ sơ" expander at `:69` appears BEFORE teacher list at `:83`. Destructive action more visible than primary data.

**Add form field grouping**
- `col1=[Họ tên, Khối môn, Chức danh]`, `col2=[Giới tính, Đơn vị, Chức vụ, Ngày bắt đầu]`. Personal info and employment info mixed.
- **Fix:** Group as `col1=[Họ tên, Giới tính, Khối môn]` (personal), `col2=[Chức danh, Đơn vị, Chức vụ, Ngày bắt đầu]` (employment).

**Gender as selectbox** (`:30`): Binary choice using dropdown. Use `st.radio(["Nam", "Nữ"], horizontal=True)`.

**Internal IDs exposed** (`:72,93`): `"name (ID: X)"` shown to end users. Remove `(ID: X)`.

**Dummy option in action selectbox** (`:172`): `"-- Chọn thao tác --"` — Streamlit can't do placeholders. Use first valid action as default.

**History filter buried** (`:321`): Filter radio is inside the main expander. User can't glance at history without expanding first.

---

### PAGE 3: Activity Log (`3_NhatKyHoatDong.py`)

**Review of all field-level issues:**

| Line | Field | Problem | Fix |
|------|-------|---------|-----|
| 28-33 | Category → Activity chain | Triggers full rerun outside form | Move inside `st.form()` |
| 53 | "Số lượng gốc" label | "Gốc" ambiguous | `"Số lượng (đơn vị: {unit})"` |
| 83 | Student count max=200 | Lecture halls >200 truncated | Remove cap or set to 500 |
| 115 | Note field type | text_input for normal, text_area for freeform | Use text_area for both |
| 141-149 | History query | Omits class_type, nckh_level, is_main_author | Add to SELECT |
| 144 | Column "Timeframe" is English | Inconsistent with Vietnamese UI | Rename to "Năm học" |

---

### PAGE 4: System Settings (`4_CaiDatHeThong.py`)

**No Edit function** — Only Add and Delete. Data entry mistakes require full delete-and-recreate.

**Tab 4 (Chức vụ) and Tab 5 (Miễn giảm)** share same `reduction_rules` table (`rule_type='ROLE'/'SPECIAL'`). Architecturally correct but visually confusing because forms are identical.

**Title display overload** (`:244-254`): Pipe-separated inline values — equal visual weight, hard to scan. Use 3 chips or 3-column grid.

**Conversion rate default risk** (`:340`): Defaults to `1.0` with no hint. User may forget to set correct rate. Remove default, add help text.

**Activity type display** (`:362-376`): `is_teaching_activity` and `is_nckh_activity` booleans invisible in list. Add badge icons.

**Delete error handling** (`:20-27`): Generic `except Exception` shows raw SQL errors. Catch FK constraint violation → user-friendly message.

**Tab flatness**: 6 tabs is OK, but "Chức vụ" and "Miễn giảm" forms are identical (same fields, same table). Consider merging with a radio or adding visual distinction.

---

### PAGE 0: Home (`app.py`)

- **Hero section wall of text** (`:56-68`): Dense legal paragraph with no CTA. First-time users have no obvious next action.
- **4-step guide not actionable**: 👉 emoji text but no hyperlinks. Replace with `st.page_link` buttons.

---

### COMPONENTS (`components.py`)

- **`render_empty_state()`** (`:36-52`): Shows "Chưa có dữ liệu" icon but no CTA button. Add "Thêm ngay" button.
- **`render_metric_card()`** (`:72-94`): Custom HTML with shadow/elevation — heavy for 5 instances. Consider `st.container(border=True)` for lighter rendering.
- **CSS all inline** (`:124-372`): 250 lines of CSS injected on every page load. Extract to a shared `.css` file or load conditionally only once via `st.session_state`.

---

### Cross-Cutting Layout Principles (from Research)

| Principle | Current State | Target State |
|-----------|--------------|--------------|
| **Form field grouping** | Random column assignment | Logical groups: personal info → employment → role-specific details |
| **Visual hierarchy** | All sections equal weight | Primary workflows prominent, secondary in expanders, destructive at bottom |
| **Information density** | Flat cards for everything | Cards for KPIs, compact inline lists for config items, dataframes for tabular data |
| **State preservation** | Only `selected_tf_id` in session_state | Persist selected teacher, expander states, tab selection |
| **Empty states** | Icon + message | Icon + message + CTA button |
| **Error handling** | Generic `except` | Specific errors with actionable messages |
| **Edit capability** | None | Add inline edit on list items (or `@st.dialog` for modals) |

### Best Practice: Column Width Decision Matrix (from Research)

| Fields per section | Columns | When |
|---|---|---|
| 1-3 | 1-col | Sequential fields (name → date → type) |
| 4-8 | 2-col | **Most data entry forms** — balance density vs readability |
| 8+ | 2-col + groups | Break into `st.container(border=True)` groups |

### Best Practice: Visual Zone Pattern

| Zone | Visual Treatment | Pages affected |
|------|-----------------|----------------|
| **View/Monitor** | Default styling, tables, metric cards | Dashboard, Home |
| **Add/Edit** | Primary border-left + container border | Teacher, Activity, Settings |
| **Delete** | Red accent + confirmation checkbox | Teacher, Activity, Settings |

### Top 12 Action Items (Ranked by Impact)

| # | Priority | Action | File | Effort |
|---|----------|--------|------|--------|
| 1 | **CRITICAL** | Fix reduction % label/example contradiction | `4_CaiDatHeThong.py:262` | 2 min |
| 2 | HIGH | Flatten nested expanders (move timeline to top level) | `2_QuanLyCanBo.py:170-376` | 2h |
| 3 | HIGH | Fix form boundary (move selectors INTO form) | `3_NhatKyHoatDong.py:26-43` | 30 min |
| 4 | HIGH | Default to 5-6 essential columns in dashboard table | `1_Dashboard.py:199` | 5 min |
| 5 | HIGH | Move "Xóa Hồ sơ" expander after teacher list | `2_QuanLyCanBo.py:69` | 5 min |
| 6 | HIGH | Show descriptive labels in delete dropdown | `3_NhatKyHoatDong.py:155` | 5 min |
| 7 | MED | Group metric cards 3+2 instead of 5-wide | `1_Dashboard.py:51` | 5 min |
ĐIỀU KHOẢN THI HÀNH

### **Điều 17. Chế độ thông tin báo cáo**

1. Trường Đại học ANND gửi về Bộ Công an (Qua Cục Đào tạo):  
a) Kế hoạch giảng dạy và học tập (Sau đây viết gọn là lịch giảng dạy) của các khóa học, chương trình và hình thức đào tạo: Chậm nhất sau 30 ngày tính từ ngày nhập học của học viên đối với lịch giảng dạy toàn khóa; trước ngày 31 tháng 8 hằng năm đối với lịch giảng dạy năm học;  
b) Kết quả thực hiện định mức giờ chuẩn, giờ nghiên cứu khoa học của nhà giáo (Thuộc biên chế và thỉnh giảng) và của đơn vị làm công tác giảng dạy trong năm học trước ngày 31 tháng 8 hằng năm.  
2. Việc báo cáo theo quy định tại khoản 1 Điều này thực hiện đến thời điểm sử dụng cơ sở dữ liệu dùng chung.

### **Điều 18. Hiệu lực thi hành**

1. Quy định này có hiệu lực thi hành kể từ ngày 05 tháng 01 năm 2026 (Theo hiệu lực của Thông tư số 108/2025/TT-BCA ngày 20 tháng 11 năm 2025 của Bộ trưởng Bộ Công an quy định chế độ làm việc đối với nhà giáo giảng dạy ở các học viện, trường Công an nhân dân) và áp dụng kể từ năm học 2025 - 2026.  
2. Nhà giáo thuộc đối tượng điều chỉnh tại Quy định này nhưng không thuộc đối tượng điều chỉnh tại Thông tư số 57/2010/TT-BCA ngày 14 tháng 12 năm 2010 của Bộ trưởng Bộ Công an quy định chế độ làm việc của các chức danh giảng dạy, huấn luyện trong các học viện, trường đại học, cao đẳng, trung cấp Công an nhân dân thì áp dụng chế độ làm việc với định mức tỉ lệ theo thời gian tính từ ngày Quy định này có hiệu lực thi hành.  
3. Nhà giáo thuộc đối tượng điều chỉnh tại Quy định này được công nhận Nhà giáo thỉnh giảng theo quy định tại Thông tư số 30/2022/TT-BCA ngày 02 tháng 8 năm 2022 của Bộ trưởng Bộ Công an quy định về Nhà giáo thỉnh giảng, Báo cáo viên tại các trường Công an nhân dân ở thời điểm trước khi Quy định này có hiệu lực thi hành thì Hiệu trưởng ban hành quyết định hủy bỏ công nhận Nhà giáo thỉnh giảng và áp dụng chế độ làm việc với định mức tỉ lệ theo thời gian tính từ ngày Quy định này có hiệu lực thi hành.  
4. Trường hợp các văn bản viện dẫn trong Quy định này được thay thế hoặc sửa đổi, bổ sung thì áp dụng theo văn bản thay thế hoặc sửa đổi, bổ sung.

### **Điều 19. Trách nhiệm thi hành**

1. Phòng Chính trị có trách nhiệm kiểm tra việc thực hiện Quy định này; chủ trì, phối hợp với Phòng Quản lý đào tạo và bồi dưỡng nâng cao theo dõi việc tổ chức thực hiện Quy định này.  
2. Phòng Quản lý đào tạo và bồi dưỡng nâng cao có trách nhiệm phổ biến, quán triệt Quy định này đến toàn thể cán bộ, nhà giáo và tổ chức thực hiện nghiêm túc Quy định này.  
3. Các đơn vị, tổ chức, cá nhân có liên quan có trách nhiệm thực hiện Quy định này.  
4. Trong quá trình tổ chức thực hiện Quy định này, nếu có khó khăn, vướng mắc, các đơn vị báo cáo về Ban Giám hiệu (Qua Phòng Chính trị) để nghiên cứu, giải quyết và có hướng dẫn kịp thời./.

---

## UI Research Session 2026-05-21 — Layout, Information Fields & Data Presentation

### Context
User reported "UI too confusing, navigation flow not clear." Our first pass analyzed navigation/sidebar. User clarified they meant **web layout, information fields, form design, visual hierarchy** — not sidebar routing. Three agents were launched to do deep-dive analysis and research.

### Architecture Overview
- **Stack:** Streamlit (Python), SQLite, custom MD3 CSS theme
- **Pages:** Home (app.py), Dashboard (1), Teacher Mgmt (2), Activity Log (3), Settings (4)
- **UI:** All custom HTML via `st.markdown(unsafe_allow_html=True)` — no external lib
- **Key components:** `render_sidebar()` in `components.py:113`, `render_metric_card()` in `components.py:72`, `render_list_item()` in `4_CaiDatHeThong.py:28`

---

### CRITICAL FIELD ISSUES (data integrity risk)

| # | Issue | File:Line | Severity | Details |
|---|-------|-----------|----------|---------|
| 1 | **Reduction % label contradicts example** | `4_CaiDatHeThong.py:262` | **CRITICAL** | Label: "Nhập % GIẢM TRỪ" — Example: "Hiệu trưởng chỉ phải làm 10% → nhập 90%". If label means "reduce by X%", 90% = do 10%. If example means "remaining X%", 90% = do 90%. Ambiguity will corrupt data. Fix: align label & example to one semantic (recommend: rename to `"% Định mức còn lại"` with example "nhập 10") |
| 2 | **Form field boundary broken** | `3_NhatKyHoatDong.py:26-43` | **HIGH** | Teacher/category/activity/date/timeframe selectors are OUTSIDE `st.form()`. Every category change triggers full page rerun, losing unsaved form input. Fix: move all selectors inside `st.form()` |
| 3 | **Start date defaults to today** | `2_QuanLyCanBo.py:35` | **HIGH** | "Ngày bắt đầu công tác" defaults to `date.today()`. For existing teachers being entered, today is almost always wrong. Silent data error. Fix: no default or default to academic year start |
| 4 | **Delete by raw DB ID** | `3_NhatKyHoatDong.py:155` | **HIGH** | `st.selectbox("Chọn ID nhật ký cần xoá", options=df_logs['id'].tolist())` User sees only numeric IDs [42,43,44...]. Must cross-reference history table. Fix: show `"ID {id}: {teacher} — {activity} ({date})"` |

---

### PAGE 1: Dashboard (`1_Dashboard.py`)

**Metric cards — layout imbalance**
- 5 cards in `st.columns(5)` (line 51). At 1366px laptop width, labels truncate. Labels inconsistent: `"Tổng số nhà giáo"` (7 chars) vs `"Kế hoạch khác (GC)"` (19 chars).
- Acronyms `GC`, `NVK` never explained on this page.
- **Fix:** Group 3+2 rows. Add tooltip/footnote explaining "GC = Giờ chuẩn".

**Conversion suggestions — O(n) scaling**
- `:76-161` — Per-teacher card loop. With 20+ teachers, user must vertically scan all cards to find who needs action.
- `st.warning()` boxes at `:151-156` look like errors but are informational.
- **Fix:** Group by deficiency type (thiếu GC / thiếu NCKH) in an expandable summary with count badges.

**Data table — column overload**
- `st.multiselect` at `:199` defaults to ALL 15+ columns. Horizontally scrolling table, information overload.
- Column names interleave full words and abbreviations: `'Vượt/Thiếu GD'` but `'Đã Giảng dạy (tổng GC)'`
- **Fix:** Default to 5-6 essential columns only. Set `height=400` on `st.dataframe` for virtual scrolling.

**Checkbox orphaned**
- `"Áp dụng Bù định mức Đơn vị"` at `:167` floats between conversion section and data table with no visual bonding to either.
- **Fix:** Move inside data table section heading or use `st.container(border=True)` to group with table.

---

### PAGE 2: Teacher Management (`2_QuanLyCanBo.py`)

**Nested expander hell — WORST LAYOUT OFFENSE**
```
Page
├── Expander: "Thêm mới Hồ sơ" (line 15)
├── Expander: "Xóa Hồ sơ (Khu vực Nguy hiểm)" (line 69) ← BEFORE teacher list!
├── Teacher List table (line 83)
├── Detail header + Status bar (line 110)
│   └── Expander: "Cập nhật Biến động & Xem Lịch sử" (line 170) ← 3rd level
│       ├── Action selectbox (line 172)
│       ├── Form for selected action (line 175-306)
│       │   └── Expander: "Chỉnh sửa số tuần" (line 253) ← 4TH LEVEL
│       ├── History table (line 319)
│       └── Expander: "Quản lý dòng lịch sử (Xóa lỗi)" (line 355)
```
- **Impact:** Timeline update is the #1 primary workflow, buried 3-4 clicks deep.
- **Fix:** Flatten to page-level sections with tabs or conditional rendering. Move history table outside expander.

**Delete positioning wrong**
- "Xóa Hồ sơ" expander at `:69` appears BEFORE teacher list at `:83`. Destructive action more visible than primary data.

**Add form field grouping**
- `col1=[Họ tên, Khối môn, Chức danh]`, `col2=[Giới tính, Đơn vị, Chức vụ, Ngày bắt đầu]`. Personal info and employment info mixed.
- **Fix:** Group as `col1=[Họ tên, Giới tính, Khối môn]` (personal), `col2=[Chức danh, Đơn vị, Chức vụ, Ngày bắt đầu]` (employment).

**Gender as selectbox** (`:30`): Binary choice using dropdown. Use `st.radio(["Nam", "Nữ"], horizontal=True)`.

**Internal IDs exposed** (`:72,93`): `"name (ID: X)"` shown to end users. Remove `(ID: X)`.

**Dummy option in action selectbox** (`:172`): `"-- Chọn thao tác --"` — Streamlit can't do placeholders. Use first valid action as default.

**History filter buried** (`:321`): Filter radio is inside the main expander. User can't glance at history without expanding first.

---

### PAGE 3: Activity Log (`3_NhatKyHoatDong.py`)

**Review of all field-level issues:**

| Line | Field | Problem | Fix |
|------|-------|---------|-----|
| 28-33 | Category → Activity chain | Triggers full rerun outside form | Move inside `st.form()` |
| 53 | "Số lượng gốc" label | "Gốc" ambiguous | `"Số lượng (đơn vị: {unit})"` |
| 83 | Student count max=200 | Lecture halls >200 truncated | Remove cap or set to 500 |
| 115 | Note field type | text_input for normal, text_area for freeform | Use text_area for both |
| 141-149 | History query | Omits class_type, nckh_level, is_main_author | Add to SELECT |
| 144 | Column "Timeframe" is English | Inconsistent with Vietnamese UI | Rename to "Năm học" |

---

### PAGE 4: System Settings (`4_CaiDatHeThong.py`)

**No Edit function** — Only Add and Delete. Data entry mistakes require full delete-and-recreate.

**Tab 4 (Chức vụ) and Tab 5 (Miễn giảm)** share same `reduction_rules` table (`rule_type='ROLE'/'SPECIAL'`). Architecturally correct but visually confusing because forms are identical.

**Title display overload** (`:244-254`): Pipe-separated inline values — equal visual weight, hard to scan. Use 3 chips or 3-column grid.

**Conversion rate default risk** (`:340`): Defaults to `1.0` with no hint. User may forget to set correct rate. Remove default, add help text.

**Activity type display** (`:362-376`): `is_teaching_activity` and `is_nckh_activity` booleans invisible in list. Add badge icons.

**Delete error handling** (`:20-27`): Generic `except Exception` shows raw SQL errors. Catch FK constraint violation → user-friendly message.

**Tab flatness**: 6 tabs is OK, but "Chức vụ" and "Miễn giảm" forms are identical (same fields, same table). Consider merging with a radio or adding visual distinction.

---

### PAGE 0: Home (`app.py`)

- **Hero section wall of text** (`:56-68`): Dense legal paragraph with no CTA. First-time users have no obvious next action.
- **4-step guide not actionable**: 👉 emoji text but no hyperlinks. Replace with `st.page_link` buttons.

---

### COMPONENTS (`components.py`)

- **`render_empty_state()`** (`:36-52`): Shows "Chưa có dữ liệu" icon but no CTA button. Add "Thêm ngay" button.
- **`render_metric_card()`** (`:72-94`): Custom HTML with shadow/elevation — heavy for 5 instances. Consider `st.container(border=True)` for lighter rendering.
- **CSS all inline** (`:124-372`): 250 lines of CSS injected on every page load. Extract to a shared `.css` file or load conditionally only once via `st.session_state`.

---

### Cross-Cutting Layout Principles (from Research)

| Principle | Current State | Target State |
|-----------|--------------|--------------|
| **Form field grouping** | Random column assignment | Logical groups: personal info → employment → role-specific details |
| **Visual hierarchy** | All sections equal weight | Primary workflows prominent, secondary in expanders, destructive at bottom |
| **Information density** | Flat cards for everything | Cards for KPIs, compact inline lists for config items, dataframes for tabular data |
| **State preservation** | Only `selected_tf_id` in session_state | Persist selected teacher, expander states, tab selection |
| **Empty states** | Icon + message | Icon + message + CTA button |
| **Error handling** | Generic `except` | Specific errors with actionable messages |
| **Edit capability** | None | Add inline edit on list items (or `@st.dialog` for modals) |

### Best Practice: Column Width Decision Matrix (from Research)

| Fields per section | Columns | When |
|---|---|---|
| 1-3 | 1-col | Sequential fields (name → date → type) |
| 4-8 | 2-col | **Most data entry forms** — balance density vs readability |
| 8+ | 2-col + groups | Break into `st.container(border=True)` groups |

### Best Practice: Visual Zone Pattern

| Zone | Visual Treatment | Pages affected |
|------|-----------------|----------------|
| **View/Monitor** | Default styling, tables, metric cards | Dashboard, Home |
| **Add/Edit** | Primary border-left + container border | Teacher, Activity, Settings |
| **Delete** | Red accent + confirmation checkbox | Teacher, Activity, Settings |

### Top 12 Action Items (Ranked by Impact)

| # | Priority | Action | File | Effort |
|---|----------|--------|------|--------|
| 1 | **CRITICAL** | Fix reduction % label/example contradiction | `4_CaiDatHeThong.py:262` | 2 min |
| 2 | HIGH | Flatten nested expanders (move timeline to top level) | `2_QuanLyCanBo.py:170-376` | 2h |
| 3 | HIGH | Fix form boundary (move selectors INTO form) | `3_NhatKyHoatDong.py:26-43` | 30 min |
| 4 | HIGH | Default to 5-6 essential columns in dashboard table | `1_Dashboard.py:199` | 5 min |
| 5 | HIGH | Move "Xóa Hồ sơ" expander after teacher list | `2_QuanLyCanBo.py:69` | 5 min |
| 6 | HIGH | Show descriptive labels in delete dropdown | `3_NhatKyHoatDong.py:155` | 5 min |
| 7 | MED | Group metric cards 3+2 instead of 5-wide | `1_Dashboard.py:51` | 5 min |
| 8 | MED | Gender as radio instead of selectbox | `2_QuanLyCanBo.py:30` | 2 min |
| 9 | MED | Remove internal IDs from user-facing labels | `2_QuanLyCanBo.py:72,93` | 5 min |
| 10 | MED | Group conversion suggestions (not per-teacher cards) | `1_Dashboard.py:76-161` | 1h |
| 11 | MED | Set `height=400` on all `st.dataframe` for virtual scroll | All pages | 5 min |
| 12 | LOW | Add search/filter above data tables | All pages | 10 min each |

---

## UI/UX Refinement Session 2026-05-21 (17:45 ICT) — System-wide Refinements Completed

### Overview of Reforms & Refinements
To make the T04 quota management application highly usable for non-technical police university staff (30-40 yo), we completed massive reforms across all forms, selectors, layout wrappers, and deletion confirmation flows.

### Reforms Implemented

#### 1. Visual Aesthetics & Styling (`src/components.py`)
- Enlarged form labels from `12px uppercase` to standard sentence-case `14px` with a semi-bold weight (`font-weight: 600`) to maximize legibility.
- Redesigned status badges/chips with increased padding (`5px 14px`) and standard `12px` font size.
- Introduced explicit `.btn-danger` classes to highlight unsafe deletion triggers.
- Streamlined sidebar text: "v2.0 — Hệ thống định mức T04".

#### 2. Welcome Page (`src/app.py`)
- Removed technical legal jargon like "Điều 12 Quy định T04" and "Timeframe", replacing them with plain Vietnamese terms such as "Quy định bù trừ giờ chuẩn" and "Năm học".

#### 3. Dashboard Page (`src/pages/1_Dashboard.py`)
- Prominently positioned the academic year selector at the very top of the page.
- Pruned active columns in the main datagrid down to 7 core items to eliminate annoying horizontal scrolling.
- Replaced shorthand acronyms (e.g., "GC", "NCKH") with clear, full terms like "Giờ giảng" and "Giờ NCKH".

#### 4. Teacher Management (`src/pages/2_QuanLyCanBo.py`)
- Stripped raw database IDs `(ID: X)` from teacher search options.
- De-cluttered layout by replacing heavily nested expanders with flat high-level tabs (`st.tabs`).
- Displayed active teacher roles/exemptions dynamically as chips in the profile status bar.
- Implemented a red-accented banner warning and a manual approval checkbox step to safeguard against accidental profile deletions.

#### 5. Activity Log Entry Flow (`src/pages/3_NhatKyHoatDong.py`)
- Combined Category and Activity selections into a single unified dropdown with prefix tags (e.g., `[Giảng dạy] Giảng bài lý thuyết...`).
- Auto-determined academic year ("Năm học") from "Ngày thực hiện" (date input), moving manual overrides into a collapsed "Cấu hình nâng cao" expander.
- Set sensible defaults for teaching logs (undergraduate class, theory type, 40 students) and tucked them away inside a collapsed "Chi tiết Lớp học" expander.
- Combined separate NCKH author checkboxes and level dropdowns into simple unified selections.
- Integrated a secure 2-step deletion pattern using local session state flags (`confirm_del_log_{id}`).
- Exposed estimated standard hours directly inside the log history datagrid.

#### 6. System Settings (`src/pages/4_CaiDatHeThong.py`)
- Updated ambiguous percentages descriptions to "% Giờ chuẩn phải hoàn thành".
- Swapped separate boolean checkboxes for clean, exclusive radio button selections.
- Applied the standard session-state-based 2-step confirmation warning to all table record deletions.

### Verification Status
- Verified syntax validity: successfully compiled all files using `python -m py_compile`.
- Tested the simplified activity creation flow, verifying that default values are assumed automatically, and that date calculations successfully resolve active timeframe limits.
- Ran all compliance unit and integration tests (`test_logic.py`, `test_auto_capping.py`, `qa_tests.py`, and `test_compliance.py`), resolving floating-point precision discrepancies in the test assertion suites. 100% of tests are passing successfully.

---

## Phase 6 Research & Brainstorming (2026-05-21)

### 1. Bulk Data Import Brainstorm
- **Goal**: Allow low-tech administrative staff to import teacher rosters and activity logs in bulk from Excel (.xlsx) files.
- **Key Flow**:
  1. Download Excel template with data validation constraints built-in (dropdowns for categories, roles, depts).
  2. Upload via `st.file_uploader` and parse via `pandas` (requires `openpyxl`).
  3. Validate rows in a dry run, highlighting errors in Vietnamese on `st.data_editor` (e.g. invalid dates, duplicate records, unresolvable teacher names).
  4. Perform bulk insert inside an atomic SQL transaction (`BEGIN`/`COMMIT`) to ensure all-or-nothing consistency.

### 2. Success/Fail Popup & Interaction Feedback Research
- **Problem**: Current actions lack explicit confirmations. Low-tech users can be confused by silent changes or rapid page updates.
- **Recommended Feedback Patterns**:
  - **Form Submissions**: Show persistent `st.success("✅ Đã lưu thành công!")` or `st.error()` callouts immediately adjacent to the submit button.
  - **Dangerous/Destructive Actions**: Implement `@st.dialog` modal overlays to block the screen and force explicit confirmation (e.g. clicking a red confirm button or typing "XOA").
  - **Error Safety**: Catch database errors (`sqlite3.IntegrityError`) and translate technical jargon into plain Vietnamese (e.g., "Không thể xóa: Cán bộ đang có lịch sử giảng dạy").

