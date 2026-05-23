import streamlit as st
import pandas as pd
from database import get_connection
from bulk_import.templates import generate_excel_template
from bulk_import.validator import validate_excel_data
from bulk_import.importer import import_teacher_totals
from components import (
    render_sidebar,
    inject_premium_css,
    render_step_header,
    render_error_report,
    render_success_preview
)

# Thiết lập trang và Style
st.set_page_config(page_title="Nhập dữ liệu hàng loạt", page_icon="📥", layout="wide")
render_sidebar("nhapdulieu")
inject_premium_css()

# Giới hạn chiều rộng và căn giữa nội dung chính
col1, col2, col3 = st.columns([1, 5, 1])

with col2:
    st.markdown('<div style="margin-bottom: 24px;">', unsafe_allow_html=True)
    st.title("📥 Nhập dữ liệu tổng hợp hàng loạt (Excel)")
    st.markdown("""
    <div style="font-size: 1.05rem; color: var(--md-on-surface-variant); margin-top: -8px; margin-bottom: 24px; line-height: 1.6;">
        Trang nhập tổng kết giờ giảng, nghiên cứu khoa học và nhiệm vụ khác cuối năm học bằng Excel. 
        Khi áp dụng dữ liệu Excel, hệ thống sẽ tạm khóa chức năng tự nhập lẻ từng hoạt động để đảm bảo tính đồng nhất.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Lấy danh sách timeframe
    conn = get_connection()
    timeframes_df = pd.read_sql_query("SELECT id, name FROM timeframes ORDER BY start_date DESC", conn)
    conn.close()

    if timeframes_df.empty:
        st.error("Chưa có năm học nào được cấu hình trong hệ thống. Vui lòng vào Cài đặt hệ thống để thêm mới.")
        st.stop()

    # Chọn năm học toàn cục cho trang này
    selected_tf_row = st.selectbox(
        "Chọn năm học áp dụng:", 
        options=range(len(timeframes_df)), 
        format_func=lambda idx: timeframes_df.iloc[idx]['name']
    )
    tf_id = int(timeframes_df.iloc[selected_tf_row]['id'])
    tf_name = timeframes_df.iloc[selected_tf_row]['name']

    # Kiểm tra trạng thái hiện tại (Đã có dữ liệu excel hay chưa)
    conn = get_connection()
    check_cursor = conn.cursor()
    check_cursor.execute("SELECT COUNT(*) FROM session_teacher_totals WHERE timeframe_id = ?", (tf_id,))
    has_excel_data = check_cursor.fetchone()[0] > 0
    conn.close()

    if has_excel_data:
        st.markdown(f"""
        <div style="
            background-color: var(--md-amber-bg);
            border: 1px solid rgba(181, 129, 5, 0.3);
            border-radius: var(--radius-md);
            padding: 20px;
            margin: 20px 0;
            color: #78350f;
        ">
            <div style="font-weight: 700; font-size: 1.05rem; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span class="material-symbols-outlined" style="font-size: 24px; color: var(--md-amber);">warning</span>
                Năm học {tf_name} đang áp dụng dữ liệu tổng kết từ Excel
            </div>
            <div style="font-size: 0.95rem; line-height: 1.5;">
                Chức năng tự nhập lẻ (Nhật ký hoạt động) cho năm học này đã bị tạm khóa để tránh sai lệch dữ liệu.<br>
                Bạn có thể xem báo cáo ngay bây giờ. Nếu muốn khôi phục lại chế độ tự nhập lẻ hoặc tải lên file Excel mới, hãy thực hiện xóa dữ liệu cũ bên dưới.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="md-card" style="margin-top: 24px;">', unsafe_allow_html=True)
        st.subheader("⚙️ Quản lý trạng thái dữ liệu")
        st.write("Xác nhận xóa dữ liệu Excel hiện tại để quay lại chế độ nhập thủ công lẻ hoặc tải lên file Excel cập nhật mới:")
        
        # Checkbox xác nhận
        confirm_delete = st.checkbox(
            "Tôi xác nhận muốn xóa toàn bộ dữ liệu Excel nhập tổng kết và mở khóa lại chức năng tự nhập lẻ cho năm học này.",
            key="confirm_delete_excel"
        )
        
        if confirm_delete:
            if st.button("🗑️ Thực hiện xóa dữ liệu Excel tổng hợp", type="primary", key="btn_delete_excel"):
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM session_teacher_totals WHERE timeframe_id = ?", (tf_id,))
                    conn.commit()
                    st.success("✅ Đã xóa dữ liệu Excel tổng kết và khôi phục chế độ tự nhập lẻ thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi xóa dữ liệu: {str(e)}")
                finally:
                    conn.close()
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.markdown("""
        <div style="
            background-color: var(--md-primary-container);
            border: 1px solid rgba(15, 76, 129, 0.2);
            border-radius: var(--radius-md);
            padding: 16px 20px;
            color: var(--md-primary);
            margin: 16px 0;
            font-size: 0.95rem;
            line-height: 1.5;
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            <span class="material-symbols-outlined" style="font-size: 24px;">info</span>
            <div>Năm học này đang ở chế độ <strong>Nhập lẻ (Nhật ký hoạt động)</strong>. Bạn có thể tải file Excel tổng hợp lên dưới đây để chuyển sang chế độ quản lý tổng kết.</div>
        </div>
        """, unsafe_allow_html=True)

        # BƯỚC 1: Tải file mẫu
        render_step_header(
            step_num=1,
            title="Tải file Excel mẫu",
            description=f"Hệ thống tự động điền sẵn mã và danh sách giảng viên hiện có cho {tf_name} để tránh sai lệch."
        )
        
        try:
            excel_bytes = generate_excel_template(tf_name)
            st.download_button(
                label="📥 Tải file mẫu Excel",
                data=excel_bytes,
                file_name=f"Mau_Nhap_Lieu_Gio_Chuan_{tf_name.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_template_btn"
            )
        except Exception as e:
            st.error(f"Lỗi khi tạo file mẫu: {str(e)}")

        st.markdown('<hr style="border: 0; border-top: 1px solid var(--md-outline-variant); margin: 32px 0;">', unsafe_allow_html=True)

        # BƯỚC 2: Tải lên và Kiểm tra dữ liệu
        render_step_header(
            step_num=2,
            title="Tải lên file dữ liệu đã điền",
            description="Tải lên file Excel sau khi điền đầy đủ giờ dạy trực tiếp, chuyên môn bồi dưỡng, NCKH và nhiệm vụ khác."
        )
        
        uploaded_file = st.file_uploader(
            "Chọn file Excel mẫu đã điền dữ liệu:", 
            type=["xlsx"],
            label_visibility="collapsed",
            key="excel_uploader"
        )
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            
            # Chạy validator
            is_valid, errors, parsed_df = validate_excel_data(file_bytes)
            
            if not is_valid:
                render_error_report(errors)
            else:
                render_success_preview(parsed_df)
                
                # Show preview table
                st.markdown('<div style="margin-top: 16px; margin-bottom: 24px;">', unsafe_allow_html=True)
                st.markdown('<div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 8px; color: var(--md-on-surface);">Xem trước danh sách dữ liệu:</div>', unsafe_allow_html=True)
                st.dataframe(
                    parsed_df[[
                        "teacher_id", "teacher_name", "giang_day_truc_tiep", 
                        "hdcm_bd", "nckh_total", "nvk_total"
                    ]].rename(columns={
                        "teacher_id": "Mã GV",
                        "teacher_name": "Họ tên giảng viên",
                        "giang_day_truc_tiep": "Giờ giảng dạy",
                        "hdcm_bd": "Chuyên môn BD",
                        "nckh_total": "Giờ NCKH",
                        "nvk_total": "Nhiệm vụ khác"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Bước 3: Xác nhận ghi đè
                st.markdown('<hr style="border: 0; border-top: 1px solid var(--md-outline-variant); margin: 32px 0;">', unsafe_allow_html=True)
                render_step_header(
                    step_num=3,
                    title="Xác nhận lưu dữ liệu",
                    description="Khi bạn lưu, hệ thống sẽ cập nhật và áp dụng dữ liệu tổng kết này làm kết quả chính thức cho năm học."
                )
                
                confirm_import = st.checkbox(
                    "Tôi đồng ý lưu dữ liệu tổng kết này và tạm khóa chức năng tự nhập lẻ cho năm học được chọn.",
                    key="confirm_import_excel"
                )
                
                if confirm_import:
                    if st.button("🚀 Lưu dữ liệu vào hệ thống", type="primary", key="btn_save_excel"):
                        success, err_msg = import_teacher_totals(tf_id, parsed_df)
                        if success:
                            st.success("🎉 Đã nhập và áp dụng dữ liệu tổng kết thành công! Báo cáo của bạn đã được cập nhật.")
                            st.rerun()
                        else:
                            st.error(f"Thao tác thất bại: {err_msg}")
                            
    st.markdown('</div>', unsafe_allow_html=True)
