import sys
import os
import time
from playwright.sync_api import sync_playwright

def main():
    print("Launching Playwright for debug...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://localhost:8501/')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        print("Initial URL: " + page.url)
        
        # Verify if login page is loaded
        if page.locator('input[type="text"]').count() > 0:
            print("Logging in...")
            # Let's find inputs and fill them
            page.fill('input[type="text"]', 'admin')
            page.fill('input[type="password"]', 'admin')
            page.click('button:has-text("Đăng nhập")')
            page.wait_for_load_state('networkidle')
            time.sleep(3)
            print("URL after login: " + page.url)
        
        print("Navigating to Quan Ly Can Bo page...")
        page.goto('http://localhost:8501/QuanLyCanBo')
        page.wait_for_load_state('networkidle')
        time.sleep(5)
        
        print("Current URL: " + page.url)
        
        screenshot_path = r'C:\Users\ADMIN\.gemini\antigravity\brain\e136ff6b-1713-41b1-b3cb-4db75a564b29\debug_quanlycanbo.png'
        page.screenshot(path=screenshot_path)
        print("Screenshot saved successfully.")
        
        browser.close()
        print("Done!")

if __name__ == '__main__':
    main()
