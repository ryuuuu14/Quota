import re

def fix_file(filepath, step_var, upload_var, old_btn_key, new_btn_key):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Remove the old "Next" button from step 1
    old_btn_pattern = rf"""\n\s*if st\.button\("Tiếp theo →", key="{old_btn_key}"\):\n\s*st\.session_state\.{step_var} = 2\n\s*st\.rerun\(\)\n"""
    content = re.sub(old_btn_pattern, '\n', content)
    
    # 2. Find the "else:" block dynamically
    # We look for "else:\n(spaces)file_bytes = {upload_var}.read()"
    pattern = r"(\s+else:\n)(\s+)file_bytes = " + re.escape(upload_var) + r"\.read\(\)"
    
    match = re.search(pattern, content)
    if not match:
        print(f"Target not found in {filepath}!")
        return
        
    start_idx = match.start()
    else_line = match.group(1) # "\n                 else:\n" (or similar)
    indent_spaces = match.group(2) # "                    "
    
    before = content[:start_idx]
    after = content[start_idx + len(match.group(0)):]
    
    # The block's baseline indentation is the length of `indent_spaces`
    baseline_indent = len(indent_spaces)
    
    lines = after.split('\n')
    indented_block_lines = []
    rest_lines = []
    
    inside_block = True
    for line in lines:
        if inside_block:
            if not line.strip():
                indented_block_lines.append(line)
            else:
                leading_spaces = len(line) - len(line.lstrip(' '))
                if leading_spaces < baseline_indent:
                    inside_block = False
                    rest_lines.append(line)
                else:
                    indented_block_lines.append(line)
        else:
            rest_lines.append(line)
            
    base_indent_str = " " * baseline_indent
    
    new_logic = match.group(0) + f"""

{base_indent_str}if st.session_state.{step_var} == 1:
{base_indent_str}    st.success("✅ Đã tải file lên thành công. Vui lòng nhấn **Tiếp theo** để chuyển sang bước Ghép cột.")
{base_indent_str}    if st.button("Tiếp theo →", key="{new_btn_key}"):
{base_indent_str}        st.session_state.{step_var} = 2
{base_indent_str}        st.rerun()

{base_indent_str}if st.session_state.{step_var} >= 2:"""
                        
    new_indented_lines = []
    for line in indented_block_lines:
        if not line.strip():
            new_indented_lines.append(line)
        else:
            new_indented_lines.append("    " + line) # Add 4 spaces
            
    new_content = before + new_logic + '\n' + '\n'.join(new_indented_lines) + '\n' + '\n'.join(rest_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Successfully patched {filepath}")

fix_file(r'f:\annd\Quota\src\pages\2_QuanLyCanBo.py', 'import_step_teachers', 'uploaded_teachers', 'step1_next_teachers', 'step1_next_teachers_after_upload')
