# -*- coding: utf-8 -*-
import time
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://localhost:8501/')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        # Log in
        user_input = page.locator('input[placeholder*="tên đăng nhập"]')
        user_input.fill('admin')
        pass_input = page.locator('input[placeholder*="mật khẩu"]')
        pass_input.fill('admin123')
        page.locator('div[data-testid="stFormSubmitButton"] button').click()
        time.sleep(4)
        
        # Click sidebar
        page.locator('span:has-text("Quản lý Cán bộ")').click()
        time.sleep(4)
        
        # Click tab 2
        tabs = page.locator('[role="tab"]')
        if tabs.count() > 1:
            tabs.nth(1).click()
            time.sleep(2)
            
            # Find expanders and print their outer HTML
            expanders = page.locator('[data-testid="stExpander"]')
            print(f"Found {expanders.count()} expanders.")
            for i in range(expanders.count()):
                html = expanders.nth(i).evaluate("el => el.outerHTML")
                print(f"\n--- Expander {i} ---")
                print(html[:1000]) # Print first 1000 chars of each
        else:
            print("Tabs not found.")
            
        browser.close()

if __name__ == '__main__':
    main()
