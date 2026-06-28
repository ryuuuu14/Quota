# Decision Log

## Format
- Each decision has a unique ID (D{number}).
- Logged by Orchestrator after each resolve.

---

## D1: Vietnamese diacritics fix scope
- Date: 2026-06-08
- Agent: Orchestrator (task.md creation)
- Context: UI labels use all-caps without diacritics (BAT BUOC, XEM TRUOC, KHONG CHON)
- Chosen: Fix only visible UI labels in 3_NhatKyHoatDong.py first; expand later
- Rejected: Big-bang find/replace across all files
- Objections: None yet
- Resolution: Pending H1 approval
