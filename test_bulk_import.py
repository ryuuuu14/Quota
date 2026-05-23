import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ALWAYS set env var BEFORE importing database module
os.environ['DB_PATH'] = 'test_bulk.sqlite'

import unittest
import pandas as pd
import openpyxl

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from database import init_db, get_connection
from bulk_import.templates import generate_excel_template
from bulk_import.validator import validate_excel_data
from bulk_import.importer import import_teacher_totals

class TestBulkImport(unittest.TestCase):
    def setUp(self):
        if os.path.exists('test_bulk.sqlite'):
            try: os.remove('test_bulk.sqlite')
            except: pass
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO timeframes (id, name, start_date, end_date) VALUES (1, 'Năm học 2025-2026', '2025-09-01', '2026-06-30')")
        cursor.execute("INSERT OR REPLACE INTO teachers (id, name, subject_group) VALUES (1, 'Nguyễn Văn A', 'Xã hội')")
        cursor.execute("INSERT OR REPLACE INTO teachers (id, name, subject_group) VALUES (2, 'Trần Thị B', 'Tự nhiên/Kỹ thuật')")
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists('test_bulk.sqlite'):
            try: os.remove('test_bulk.sqlite')
            except: pass

    def test_template_generation(self):
        template_bytes = generate_excel_template("Năm học 2025-2026")
        self.assertIsNotNone(template_bytes)
        self.assertTrue(len(template_bytes) > 0)
        
        from io import BytesIO
        wb = openpyxl.load_workbook(BytesIO(template_bytes))
        self.assertIn("Nhập dữ liệu", wb.sheetnames)
        sheet = wb["Nhập dữ liệu"]
        
        headers = [cell.value for cell in sheet[4]]
        self.assertIn("Mã GV (Khóa)", headers)
        self.assertIn("Họ tên (Khóa)", headers)
        
        row5_vals = [cell.value for cell in sheet[5]]
        self.assertEqual(row5_vals[0], 1)
        self.assertEqual(row5_vals[1], "Nguyễn Văn A")

    def test_validation_and_import(self):
        # Generate template
        template_bytes = generate_excel_template("Năm học 2025-2026")
        
        # Open and modify values in template
        from io import BytesIO
        wb = openpyxl.load_workbook(BytesIO(template_bytes))
        sheet = wb["Nhập dữ liệu"]
        
        # Nguyễn Văn A (Row 5): Giang day = 150.0, hdcm = 20.0, nckh = 30.0, nvk = 40.0
        sheet["C5"] = 150.0
        sheet["D5"] = 20.0
        sheet["E5"] = 30.0
        sheet["F5"] = 40.0
        
        out = BytesIO()
        wb.save(out)
        modified_bytes = out.getvalue()
        
        # Run validation
        is_valid, errors, parsed_df = validate_excel_data(BytesIO(modified_bytes))
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(parsed_df), 2)
        
        # Import to DB
        success, err = import_teacher_totals(1, parsed_df)
        self.assertTrue(success)
        self.assertIsNone(err)
        
        # Check database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM session_teacher_totals WHERE teacher_id = 1")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row['giang_day_truc_tiep'], 150.0)
        self.assertEqual(row['hdcm_bd'], 20.0)
        self.assertEqual(row['nckh_total'], 30.0)
        self.assertEqual(row['nvk_total'], 40.0)

if __name__ == "__main__":
    unittest.main()
