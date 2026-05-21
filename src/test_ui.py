import re
from playwright.sync_api import Page, expect

def test_teacher_management_flow(page: Page):
    # 1. Truy cập ứng dụng Streamlit
    page.goto("http://localhost:8501")
    
    # 2. Kiểm tra tiêu đề trang
    expect(page).to_have_title(re.compile("Quản lý Cán bộ"))
    
    # 3. Kiểm tra xem có danh sách hồ sơ không
    expect(page.get_by_text("📋 Danh sách Hồ sơ")).to_be_visible()
    
    # 4. Chọn một nhà giáo từ selectbox
    page.get_by_label("Chọn Nhà giáo để xem/cập nhật").select_option(label="Nguyễn Văn A")
    
    # 5. Kiểm tra xem Status Bar có hiển thị không
    expect(page.get_by_text("Nhà giáo")).to_be_visible()
    
    # 6. Kiểm tra xem Expander có mở rộng được không
    page.get_by_text("⚙️ Cập nhật Biến động & Xem Lịch sử Chi tiết").click()
    
    # 7. Kiểm tra xem ô chọn thao tác có xuất hiện không
    expect(page.get_by_text("Chọn thao tác cần thực hiện")).to_be_visible()

def test_dashboard_flow(page: Page):
    # Giả định Dashboard là trang mặc định hoặc truy cập qua sidebar
    page.goto("http://localhost:8501/Dashboard") # Hoặc URL tương ứng
    
    # Kiểm tra các thẻ KPI
    expect(page.get_by_text("Tổng số nhà giáo")).to_be_visible()
    expect(page.get_by_text("Tổng định mức GC")).to_be_visible()
    
    # Kiểm tra bộ lọc cột
    expect(page.get_by_text("Chọn cột hiển thị")).to_be_visible()

def test_activity_logging_flow(page: Page):
    page.goto("http://localhost:8501/NhatKyHoatDong") # Hoặc URL tương ứng
    
    # Kiểm tra form nhập liệu
    expect(page.get_by_text("Chọn Nhà giáo")).to_be_visible()
    expect(page.get_by_text("Danh mục hoạt động")).to_be_visible()
