# Canbo UI Fix Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Stack tag and salary in flex row, format salary with dot separator.

**Architecture:** Update Streamlit markdown string and python f-string formatting in `2_QuanLyCanBo.py`.

**Tech Stack:** Python, Streamlit, HTML/CSS.

---

### Task 1: Update UI Layout and Format

**Files:**
- Modify: `src/pages/2_QuanLyCanBo.py:114-150`

**Step 1: Write minimal implementation**

```python
            sal = t_data['total_12m_salary']
            if pd.notna(sal) and sal > 0:
                salary_info = f"Lương 12T: {sal:,.0f} đ".replace(',', '.')
            else:
                salary_info = "Lương 12T: Chưa cập nhật"

        # Summary Card
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, var(--md-surface-container), var(--md-surface-container-low));
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--md-outline-variant);
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 16px;
        ">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <div style="
                    width: 48px; height: 48px; border-radius: 50%; 
                    background-color: var(--md-primary-container); 
                    color: var(--md-on-primary-container);
                    display: flex; justify-content: center; align-items: center;
                    font-size: 24px; font-weight: bold;
                ">
                    {t_data['name'][0].upper()}
                </div>
                <div>
                    <h3 style="margin: 0; font-size: 1.1rem; color: var(--md-on-surface);">{t_data['name']}</h3>
                    <div style="font-size: 0.85rem; color: var(--md-on-surface-variant);">{gender} • {t_data['subject_group']}</div>
                </div>
            </div>
            
            <div style="font-size: 0.9rem; line-height: 1.6;">
                <div><strong style="color: var(--md-primary);">🏛️ Đơn vị:</strong> {c_dept}</div>
                <div><strong style="color: var(--md-primary);">💼 Chức danh:</strong> {c_title}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--md-outline-variant);">
                    <span class="md-chip md-chip-primary">{emp_label}</span>
                    <span style="font-weight: 500;">{salary_info}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
```

**Step 2: Commit**

```bash
git add src/pages/2_QuanLyCanBo.py
git commit -m "fix(ui): use flex row and dot format for salary"
```
