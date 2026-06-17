import unittest
import sqlite3
import os
from database import init_db, get_connection, delete_timeframe, DB_PATH

class TestCascadeDelete(unittest.TestCase):
    def setUp(self):
        # We will use the actual DB path for testing or a separate test db.
        # Since DB_PATH is configurable, we can use it. But let's verify on a test db.
        self.test_db_path = "test_cascade_delete.sqlite"
        os.environ["DB_PATH"] = self.test_db_path
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        init_db()
        self.conn = get_connection()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.environ.pop("DB_PATH", None)

    def test_cascade_delete_timeframe(self):
        cursor = self.conn.cursor()
        
        # 1. Create a timeframe
        cursor.execute("INSERT INTO timeframes (name, start_date, end_date) VALUES ('TF Test', '2026-09-01', '2027-06-30')")
        tf_id = cursor.lastrowid
        
        # 2. Add dependent records
        # academic_holidays
        cursor.execute("INSERT INTO academic_holidays (timeframe_id, name, start_date, end_date) VALUES (?, 'Holiday Test', '2026-12-24', '2027-01-02')", (tf_id,))
        holiday_id = cursor.lastrowid
        
        # activity_logs (needs a teacher first)
        cursor.execute("INSERT INTO teachers (name, subject_group, employment_type) VALUES ('Teacher Test', 'MATH', 'TEACHER')")
        teacher_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO activity_types (name, category, unit, base_conversion_rate) VALUES ('Act Test', 'Giảng dạy', 'Giờ', 1.0)")
        act_type_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, class_level, class_type, student_count, converted_hours, timeframe_id)
            VALUES (?, ?, '2026-10-10', 10.0, 'L1', 'T1', 30, 10.0, ?)
        """, (teacher_id, act_type_id, tf_id))
        log_id = cursor.lastrowid

        # payroll_records
        cursor.execute("""
            INSERT INTO payroll_records (teacher_id, timeframe_id, task_type, quantity, amount_vnd, log_date)
            VALUES (?, ?, 'LCB', 10.0, 100000.0, '2026-10-10')
        """, (teacher_id, tf_id))
        payroll_id = cursor.lastrowid

        # manual_conversions
        cursor.execute("""
            INSERT INTO manual_conversions (teacher_id, timeframe_id, from_category, to_category, from_amount, to_amount)
            VALUES (?, ?, 'NCKH', 'Giảng dạy', 5.0, 5.0)
        """, (teacher_id, tf_id))
        conv_id = cursor.lastrowid

        # session_teacher_totals
        cursor.execute("""
            INSERT INTO session_teacher_totals (timeframe_id, teacher_id, giang_day_truc_tiep)
            VALUES (?, ?, 10.0)
        """, (tf_id, teacher_id))

        # bulk_teaching_assignments
        cursor.execute("""
            INSERT INTO bulk_teaching_assignments (timeframe_id, teacher_id, subject_name, loai, si_so, tiet_quy_doi, he_so_lop_dong, tiet_thuc_day)
            VALUES (?, ?, 'Math', 'Lý thuyết', 30, 10.0, 1.0, 10.0)
        """, (tf_id, teacher_id))

        # bulk_import_files
        cursor.execute("""
            INSERT INTO bulk_import_files (timeframe_id, filename, file_blob)
            VALUES (?, 'test.xlsx', ?)
        """, (tf_id, b"dummy blob"))

        # teacher_calculated_totals
        cursor.execute("""
            INSERT INTO teacher_calculated_totals (timeframe_id, teacher_id, tong_gc_da_thuc_hien)
            VALUES (?, ?, 10.0)
        """, (tf_id, teacher_id))

        self.conn.commit()

        # Verify records exist before deletion
        cursor.execute("SELECT COUNT(*) FROM timeframes WHERE id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 1)
        
        cursor.execute("SELECT COUNT(*) FROM academic_holidays WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 1)
        
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 1)

        # 3. Perform cascade delete using the function
        delete_timeframe(tf_id, conn=self.conn)
        self.conn.commit()

        # 4. Verify all records have been deleted
        cursor.execute("SELECT COUNT(*) FROM timeframes WHERE id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)
        
        cursor.execute("SELECT COUNT(*) FROM academic_holidays WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)
        
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT COUNT(*) FROM payroll_records WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT COUNT(*) FROM manual_conversions WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT COUNT(*) FROM session_teacher_totals WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT COUNT(*) FROM bulk_teaching_assignments WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT COUNT(*) FROM bulk_import_files WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT COUNT(*) FROM teacher_calculated_totals WHERE timeframe_id = ?", (tf_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

if __name__ == "__main__":
    unittest.main()
