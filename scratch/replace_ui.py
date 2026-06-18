import codecs

with codecs.open('f:/annd/Quota/src/pages/4_CaiDatHeThong.py', 'r', 'utf-8-sig') as f:
    lines = f.readlines()

out_lines = []
skip = False
for i, line in enumerate(lines):
    if "Ghi nhận các ngày nghỉ trong năm học (Tết Nguyên đán, Nghỉ hè, 30/4, nghỉ do bão lũ, v.v.)." in line:
        out_lines.append('<p style="color: var(--md-on-surface-variant); font-size: 14px;">\n')
        out_lines.append('Ghi nhận các ngày nghỉ trong năm học (Tết Nguyên đán, Nghỉ hè, 30/4, v.v.).<br>\n')
        out_lines.append('<b>QUAN TRỌNG:</b> Luật quy định 44 tuần làm việc + 8 tuần nghỉ (52 tuần/năm). \n')
        out_lines.append('Nếu không khai báo đủ 8 tuần nghỉ (Tết + Hè), hệ thống đếm dư số tuần làm việc (>44) \n')
        out_lines.append('→ Tự động kích hoạt cơ chế Cap (ép định mức bảo vệ GV) → Sai số tính toán miễn giảm (vd: 177.2 -> 186.7).\n')
        out_lines.append('Bắt buộc nhập 8 tuần nghỉ để hệ thống trừ lùi về 44 tuần chuẩn.\n')
        out_lines.append('</p>\n')
        out_lines.append('    """, unsafe_allow_html=True)\n\n')
        
        # Add auto seed button
        out_lines.append('    if not read_only:\n')
        out_lines.append('        if st.button("⚡ Tự động điền 8 tuần nghỉ chuẩn (Tết & Hè) cho Năm học hiện tại"):\n')
        out_lines.append('            try:\n')
        out_lines.append('                cursor = conn.cursor()\n')
        out_lines.append('                cursor.execute("SELECT id FROM timeframes ORDER BY start_date DESC LIMIT 1")\n')
        out_lines.append('                tf_row = cursor.fetchone()\n')
        out_lines.append('                if tf_row:\n')
        out_lines.append('                    tf_id = tf_row[0]\n')
        out_lines.append('                    cursor.execute("INSERT INTO academic_holidays (timeframe_id, name, start_date, end_date) VALUES (?, ?, ?, ?)", (tf_id, "Nghỉ Tết Nguyên Đán", "2026-02-02", "2026-03-01"))\n')
        out_lines.append('                    cursor.execute("INSERT INTO academic_holidays (timeframe_id, name, start_date, end_date) VALUES (?, ?, ?, ?)", (tf_id, "Nghỉ Hè", "2026-06-08", "2026-07-05"))\n')
        out_lines.append('                    conn.commit()\n')
        out_lines.append('                    st.success("Đã tự động thêm 8 tuần nghỉ. Định mức đã được nắn về chuẩn 44 tuần!")\n')
        out_lines.append('                    st.rerun()\n')
        out_lines.append('                else:\n')
        out_lines.append('                    st.error("Chưa có Năm học nào được cấu hình.")\n')
        out_lines.append('            except Exception as e:\n')
        out_lines.append('                conn.rollback()\n')
        out_lines.append('                st.error(f"Lỗi: {e}")\n')

        skip = True
    elif skip and '""", unsafe_allow_html=True)' in line:
        skip = False
    elif not skip:
        # Check warning replacement
        if "Tính toán miễn giảm (như thai sản, đi học) sẽ bị sai lệch nếu chưa cấu hình đủ Nghỉ hè và Tết (cần tối thiểu ~40 ngày)" in line:
            line = line.replace("Tính toán miễn giảm (như thai sản, đi học) sẽ bị sai lệch nếu chưa cấu hình đủ Nghỉ hè và Tết (cần tối thiểu ~40 ngày)", "Tính toán miễn giảm sẽ bị lệch do Cap kích hoạt. Cần tối thiểu ~56 ngày (8 tuần)")
            line = line.replace("< 40:", "< 50:")
        
        out_lines.append(line)

with codecs.open('f:/annd/Quota/src/pages/4_CaiDatHeThong.py', 'w', 'utf-8-sig') as f:
    f.writelines(out_lines)

print("Done")
