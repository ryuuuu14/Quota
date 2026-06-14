import sqlite3
import os
from database import get_connection

REDUCTIONS = [
    # Core Roles from Điều 7
    ('Hiệu trưởng', 'ROLE', 90.0, 0.0, None),
    ('Phó Bí thư Đảng ủy Trường', 'ROLE', 85.0, 0.0, None),
    ('Phó Hiệu trưởng', 'ROLE', 80.0, 0.0, None),
    ('Trưởng phòng', 'ROLE', 75.0, 0.0, None),
    ('Phó Trưởng phòng', 'ROLE', 70.0, 0.0, None),
    ('Trưởng khoa', 'ROLE', 40.0, 0.0, None),
    ('Phó Trưởng khoa', 'ROLE', 30.0, 0.0, None),
    ('Công tác tại phòng, trung tâm không giữ chức vụ lãnh đạo', 'ROLE', 60.0, 0.0, None),

    # Table 2 rules (Miễn giảm theo tỉ lệ phần trăm còn lại)
    # Format: (Name, Type, Teaching_Reduction_Pct, NCKH_Reduction_Pct, Condition_Note)
    
    ('Ủy viên UBKT Đảng ủy Trường (Tại đơn vị giảng dạy)', 'ROLE', 15.0, 0.0, None),
    ('Ủy viên UBKT Đảng ủy Trường (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 65.0, 0.0, None),
    
    ('Cấp ủy chi bộ hoặc Đảng bộ cơ sở (Tại đơn vị giảng dạy)', 'ROLE', 15.0, 0.0, None),
    ('Cấp ủy chi bộ hoặc Đảng bộ cơ sở (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 65.0, 0.0, None),
    
    ('Phó Chủ nhiệm chuyên trách UBKT (Tại đơn vị giảng dạy)', 'ROLE', 15.0, 0.0, None),
    ('Phó Chủ nhiệm chuyên trách UBKT (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 65.0, 0.0, None),
    
    ('Ủy viên chuyên trách UBKT (Tại đơn vị giảng dạy)', 'ROLE', 10.0, 0.0, None),
    ('Ủy viên chuyên trách UBKT (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 63.0, 0.0, None),
    
    ('Bí thư Đoàn Thanh niên Trường (Tại đơn vị giảng dạy)', 'ROLE', 20.0, 0.0, None),
    ('Bí thư Đoàn Thanh niên Trường (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 70.0, 0.0, None),
    
    ('Phó Bí thư Đoàn Thanh niên Trường (Tại đơn vị giảng dạy)', 'ROLE', 10.0, 0.0, None),
    ('Phó Bí thư Đoàn Thanh niên Trường (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 65.0, 0.0, None),
    
    ('Ủy viên BCH Đoàn Thanh niên Trường (Tại đơn vị giảng dạy)', 'ROLE', 5.0, 0.0, None),
    ('Ủy viên BCH Đoàn Thanh niên Trường (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 63.0, 0.0, None),
    
    ('Chủ tịch Hội Phụ nữ Trường (Tại đơn vị giảng dạy)', 'ROLE', 20.0, 0.0, None),
    ('Chủ tịch Hội Phụ nữ Trường (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 70.0, 0.0, None),
    
    ('Phó Chủ tịch Hội Phụ nữ Trường (Tại đơn vị giảng dạy)', 'ROLE', 10.0, 0.0, None),
    ('Phó Chủ tịch Hội Phụ nữ Trường (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 65.0, 0.0, None),
    
    ('Ủy viên BCH Hội Phụ nữ Trường (Tại đơn vị giảng dạy)', 'ROLE', 5.0, 0.0, None),
    ('Ủy viên BCH Hội Phụ nữ Trường (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 63.0, 0.0, None),
    
    ('Đội trưởng (Tại đơn vị giảng dạy)', 'ROLE', 68.0, 0.0, None),
    ('Phó Đội trưởng (Tại đơn vị giảng dạy)', 'ROLE', 64.0, 0.0, None),
    
    ('Tham gia Ban Chủ nhiệm CLB học tập (Tại đơn vị giảng dạy)', 'ROLE', 10.0, 0.0, None),
    ('Tham gia Ban Chủ nhiệm CLB học tập (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 63.0, 0.0, None),
    
    ('Giáo vụ Khoa (Tối đa 20% nếu 1 người)', 'ROLE', 20.0, 0.0, None),
    
    ('Quản lý phòng học TH/TN (Tại đơn vị giảng dạy)', 'ROLE', 15.0, 0.0, None),
    ('Quản lý phòng học TH/TN (Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm)', 'ROLE', 65.0, 0.0, None),
    
    # Missing T04 Rules (Điều 10 & 11)
    ('Trợ giảng (12 tháng đầu)', 'SPECIAL', 50.0, 0.0, 'Chỉ áp dụng 12 tháng tính từ ngày bổ nhiệm.'),
    ('Trợ giảng (tháng 13-24)', 'SPECIAL', 20.0, 0.0, 'Chỉ áp dụng từ tháng thứ 13 đến hết tháng 24.'),
    
    ('Đi thực tế / Trưng tập (dưới 10 tháng)', 'SPECIAL', 100.0, 0.0, 'Yêu cầu tổng thời gian < 10 tháng.'),
    ('Đi thực tế / Trưng tập (từ 10 tháng trở lên)', 'SPECIAL', 100.0, 100.0, 'Yêu cầu tổng thời gian >= 10 tháng.'),
    
    ('Đi học / Bồi dưỡng (từ 6 đến dưới 10 tháng)', 'SPECIAL', 100.0, 50.0, 'Yêu cầu thời gian >= 6 tháng.'),
    ('Đi học / Bồi dưỡng (từ 10 tháng trở lên)', 'SPECIAL', 100.0, 100.0, 'Yêu cầu thời gian >= 10 tháng.'),
    ('Đi học / Bồi dưỡng (dưới 6 tháng)', 'SPECIAL', 100.0, 0.0, 'Yêu cầu thời gian < 6 tháng.'),
    
    ('Nam nuôi con nhỏ (vợ mất) dưới 12 tháng', 'SPECIAL', 0.0, 15.0, 'Yêu cầu có xác nhận của địa phương.'),
    ('Nam nuôi con nhỏ (vợ mất) từ 12 đến 36 tháng', 'SPECIAL', 0.0, 10.0, 'Yêu cầu có xác nhận của địa phương.'),
    
    ('Nữ nuôi con nhỏ dưới 12 tháng', 'SPECIAL', 15.0, 60.0, 'Chỉ áp dụng cho giáo viên Nữ.'),
    ('Nữ nuôi con nhỏ từ 12 đến dưới 36 tháng', 'SPECIAL', 10.0, 30.0, 'Chỉ áp dụng cho giáo viên Nữ.'),
    
    ('Đang nghiên cứu luận án, đề án', 'SPECIAL', 15.0, 0.0, None),
    ('Thành viên Tổ tư vấn/Nhóm nghiên cứu', 'SPECIAL', 15.0, 0.0, None),
    
    ('Công tác tại phòng không giữ chức danh (Giảm NCKH)', 'SPECIAL', 0.0, 50.0, 'Không áp dụng cho Giáo sư, Phó Giáo sư.'),
    ('Nghỉ có phép', 'SPECIAL', 100.0, 0.0, 'Khấu trừ giờ dạy theo thời gian nghỉ phép'),
]


def run():
    conn = get_connection()
    cursor = conn.cursor()
    added, skipped = 0, 0
    for r in REDUCTIONS:
        try:
            cursor.execute(
                "INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct, condition_note) VALUES (?,?,?,?,?)", r
            )
            added += 1
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                skipped += 1
            else:
                print(f"Error inserting {r[0]}: {e}")
                skipped += 1
    conn.commit()
    conn.close()
    print(f"Done. Added: {added}, Skipped (already exist): {skipped}")


if __name__ == "__main__":
    run()
