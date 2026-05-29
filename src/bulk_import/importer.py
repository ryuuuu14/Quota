import sqlite3
from database import get_connection

def import_bulk_data(timeframe_id, df_calculated, excel_bytes, filename):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN TRANSACTION")

        cursor.execute("DELETE FROM bulk_teaching_assignments WHERE timeframe_id = ?", (timeframe_id,))
        cursor.execute("DELETE FROM session_teacher_totals WHERE timeframe_id = ?", (timeframe_id,))
        cursor.execute("DELETE FROM bulk_import_files WHERE timeframe_id = ?", (timeframe_id,))

        insert_assign = """
        INSERT INTO bulk_teaching_assignments
            (timeframe_id, teacher_id, subject_name, loai, nhom, si_so,
             tiet_quy_doi, he_so_tin_chi, ghi_chu, he_so_lop_dong, tiet_thuc_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = []
        for _, r in df_calculated.iterrows():
            rows.append((
                int(timeframe_id),
                int(r["teacher_id"]),
                str(r["subject_name"]),
                str(r["loai"]),
                str(r.get("nhom", "") or ""),
                int(r["si_so"]),
                float(r["tiet_quy_doi"]),
                float(r["he_so_tin_chi"]),
                str(r.get("ghi_chu", "") or ""),
                float(r["he_so_lop_dong"]),
                float(r["tiet_thuc_day"]),
            ))
        cursor.executemany(insert_assign, rows)

        agg = df_calculated.groupby("teacher_id")["tiet_thuc_day"].sum().reset_index()
        insert_session = """
        INSERT INTO session_teacher_totals
            (timeframe_id, teacher_id, giang_day_truc_tiep, hdcm_bd, nckh_total, nvk_total)
        VALUES (?, ?, ?, 0, 0, 0)
        """
        for _, r in agg.iterrows():
            cursor.execute(insert_session, (
                int(timeframe_id), int(r["teacher_id"]), float(r["tiet_thuc_day"])
            ))

        cursor.execute(
            "INSERT INTO bulk_import_files (timeframe_id, filename, file_blob) VALUES (?, ?, ?)",
            (int(timeframe_id), filename, sqlite3.Binary(excel_bytes))
        )

        conn.commit()
        return True, None

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, str(e)

    finally:
        conn.close()
