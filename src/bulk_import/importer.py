import sqlite3
from database import get_connection

def import_teacher_totals(timeframe_id, parsed_df):
    """
    Thực hiện lưu dữ liệu đã parse vào bảng session_teacher_totals.
    Toàn bộ quá trình chạy trong một Transaction nguyên tử (Atomic).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Bắt đầu transaction thủ công (sqlite3 mặc định tự động bắt đầu nếu không tự thiết lập)
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Xóa toàn bộ dữ liệu cũ của timeframe này
        cursor.execute("DELETE FROM session_teacher_totals WHERE timeframe_id = ?", (timeframe_id,))
        
        # 2. Insert dữ liệu mới
        insert_query = """
        INSERT INTO session_teacher_totals (
            timeframe_id, teacher_id, giang_day_truc_tiep, hdcm_bd, nckh_total, nvk_total
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        insert_data = []
        for _, row in parsed_df.iterrows():
            insert_data.append((
                int(timeframe_id),
                int(row['teacher_id']),
                float(row['giang_day_truc_tiep']),
                float(row['hdcm_bd']),
                float(row['nckh_total']),
                float(row['nvk_total'])
            ))
            
        cursor.executemany(insert_query, insert_data)
        
        # Commit transaction
        conn.commit()
        return True, None
        
    except sqlite3.Error as e:
        # Rollback nếu xảy ra lỗi
        try:
            conn.rollback()
        except:
            pass
        return False, f"Lỗi cơ sở dữ liệu: {str(e)}"
        
    finally:
        conn.close()
