import os


def test_sidebar_has_phe_duyet():
    components_path = os.path.join(os.path.dirname(__file__), "..", "src", "components.py")
    with open(components_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "pages/7_PheDuyet.py" in content
    assert "Phê duyệt Dữ liệu" in content


def test_pages_gatekeeper():
    # Verify that CaiDatHeThong, PheDuyet, and Payroll have require_role checks
    for page_name in ["4_CaiDatHeThong.py", "7_PheDuyet.py", "6_Payroll.py"]:
        page_path = os.path.join(os.path.dirname(__file__), "..", "src", "pages", page_name)
        with open(page_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "require_role" in content or "session_state" in content


def test_login_page_exists():
    login_path = os.path.join(os.path.dirname(__file__), "..", "src", "pages", "8_DangNhap.py")
    assert os.path.exists(login_path)

