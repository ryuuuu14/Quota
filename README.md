# Quản lý Chế độ Làm việc Nhà giáo

Đây là ứng dụng web quản lý định mức giờ chuẩn, giờ NCKH và tổng hợp thông kê cho giảng viên theo **Quy định T04**. Ứng dụng hỗ trợ tự động tính toán hệ số giờ chuẩn tùy theo loại hình giảng dạy (lý thuyết, thực hành), cấp học và sĩ số; theo dõi tỷ lệ phần trăm các quy tắc giảm định mức; và tự động gợi ý quy đổi giữa giờ chuẩn và giờ nghiên cứu khoa học.

## Các Quy tắc và Cấu trúc Logic T04
Ứng dụng được xây dựng với logic tính toán nghiêm ngặt bám sát quy định gốc.
Bạn có thể tham khảo bảng tra cứu, quy tắc bù trừ và các hệ số quy đổi chi tiết tại [Quy tắc Logic (rules_logic.md)](./rules_logic.md).

## Cài đặt và Khởi chạy

### Cách 1: Sử dụng Docker (Khuyến nghị)
Sử dụng [Docker](https://docs.docker.com/get-docker/).

```bash
docker-compose up -d --build
```

Truy cập qua trình duyệt: 👉 **http://localhost:8501**
Dữ liệu được lưu trong thư mục `data/` không bị mất khi reset container.

### Cách 2: Chạy trực tiếp
Yêu cầu Python 3.10 trở lên.
```bash
pip install -r requirements.txt
export DB_PATH=data/database.sqlite
streamlit run src/app.py
```

## Kiểm thử Logic Hệ thống
Ứng dụng bao gồm một bộ unit test để xác minh tính toán giờ chuẩn.

```bash
python3 test_logic.py
```

## Ghi chú thiết kế (Stitch UI)
Ngoài giao diện Streamlit, có thể tham khảo giao diện Stitch: `16682207781060267797`.
