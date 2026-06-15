import re

def restore_preview(filepath, step_var):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out_lines = []
    in_stage_2 = False
    
    # We will look for `if st.session_state.import_step == 2:`
    start_str = f"if st.session_state.{step_var} == 2:"
    end_str = f"if st.session_state.{step_var} >= 3:"
    
    # We need to capture the indentation of the start string.
    base_indent = ""
    
    for line in lines:
        if start_str in line:
            in_stage_2 = True
            base_indent = line[:line.index("if")]
            out_lines.append(line)
            out_lines.append(f"{base_indent}    col_left, col_right = st.columns([0.4, 0.6])\n")
            out_lines.append(f"{base_indent}    with col_left:\n")
            continue
            
        if in_stage_2:
            if end_str in line:
                in_stage_2 = False
                
                # We reached the end of Stage 2! Let's inject `with col_right:` right before this line.
                preview_code = f"""{base_indent}    with col_right:
{base_indent}        st.caption("XEM TRƯỚC DỮ LIỆU GỐC")
{base_indent}        try:
{base_indent}            import io as _io
{base_indent}            import pandas as pd
{base_indent}            df_full = pd.read_excel(_io.BytesIO(file_bytes), sheet_name=selected_sheet, header=header_row)
{base_indent}            if not df_full.empty:
{base_indent}                n = len(df_full)
{base_indent}                st.markdown(f'<span style="font-size:12px;color:#6b7280;">50 dòng đầu ({{n}} dòng — file gốc)</span>', unsafe_allow_html=True)
{base_indent}                st.dataframe(df_full.head(50), use_container_width=True, height=200)
{base_indent}                st.markdown(f'<span style="font-size:12px;color:#6b7280;">50 dòng cuối</span>', unsafe_allow_html=True)
{base_indent}                st.dataframe(df_full.tail(50), use_container_width=True, height=200)
{base_indent}            else:
{base_indent}                st.caption("Không có dữ liệu để xem trước")
{base_indent}        except Exception as _e:
{base_indent}            st.caption(f"Không thể đọc dữ liệu xem trước: {{_e}}")

"""
                out_lines.append(preview_code)
                out_lines.append(line)
            else:
                # Add 4 spaces of indentation
                out_lines.append("    " + line if line.strip() else line)
        else:
            out_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

restore_preview(r"f:\annd\Quota\src\pages\3_NhatKyHoatDong.py", "import_step")
restore_preview(r"f:\annd\Quota\src\pages\2_QuanLyCanBo.py", "import_step_teachers")
print("Preview tables restored to Stage 2 mapping UI.")
