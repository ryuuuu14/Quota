# -*- coding: utf-8 -*-
import sys
import os
import time
from playwright.sync_api import sync_playwright

def main():
    print("Launching Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://localhost:8501/')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        # Wait for login page input
        try:
            print("Waiting for login inputs...")
            page.wait_for_selector('input[placeholder*="tên đăng nhập"]', timeout=10000)
            
            print("Focusing and typing username...")
            user_input = page.locator('input[placeholder*="tên đăng nhập"]')
            user_input.click()
            user_input.fill("")
            user_input.type('admin', delay=100)
            time.sleep(0.5)
            
            print("Focusing and typing password...")
            pass_input = page.locator('input[placeholder*="mật khẩu"]')
            pass_input.click()
            pass_input.fill("")
            pass_input.type('admin123', delay=100)
            time.sleep(0.5)
            
            # Click submit button
            print("Clicking login button...")
            submit_btn = page.locator('div[data-testid="stFormSubmitButton"] button')
            submit_btn.click()
            
            print("Waiting for login completion...")
            page.wait_for_load_state('networkidle')
            time.sleep(5)
            print("URL after login: " + page.url)
            
        except Exception as e:
            print(f"Login error: {e}")
            
        print("Clicking sidebar link...")
        try:
            sidebar_link = page.locator('span:has-text("Quản lý Cán bộ")')
            sidebar_link.click()
            time.sleep(5)
            print("Current URL: " + page.url)
        except Exception as e:
            print(f"Sidebar click error: {e}")
        
        # Click the second tab (tab 2)
        print("Clicking tab index 1...")
        tabs = page.locator('[role="tab"]')
        print(f"Found tabs count: {tabs.count()}")
        if tabs.count() > 1:
            tabs.nth(1).click()
            time.sleep(3)
            
            # Click expander to open it
            print("Clicking expander inside tab 2...")
            page.locator('summary:has-text("Thêm mới Hồ sơ Nhà giáo")').click()
            time.sleep(2)
            
            # Locate within expander
            expander = page.locator('[data-testid="stExpander"]', has_text="Thêm mới Hồ sơ Nhà giáo")
            
            # Fill name
            test_name = f"Test Toast {int(time.time())}"
            print(f"Filling name: {test_name}")
            name_input = expander.locator('input[aria-label*="Họ và tên"]').first
            name_input.click()
            name_input.fill(test_name)
            time.sleep(1)
            
            # Submit form
            print("Submitting the form...")
            submit_btn = expander.locator('button:has-text("Lưu Hồ sơ")')
            submit_btn.click()
            
            # Wait for toast to appear
            print("Waiting for toast notification...")
            page.wait_for_selector('div[data-testid="stToast"]', timeout=10000)
            
            toast_elem = page.locator('div[data-testid="stToast"]')
            print(f"Success! Toast text: {toast_elem.inner_text()}")
            
            # Take screenshot of the toast
            screenshot_path = r'C:\Users\ADMIN\.gemini\antigravity\brain\e136ff6b-1713-41b1-b3cb-4db75a564b29\profile_creation_toast.png'
            page.screenshot(path=screenshot_path)
            print("Toast screenshot saved.")
        else:
            print("Tabs not found or page not loaded correctly.")
        
        browser.close()
        print("Done!")

if __name__ == '__main__':
    main()
