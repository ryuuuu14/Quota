import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

os.environ['DB_PATH'] = 'test_bulk.sqlite'

import unittest
import pandas as pd
import openpyxl
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from database import init_db, get_connection
from bulk_import.templates import generate_excel_template, ALLOWED_LOAI
from bulk_import.validator import validate_excel_data
from bulk_import.calculator import calculate_rows, aggregate_by_teacher, lookup_he_so_loai
from bulk_import.importer import import_bulk_data


class TestBulkImport(unittest.TestCase):
    def setUp(self):
        if os.path.exists('test_bulk.sqlite'):
            try:
                os.remove('test_bulk.sqlite')
            except:
                pass
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO timeframes (id, name, start_date, end_date) "
            "VALUES (1, 'Năm học 2025-2026', '2025-09-01', '2026-06-30')"
        )
        cursor.execute(
            "INSERT OR REPLACE INTO teachers (id, name, subject_group, employment_type) "
            "VALUES (1, 'Nguyễn Văn A', 'Chính trị/Nghiệp vụ', 'TEACHER')"
        )
        cursor.execute(
            "INSERT OR REPLACE INTO teachers (id, name, subject_group, employment_type) "
            "VALUES (2, 'Trần Thị B', 'Tự nhiên/Kỹ thuật', 'TEACHER')"
        )
        cursor.execute(
            "INSERT OR REPLACE INTO teacher_role_history "
            "(teacher_id, record_type, value_text, start_date, end_date) "
            "VALUES (1, 'TITLE', 'Giảng viên', '2025-09-01', NULL)"
        )
        cursor.execute(
            "INSERT OR REPLACE INTO teacher_role_history "
            "(teacher_id, record_type, value_text, start_date, end_date) "
            "VALUES (1, 'DEPARTMENT', 'Khoa Xã hội', '2025-09-01', NULL)"
        )
        cursor.execute(
            "INSERT OR REPLACE INTO teacher_role_history "
            "(teacher_id, record_type, value_text, start_date, end_date) "
            "VALUES (2, 'TITLE', 'Giảng viên chính', '2025-09-01', NULL)"
        )
        cursor.execute(
            "INSERT OR REPLACE INTO teacher_role_history "
            "(teacher_id, record_type, value_text, start_date, end_date) "
            "VALUES (2, 'DEPARTMENT', 'Khoa Kỹ thuật', '2025-09-01', NULL)"
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists('test_bulk.sqlite'):
            try:
                os.remove('test_bulk.sqlite')
            except:
                pass

    def test_template_generation(self):
        template_bytes = generate_excel_template("Năm học 2025-2026")
        self.assertIsNotNone(template_bytes)
        self.assertTrue(len(template_bytes) > 0)

        wb = openpyxl.load_workbook(BytesIO(template_bytes))
        sheet = wb.active
        self.assertIn("Nhập", wb.sheetnames[0])

        headers = [cell.value for cell in sheet[4]]
        self.assertIn("Mã GV (Khóa)", headers)
        self.assertIn("Họ tên (Khóa)", headers)
        self.assertIn("Chức danh (Khóa)", headers)
        self.assertIn("Đơn vị (Khóa)", headers)
        self.assertIn("Tên môn học", headers)
        self.assertIn("Loại", headers)
        self.assertIn("Sỉ số", headers)
        self.assertIn("Tiết quy đổi", headers)
        self.assertIn("Hệ số tín chỉ", headers)
        self.assertEqual(len(headers), 11)

        row5 = [cell.value for cell in sheet[5]]
        self.assertEqual(row5[0], 1)
        self.assertEqual(row5[1], "Nguyễn Văn A")

    def test_lookup_he_so_loai(self):
        self.assertEqual(lookup_he_so_loai("LT", 30), 1.0)
        self.assertEqual(lookup_he_so_loai("LT", 45), 1.2)
        self.assertEqual(lookup_he_so_loai("LT", 70), 1.4)
        self.assertEqual(lookup_he_so_loai("LT", 100), 1.5)
        self.assertEqual(lookup_he_so_loai("TH", 30), 1.0)
        self.assertEqual(lookup_he_so_loai("TH", 50), 1.2)
        self.assertEqual(lookup_he_so_loai("TH", 65), 1.4)
        self.assertEqual(lookup_he_so_loai("TH", 80), 1.5)
        self.assertEqual(lookup_he_so_loai("NN_CNTT", 20), 1.0)
        self.assertEqual(lookup_he_so_loai("NN_CNTT", 30), 1.2)
        self.assertEqual(lookup_he_so_loai("THẠC SĨ", 30), 1.3)
        self.assertEqual(lookup_he_so_loai("THẠC SĨ", 60), 1.5)
        self.assertEqual(lookup_he_so_loai("TIẾN SĨ", 10), 2.0)
        self.assertEqual(lookup_he_so_loai("LLCT TRUNG CẤP", 40), 1.0)
        self.assertEqual(lookup_he_so_loai("LLCT TRUNG CẤP", 55), 1.2)
        self.assertEqual(lookup_he_so_loai("LLCT CAO CẤP", 40), 1.3)
        self.assertEqual(lookup_he_so_loai("LLCT CAO CẤP", 55), 1.5)
        self.assertEqual(lookup_he_so_loai("BỒI DƯỠNG", 100), 1.0)

    def test_full_flow(self):
        template_bytes = generate_excel_template("Năm học 2025-2026")

        wb = openpyxl.load_workbook(BytesIO(template_bytes))
        sheet = wb.active

        sheet["E5"] = "Toán cao cấp"
        sheet["F5"] = "LT"
        sheet["G5"] = "01"
        sheet["H5"] = 45
        sheet["I5"] = 45
        sheet["J5"] = 2.0

        sheet["E5"] = "Toán cao cấp"
        sheet["F5"] = "LT"
        sheet["G5"] = "01"
        sheet["H5"] = 45
        sheet["I5"] = 45
        sheet["J5"] = 2.0

        sheet["E6"] = "Cấu trúc dữ liệu"
        sheet["F6"] = "LT"
        sheet["G6"] = "02"
        sheet["H6"] = 60
        sheet["I6"] = 30
        sheet["J6"] = 2.0

        out = BytesIO()
        wb.save(out)
        modified_bytes = out.getvalue()

        is_valid, errors, parsed_df = validate_excel_data(BytesIO(modified_bytes))
        self.assertTrue(is_valid, msg=f"Validation failed: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(parsed_df), 2)

        df_calc = calculate_rows(parsed_df)
        self.assertIn("he_so_lop_dong", df_calc.columns)
        self.assertIn("tiet_thuc_day", df_calc.columns)

        agg = aggregate_by_teacher(df_calc)
        self.assertEqual(len(agg), 2)
        t1 = agg[agg["teacher_id"] == 1]
        self.assertFalse(t1.empty)

        success, err = import_bulk_data(1, df_calc, modified_bytes, "test.xlsx")
        self.assertTrue(success, msg=f"Import failed: {err}")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT giang_day_truc_tiep FROM session_teacher_totals "
            "WHERE timeframe_id = 1 AND teacher_id = 1"
        )
        row1 = cur.fetchone()
        self.assertIsNotNone(row1)
        self.assertGreater(row1["giang_day_truc_tiep"], 0)

        cur.execute(
            "SELECT COUNT(*) as cnt FROM bulk_teaching_assignments WHERE timeframe_id = 1"
        )
        cnt = cur.fetchone()["cnt"]
        self.assertEqual(cnt, 2)

        cur.execute(
            "SELECT id FROM bulk_import_files WHERE timeframe_id = 1"
        )
        self.assertIsNotNone(cur.fetchone())

        conn.close()


if __name__ == "__main__":
    unittest.main()
