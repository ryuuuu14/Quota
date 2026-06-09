import re
import socket
import pytest
from playwright.sync_api import Page, expect

def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except:
            return False

has_playwright = False
try:
    import pytest_playwright
    has_playwright = True
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    not has_playwright or not is_port_open("localhost", 8501),
    reason="pytest-playwright is not installed or Streamlit server is not running on localhost:8501"
)

def login_as_admin(page: Page):
    page.goto("http://localhost:8501/DangNhap")
    page.wait_for_selector("input")
    page.get_by_placeholder("Nhập tên đăng nhập...").fill("admin")
    page.get_by_placeholder("Nhập mật khẩu...").fill("admin123")
    page.get_by_role("button", name="🔐 Đăng nhập").click()
    page.wait_for_timeout(2000)

def test_teacher_management_flow(page: Page):
    login_as_admin(page)
    # 1. Truy cập trang bằng cách click sidebar
    page.get_by_role("link", name="Quản lý Cán bộ").click()
    page.wait_for_timeout(1000)
    
    # 2. Kiểm tra tiêu đề trang
    expect(page).to_have_title(re.compile("Quản lý Hồ sơ Nhà giáo"))
    
    # 3. Kiểm tra xem selectbox "🔍 Chọn Nhà giáo" có hiển thị không
    expect(page.get_by_text("🔍 Chọn Nhà giáo")).to_be_visible()
    
    # 4. Kiểm tra xem "Toàn bộ quá trình công tác" có hiển thị không
    expect(page.get_by_text("Toàn bộ quá trình công tác")).to_be_visible()
    
    # 5. Kiểm tra xem tiêu đề phần cập nhật có hiển thị không
    expect(page.get_by_text("Cập nhật Quá trình Công tác")).to_be_visible()

def test_dashboard_flow(page: Page):
    login_as_admin(page)
    page.get_by_role("link", name="Bảng điều khiển").click()
    page.wait_for_timeout(1000)
    
    # Kiểm tra các thẻ KPI
    expect(page.get_by_text("Tổng số nhà giáo")).to_be_visible()
    expect(page.get_by_text("Tổng định mức GC")).to_be_visible()
    
    # Kiểm tra bộ lọc cột
    expect(page.get_by_text("Chọn cột hiển thị")).to_be_visible()

def test_activity_logging_flow(page: Page):
    login_as_admin(page)
    page.get_by_role("link", name="Nhật ký Hoạt động").click()
    page.wait_for_timeout(1000)
    
    page.get_by_role("tab", name="➕ Ghi nhận mới").click()
    page.wait_for_timeout(1000)
    
    # Kiểm tra form nhập liệu
    expect(page.get_by_text("Chọn Nhà giáo")).to_be_visible()
    expect(page.get_by_text("Chọn Hoạt động")).to_be_visible()
