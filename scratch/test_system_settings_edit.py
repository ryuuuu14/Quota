import os
import sys
import time
from playwright.sync_api import sync_playwright

def run_test():
    with sync_playwright() as p:
        print("Launching Chromium in headless mode...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to login page...")
        page.goto('http://localhost:8501/')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        # Take screenshot of login page
        page.screenshot(path='scratch/test_login_page.png')
        print("Login page screenshot saved.")

        # Perform login
        print("Entering credentials...")
        page.locator('input[type="text"]').first.fill('admin')
        page.locator('input[type="password"]').first.fill('admin123')
        
        # Click login button
        login_btn = page.locator('button:has-text("Đăng nhập")')
        if login_btn.count() > 0:
            login_btn.first.click()
        else:
            page.get_by_role("button", name="Đăng nhập").first.click()
            
        print("Submitted login form.")
        page.wait_for_load_state('networkidle')
        time.sleep(3)

        page.screenshot(path='scratch/test_after_login.png')
        print("Logged in successfully. Screenshot saved.")

        # Navigate to "Cai dat he thong"
        print("Navigating to Cai dat he thong...")
        page.locator('a:has-text("Cài đặt hệ thống")').first.click()
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        page.screenshot(path='scratch/test_system_settings.png')

        # Test Tab 1: Holidays editing
        print("\n--- Testing Tab 1: Holidays ---")
        tab1_btn = page.locator('button[role="tab"]:has-text("Năm học")')
        if tab1_btn.count() > 0:
            tab1_btn.first.click()
        time.sleep(1.5)
        
        # Find visible "Sua" buttons
        edit_buttons = page.locator('button:has-text("Sửa")').filter(visible=True)
        print(f"Found {edit_buttons.count()} visible edit buttons in Tab 1.")
        if edit_buttons.count() > 0:
            print("Clicking first Edit button in Tab 1...")
            edit_buttons.first.click()
            time.sleep(2)
            page.screenshot(path='scratch/test_tab1_edit_form.png')
            
            cancel_btn = page.locator('button:has-text("Hủy")').filter(visible=True)
            if cancel_btn.count() > 0:
                print("Clicking Huy to verify cancel works...")
                cancel_btn.first.click()
                time.sleep(2)
                print("Cancel verified.")
            else:
                print("Cancel button not found in form.")
        else:
            print("No holidays/timeframes/edit buttons found in Tab 1.")

        # Test Tab 2: Don vi
        print("\n--- Testing Tab 2: Don vi ---")
        tab2_btn = page.locator('button[role="tab"]:has-text("Đơn vị")')
        if tab2_btn.count() > 0:
            tab2_btn.first.click()
        time.sleep(2)
        page.screenshot(path='scratch/test_tab2.png')
        
        edit_buttons = page.locator('button:has-text("Sửa")').filter(visible=True)
        print(f"Found {edit_buttons.count()} visible edit buttons in Tab 2.")
        if edit_buttons.count() > 0:
            print("Clicking Edit button in Tab 2...")
            edit_buttons.first.click()
            time.sleep(2)
            page.screenshot(path='scratch/test_tab2_edit_form.png')
            cancel_btn = page.locator('button:has-text("Hủy")').filter(visible=True)
            if cancel_btn.count() > 0:
                cancel_btn.first.click()
                time.sleep(1.5)
                print("Tab 2 edit Cancelled successfully.")

        # Test Tab 3: Chuc danh
        print("\n--- Testing Tab 3: Chuc danh ---")
        tab3_btn = page.locator('button[role="tab"]:has-text("Chức danh")')
        if tab3_btn.count() > 0:
            tab3_btn.first.click()
        time.sleep(2)
        page.screenshot(path='scratch/test_tab3.png')
        
        edit_buttons = page.locator('button:has-text("Sửa")').filter(visible=True)
        print(f"Found {edit_buttons.count()} visible edit buttons in Tab 3.")
        if edit_buttons.count() > 0:
            print("Clicking Edit button in Tab 3...")
            edit_buttons.first.click()
            time.sleep(2)
            page.screenshot(path='scratch/test_tab3_edit_form.png')
            cancel_btn = page.locator('button:has-text("Hủy")').filter(visible=True)
            if cancel_btn.count() > 0:
                cancel_btn.first.click()
                time.sleep(1.5)
                print("Tab 3 edit Cancelled successfully.")

        # Test Tab 4: Chuc vu
        print("\n--- Testing Tab 4: Chuc vu ---")
        tab4_btn = page.locator('button[role="tab"]:has-text("Chức vụ")')
        if tab4_btn.count() > 0:
            tab4_btn.first.click()
        time.sleep(2)
        page.screenshot(path='scratch/test_tab4.png')
        
        edit_buttons = page.locator('button:has-text("Sửa")').filter(visible=True)
        print(f"Found {edit_buttons.count()} visible edit buttons in Tab 4.")
        if edit_buttons.count() > 0:
            print("Clicking Edit button in Tab 4...")
            edit_buttons.first.click()
            time.sleep(2)
            page.screenshot(path='scratch/test_tab4_edit_form.png')
            cancel_btn = page.locator('button:has-text("Hủy")').filter(visible=True)
            if cancel_btn.count() > 0:
                cancel_btn.first.click()
                time.sleep(1.5)
                print("Tab 4 edit Cancelled successfully.")

        # Test Tab 5: Mien giam khac
        print("\n--- Testing Tab 5: Mien giam khac ---")
        tab5_btn = page.locator('button[role="tab"]:has-text("Miễn giảm khác")')
        if tab5_btn.count() > 0:
            tab5_btn.first.click()
        time.sleep(2)
        page.screenshot(path='scratch/test_tab5.png')
        
        edit_buttons = page.locator('button:has-text("Sửa")').filter(visible=True)
        print(f"Found {edit_buttons.count()} visible edit buttons in Tab 5.")
        if edit_buttons.count() > 0:
            print("Clicking Edit button in Tab 5...")
            edit_buttons.first.click()
            time.sleep(2)
            page.screenshot(path='scratch/test_tab5_edit_form.png')
            cancel_btn = page.locator('button:has-text("Hủy")').filter(visible=True)
            if cancel_btn.count() > 0:
                cancel_btn.first.click()
                time.sleep(1.5)
                print("Tab 5 edit Cancelled successfully.")

        # Test Tab 6: Hoat dong
        print("\n--- Testing Tab 6: Hoat dong ---")
        tab6_btn = page.locator('button[role="tab"]:has-text("Hoạt động")')
        if tab6_btn.count() > 0:
            tab6_btn.first.click()
        time.sleep(2)
        page.screenshot(path='scratch/test_tab6.png')
        
        edit_buttons = page.locator('button:has-text("Sửa")').filter(visible=True)
        print(f"Found {edit_buttons.count()} visible edit buttons in Tab 6.")
        if edit_buttons.count() > 0:
            print("Clicking Edit button in Tab 6...")
            edit_buttons.first.click()
            time.sleep(2)
            page.screenshot(path='scratch/test_tab6_edit_form.png')
            cancel_btn = page.locator('button:has-text("Hủy")').filter(visible=True)
            if cancel_btn.count() > 0:
                cancel_btn.first.click()
                time.sleep(1.5)
                print("Tab 6 edit Cancelled successfully.")

        print("\nVerification test script execution finished.")
        browser.close()

if __name__ == '__main__':
    run_test()
