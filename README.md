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

## 3. Triển khai Offline qua USB (1-Click Deployment)

Ứng dụng được thiết kế để triển khai hoàn toàn offline trên mạng LAN nội bộ. **Không cần cài đặt Python thủ công** — hệ thống tự động cài đặt và cấu hình mọi thứ.

### Bước 1: Chuẩn bị (chỉ làm 1 lần, trên máy có internet)
Trên máy phát triển có kết nối internet, chạy:
```cmd
prepare_bundle.bat
```
Script này sẽ tải Python và tất cả thư viện phụ thuộc vào thư mục `vendor/` (~100 MB).

### Bước 2: Sao chép qua USB
Sao chép **toàn bộ thư mục `Quota-main/`** vào USB (bao gồm cả `vendor/`).

### Bước 3: Triển khai trên máy chủ
Trên máy chủ Windows 11 (mạng LAN), dán thư mục từ USB và double-click:
```cmd
App.bat
```

### Các bước tự động khi chạy lần đầu:
1. **Cài đặt Python**: Tự động giải nén Python 3.13 từ `vendor/` vào `runtime/` (~30 giây).
2. **Cài đặt Thư viện**: Tự động cài đặt toàn bộ thư viện từ `vendor/packages/` (offline).
3. **Kiểm tra Cổng mạng**: Đảm bảo cổng `8501` đang rảnh.
4. **Khởi tạo CSDL**: Tự động tạo `data/database.sqlite` và seed dữ liệu chuẩn.
5. **Cấu hình mạng**: Tự động mở cổng tường lửa `1111` để cho phép các máy khách truy cập.
6. **Khởi chạy máy chủ**: Mở ứng dụng tại 👉 **http://<SERVER_IP>:1111** (Địa chỉ IP của máy chủ được tự động phát hiện và hiển thị trên cửa sổ console khi chạy).

> **Lưu ý**: Lần chạy thứ hai trở đi sẽ khởi động ngay lập tức. Cần chấp nhận hộp thoại yêu cầu quyền Administrator (UAC) ở lần chạy đầu tiên để cấu hình tường lửa cho phép các thiết bị di động truy cập.

### Cách truy cập từ thiết bị khác (Điện thoại, Máy tính khác) trong mạng LAN:
Bạn có thể truy cập trực tiếp bằng địa chỉ IP của máy chủ (địa chỉ kết nối thống nhất):

1. Đảm bảo thiết bị di động hoặc máy tính khách kết nối cùng mạng Wi-Fi/mạng LAN với máy chủ.
2. Mở trình duyệt trên thiết bị khách và truy cập theo địa chỉ hiển thị trên màn hình console khi khởi động `App.bat`:
   ```
   http://<SERVER_IP>:1111
   ```

---

## 4. Công cụ chẩn đoán & Giám sát (Observability)
Hệ thống tích hợp bảng chẩn đoán lỗi mạng và nhật ký giám sát hoạt động ngoại tuyến (offline):

* **Bảng chẩn đoán**: Chạy file `diagnose_network.bat` để kiểm tra trạng thái tường lửa, kiểm tra dịch vụ Streamlit đang chạy và khả năng truy cập qua IP tùy chỉnh.
* **Nhật ký hệ thống (`data/logs/`)**:
  * `network_setup.log`: Ghi nhận lịch sử cấu hình cổng mạng và tường lửa.


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
