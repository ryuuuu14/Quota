import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.utils import get_column_letter
from database import get_connection

def generate_excel_template(timeframe_name):
    """
    Tạo file Excel mẫu chứa danh sách giảng viên để nhập liệu hàng loạt.
    Khóa các cột Mã GV, Họ tên để bảo vệ cấu trúc dữ liệu.
    """
    # 1. Lấy danh sách giảng viên từ DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM teachers ORDER BY name")
    teachers = cursor.fetchall()
    conn.close()
    
    # 2. Khởi tạo Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nhập dữ liệu"
    
    # Kích hoạt tính năng bảo vệ sheet (Khóa mặc định toàn bộ sheet)
    ws.protection.sheet = True
    ws.protection.enable()
    
    # Định dạng font và màu sắc (Premium Palette: Emerald/Charcoal)
    font_family = "Segoe UI"
    title_font = Font(name=font_family, size=14, bold=True, color="1F5F3F")
    header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    data_font = Font(name=font_family, size=11, color="000000")
    instruction_font = Font(name=font_family, size=10, italic=True, color="555555")
    
    header_fill = PatternFill(start_color="1F5F3F", end_color="1F5F3F", fill_type="solid")
    instruction_fill = PatternFill(start_color="EAF2EC", end_color="EAF2EC", fill_type="solid")
    
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # 3. Ghi Tiêu đề & Hướng dẫn
    ws.merge_cells("A1:G1")
    ws["A1"] = f"MẪU NHẬP LIỆU GIỜ CHUẨN - {timeframe_name.upper()}"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40
    
    ws.merge_cells("A2:G2")
    ws["A2"] = "Hướng dẫn: Nhập số giờ thực tế đã làm vào các cột màu trắng. Cột màu xám không được chỉnh sửa. Không đổi cấu trúc file."
    ws["A2"].font = instruction_font
    ws["A2"].fill = instruction_fill
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 25
    
    # 4. Định nghĩa Headers
    headers = [
        "Mã GV (Khóa)", 
        "Họ tên (Khóa)", 
        "Giảng dạy trực tiếp*", 
        "HĐ chuyên môn & Bồi dưỡng*", 
        "NCKH*", 
        "Nhiệm vụ khác*", 
        "Ghi chú"
    ]
    
    ws.row_dimensions[4].height = 30
    for col_idx, h_text in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.value = h_text
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
        
    # 5. Điền dữ liệu GV
    start_row = 5
    for idx, t in enumerate(teachers):
        current_row = start_row + idx
        ws.row_dimensions[current_row].height = 22
        
        # Mã GV
        c_id = ws.cell(row=current_row, column=1)
        c_id.value = t['id']
        c_id.font = data_font
        c_id.alignment = Alignment(horizontal="center", vertical="center")
        c_id.border = thin_border
        c_id.protection = Protection(locked=True) # Khóa
        
        # Họ tên
        c_name = ws.cell(row=current_row, column=2)
        c_name.value = t['name']
        c_name.font = data_font
        c_name.alignment = Alignment(vertical="center")
        c_name.border = thin_border
        c_name.protection = Protection(locked=True) # Khóa
        
        # Các cột cho phép nhập (unlock)
        for col in range(3, 8):
            cell = ws.cell(row=current_row, column=col)
            if col < 7:
                cell.value = 0.0  # Mặc định là 0.0
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.value = ""
                cell.alignment = Alignment(vertical="center")
            cell.font = data_font
            cell.border = thin_border
            cell.protection = Protection(locked=False) # Cho phép sửa
            
    # 6. Auto-fit chiều rộng cột
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        # Chỉ check từ row 4 trở xuống để tránh chiều rộng quá lớn do dòng merged A1/A2
        for cell in col[3:]:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 15)
        
    # Freeze panes dưới dòng header (dòng 4)
    ws.freeze_panes = "A5"
    
    # 7. Xuất file dạng bytes
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out.getvalue()
