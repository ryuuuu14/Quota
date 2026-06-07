import json
from database import get_connection

def load_mapping_templates():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'excel_mapping_templates'")
        row = cursor.fetchone()
        if row:
            return json.loads(row["value"])
        return {}
    except Exception:
        return {}
    finally:
        conn.close()

def save_mapping_template(name, mapping):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'excel_mapping_templates'")
        row = cursor.fetchone()
        templates = json.loads(row["value"]) if row else {}
        templates[name] = mapping
        
        cursor.execute("""
            INSERT INTO settings (key, value, description)
            VALUES ('excel_mapping_templates', ?, 'Excel column mapping templates')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (json.dumps(templates),))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def delete_mapping_template(name):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'excel_mapping_templates'")
        row = cursor.fetchone()
        if row:
            templates = json.loads(row["value"])
            if name in templates:
                del templates[name]
                cursor.execute("""
                    UPDATE settings SET value = ? WHERE key = 'excel_mapping_templates'
                """, (json.dumps(templates),))
                conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
