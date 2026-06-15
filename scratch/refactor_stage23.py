import re

def refactor_ui(filepath, step_var, btn_confirm_key):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update stepper steps
    content = content.replace(
        'stepper_steps = ["Tải lên", "Ghép cột", "Kiểm tra", "Gửi"]',
        'stepper_steps = ["Tải lên", "Ghép cột", "Kiểm tra & Gửi"]'
    )
    
    # Remove the stray "Tiếp theo" button at step 2 if it exists
    stray_btn_pattern = r'(\s+if st\.button\("Tiếp theo →", key="step2_next"\):\n\s+st\.session_state\.' + step_var + r' = 3\n\s+st\.rerun\(\)\n)'
    content = re.sub(stray_btn_pattern, '\n', content)

    # We need to split the "if import_step >= 2:" block into two distinct blocks depending on `step_var == 2` and `step_var == 3`.
    # First, let's find the line: "col_left, col_right = st.columns([0.4, 0.6])"
    # We will remove this columns layout, and instead do full-width for both stages!
    # Wait, the user wants "big preview of data", so making it full width is great.
    
    # Let's just use Python AST or string manipulation to inject the 'if step == 2:' and 'if step == 3:' checks.
    # Actually, it's easier to manually replace the layout structure using exact string matches.

    # 2. Find the start of the mapping UI:
    map_start = '                                    col_left, col_right = st.columns([0.4, 0.6])\n\n                                    with col_left:\n                                        st.caption("GHÉP CỘT")'
    if map_start not in content:
        # Fallback for 2_QuanLyCanBo if different
        map_start = '                                        col_left, col_right = st.columns([0.4, 0.6])\n\n                                        with col_left:\n                                            st.caption("GHÉP CỘT")'

    map_new = f'''                                    if st.session_state.{step_var} == 2:
                                        st.caption("GHÉP CỘT DỮ LIỆU")
                                        st.markdown("Vui lòng ghép các cột từ file Excel của bạn tương ứng với các trường dữ liệu hệ thống yêu cầu.")'''
    
    content = content.replace(map_start, map_new)
    
    # 3. Replace the confirmation block in Stage 2 to instead navigate to Stage 3
    confirm_block_old = f'''                                        tpl_name = st.text_input("Lưu mẫu:", key="sp_tpl_name", placeholder="Tên mẫu...", label_visibility="collapsed")
                                        c_save, c_submit = st.columns([1, 1])
                                        with c_save:
                                            if st.button("Lưu mẫu", use_container_width=True, key="sp_save_tpl"):
                                                if tpl_name.strip():
                                                    save_mapping_template(tpl_name.strip(), dict(current_mapping))
                                                    st.success("Đã lưu mẫu")
                                        with c_submit:
                                            if st.button("Xác nhận", type="primary", use_container_width=True, key="{btn_confirm_key}"):
                                                st.session_state["mapping_confirmed"] = True'''

    confirm_block_new = f'''                                        st.markdown("---")
                                        tpl_name = st.text_input("Lưu mẫu cấu hình hiện tại (nếu cần):", key="{btn_confirm_key}_tpl_name", placeholder="Nhập tên mẫu để lưu...")
                                        c_back, c_save, c_next = st.columns([1, 1, 1.5])
                                        with c_back:
                                            if st.button("← Tải file khác", use_container_width=True, key="{btn_confirm_key}_back_1"):
                                                st.session_state.{step_var} = 1
                                                st.rerun()
                                        with c_save:
                                            if st.button("💾 Lưu mẫu", use_container_width=True, key="{btn_confirm_key}_save_tpl"):
                                                if tpl_name.strip():
                                                    save_mapping_template(tpl_name.strip(), dict(current_mapping))
                                                    st.success("Đã lưu mẫu!")
                                                else:
                                                    st.error("Vui lòng nhập tên mẫu.")
                                        with c_next:
                                            if st.button("Kiểm tra dữ liệu →", type="primary", use_container_width=True, key="{btn_confirm_key}_next_3"):
                                                missing_required = [c for c in required_cols if current_mapping.get(c) is None]
                                                if missing_required:
                                                    st.error(f"⚠️ Vui lòng ghép tất cả các cột bắt buộc: {{', '.join(missing_required)}}")
                                                else:
                                                    st.session_state.{step_var} = 3
                                                    st.rerun()'''
    content = content.replace(confirm_block_old, confirm_block_new)

    # 4. Find the start of the Preview/Validation block and wrap it in `if step == 3:`
    # We will remove `with col_right:` and `st.session_state["mapping_confirmed"] = True`
    preview_start_old = f'''                                                st.session_state["mapping_confirmed"] = True

                                    with col_right:
                                        st.caption("XEM TRƯỚC DỮ LIỆU GỐC")'''

    preview_start_new = f'''
                                    if st.session_state.{step_var} >= 3:
                                        st.caption("XEM TRƯỚC DỮ LIỆU ĐÃ GHÉP")
                                        
                                        nav_c1, nav_c2 = st.columns([1, 4])
                                        with nav_c1:
                                            if st.button("← Quay lại sửa ghép cột", key="{btn_confirm_key}_back_2"):
                                                st.session_state.{step_var} = 2
                                                st.rerun()
                                        st.markdown("---")'''
    content = content.replace(preview_start_old, preview_start_new)
    
    # Also clean up the indentation of the blocks. Because we removed `with col_left:` and `with col_right:`, 
    # we need to outdent the contents by 4 spaces.
    # It's safer to just let Python run with the extra indentation (Python doesn't care if there's extra indentation as long as it's consistent, but since `if st.session_state.import_step == 2:` replaces `with col_left:`, the indentation is perfectly preserved!)
    # `if st.session_state.import_step >= 3:` replaces `with col_right:`. So the indentation is also perfectly preserved!

    # 5. Remove the redundant `missing_required` check in Step 3 since we now block it at Step 2's button.
    # Wait, the validation block in Step 3 still needs to run `parse_excel_to_df`.
    # Let's just find `missing_required = [c for c in required_cols if current_mapping.get(c) is None]`
    
    check_req_old = '''                                    # Verify required mapping completed
                                    missing_required = [c for c in required_cols if current_mapping.get(c) is None]
                                    if missing_required:
                                        st.warning(f"⚠️ Vui lòng ghép tất cả các cột bắt buộc: {', '.join(missing_required)}")
                                    else:
                                        # Read & remap'''
                                        
    check_req_new = '''                                    if True:
                                        # Read & remap'''
    
    content = content.replace(check_req_old, check_req_new)
    
    # Save back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully refactored {filepath}")

# We will apply this to 3_NhatKyHoatDong.py first
refactor_ui(r"f:\annd\Quota\src\pages\3_NhatKyHoatDong.py", "import_step", "sp_confirm")
