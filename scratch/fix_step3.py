import re

filepath = r"f:\annd\Quota\src\pages\3_NhatKyHoatDong.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the stray `with col_right:` block and everything up to `if True:`
# with the proper Step 3 header.

# We will just find "with col_right:" and replace it with:
new_step_3_header = """
                                    if st.session_state.import_step >= 3:
                                        st.caption("XEM TRƯỚC DỮ LIỆU ĐÃ GHÉP")
                                        
                                        nav_c1, nav_c2 = st.columns([1, 4])
                                        with nav_c1:
                                            if st.button("← Quay lại sửa ghép cột", key="sp_confirm_back_2"):
                                                st.session_state.import_step = 2
                                                st.rerun()
                                        st.markdown("---")"""

content = re.sub(r'(\s+)with col_right:\n\s+st\.caption\("XEM TRƯỚC DỮ LIỆU GỐC"\).*?(\s+if True:\n\s+# Read & remap)',
                 new_step_3_header + r'\2', 
                 content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed 3_NhatKyHoatDong.py")
