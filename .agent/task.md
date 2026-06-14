# Task Backlog — UI/UX Improvements

## Format
- Tasks are numbered and ordered by priority.
- Status: PENDING / IN PROGRESS / DONE / BLOCKED

---

[1] PENDING: Fix Vietnamese diacritics across all UI labels
     Files: 3_NhatKyHoatDong.py (BAT BUOC → BẮT BUỘC, KHONG CHON → KHÔNG CHỌN, XEM TRUOC → XEM TRƯỚC, etc.)
     Risk: LOW
     Acceptance: All-caps labels use proper Vietnamese diacritics

[2] PENDING: Add column search/filter to Dashboard data table
     Files: 1_Dashboard.py
     Risk: MEDIUM
     Acceptance: Users can filter by column values, toggle column visibility

[3] PENDING: Consistent empty states across all pages
     Files: 1_Dashboard.py, 6_Payroll.py, 7_PheDuyet.py
     Risk: LOW
     Acceptance: Every page uses render_empty_state() instead of st.info/warning

[4] PENDING: Add skeleton loading states for long operations
     Files: 1_Dashboard.py, 2_QuanLyCanBo.py
     Risk: LOW
     Acceptance: Loading shows layout-matched skeleton placeholders

[5] PENDING: User-friendly error messages (hide technical details)
     Files: 3_NhatKyHoatDong.py, 2_QuanLyCanBo.py
     Risk: LOW
     Acceptance: Errors show "Chi tiết kỹ thuật" only in expander

[6] PENDING: Approval pipeline visual indicator (pending/under-review/approved)
     Files: 7_PheDuyet.py, 3_NhatKyHoatDong.py
     Risk: MEDIUM
     Acceptance: Each batch shows colored status badge
