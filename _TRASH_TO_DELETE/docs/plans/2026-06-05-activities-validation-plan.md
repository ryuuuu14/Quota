# Category-Specific Validation & Interactive Preview for Bulk Import Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement strict, category-aware validation for bulk activities upload, matching inputs against allowed calculation engine categories, and provide an interactive error-annotated preview table in the UI when validation fails.

**Architecture:** 
1. Cache activity types and check each row category during validation.
2. Cross-reference inputs against supported engines options (`class_level` options, `class_type` options, and `nckh_level` options).
3. If errors are found, construct a preview DataFrame containing a `"Trạng thái / Chi tiết lỗi"` column. Show this dataframe in the UI to give immediate feedback.

**Tech Stack:** Python, Pandas, Streamlit, SQLite

---

### Task 1: Update validation logic in `src/pipeline/validator.py`

**Files:**
- Modify: `src/pipeline/validator.py`
- Test: `test_bulk_import.py`

**Step 1: Write the failing test**

We will write a test case verifying that:
- Invalid class levels (e.g. "Tiểu học"), invalid class types (e.g. "Chơi game"), or invalid student counts (e.g. -5) are rejected.
- Invalid NCKH levels (e.g. "Cấp Vũ Trụ") are rejected.
- Error list correctly captures specific validation messages.

```python
def test_strict_engine_variables_validation():
    import pandas as pd
    from pipeline.validator import validate_activities_data
    from database import get_connection
    
    conn = get_connection()
    df = pd.DataFrame([
        {
            "Mã GV": "1",
            "Tên loại hoạt động": "GD - Lý thuyết ĐH (dùng class_level+student_count để nhân hệ số)",
            "Ngày thực hiện": "2026-06-01",
            "Số lượng": 10,
            "Cấp lớp": "Tiểu học",      # Invalid
            "Loại lớp": "Lý thuyết",
            "Số học viên": 40,
            "Cấp đề tài": None
        },
        {
            "Mã GV": "1",
            "Tên loại hoạt động": "NCKH - Đề tài cấp Cơ sở",
            "Ngày thực hiện": "2026-06-02",
            "Số lượng": 1,
            "Cấp lớp": None,
            "Loại lớp": None,
            "Số học viên": 0,
            "Cấp đề tài": "Cấp Vũ Trụ"  # Invalid
        }
    ])
    
    errors = validate_activities_data(df, conn)
    conn.close()
    
    assert len(errors) == 2
    assert "Cấp học 'Tiểu học' không hợp lệ" in errors[0][2]
    assert "Cấp đề tài 'Cấp Vũ Trụ' không hợp lệ" in errors[1][2]
```

**Step 2: Run test to verify it fails**

Expected: Fail because validator doesn't enforce specific options yet.

**Step 3: Modify `src/pipeline/validator.py` to enforce engine variables**

```python
# Allowed variables definitions matching engine requirements
ALLOWED_CLASS_LEVELS = {"Đại học", "Thạc sĩ", "Tiến sĩ", "LLCT Trung cấp", "LLCT Cao cấp", "Bồi dưỡng"}
ALLOWED_CLASS_TYPES = {"Lý thuyết", "Thực hành", "Ngoại ngữ/CNTT", "Thảo luận", "Bài tập", "Xêmina"}
ALLOWED_NCKH_LEVELS = {"Quốc gia", "Bộ/Tỉnh", "Cơ sở", "Trường"}
```

In `validate_activities_data` (modify loops around line 50-100):
```python
        # Resolve activity type details
        act_info = None
        if not is_empty_cell(act_type):
            act_name_clean = str(act_type).strip().lower()
            act_info = act_types.get(act_name_clean)

        if act_info:
            if act_info["is_teaching_activity"] == 1:
                class_lvl = row.get("Cấp lớp")
                if is_empty_cell(class_lvl):
                    errors.append((idx, row_num, "Hoạt động giảng dạy yêu cầu thông tin 'Cấp lớp'."))
                elif str(class_lvl).strip() not in ALLOWED_CLASS_LEVELS:
                    errors.append((idx, row_num, f"Cấp học '{class_lvl}' không hợp lệ (Phải là một trong: {', '.join(ALLOWED_CLASS_LEVELS)})."))
                
                class_typ = row.get("Loại lớp")
                if is_empty_cell(class_typ):
                    errors.append((idx, row_num, "Hoạt động giảng dạy yêu cầu thông tin 'Loại lớp'."))
                elif str(class_typ).strip() not in ALLOWED_CLASS_TYPES:
                    errors.append((idx, row_num, f"Loại hình lớp '{class_typ}' không hợp lệ (Phải là một trong: {', '.join(ALLOWED_CLASS_TYPES)})."))
                
                std_cnt = row.get("Số học viên")
                if is_empty_cell(std_cnt):
                    errors.append((idx, row_num, "Hoạt động giảng dạy yêu cầu thông tin 'Số học viên' lớn hơn 0."))
                else:
                    try:
                        std_cnt_val = int(float(str(std_cnt).strip()))
                        if std_cnt_val <= 0:
                            errors.append((idx, row_num, "Hoạt động giảng dạy yêu cầu thông tin 'Số học viên' lớn hơn 0."))
                    except ValueError:
                        errors.append((idx, row_num, "Thông tin 'Số học viên' không hợp lệ."))
            
            elif act_info["is_nckh_activity"] == 1:
                nckh_lvl = row.get("Cấp đề tài")
                if is_empty_cell(nckh_lvl):
                    errors.append((idx, row_num, "Hoạt động NCKH yêu cầu thông tin 'Cấp đề tài'."))
                elif str(nckh_lvl).strip() not in ALLOWED_NCKH_LEVELS:
                    errors.append((idx, row_num, f"Cấp đề tài '{nckh_lvl}' không hợp lệ (Phải là một trong: {', '.join(ALLOWED_NCKH_LEVELS)})."))
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/test_bulk_import.py`
Expected: PASS.

---

### Task 2: Implement UI Error Preview Table in `src/pages/3_NhatKyHoatDong.py`

**Files:**
- Modify: `src/pages/3_NhatKyHoatDong.py`

**Step 1: Code the preview DataFrame generator**

If `errors` is not empty, instead of just displaying bullet points, we will:
1. Construct a preview dataframe `df_preview` containing all rows from `df_parsed`.
2. Add a column `"Trạng thái / Chi tiết lỗi"` at the first position.
3. Populate rows that have errors with their error descriptions.
4. Display this dataframe using `st.dataframe` with custom styling or error prefixes so the user can easily see which rows are broken and why.

```python
# In src/pages/3_NhatKyHoatDong.py around line 474:
if errors:
    st.error("❌ Phát hiện lỗi định dạng dữ liệu trong file Excel. Vui lòng sửa lại trước khi tiếp tục:")
    
    # Render detailed bullet list for first 5 errors
    for idx_e, r_num, err_msg in errors[:5]:
        st.write(f"- Dòng {r_num}: {err_msg}")
    if len(errors) > 5:
        st.caption(f"... và {len(errors) - 5} lỗi khác.")
    
    # Create preview with errors
    df_preview = df_parsed.copy()
    
    # Map row index to errors
    error_map = {}
    for idx_err, r_num, err_msg in errors:
        if idx_err not in error_map:
            error_map[idx_err] = []
        error_map[idx_err].append(err_msg)
        
    status_col = []
    for idx_r, _ in df_preview.iterrows():
        if idx_r in error_map:
            status_col.append("❌ Lỗi: " + "; ".join(error_map[idx_r]))
        else:
            status_col.append("✓ Hợp lệ")
            
    df_preview.insert(0, "Trạng thái / Chi tiết lỗi", status_col)
    
    st.markdown("##### 🔍 Xem trước toàn bộ dữ liệu tải lên và lỗi phát hiện:")
    st.dataframe(df_preview, use_container_width=True, hide_index=True)
```

**Step 2: Manual Verification**

1. Upload an Excel sheet containing invalid/missing values.
2. Confirm the interactive preview table renders correctly with the red error icons and clear status strings.
