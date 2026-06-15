import os

file_path = r"f:\annd\Quota\src\pages\3_NhatKyHoatDong.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """                                    conditional_cols = []
                                    if import_method == "activities":
                                        required_cols = ["Mã GV", "Tên loại hoạt động", "Ngày thực hiện", "Số lượng"]
                                        conditional_cols = ["Cấp lớp", "Loại lớp", "Số học viên", "Cấp đề tài"]
                                        optional_cols = ["Tác giả chính", "Giảng dạy tiếng nước ngoài", "Ghi chú"]
                                    else:"""

new_block = """                                    conditional_cols = []
                                    if import_method == "activities":
                                        is_teaching_sheet = any(k in selected_sheet.lower() for k in ["chuyên môn", "giảng dạy"])
                                        is_nckh_sheet = any(k in selected_sheet.lower() for k in ["nckh", "nghiên cứu"])

                                        required_cols = ["Mã GV", "Tên loại hoạt động", "Ngày thực hiện", "Số lượng"]
                                        
                                        if is_teaching_sheet:
                                            required_cols.extend(["Cấp lớp", "Loại lớp", "Số học viên"])
                                            optional_cols = ["Cấp đề tài", "Tác giả chính", "Giảng dạy tiếng nước ngoài", "Ghi chú"]
                                        elif is_nckh_sheet:
                                            required_cols.extend(["Cấp đề tài"])
                                            optional_cols = ["Cấp lớp", "Loại lớp", "Số học viên", "Tác giả chính", "Giảng dạy tiếng nước ngoài", "Ghi chú"]
                                        else:
                                            conditional_cols = ["Cấp lớp", "Loại lớp", "Số học viên", "Cấp đề tài"]
                                            optional_cols = ["Tác giả chính", "Giảng dạy tiếng nước ngoài", "Ghi chú"]
                                    else:"""

content = content.replace(old_block, new_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully added sheet-name dynamic logic to 3_NhatKyHoatDong.py")
