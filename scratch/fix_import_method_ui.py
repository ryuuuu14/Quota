import os

file_path = r"f:\annd\Quota\src\pages\3_NhatKyHoatDong.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """                # Selection of import method
                import_method = st.radio(
                    "Phương thức nhập dữ liệu:",
                    options=["activities", "aggregate_totals"],
                    format_func=lambda x: "Nhập chi tiết Nhật ký Hoạt động" if x == "activities" else "Nhập tổng số giờ chuẩn tích lũy (Ghi đè)",
                    key="import_method_radio_choice"
                )"""

new_block = """                # Selection of import method
                st.markdown("##### ⚙️ Phương thức nhập dữ liệu:")
                import_method = st.radio(
                    "Phương thức nhập dữ liệu:",
                    options=["activities", "aggregate_totals"],
                    format_func=lambda x: "📝 Nhập chi tiết từng hoạt động (Khuyên dùng)" if x == "activities" else "⚡ Nhập tổng số Giờ chuẩn tích lũy (Ghi đè trực tiếp)",
                    key="import_method_radio_choice",
                    label_visibility="collapsed"
                )
                
                if import_method == "activities":
                    st.info("💡 **Chế độ Nhập chi tiết:** Bạn sẽ tải lên bảng Excel liệt kê từng công việc cụ thể (VD: Dạy lớp A, Nghiên cứu đề tài B). Hệ thống sẽ tự động đối chiếu định mức, áp dụng các quy tắc quy đổi và tự động tính toán số Giờ chuẩn (GC) cho từng dòng.")
                else:
                    st.warning("⚠️ **Chế độ Ghi đè tổng số:** Bạn sẽ tải lên bảng tổng hợp ĐÃ CÓ SẴN con số tổng GC của từng cán bộ. Dữ liệu này sẽ **ghi đè trực tiếp** lên hệ thống mà không qua tính toán quy đổi. Chỉ nên dùng khi bạn đã chốt số liệu thủ công từ trước.")
"""

content = content.replace(old_block, new_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully detailed the import method UI in 3_NhatKyHoatDong.py")
