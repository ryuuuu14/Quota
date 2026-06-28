# Auth Portal — Full-Screen Login & Redirect

Upgrade auth from sidebar login to full-screen portal with `st.switch_page()` redirect.

## Rationale
- Current login (sidebar form) is confusing — users don't notice it
- `st.switch_page()` replaces manual URL navigation; available in Streamlit ≥1.36.0
- Need root auth gate to prevent unauthenticated access to any page

## Tasks

### Task 1: Upgrade Streamlit + verify compatibility
- `requirements.txt`: `streamlit>=1.36.0`
- Verify `st.switch_page()` works
- Current: 1.32.2 → Target: 1.36.0+
- ⚠️ Potential breaking changes: API deprecations between 1.32→1.36

### Task 2: Rewrite `8_DangNhap.py` — Full-screen login portal
- Remove sidebar entirely via CSS (`#MainMenu`, header, footer)
- Full-viewport centered glassmorphic card
- Use `st.switch_page("app.py")` on success instead of URL reroute
- Hide sidebar menu items from this page
- Maintain existing MD3 design system (primary `#0056B3`, surface `#f9f9ff`, Inter font)

### Task 3: Rewrite `require_role()` in `auth.py` — Redirect instead of warning
- Replace `st.warning("Bạn không có quyền truy cập trang này")` with:
  ```python
  st.switch_page("pages/8_DangNhap.py")
  st.stop()
  ```
- Keep role checking logic intact
- Maintain backward compatibility for tests

### Task 4: Root auth gate in `app.py` + logout in sidebar
- `app.py`: Check `get_current_user()` before render_sidebar
  - If no user → `st.switch_page("pages/8_DangNhap.py")` + `st.stop()`
  - If user exists → render normally
- `components.py`: Add logout button to `render_sidebar()`:
  - Calls `logout()` from auth
  - Then `st.switch_page("pages/8_DangNhap.py")` + `st.rerun()`

### Task 5: Audit all pages for `require_role()` guards
- Check: `3_NhatKyHoatDong.py`, `5_NhapDuLieu.py`
- Add guards where missing (use appropriate role level)
- Ensure all protected pages redirect to login

## Task Dependencies
```
Task 1 (no deps)
  ↓
Task 2 (no deps, but needs 1 for switch_page)
  ↓
Task 3 (depends on Task 2 conceptually — both use switch_page)
Task 4 (depends on Task 2 + Task 3)
Task 5 (last — audit pass after all changes)
```

## Acceptance Criteria
- Unauthenticated user attempting any URL → redirected to login page
- Login page is full-screen, no sidebar
- Successful login → redirects to app.py
- Unauthorized role accessing page → redirected to login
- Logout button in sidebar → redirects to login
- All existing auth tests pass
- No regression in app.py sidebar rendering for authenticated users
