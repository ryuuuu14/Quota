import re

filepath = r"f:\annd\Quota\src\pages\2_QuanLyCanBo.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update stepper steps
content = content.replace(
    'stepper_steps = ["Tải lên", "Ghép cột", "Kiểm tra", "Gửi"]',
    'stepper_steps = ["Tải lên", "Ghép cột", "Kiểm tra & Gửi"]'
)

# 2. Find the start of the mapping UI:
map_start = '                                col_left, col_right = st.columns([0.4, 0.6])\n\n                                with col_left:\n                                    st.caption("GHEP CỘT")'

map_new = '''                                if st.session_state.import_step_teachers == 2:
                                    st.caption("GHÉP CỘT DỮ LIỆU")
                                    st.markdown("Vui lòng ghép các cột từ file Excel của bạn tương ứng với các trường dữ liệu hệ thống yêu cầu.")'''

content = content.replace(map_start, map_new)

# 3. Replace the confirmation block in Stage 2
# Note: In 2_QuanLyCanBo.py, the confirm block is slightly different from 3_NhatKyHoatDong.py
confirm_block_old = '''                                    tpl_name = st.text_input("Lưu mẫu:", key="sp_tpl_name", placeholder="Tên mẫu...", label_visibility="collapsed")
                                    c_save, c_confirm = st.columns([1, 1])
                                    with c_save:
                                        if st.button("Lưu mẫu", use_container_width=True, key="sp_save_tpl"):
                                            if tpl_name.strip():
                                                save_mapping_template(tpl_name.strip(), dict(current_mapping))
                                                st.success("Đã lưu mẫu")
                                    with c_confirm:
                                        if st.button("Xác nhận", type="primary", use_container_width=True, key="sp_confirm"):
                                            st.session_state["mapping_confirmed"] = True

                                    if st.session_state.import_step_teachers == 2:
                                        st.markdown("---")
                                        if st.button("Tiếp theo →", key="step2_next_teachers"):
                                            st.session_state.import_step_teachers = 3
                                            st.rerun()'''

confirm_block_new = '''                                    st.markdown("---")
                                    tpl_name = st.text_input("Lưu mẫu cấu hình hiện tại (nếu cần):", key="sp_confirm_tpl_name", placeholder="Nhập tên mẫu để lưu...")
                                    c_back, c_save, c_next = st.columns([1, 1, 1.5])
                                    with c_back:
                                        if st.button("← Tải file khác", use_container_width=True, key="sp_confirm_back_1"):
                                            st.session_state.import_step_teachers = 1
                                            st.rerun()
                                    with c_save:
                                        if st.button("💾 Lưu mẫu", use_container_width=True, key="sp_confirm_save_tpl"):
                                            if tpl_name.strip():
                                                save_mapping_template(tpl_name.strip(), dict(current_mapping))
                                                st.success("Đã lưu mẫu!")
                                            else:
                                                st.error("Vui lòng nhập tên mẫu.")
                                    with c_next:
                                        if st.button("Kiểm tra dữ liệu →", type="primary", use_container_width=True, key="sp_confirm_next_3"):
                                            missing_required = [c for c in required_cols if current_mapping.get(c) is None]
                                            if missing_required:
                                                st.error(f"⚠️ Vui lòng ghép tất cả các cột bắt buộc: {', '.join(missing_required)}")
                                            else:
                                                st.session_state.import_step_teachers = 3
                                                st.rerun()'''

content = content.replace(confirm_block_old, confirm_block_new)

# 4. Remove `with col_right:` and add Step 3 header
preview_start_old = r'(\s+)with col_right:\n\s+st\.caption\("XEM TRƯỚC DỮ LIỆU"\).*?(\s+if True:\n\s+# Read & remap)'

preview_start_new = """
                                if st.session_state.import_step_teachers >= 3:
                                    st.caption("XEM TRƯỚC DỮ LIỆU ĐÃ GHÉP")
                                    
                                    nav_c1, nav_c2 = st.columns([1, 4])
                                    with nav_c1:
                                        if st.button("← Quay lại sửa ghép cột", key="sp_confirm_back_2"):
                                            st.session_state.import_step_teachers = 2
                                            st.rerun()
                                    st.markdown("---")"""

content = re.sub(r'(\s+)with col_right:\n\s+st\.caption\("XEM TRƯỚC DỮ LIỆU"\).*?(\s+missing_req =)',
                 preview_start_new + r'\2', 
                 content, flags=re.DOTALL)

# Also remove `missing_req = ...` block up to `# Read & remap` in QuanLyCanBo
# Wait, in QuanLyCanBo.py line 1251:
# missing_req = [c for c in required_cols if current_mapping.get(c) is None]
# if missing_req:
#    st.warning(...)
# else:
#    df_raw = parse_excel_to_df(...)
# We want to replace `missing_req ... else:` with just `if True:` so the indentation stays identical.

check_req_old = '''                                missing_req = [c for c in required_cols if current_mapping.get(c) is None]
                                if missing_req:
                                    st.warning(f"⚠️ Vui lòng ghép tất cả các cột bắt buộc: {', '.join(missing_req)}")
                                else:
                                    # Read & remap'''

check_req_new = '''                                if True:
                                    # Read & remap'''

content = content.replace(check_req_old, check_req_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully refactored {filepath}")
