import bcrypt
import streamlit as st
from database import get_connection

ROLE_HIERARCHY = {"teacher": 0, "head_dept": 1, "admin": 2}


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Verifies user credentials from database using bcrypt.
    Handles legacy plaintext passwords with auto-upgrade on successful match.
    """
    if not username or not password:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT username, password, role, department_name, teacher_id FROM admin_users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        stored_password = row["password"]
        role = row["role"]

        if role == "teacher":
            return {"error": "teacher_disabled"}

        # Try bcrypt check first
        try:
            if bcrypt.checkpw(
                password.encode("utf-8"), stored_password.encode("utf-8")
            ):
                return {
                    "username": row["username"],
                    "role": role,
                    "department_name": row["department_name"],
                    "teacher_id": row["teacher_id"],
                }
        except ValueError:
            # Fallback for plaintext legacy passwords
            if stored_password == password:
                # Auto-upgrade to bcrypt
                hashed = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
                cursor.execute(
                    "UPDATE admin_users SET password = ? WHERE username = ?",
                    (hashed, username),
                )
                conn.commit()
                return {
                    "username": row["username"],
                    "role": role,
                    "department_name": row["department_name"],
                    "teacher_id": row["teacher_id"],
                }
    except Exception:
        pass
    finally:
        conn.close()
    return None


def login_user(user_dict: dict):
    """
    Sets session state keys for authenticated user.
    """
    st.session_state["is_admin"] = user_dict["role"] == "admin"
    st.session_state["admin_username"] = user_dict["username"]
    st.session_state["user_role"] = user_dict["role"]
    st.session_state["user_department"] = user_dict["department_name"]
    st.session_state["user_teacher_id"] = user_dict["teacher_id"]


def get_current_user() -> dict | None:
    """
    Retrieves current user dict from session state.
    """
    username = st.session_state.get("admin_username")
    if not username:
        return None
    return {
        "username": username,
        "role": st.session_state.get("user_role", "teacher"),
        "department_name": st.session_state.get("user_department"),
        "teacher_id": st.session_state.get("user_teacher_id"),
    }


def require_role(allowed_roles: list[str], page_title: str = "") -> bool:
    """
    Page guard. Redirects to login page if current role not permitted.
    """
    user = get_current_user()
    if not user or user["role"] not in allowed_roles:
        st.switch_page("pages/8_DangNhap.py")
        st.stop()
        return False
    return True


def get_scoped_teacher_ids(user: dict = None) -> list[int] | None:
    """
    Returns lists of visible teacher IDs based on role:
    - admin -> None (all)
    - head_dept -> teachers in department
    - unauthenticated -> None (public read-only)
    """
    if not user:
        user = get_current_user()
    if not user:
        return None

    role = user["role"]
    if role == "admin":
        return None

    if role == "head_dept":
        dept = user["department_name"]
        if not dept:
            return []

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Get latest department assignment for each teacher
            cursor.execute(
                """
                SELECT teacher_id FROM (
                    SELECT teacher_id, value_text,
                           ROW_NUMBER() OVER (PARTITION BY teacher_id ORDER BY start_date DESC, id DESC) as rn
                    FROM teacher_role_history
                    WHERE record_type = 'DEPARTMENT'
                ) WHERE rn = 1 AND value_text = ?
            """,
                (dept,),
            )
            return [row["teacher_id"] for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    if role == "teacher":
        tid = user["teacher_id"]
        return [tid] if tid is not None else []

    return None


def logout():
    """
    Clears all auth keys from session state.
    """
    for key in [
        "is_admin",
        "admin_username",
        "user_role",
        "user_department",
        "user_teacher_id",
    ]:
        if key in st.session_state:
            del st.session_state[key]


# --- Backward compatibility functions ---


def verify_admin(username, password) -> bool:
    """
    Checks if credentials are admin.
    """
    user = authenticate_user(username, password)
    return user is not None and user.get("role") == "admin"


def verify_department_code(dept_name, code) -> bool:
    """
    Verifies that department name matches the provided 4-digit code.
    """
    if not code:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT dept_code FROM departments WHERE name = ?", (dept_name,))
        row = cursor.fetchone()
        if row and row["dept_code"] == str(code).strip():
            return True
    except Exception:
        pass
    finally:
        conn.close()
    return False


def get_all_departments_with_codes():
    """
    Retrieves all departments.
    """
    conn = get_connection()
    cursor = conn.cursor()
    depts = []
    try:
        cursor.execute("SELECT name, is_teaching_dept, dept_code FROM departments")
        depts = [dict(row) for row in cursor.fetchall()]
    except Exception:
        pass
    finally:
        conn.close()
    return depts


def get_department_by_code(code):
    """
    Retrieves department details by code.
    """
    if not code:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT name FROM departments WHERE dept_code = ?", (str(code).strip(),)
        )
        row = cursor.fetchone()
        if row:
            return (row["name"], row["name"])
    except Exception:
        pass
    finally:
        conn.close()
    return None
