import pandas as pd
import io

def sanitize_value(val):
    """
    Sanitize string values against CSV/Formula injection and normalize empty/NaN values.
    Returns None for empty/NaN cells.
    """
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, str):
        val = val.strip()
        if not val or val.lower() == 'nan':
            return None
        if any(val.startswith(prefix) for prefix in ('=', '+', '-', '@')):
            return "'" + val
    return val

def drop_ghost_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops rows where all non-metadata columns are None/empty.
    Metadata columns include 'Đơn vị' (case-insensitive) and columns starting with '_'.
    """
    if df.empty:
        return df
    
    meta_cols = [c for c in df.columns if "đơn vị" in c.lower() or str(c).startswith('_')]
    data_cols = [c for c in df.columns if c not in meta_cols]
    
    if not data_cols:
        return df.dropna(how='all').reset_index(drop=True)
        
    # Check if a row is completely null in all data columns
    is_null_row = df[data_cols].isna().all(axis=1)
    return df[~is_null_row].reset_index(drop=True)

def get_excel_sheet_names(file_bytes) -> list:
    """
    Returns non-metadata sheet names from excel file.
    Supports both .xlsx and .xls formats.
    """
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
        return [name for name in wb.sheetnames if name.lower() != 'metadata']
    except Exception:
        try:
            import xlrd
            wb = xlrd.open_workbook(file_contents=file_bytes)
            return [name for name in wb.sheet_names() if name.lower() != 'metadata']
        except Exception as e:
            raise ValueError(f"File không hợp lệ hoặc không được hỗ trợ: {str(e)}")

def get_excel_headers(file_bytes, sheet_name=None, header_row=0) -> list:
    """
    Returns headers of the selected sheet at header_row (0-indexed).
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=header_row, nrows=1)
        return [str(c).strip() for c in df.columns if not pd.isna(c)]
    except Exception as e:
        raise ValueError(f"Không thể lấy danh sách tiêu đề cột: {str(e)}")

def parse_excel_to_df(file_bytes, header_row=3, read_all_sheets=False, sheet_name=0) -> pd.DataFrame:
    """
    Parses Excel file bytes into a DataFrame starting at header_row (0-indexed).
    If read_all_sheets is True and sheet_name is None, reads all sheets and concatenates them.
    Applies sanitization to all cells to prevent CSV injection.
    """
    try:
        if read_all_sheets and sheet_name is None:
            sheet_dict = pd.read_excel(io.BytesIO(file_bytes), header=header_row, sheet_name=None)
            df_list = []
            for name, sheet_df in sheet_dict.items():
                if name.lower() == 'metadata':
                    continue
                # Sanitize first
                for col in sheet_df.columns:
                    sheet_df[col] = sheet_df[col].apply(sanitize_value)
                sheet_df = drop_ghost_rows(sheet_df)
                if not sheet_df.empty:
                    sheet_df['_sheet_name'] = name
                    df_list.append(sheet_df)
            if df_list:
                df = pd.concat(df_list, ignore_index=True)
            else:
                df = pd.DataFrame()
        else:
            # If sheet_name is None and not read_all_sheets, read first sheet (0)
            s_name = 0 if sheet_name is None else sheet_name
            df = pd.read_excel(io.BytesIO(file_bytes), header=header_row, sheet_name=s_name)
            for col in df.columns:
                df[col] = df[col].apply(sanitize_value)
            df = drop_ghost_rows(df)
            if sheet_name:
                df['_sheet_name'] = sheet_name
    except Exception as e:
        raise ValueError(f"Không thể đọc file Excel: {str(e)}")
        
    return df

def remap_dataframe_columns(df: pd.DataFrame, mapping_dict: dict) -> pd.DataFrame:
    """
    Remaps columns of the DataFrame from external/user columns to target expected columns.
    Expected format: mapping_dict = { expected_col_name: actual_user_excel_col_name }
    """
    if df.empty:
        return df
    
    # Reverse mapping for pandas rename: { actual_user_excel_col_name: expected_col_name }
    rename_dict = {val: key for key, val in mapping_dict.items() if val is not None}
    
    # Keep metadata columns starting with '_'
    meta_cols = {c: c for c in df.columns if str(c).startswith('_')}
    rename_dict.update(meta_cols)
    
    df_mapped = df.rename(columns=rename_dict)
    
    # Fill missing expected columns with None/NaN so validators do not crash on missing keys
    for expected in mapping_dict.keys():
        if expected not in df_mapped.columns:
            df_mapped[expected] = None
            
    return df_mapped
