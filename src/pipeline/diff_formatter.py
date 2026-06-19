import json
import pandas as pd


# Display column definitions per domain — maps DB column → friendly header
DISPLAY_CONFIG = {
    "teachers": {
        "key_cols": ["teacher_name", "department"],
        "display_cols": [
            "row_num",
            "teacher_id",
            "teacher_name",
            "department",
            "title",
            "role",
            "employment_type",
            "subject_group",
        ],
        "rename": {
            "row_num": "Dòng",
            "teacher_id": "Mã GV",
            "teacher_name": "Họ tên",
            "department": "Đơn vị",
            "title": "Chức danh",
            "role": "Chức vụ",
            "employment_type": "Loại HĐ",
            "subject_group": "Tổ môn",
        },
    },
    "activities": {
        "key_cols": ["teacher_name", "activity_type_name", "log_date", "quantity"],
        "display_cols": [
            "row_num",
            "teacher_name",
            "activity_type_name",
            "log_date",
            "quantity",
            "timeframe_name",
        ],
        "rename": {
            "row_num": "Dòng",
            "teacher_name": "Mã GV",
            "activity_type_name": "Hoạt động",
            "log_date": "Ngày",
            "quantity": "Số lượng",
            "timeframe_name": "Năm học",
        },
    },
    "schedule": {
        "key_cols": ["teacher_name", "subject_name", "loai", "nhom"],
        "display_cols": [
            "row_num",
            "teacher_name",
            "subject_name",
            "loai",
            "nhom",
            "si_so",
            "tiet_quy_doi",
            "he_so_tin_chi",
        ],
        "rename": {
            "row_num": "Dòng",
            "teacher_name": "Họ tên",
            "subject_name": "Tên môn",
            "loai": "Loại",
            "nhom": "Nhóm",
            "si_so": "Sỉ số",
            "tiet_quy_doi": "Tiết QĐ",
            "he_so_tin_chi": "HS TC",
        },
    },
    "aggregate_totals": {
        "key_cols": ["teacher_name"],
        "display_cols": [
            "row_num",
            "teacher_name",
            "tong_gc_da_thuc_hien",
            "nckh_da_thuc_hien",
            "so_gio_duoc_mien_giam",
            "dinh_muc_gc_phai_thuc_hien",
            "timeframe_name",
        ],
        "rename": {
            "row_num": "Dòng",
            "teacher_name": "Mã GV",
            "tong_gc_da_thuc_hien": "Tổng GC thực hiện",
            "nckh_da_thuc_hien": "NCKH thực hiện",
            "so_gio_duoc_mien_giam": "Miễn giảm",
            "dinh_muc_gc_phai_thuc_hien": "Định mức GC",
            "timeframe_name": "Năm học",
        },
    },
}

STATUS_LABELS = {
    "NEW": "🆕 Mới",
    "UPDATE": "🟡 Cập nhật",
    "DELETE": "🔴 Xóa",
    "SKIP": "⚪ Bỏ qua",
}


def format_cell_value(val):
    """Format a single cell value for display — handles None, NaN, numbers."""
    if val is None:
        return "—"
    if isinstance(val, float):
        if val != val:
            return "—"
        if val == int(val):
            return str(int(val))
        return f"{val:,.2f}"
    return str(val)


def format_diff_json(
    diff_json_str: str, domain: str, staging_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Convert a raw diff_json string + staging DataFrame into a display-ready DataFrame
    with cell-level styling hints for AgGrid.

    Parameters
    ----------
    diff_json_str : str
        JSON string from import_batches.diff_json (or empty string "{}").
    domain : str
        One of VALID_DOMAINS.
    staging_df : pd.DataFrame
        The staging rows (used for row_num and current values).

    Returns
    -------
    pd.DataFrame with columns:
        - All display columns from DISPLAY_CONFIG
        - _diff_marker (str): machine-readable marker
        - _diff_detail (str): human-readable summary
        - _cell_styles (dict): {col_name: "added"/"removed"/"changed"} for cell-level CSS
    """
    if domain not in DISPLAY_CONFIG:
        raise ValueError(f"Domain '{domain}' not configured for display")

    config = DISPLAY_CONFIG[domain]
    staging_df = staging_df.copy()

    if "diff_marker" not in staging_df.columns:
        staging_df["diff_marker"] = "NEW"
    if "diff_detail" not in staging_df.columns:
        staging_df["diff_detail"] = ""

    staging_df["_diff_marker"] = staging_df["diff_marker"]
    staging_df["_cell_styles"] = None

    if not diff_json_str or diff_json_str in ("{}", "null", "None", ""):
        staging_df["_diff_marker_display"] = staging_df["_diff_marker"].map(
            STATUS_LABELS
        )
        return _apply_display_columns(staging_df, config)

    try:
        diff_data = (
            json.loads(diff_json_str)
            if isinstance(diff_json_str, str)
            else diff_json_str
        )
    except (json.JSONDecodeError, TypeError):
        staging_df["_diff_marker_display"] = staging_df["_diff_marker"].map(
            STATUS_LABELS
        )
        return _apply_display_columns(staging_df, config)

    if not isinstance(diff_data, dict) or "diffs" not in diff_data:
        staging_df["_diff_marker_display"] = staging_df["_diff_marker"].map(
            STATUS_LABELS
        )
        return _apply_display_columns(staging_df, config)

    key_cols = config["key_cols"]
    diffs = diff_data.get("diffs", {})

    def _make_key(row):
        return "|".join(str(row.get(k, "")).strip().lower() for k in key_cols)

    for idx, row in staging_df.iterrows():
        key = _make_key(row)
        diff_entry = diffs.get(key)

        if diff_entry is None:
            continue

        marker = diff_entry.get("marker", row.get("diff_marker", "NEW"))
        staging_df.at[idx, "_diff_marker"] = marker

        changes = diff_entry.get("changes", {})
        cell_styles = {}

        if marker == "NEW":
            cell_styles = {
                col: "added"
                for col in config["display_cols"]
                if col in staging_df.columns
            }
        elif marker == "DELETE":
            cell_styles = {
                col: "removed"
                for col in config["display_cols"]
                if col in staging_df.columns
            }
        elif marker == "UPDATE":
            for field, change in changes.items():
                stylized_col = field
                if stylized_col in staging_df.columns:
                    cell_styles[stylized_col] = "changed"

        staging_df.at[idx, "_cell_styles"] = cell_styles

    staging_df["_diff_marker_display"] = staging_df["_diff_marker"].map(STATUS_LABELS)

    return _apply_display_columns(staging_df, config)


def _apply_display_columns(staging_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Select and rename display columns, attach diff metadata."""
    display_cols = config["display_cols"]
    rename = config["rename"]

    available = [c for c in display_cols if c in staging_df.columns]
    result = staging_df[available].rename(columns=rename)

    result["_diff_marker"] = staging_df["_diff_marker"].values
    result["_diff_detail"] = staging_df.get("diff_detail", "")
    result["_diff_marker_display"] = staging_df.get(
        "_diff_marker_display", staging_df["_diff_marker"]
    )
    result["_cell_styles"] = staging_df.get("_cell_styles", None)

    return result


def build_diff_detail_text(
    staging_df: pd.DataFrame, diff_json_str: str, domain: str
) -> pd.Series:
    """
    Build a human-readable _diff_detail string from diff_json for rows that lack it.
    """
    try:
        diff_data = (
            json.loads(diff_json_str)
            if isinstance(diff_json_str, str)
            else diff_json_str
        )
    except (json.JSONDecodeError, TypeError):
        return staging_df.get("diff_detail", pd.Series([""] * len(staging_df)))

    if not isinstance(diff_data, dict) or "diffs" not in diff_data:
        return staging_df.get("diff_detail", pd.Series([""] * len(staging_df)))

    config = DISPLAY_CONFIG.get(domain)
    if not config:
        return staging_df.get("diff_detail", pd.Series([""] * len(staging_df)))

    key_cols = config["key_cols"]
    diffs = diff_data.get("diffs", {})
    details = []

    for _, row in staging_df.iterrows():
        key = "|".join(str(row.get(k, "")).strip().lower() for k in key_cols)
        entry = diffs.get(key)
        if not entry:
            details.append("")
            continue

        marker = entry.get("marker", "SKIP")
        if marker == "NEW":
            details.append("Dòng mới")
        elif marker == "DELETE":
            details.append("Dòng bị xóa")
        elif marker == "SKIP":
            details.append("Không thay đổi")
        elif marker == "UPDATE":
            changes = entry.get("changes", {})
            parts = []
            for field, change in changes.items():
                old_val = format_cell_value(change.get("old"))
                new_val = format_cell_value(change.get("new"))
                parts.append(f"{field}: {old_val} → {new_val}")
            details.append("; ".join(parts) if parts else "Có thay đổi")
        else:
            details.append("")

    return pd.Series(details)
