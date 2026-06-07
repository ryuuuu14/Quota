# Bộ nhớ dùng chung (Swarm Shared Memory Log)

File này đóng vai trò là bộ nhớ lưu trữ ngữ cảnh (context), lịch sử lỗi, quyết định thiết kế và kiến trúc của dự án.

---

## 1. Lịch sử Sửa lỗi & Debug (Debug & Bug History)

### Debug Session (2026-05-20)
*   **BUG 1 — DB_PATH Mismatch (FIXED):** `app.py` mặc định dùng `src/database.sqlite` trong khi dữ liệu seed nằm ở `data/database.sqlite`. Đã sửa để mặc định dùng `data/database.sqlite` (xác định tuyệt đối từ vị trí `database.py`).
*   **BUG 2 — Thiếu "Nhiệm vụ khác" (NVK) trong tính toán (FIXED):** Đã bổ sung nhóm category `Nhiệm vụ khác` và `Bồi dưỡng` vào tính toán GC theo Điều 9.
*   **BUG 3 — `converted_hours` lưu là 0.0 (BY DESIGN):** Hours được tính động tại thời điểm query thay vì lưu cứng.

### Streamlit Page Reload & HTML Metric Cards (2026-05-21)
*   **404 Route errors:** Lỗi Streamlit router khi truy cập trực tiếp subpages (ví dụ `/Dashboard`). Đây là hành vi mặc định của Streamlit 1.32.2, tự động fallback về root path, không ảnh hưởng hệ thống.
*   **Raw HTML rendering:** Do thụt lề (indentation) trong f-string HTML template của `render_metric_card` dẫn đến markdown parser hiểu nhầm là code block. Đã xóa thụt lề để render HTML chuẩn.

### Critical Math Audit & Bug Fixes in calculations.py (2026-05-22)
*   **Bug 1 — Quota Assignment (Điều 10.3.đ):** Reductions được tính nhưng không trừ vào quota. Đã sửa: `dinh_muc_gc_phai_thuc_hien = max(0.0, total_required_gc - total_reduced_gc)`.
*   **Bug 2 — Additive Stacking of Partial Reductions (Điều 10.1.c):** Các trường hợp giảm định mức một phần (15%, 20%, 30%) bị cộng dồn đè lên nhau bằng `+=`. Đã sửa dùng interval-merging logic với `max()` cho các khoảng thời gian trùng nhau.
*   **Bug 3 — Foreign Language Multiplier (Điều 8.1.g):** Multiplier giảng dạy bằng tiếng nước ngoài bị nhân dồn trên multiplier số học viên. Đã sửa: flag tiếng nước ngoài ghi đè hoàn toàn multiplier thành hệ số cố định 1.5 / 1.7 / 2.0.
*   **Bug 4 — NCKH Reduction Logic:** NCKH reductions (như thai sản 60%) bị chia tỉ lệ theo phân đoạn thời gian. Đã sửa thành flat reduction theo năm học.

### UI & Bug Fixes (2026-06-04)
*   Sửa lỗi `NameError: name 'base_salary' is not defined` trong `2_QuanLyCanBo.py` khi non-admin xem profile.
*   Sửa lỗi `NameError: name 'tab_new' is not defined` trong `3_NhatKyHoatDong.py` khi render view của khách.

---

## 2. Kiến trúc & Thiết kế Hệ thống (System Architecture & Design)

### Kiến trúc Tính toán Định mức (Gross vs Net Norm)
*   **Layer 1 (Gross Norm):** Định mức thô = `Σ(base_gc * role_retention% * weeks_in_role/44)`.
*   **Layer 2 (Net Obligation):** Định mức thực tế phải hoàn thành = `Gross Norm - Σ(special_reductions)` (leaves, thai sản, đi học...).
*   **Surplus/Deficit:** `tổng_đã_thực_hiện - Net Obligation`.

### Quy tắc Trùng lặp (Overlap Rules)
*   **Point 2 leaves (Miễn giảm 100%):** Dùng interval-merge với `max()`.
*   **Point 3 leaves (Miễn giảm một phần):** Dùng interval-merge với `max()`.
*   **Cross-point overlap:** Nếu Point 2 và Point 3 trùng nhau, Point 2 (100%) ưu tiên cao hơn.
*   **Kiêm nhiệm nhiều chức vụ:** Áp dụng định mức thấp nhất (Điều 3.4).

### Quy định Chế độ làm việc đối với Nhà giáo (TT108)
*   Toàn văn quy định được lưu trữ tại file riêng: [Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md](file:///f:/annd/Quota/Quy%20định%20chế%20độ%20làm%20việc%20đối%20với%20nhà%20giáo%20(Bản%20chuẩn%20toàn%20văn).md).

### Pipeline chạy thử nghiệm & Tự động hóa
*   **Design Pipeline (`src/pipeline.py`):** Editor -> Validator -> Critic -> Router (Loop).
*   **Debug Pipeline (`src/debug_pipeline.py`):** Sandbox Runner (Playwright) -> Telemetry Critic -> Router.
*   **Stitch Tool Adapter (`src/stitch_tool_adapter.py`):** Cache kết quả từ Stitch MCP tool.

---

## 3. Lịch sử Nâng cấp Tính năng & Cấu trúc Dữ liệu (Features & Evolution)

### UI/UX Refinement Session (2026-05-21)
*   Tăng font label lên `14px (font-weight: 600)`, thiết kế lại status badges/chips với padding `5px 14px`.
*   Thay thế expander lồng nhau bằng `st.tabs` phẳng tại trang Quản lý cán bộ.
*   Thiết lập luồng xác nhận xóa 2 bước qua session state tránh xóa nhầm dữ liệu.

### Chuyển đổi luồng Excel Bulk Import (2026-05-23)
*   Chuyển dịch từ nhập lẻ từng hoạt động sang nhập tổng số cuối năm qua Excel. File Excel là source of truth; SQLite đóng vai trò cache làm việc.
*   Thêm bảng `session_teacher_totals` chứa dữ liệu upload tạm thời:
    ```sql
    CREATE TABLE session_teacher_totals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        gc_total REAL NOT NULL DEFAULT 0,
        nckh_total REAL NOT NULL DEFAULT 0,
        nvk_total REAL NOT NULL DEFAULT 0,
        UNIQUE(timeframe_id, teacher_id)
    );
    ```
*   Khóa chức năng nhập lẻ tại `3_NhatKyHoatDong.py` sau khi đã import dữ liệu Excel cho năm học tương ứng.
*   Tích hợp LangGraph Validator (`validator_graph.py`) để xác thực file Excel (kiểm tra tên giáo viên, tính hợp lệ của số liệu, trùng lặp).

### Cổng Đăng nhập Tập trung & Phân quyền (2026-06-03 & 2026-06-04)
*   **Cổng đăng nhập tập trung (`8_DangNhap.py`):** Xác thực admin/head_of_dept. Lưu trạng thái admin qua `st.session_state["is_admin"]`. Các trang quản trị thực hiện check quyền và hiển thị link điều hướng về trang đăng nhập nếu chưa authenticate.
*   **Phân quyền chi tiết (RBAC):**
    *   **Admin:** Toàn quyền quản trị, duyệt các thay đổi.
    *   **Heads of Departments (Trưởng khoa):** Thao tác chỉnh sửa/thêm mới/xóa sẽ được chuyển thành `change_requests` (Yêu cầu thay đổi) lưu trong DB chờ Admin phê duyệt thay vì ghi đè trực tiếp.
    *   **Guest / Teacher:** View-only (Read-only), ẩn hoặc vô hiệu hóa các nút ghi dữ liệu.
*   **Mã xác thực khoa (Department Verification Code):** Khi import Excel, Trưởng khoa phải nhập mã xác thực riêng (ví dụ: `1111` khoa Tự nhiên, `2222` khoa Thực hành) để tránh sửa chéo dữ liệu của khoa khác.

---

## 4. Tài khoản Kiểm thử (Test Credentials)

*   **System Admin:** `admin` / `admin123`
*   **Head of Dept (Tự nhiên, Kỹ thuật...):** `head_tunhien` / `head123` (Mã xác thực: `1111`)
*   **Head of Dept (Thực hành):** `head_thuchanh` / `head123` (Mã xác thực: `2222`)
*   **Head of Dept (Chính trị, Pháp luật...):** `head_chinhtri` / `head123` (Mã xác thực: `3333`)
*   **Head of Dept (Phòng, trung tâm):** `head_phong` / `head123` (Mã xác thực: `4444`)

---

## 5. Lệnh vận hành Dự án (Operational Commands)

```bash
# Chạy ứng dụng Streamlit
streamlit run src/app.py

# Chạy test suite (unit tests & integration tests)
pytest src/test_compliance.py src/test_teacher_integration.py src/test_approval_flow.py

# Seed lại cơ sở dữ liệu
python src/seed_full.py
```
