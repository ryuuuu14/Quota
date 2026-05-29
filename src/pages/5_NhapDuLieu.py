import streamlit as st
import pandas as pd
from database import get_connection, init_db
from bulk_import.templates import generate_excel_template
from bulk_import.validator import validate_excel_data
from bulk_import.calculator import calculate_rows, calculate_preview
from bulk_import.importer import import_bulk_data
from components import (
    render_sidebar,
    inject_premium_css,
    render_step_header,
    render_error_report,
)

init_db()

st.set_page_config(page_title="Nhập giờ giảng hàng loạt", page_icon="📥", layout="wide")
render_sidebar("nhapdulieu")
inject_premium_css()

col1, col2, col3 = st.columns([1, 5, 1])

with col2:
    st.markdown('<div style="margin-bottom: 24px;">', unsafe_allow_html=True)
    st.title("📥 Nhập giờ giảng chi tiết từ Excel")
    st.markdown("""
    <div style="font-size: 1.05rem; color: var(--md-on-surface-variant); margin-top: -8px; margin-bottom: 24px; line-height: 1.6;">
        Tải lên danh sách lịch giảng dạy chi tiết (từng lớp/môn học).
        Hệ thống tự động tra bảng quy đổi theo Điều 8 và tính giờ chuẩn (GC).
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    conn = get_connection()
    timeframes_df = pd.read_sql_query("SELECT id, name FROM timeframes ORDER BY start_date DESC", conn)

    if timeframes_df.empty:
        st.error("Chưa có năm học nào. Vui lòng vào Cài đặt hệ thống.")
        st.stop()

    selected_tf_row = st.selectbox(
        "Chọn năm học áp dụng:",
        options=range(len(timeframes_df)),
        format_func=lambda idx: timeframes_df.iloc[idx]['name'],
    )
    tf_id = int(timeframes_df.iloc[selected_tf_row]['id'])
    tf_name = timeframes_df.iloc[selected_tf_row]['name']

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM session_teacher_totals WHERE timeframe_id = ?", (tf_id,))
    has_excel_data = cursor.fetchone()[0] > 0
    has_file = False
    cursor.execute("SELECT id FROM bulk_import_files WHERE timeframe_id = ?", (tf_id,))
    if cursor.fetchone():
        has_file = True
    conn.close()

    RAW_KEY = f"bulk_raw_df_{tf_id}"
    CALC_KEY = f"bulk_calc_df_{tf_id}"
    METRICS_KEY = f"bulk_metrics_df_{tf_id}"

    if has_excel_data:
        st.error("""
        <div style="
            background-color: var(--md-amber-bg);
            border: 1px solid rgba(181, 129, 5, 0.3);
            border-radius: var(--radius-md);
            padding: 20px;
            margin: 20px 0;
            color: #78350f;
            font-size: 0.95rem;
            line-height: 1.5;
        ">
            <strong>⚠️ Năm học này đã có dữ liệu giờ giảng.</strong><br>
            Nếu tải lên file mới, dữ liệu cũ sẽ bị ghi đè hoàn toàn.
        </div>
        """, unsafe_allow_html=True)

        confirm_delete = st.checkbox(
            "Tôi xác nhận muốn xoá dữ liệu cũ và tải lên file mới.",
            key=f"confirm_override_{tf_id}",
        )
        if confirm_delete:
            if st.button("🗑️ Xoá dữ liệu cũ, bắt đầu lại", type="primary", key=f"btn_reset_{tf_id}"):
                conn = get_connection()
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM bulk_teaching_assignments WHERE timeframe_id = ?", (tf_id,))
                    cur.execute("DELETE FROM session_teacher_totals WHERE timeframe_id = ?", (tf_id,))
                    cur.execute("DELETE FROM bulk_import_files WHERE timeframe_id = ?", (tf_id,))
                    for k in [RAW_KEY, CALC_KEY, METRICS_KEY, FILE_BYTES_KEY, FILENAME_KEY]:
                        if k in st.session_state:
                            del st.session_state[k]
                    conn.commit()
                    st.success("✅ Đã xoá dữ liệu cũ.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")
                finally:
                    conn.close()
        st.stop()

    st.markdown("---")

    render_step_header(
        step_num=1,
        title="Tải file Excel mẫu",
        description=f"Tải template có sẵn danh sách giảng viên cho {tf_name}.",
    )
    try:
        excel_bytes = generate_excel_template(tf_name)
        st.download_button(
            label="📥 Tải file mẫu Excel",
            data=excel_bytes,
            file_name=f"Mau_Nhap_Gio_Giang_{tf_name.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_template_btn",
        )
    except Exception as e:
        st.error(f"Lỗi tạo file mẫu: {str(e)}")

    st.markdown('<hr style="border: 0; border-top: 1px solid var(--md-outline-variant); margin: 28px 0;">', unsafe_allow_html=True)

    render_step_header(
        step_num=2,
        title="Tải lên file dữ liệu đã điền",
        description="Upload file Excel đã điền thông tin các lớp/môn giảng dạy.",
    )

    uploaded_file = st.file_uploader(
        "Chọn file Excel:",
        type=["xlsx"],
        label_visibility="collapsed",
        key=f"excel_uploader_{tf_id}",
    )

    FILE_BYTES_KEY = f"bulk_file_bytes_{tf_id}"
    FILENAME_KEY = f"bulk_filename_{tf_id}"

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
        st.session_state[FILE_BYTES_KEY] = file_bytes
        st.session_state[FILENAME_KEY] = filename

        is_valid, errors, parsed_df = validate_excel_data(file_bytes)

        if not is_valid:
            render_error_report(errors)
            for k in [RAW_KEY, CALC_KEY, METRICS_KEY, FILE_BYTES_KEY, FILENAME_KEY]:
                if k in st.session_state:
                    del st.session_state[k]
        else:
            st.session_state[RAW_KEY] = parsed_df
            if CALC_KEY in st.session_state:
                del st.session_state[CALC_KEY]
            if METRICS_KEY in st.session_state:
                del st.session_state[METRICS_KEY]

            st.success(f"✅ File hợp lệ! Phát hiện {len(parsed_df)} dòng dữ liệu giảng dạy.")

            st.markdown("### 📋 Xem trước dữ liệu thô")
            raw_cols = [
                "teacher_id", "teacher_name", "subject_name", "loai",
                "nhom", "si_so", "tiet_quy_doi", "he_so_tin_chi",
            ]
            raw_rename = {
                "teacher_id": "Mã GV",
                "teacher_name": "Họ tên",
                "subject_name": "Tên môn",
                "loai": "Loại",
                "nhom": "Nhóm",
                "si_so": "Sỉ số",
                "tiet_quy_doi": "Tiết QĐ",
                "he_so_tin_chi": "HS TC",
            }
            if "ghi_chu" in parsed_df.columns:
                raw_cols.append("ghi_chu")
                raw_rename["ghi_chu"] = "Ghi chú"
            raw_display = parsed_df[raw_cols].rename(columns=raw_rename)
            st.dataframe(raw_display, use_container_width=True, hide_index=True)

            teacher_count = parsed_df["teacher_id"].nunique()
            st.caption(f"👥 {teacher_count} giảng viên — 📚 {len(parsed_df)} lớp/môn")

            st.markdown("---")

            render_step_header(
                step_num=3,
                title="Xử lý & Tính toán giờ chuẩn (GC)",
                description="Hệ thống tra bảng quy đổi Điều 8 và tính giờ chuẩn cho từng giảng viên.",
            )

            if st.button("⚙️ Xử lý và tính toán", type="primary", key=f"btn_calc_{tf_id}"):
                with st.spinner("Đang tính toán định mức và giờ chuẩn..."):
                    df_calc = calculate_rows(parsed_df)
                    df_metrics = calculate_preview(tf_id, df_calc)
                    st.session_state[CALC_KEY] = df_calc
                    st.session_state[METRICS_KEY] = df_metrics
                st.rerun()

    if METRICS_KEY in st.session_state:
        df_metrics = st.session_state[METRICS_KEY]
        df_calc = st.session_state.get(CALC_KEY)

        st.markdown("---")
        st.markdown("## 📊 Kết quả tính toán giờ chuẩn")

        # cột tổng quan
        tong_gv = len(df_metrics)
        tong_gc = df_metrics["tong_tiet_thuc_day"].sum()
        tong_dinh_muc = df_metrics["dinh_muc_gc_phai_thuc_hien"].sum()
        dat_count = len(df_metrics[df_metrics["trang_thai_chung"] == "Đạt"])
        khong_dat_count = tong_gv - dat_count

        cols = st.columns(5)
        with cols[0]:
            st.metric("👥 Tổng GV", f"{tong_gv}")
        with cols[1]:
            st.metric("📊 Tổng GC đã dạy", f"{tong_gc:,.1f}")
        with cols[2]:
            st.metric("🎯 Tổng định mức GC", f"{tong_dinh_muc:,.1f}")
        with cols[3]:
            st.metric("✅ Đạt", f"{dat_count}", delta_color="normal")
        with cols[4]:
            st.metric("❌ Không đạt", f"{khong_dat_count}", delta_color="inverse")

        # bảng chi tiết
        st.markdown("### Bảng chi tiết theo giảng viên")

        display_cols = {
            "id": "Mã GV",
            "name": "Họ và tên",
            "title_name": "Chức danh",
            "tong_mon": "Số môn",
            "tong_tiet_quy_doi": "Tổng Tiết QĐ",
            "tong_tiet_thuc_day": "Tổng GC",
            "dinh_muc_gc_phai_thuc_hien": "Định mức GC",
            "gc_vuot_thieu_sau_quy_doi": "Vượt/Thiếu GC",
            "nckh_da_thuc_hien": "NCKH đã làm",
            "dinh_muc_nckh_phai_thuc_hien": "Định mức NCKH",
            "hoan_thanh_gd": "GC",
            "hoan_thanh_nckh": "NCKH",
            "trang_thai_chung": "Trạng thái",
        }
        available = [k for k in display_cols if k in df_metrics.columns]
        df_table = df_metrics[available].copy()
        df_table.columns = [display_cols[c] for c in available]

        def fmt_num(v):
            import math
            if isinstance(v, (int, float)) and not math.isnan(v) and not math.isinf(v):
                return f"{v:,.1f}"
            return v

        float_display = [c for c in df_table.columns if c.startswith("Tổng") or c.startswith("Định mức") or c.startswith("Vượt") or c.startswith("NCKH")]

        def highlight_row(val):
            if val == "Đạt":
                return "background-color: #ecfdf5; color: #047857; font-weight: bold;"
            if val == "Không đạt":
                return "background-color: #fef2f2; color: #b91c1c; font-weight: bold;"
            if isinstance(val, (int, float)):
                if val < 0:
                    return "color: #b91c1c; font-weight: bold;"
                if val > 0:
                    return "color: #047857;"
            return ""

        try:
            styled = df_table.style
            if float_display:
                styled = styled.format({c: fmt_num for c in float_display})
            status_cols = ["GC", "NCKH", "Trạng thái"]
            avail_status = [c for c in status_cols if c in df_table.columns]
            if avail_status:
                styled = styled.map(highlight_row, subset=avail_status)
            if "Vượt/Thiếu GC" in df_table.columns:
                styled = styled.map(highlight_row, subset=["Vượt/Thiếu GC"])
            st.dataframe(styled, use_container_width=True)
        except Exception:
            st.dataframe(df_table, use_container_width=True)

        # detail
        st.markdown("### 📋 Chi tiết lớp/môn theo giảng viên")
        teacher_opts = df_metrics[["id", "name"]].drop_duplicates("id")
        sel_id = st.selectbox(
            "Chọn giảng viên:",
            options=teacher_opts["id"].tolist(),
            format_func=lambda x: f"{x} - {teacher_opts[teacher_opts['id'] == x]['name'].values[0]}",
            key="detail_select",
        )
        if df_calc is not None:
            detail = df_calc[df_calc["teacher_id"] == sel_id][[
                "subject_name", "loai", "nhom", "si_so",
                "tiet_quy_doi", "he_so_tin_chi", "he_so_lop_dong", "tiet_thuc_day",
            ]].rename(columns={
                "subject_name": "Tên môn",
                "loai": "Loại",
                "nhom": "Nhóm",
                "si_so": "Sỉ số",
                "tiet_quy_doi": "Tiết QĐ",
                "he_so_tin_chi": "HS TC",
                "he_so_lop_dong": "HS Lớp đông",
                "tiet_thuc_day": "Tiết thực dạy",
            })
            st.dataframe(detail, use_container_width=True, hide_index=True)
            st.caption(f"Tổng: {detail['Tiết thực dạy'].sum():.1f} GC")

        # Lưu
        st.markdown("---")
        render_step_header(
            step_num=4,
            title="Xác nhận và lưu vào hệ thống",
            description="Dữ liệu cũ (nếu có) sẽ bị ghi đè. Hành động này không thể hoàn tác.",
        )

        confirm_save = st.checkbox(
            "Tôi xác nhận lưu dữ liệu này và ghi đè dữ liệu cũ (nếu có).",
            key=f"confirm_save_{tf_id}",
        )
        if confirm_save:
            if st.button("💾 Lưu dữ liệu vào hệ thống", type="primary", key=f"btn_save_{tf_id}"):
                with st.spinner("Đang lưu dữ liệu..."):
                    fb = st.session_state.get(FILE_BYTES_KEY, b"")
                    fn = st.session_state.get(FILENAME_KEY, "unknown.xlsx")
                    success, err = import_bulk_data(tf_id, df_calc, fb, fn)
                if success:
                    for k in [RAW_KEY, CALC_KEY, METRICS_KEY, FILE_BYTES_KEY, FILENAME_KEY]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.success("🎉 Lưu thành công! Báo cáo đã được cập nhật.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Lỗi khi lưu: {err}")

    st.markdown('</div>', unsafe_allow_html=True)
