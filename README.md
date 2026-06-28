# Hệ Thống Quản lý Chế độ làm việc - Đại học An ninh nhân dân

Ứng dụng quản lý định mức giờ chuẩn giảng dạy, giờ nghiên cứu khoa học (NCKH) và tổng hợp thống kê cho nhà giáo tại **Đại học An ninh nhân dân** theo **Quy định T04** và chế độ chi hoạt động giáo dục theo **Thông tư 11/2026/TT-BCA**.

---

## 1. Tính năng cốt lõi
* **Tính toán tự động**: Tự động phân bổ định mức giảng dạy & NCKH theo số tuần/ngày làm việc thực tế (trừ ngày lễ, Tết, hè) theo Điều 10.1.b.
* **Quy đổi & Bù trừ linh hoạt**: Hỗ trợ quy đổi tự động/thủ công giữa giờ giảng và giờ NCKH theo tỷ lệ quy định tại Điều 12 (1 GC = 3 giờ NCKH).
* **Miễn giảm tự động**: Tự động giảm trừ định mức khi có các sự kiện đặc biệt (nuôi con nhỏ, đi học tập trung, thai sản, làm lãnh đạo kiêm nhiệm).
* **Phê duyệt phân quyền**: Hỗ trợ Trưởng bộ môn khai báo/import và Quản trị viên duyệt dữ liệu.

---

## 2. Các quy định và logic nghiệp vụ
* Tra cứu chi tiết quy tắc tính toán định mức và quy đổi giờ tại: [Quy tắc Logic T04 (rules_logic.md)](./rules_logic.md).
* Tra cứu toàn văn văn bản gốc tại:
  * [Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md](./Quy%20định%20chế%20độ%20làm%20việc%20đối%20với%20nhà%20giáo%20\(Bản%20chuẩn%20toàn%20văn\).md)
  * [Thông tư 11_2026_TT-BCA - Chế độ chi hoạt động giáo dục, đào tạo CAND.md](./Thông%20tư%2011_2026_TT-BCA%20-%20Chế%20độ%20chi%20hoạt%20động%20giáo%20dục,%20đào%20tạo%20CAND.md)

---

## 3. Hướng dẫn khởi chạy ứng dụng (Unified Launchers)

Ứng dụng hỗ trợ hai kịch bản khởi chạy đồng nhất giúp tự động cài đặt và kiểm tra môi trường:

### Cách 1: Chạy trên Windows (Khuyên dùng)
Double-click trực tiếp vào file `App.bat` ở thư mục gốc hoặc chạy lệnh sau trong cmd/PowerShell:
```cmd
App.bat
```

### Cách 2: Chạy trên Linux / macOS
Cấp quyền thực thi và chạy file `App.sh` ở thư mục gốc:
```bash
chmod +x App.sh
./App.sh
```

### Các bước xác thực tự động của launcher:
1. **Kiểm tra môi trường Python**: Tự động dò tìm phiên bản Python khả dụng ($\ge$ 3.8).
2. **Kiểm tra Thư viện phụ thuộc**: Kiểm tra và hiển thị trạng thái của từng thư viện (`streamlit`, `pandas`, `openpyxl`, `bcrypt`, `st-aggrid`, v.v.).
3. **Kiểm tra Cổng mạng**: Đảm bảo cổng chạy mặc định `8501` đang rảnh.
4. **Khởi tạo và Seed cơ sở dữ liệu**: Tự động tạo cơ sở dữ liệu `data/database.sqlite` và chạy seed dữ liệu chuẩn nếu phát hiện CSDL trống.
5. **Khởi chạy máy chủ**: Mở trình duyệt tại địa chỉ 👉 **http://localhost:8501**.

---

## 4. Tài khoản Đăng nhập Mặc định
Sau khi chạy seed dữ liệu lần đầu, bạn có thể đăng nhập bằng tài khoản quản trị hệ thống:
* **Tên đăng nhập (Username)**: `admin`
* **Mật khẩu (Password)**: `admin123`

---

## 5. Chạy kiểm thử hệ thống (Unit Testing)
Bộ kiểm thử tự động sử dụng `pytest` để xác minh tính toàn vẹn của logic tính toán định mức và quy đổi giờ:
```bash
# Thiết lập biến môi trường mã hóa ký tự để tránh lỗi hiển thị tiếng Việt trên Windows console
$env:PYTHONIOENCODING="utf-8"

# Chạy toàn bộ các ca kiểm thử
python -m pytest tests/
```
