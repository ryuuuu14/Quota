import os

file_path = r"f:\annd\Quota\src\pages\3_NhatKyHoatDong.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace block 1: Variable definitions
old_block_1 = """                                    if import_method == "activities":
                                        required_cols = ["Mã GV", "Tên loại hoạt động", "Ngày thực hiện", "Số lượng"]
                                        optional_cols = ["Cấp lớp", "Loại lớp", "Số học viên", "Cấp đề tài", "Tác giả chính", "Giảng dạy tiếng nước ngoài", "Ghi chú"]
                                    else:
                                        required_cols = ["Mã GV", "Tổng GC thực hiện", "NCKH thực hiện", "Số giờ miễn giảm", "Định mức GC"]
                                        optional_cols = ["Ghi chú"]

                                    all_target_cols = required_cols + optional_cols"""

new_block_1 = """                                    conditional_cols = []
                                    if import_method == "activities":
                                        required_cols = ["Mã GV", "Tên loại hoạt động", "Ngày thực hiện", "Số lượng"]
                                        conditional_cols = ["Cấp lớp", "Loại lớp", "Số học viên", "Cấp đề tài"]
                                        optional_cols = ["Tác giả chính", "Giảng dạy tiếng nước ngoài", "Ghi chú"]
                                    else:
                                        required_cols = ["Mã GV", "Tổng GC thực hiện", "NCKH thực hiện", "Số giờ miễn giảm", "Định mức GC"]
                                        optional_cols = ["Ghi chú"]

                                    all_target_cols = required_cols + conditional_cols + optional_cols"""

# Replace block 2: UI rendering
old_block_2 = """                                            with rc[2]:
                                                di = 0
                                                cur = current_mapping.get(col)
                                                if cur in headers:
                                                    di = headers.index(cur) + 1
                                                elif m and m.matched_header in headers:
                                                    di = headers.index(m.matched_header) + 1
                                                sel = st.selectbox("", ["(Không chọn)"] + headers, index=di,
                                                                   key=f"sp_req_{col}", label_visibility="collapsed")
                                                current_mapping[col] = None if sel == "(Không chọn)" else sel

                                        if opt_cols_list:"""

new_block_2 = """                                            with rc[2]:
                                                di = 0
                                                cur = current_mapping.get(col)
                                                if cur in headers:
                                                    di = headers.index(cur) + 1
                                                elif m and m.matched_header in headers:
                                                    di = headers.index(m.matched_header) + 1
                                                sel = st.selectbox("", ["(Không chọn)"] + headers, index=di,
                                                                   key=f"sp_req_{col}", label_visibility="collapsed")
                                                current_mapping[col] = None if sel == "(Không chọn)" else sel

                                        for col in conditional_cols:
                                            m = col_map.get(col)
                                            val = current_mapping.get(col)
                                            is_missing = val is None
                                            dot = "y" if is_missing else ("g" if m and m.confidence >= 90 else "y")

                                            rc = st.columns([0.3, 1.5, 2.8])
                                            with rc[0]:
                                                st.markdown(f'<span class="sp-dot {dot}"></span>', unsafe_allow_html=True)
                                            with rc[1]:
                                                st.markdown(f'<span style="font-size:13px;font-weight:500;">{col}<span class="sp-badge" style="background:#ca8a04;">THEO LOẠI</span></span>',
                                                            unsafe_allow_html=True)
                                            with rc[2]:
                                                di = 0
                                                cur = current_mapping.get(col)
                                                if cur in headers:
                                                    di = headers.index(cur) + 1
                                                elif m and m.matched_header in headers:
                                                    di = headers.index(m.matched_header) + 1
                                                sel = st.selectbox("", ["(Không chọn)"] + headers, index=di,
                                                                   key=f"sp_cond_{col}", label_visibility="collapsed")
                                                current_mapping[col] = None if sel == "(Không chọn)" else sel

                                        if opt_cols_list:"""

content = content.replace(old_block_1, new_block_1)
content = content.replace(old_block_2, new_block_2)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully replaced UI logic in 3_NhatKyHoatDong.py")
