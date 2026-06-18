import streamlit as st
try:
    from calculations import calculate_teacher_metrics, get_conversion_limits, calculate_department_compensation, get_teacher_formula_breakdown
    _HAS_FORMULA_BREAKDOWN = True
except ImportError:
    from calculations import calculate_teacher_metrics, get_conversion_limits, calculate_department_compensation
    get_teacher_formula_breakdown = None
    _HAS_FORMULA_BREAKDOWN = False
from database import get_connection, get_cached_timeframes, ThreadLocalConnectionProxy
try:
    from components import render_metric_card, render_empty_state, render_warning_state, render_chip, render_sidebar, render_formula_card
except ImportError:
    from components import render_metric_card, render_empty_state, render_warning_state, render_chip, render_sidebar
    render_formula_card = None
from auth import require_role

@st.fragment
def _render_conversion_suggestions(df_display, selected_tf_id, conn):
    import pandas as pd
    with st.expander("Quy đổi & Bù trừ Giờ chuẩn thủ công", expanded=False):
        st.markdown("<p style='font-size: 14px; color: var(--md-on-surface-variant);'>Gợi ý quy đổi thủ công dựa trên số giờ thừa/thiếu (Điều 12). Bấm nút 'Quy đổi' để áp dụng.</p>", unsafe_allow_html=True)
        has_suggestion = False
        for _, row in df_display.iterrows():
            limits = get_conversion_limits(row['id'], selected_tf_id, teacher_row=row)
            if not limits: continue

            cursor_check = conn.cursor()
            cursor_check.execute("""
                SELECT from_category, to_category, from_amount, to_amount 
                FROM manual_conversions 
                WHERE teacher_id = ? AND timeframe_id = ?
            """, (int(row['id']), selected_tf_id))
            existing_conv = cursor_check.fetchone()

            if existing_conv:
                has_suggestion = True
                from_cat, to_cat, from_amt, to_amt = existing_conv
                with st.container():
                    st.markdown(f"""
<div style="
    background-color: var(--md-surface-container-lowest);
    padding: 16px 20px;
    border-radius: var(--radius-lg);
    border: 1px solid var(--md-outline-variant);
    border-left: 4px solid var(--md-amber);
    margin-bottom: 12px;
    box-shadow: var(--shadow-card);
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: var(--md-on-surface); font-weight: 700; font-size: 1rem;">{row['name']}</div>
            <div style="color: var(--md-on-surface-variant); font-size: 0.9rem; margin-top: 4px;">
                Đang áp dụng quy đổi thủ công: <b>{from_amt:.1f} {from_cat}</b> → <b>{to_amt:.1f} {to_cat}</b>
            </div>
        </div>
        <div>
            <span class="material-symbols-outlined" style="color: var(--md-amber); font-size: 32px;">verified</span>
        </div>
    </div>
</div>
                    """, unsafe_allow_html=True)
                    col_reset, _ = st.columns([3, 7])
                    if col_reset.button("Hủy quy đổi", key=f"reset_{row['id']}_{selected_tf_id}"):
                        try:
                            with get_connection() as conn_write:
                                cursor_write = conn_write.cursor()
                                cursor_write.execute("""
                                    DELETE FROM manual_conversions 
                                    WHERE teacher_id = ? AND timeframe_id = ?
                                """, (int(row['id']), selected_tf_id))
                                conn_write.commit()
                            st.success(f"Đã hủy quy đổi thủ công cho {row['name']}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi hủy quy đổi: {e}")
                continue

            if limits['can_convert_nckh_to_gc']:
                has_suggestion = True
                with st.container():
                    st.markdown(f"""
<div style="
    background-color: var(--md-surface-container-lowest);
    padding: 20px;
    border-radius: var(--radius-lg);
    border: 1px solid var(--md-outline-variant);
    border-left: 4px solid var(--md-primary-container);
    margin-bottom: 12px;
    box-shadow: var(--shadow-card);
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: var(--md-on-surface); font-weight: 700; font-size: 1rem;">{row['name']}</div>
            <div style="color: var(--md-on-surface-variant); font-size: 0.9rem; margin-top: 4px;">
                Đang thiếu {render_chip(f"{abs(row['gc_vuot_thieu_sau_quy_doi']):.1f} GC", "red", "arrow_downward")}
                nhưng thừa {render_chip(f"{row['nckh_vuot_thieu_sau_quy_doi']:.1f} NCKH", "green", "arrow_upward")}
            </div>
        </div>
        <div>
            <span class="material-symbols-outlined" style="color: var(--md-primary-container); font-size: 32px;">sync</span>
        </div>
    </div>
</div>
                    """, unsafe_allow_html=True)
                    col_btn, _ = st.columns([3, 7])
                    if col_btn.button(f"Quy đổi: {limits['max_nckh_to_spend']:.1f} NCKH → {limits['gc_gained']:.1f} GC", key=f"n2g_{row['id']}_{selected_tf_id}"):
                        try:
                            with get_connection() as conn_write:
                                cursor_write = conn_write.cursor()
                                cursor_write.execute("""
                                    DELETE FROM manual_conversions 
                                    WHERE teacher_id = ? AND timeframe_id = ?
                                """, (int(row['id']), selected_tf_id))
                                cursor_write.execute("""
                                    INSERT INTO manual_conversions (teacher_id, timeframe_id, from_category, to_category, from_amount, to_amount)
                                    VALUES (?, ?, 'NCKH', 'Giảng dạy', ?, ?)
                                """, (int(row['id']), selected_tf_id, limits['max_nckh_to_spend'], limits['gc_gained']))
                                conn_write.commit()
                            st.success(f"Đã áp dụng quy đổi {limits['max_nckh_to_spend']:.1f} NCKH sang {limits['gc_gained']:.1f} Giảng dạy cho {row['name']}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi thực hiện quy đổi: {e}")

            if limits['can_convert_gc_to_nckh']:
                has_suggestion = True
                with st.container():
                    st.markdown(f"""
<div style="
    background-color: var(--md-surface-container-lowest);
    padding: 20px;
    border-radius: var(--radius-lg);
    border: 1px solid var(--md-outline-variant);
    border-left: 4px solid var(--md-green);
    margin-bottom: 12px;
    box-shadow: var(--shadow-card);
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: var(--md-on-surface); font-weight: 700; font-size: 1rem;">{row['name']}</div>
            <div style="color: var(--md-on-surface-variant); font-size: 0.9rem; margin-top: 4px;">
                Đang thiếu {render_chip(f"{abs(row['nckh_vuot_thieu_sau_quy_doi']):.1f} NCKH", "red", "arrow_downward")}
                nhưng thừa {render_chip(f"{row['gc_vuot_thieu_sau_quy_doi']:.1f} GC", "green", "arrow_upward")}
            </div>
        </div>
        <div>
            <span class="material-symbols-outlined" style="color: var(--md-green); font-size: 32px;">sync</span>
        </div>
    </div>
</div>
                    """, unsafe_allow_html=True)
                    col_btn, _ = st.columns([3, 7])
                    if col_btn.button(f"Quy đổi: {limits['max_gc_to_spend']:.1f} GC → {limits['nckh_gained']:.1f} NCKH", key=f"g2n_{row['id']}_{selected_tf_id}"):
                        try:
                            with get_connection() as conn_write:
                                cursor_write = conn_write.cursor()
                                cursor_write.execute("""
                                    DELETE FROM manual_conversions 
                                    WHERE teacher_id = ? AND timeframe_id = ?
                                """, (int(row['id']), selected_tf_id))
                                cursor_write.execute("""
                                    INSERT INTO manual_conversions (teacher_id, timeframe_id, from_category, to_category, from_amount, to_amount)
                                    VALUES (?, ?, 'Giảng dạy', 'NCKH', ?, ?)
                                """, (int(row['id']), selected_tf_id, limits['max_gc_to_spend'], limits['nckh_gained']))
                                conn_write.commit()
                            st.success(f"Đã áp dụng quy đổi {limits['max_gc_to_spend']:.1f} Giảng dạy sang {limits['nckh_gained']:.1f} NCKH cho {row['name']}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi thực hiện quy đổi: {e}")
            elif limits['warning'] and row['nckh_vuot_thieu_sau_quy_doi'] < 0 and row['gc_vuot_thieu_sau_quy_doi'] > 0:
                has_suggestion = True
                warning_text = limits['warning'].replace("NCKH", "NCKH").replace("Giảng dạy", "GC")
                st.warning(f"**{row['name']}**: Thừa GC, thiếu NCKH nhưng **{warning_text}**")
            elif limits['warning'] and row['gc_vuot_thieu_sau_quy_doi'] < 0 and row['nckh_vuot_thieu_sau_quy_doi'] > 0:
                has_suggestion = True
                warning_text = limits['warning'].replace("NCKH", "NCKH").replace("Giảng dạy", "GC")
                st.warning(f"**{row['name']}**: Thừa NCKH, thiếu GC nhưng **{warning_text}**")

        if not has_suggestion:
            st.markdown('<p style="color: var(--md-on-surface-variant);">Không có gợi ý quy đổi nào tại thời điểm này. Các cán bộ đã hoàn thành hoặc chưa đủ điều kiện.</p>', unsafe_allow_html=True)


render_sidebar("dashboard")
require_role(["admin", "head_dept"], "Bảng điều khiển")

st.title("Bảng điều khiển (Dashboard)")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Giám sát định mức theo thời gian thực và thực hiện quy đổi giờ theo Điều 12.</p>', unsafe_allow_html=True)

conn = ThreadLocalConnectionProxy()
df_tf = get_cached_timeframes()

selected_tf_id = st.session_state.get('global_tf_id')

if df_tf.empty:
    render_warning_state("Hệ thống chưa có Năm học. Vui lòng tạo trong Cài đặt Hệ thống.")

if selected_tf_id:
    with st.spinner("Đang tính toán định mức và hệ số..."):
        df_teachers = calculate_teacher_metrics(timeframe_id=selected_tf_id)

    if not df_teachers.empty:
        if df_teachers['applied_reductions'].str.contains('Bị ép định mức').any():
            st.warning("⚠️ **Cơ chế Cap (Ép định mức) đang hoạt động:** Số tuần làm việc thực tế đang vượt quá định mức chuẩn của Năm học. Hệ thống tự động co giãn định mức và miễn giảm để bảo đảm công bằng. Vui lòng kiểm tra lại cấu hình ngày nghỉ Lễ/Tết/Hè trong **Cài đặt Hệ thống** nếu điều này là ngoài ý muốn.")
            
        import pandas as pd
        hist_query = "SELECT teacher_id, value_text as dept_name FROM teacher_role_history WHERE record_type = 'DEPARTMENT' ORDER BY start_date DESC"
        df_dept_hist = pd.read_sql_query(hist_query, conn)
        df_dept_latest = df_dept_hist.drop_duplicates(subset=['teacher_id'], keep='first')

        df_display = pd.merge(df_teachers, df_dept_latest, left_on='id', right_on='teacher_id', how='left')
        df_display['dept_name'] = df_display['dept_name'].fillna('Chưa phân công')

        from auth import get_current_user
        user = get_current_user()
        is_head_dept = (user and user.get("role") == "head_dept")
        dept_name = user.get("department_name") if is_head_dept else None

        if is_head_dept:
            df_display = df_display[df_display['dept_name'] == dept_name]
            st.markdown(f'<h3 style="display: flex; align-items: center; gap: 8px; margin-top: 32px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">dashboard</span> Tổng quan Bộ môn: {dept_name}</h3>', unsafe_allow_html=True)
            
            # Fetch unread notifications
            try:
                with conn:
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM notifications WHERE target_dept = ? AND target_role = 'head' AND is_read = 0 ORDER BY created_at DESC", (dept_name,))
                    unread_notifications = cur.fetchall()
                    if unread_notifications:
                        st.info(f"**🔔 Bạn có {len(unread_notifications)} thông báo mới về kết quả phê duyệt dữ liệu.**")
                        for notif in unread_notifications:
                            col_text, col_btn = st.columns([8, 2])
                            col_text.markdown(f"**{notif['title']}**: {notif['message']}")
                            if col_btn.button("Xong", key=f"read_notif_{notif['id']}"):
                                cur.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif['id'],))
                                conn.commit()
                                st.rerun()
            except Exception as e:
                pass # Fail silently if notifications table isn't ready

        else:
            st.markdown('<h3 style="display: flex; align-items: center; gap: 8px; margin-top: 32px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">dashboard</span> Tổng quan Toàn trường</h3>', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)

        tong_nha_giao = len(df_display)
        tong_dinh_muc_gc = df_display['dinh_muc_gc_phai_thuc_hien'].sum()
        tong_thuc_hien_gc = df_display['tổng_gc_da_thuc_hien'].sum()
        tong_nvk = df_display['nvk_da_thuc_hien'].sum() if 'nvk_da_thuc_hien' in df_display.columns else 0
        ti_le_hoan_thanh = (tong_thuc_hien_gc / tong_dinh_muc_gc * 100) if tong_dinh_muc_gc > 0 else 0

        with col1:
            render_metric_card("Tổng số nhà giáo", f"{tong_nha_giao}", icon="groups")
        with col2:
            render_metric_card("Tổng định mức GC", f"{tong_dinh_muc_gc:,.1f}", icon="contract")
        with col3:
            render_metric_card("Tổng GC đã thực hiện", f"{tong_thuc_hien_gc:,.1f}", icon="task_alt")
        with col4:
            render_metric_card("Tỷ lệ hoàn thành GC", f"{ti_le_hoan_thanh:.1f}%", icon="pie_chart")
        with col5:
            render_metric_card("Nhiệm vụ khác (Giờ hành chính)", f"{tong_nvk:,.1f}", icon="assignment")

        st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 32px 0;">', unsafe_allow_html=True)
        st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">table_chart</span> Bảng Dữ liệu Chi tiết</h3>', unsafe_allow_html=True)

        # Chế độ bù định mức
        comp_mode = st.selectbox(
            "Chế độ bù trừ định mức:",
            ["Không bù", "Bù trừ cá nhân (Điều 12)", "Tập thể (theo Đơn vị)"],
            index=1
        )
        if comp_mode == "Không bù":
            df_display['gc_vuot_thieu_sau_quy_doi'] = df_display['gc_vuot_thieu']
            df_display['nckh_vuot_thieu_sau_quy_doi'] = df_display['nckh_vuot_thieu']
        elif comp_mode == "Tập thể (theo Đơn vị)":
            df_display = calculate_department_compensation(df_display)

        df_display['hoan_thanh_gd'] = df_display['gc_vuot_thieu_sau_quy_doi'].apply(lambda x: "Đạt" if x >= 0 else "Không đạt")
        df_display['hoan_thanh_nckh'] = df_display['nckh_vuot_thieu_sau_quy_doi'].apply(lambda x: "Đạt" if x >= 0 else "Không đạt")
        
        df_display['Trạng thái Chung'] = df_display.apply(
            lambda row: "Đạt" if row['hoan_thanh_gd'] == "Đạt" and row['hoan_thanh_nckh'] == "Đạt" and row['hoan_thanh_nvk'] == "Đạt" else "Không đạt",
            axis=1
        )

        filter_status = st.selectbox("Lọc theo Trạng thái Chung:", ["Tất cả", "Đạt", "Không đạt"])
        if filter_status != "Tất cả":
            df_display = df_display[df_display['Trạng thái Chung'] == filter_status]

        search_query = st.text_input("Tìm kiếm theo từ khóa (tên, đơn vị, chức danh...):", placeholder="Nhập từ khóa...")
        if search_query:
            mask = df_display.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False).any(), axis=1)
            df_display = df_display[mask]

        col_mapping = {
            'id': 'ID',
            'name': 'Họ và tên',
            'nguon_du_lieu': 'Nguồn',
            'title_name': 'Chức danh',
            'dept_name': 'Đơn vị',
            'applied_reductions': 'Miễn giảm áp dụng',
            'base_gc': 'Định mức gốc GC',
            'dinh_muc_gc_phai_thuc_hien': 'Định mức thực tế GC',
            'so_gio_duoc_mien_giam': 'Số giờ được miễn giảm',
            'tổng_gc_da_thuc_hien': 'Đã thực hiện (tổng GC)',
            'hdcm_bd_da_thuc_hien': 'Trong đó: Kế hoạch khác',
            'gc_vuot_thieu_sau_quy_doi': 'Vượt/Thiếu GC',
            'base_nckh': 'Định mức gốc NCKH',
            'dinh_muc_nckh_phai_thuc_hien': 'Định mức thực tế NCKH',
            'nckh_da_thuc_hien': 'Đã làm NCKH',
            'nckh_vuot_thieu_sau_quy_doi': 'Vượt/Thiếu NCKH',
            'dinh_muc_nvk_goc': 'Định mức gốc NVK',
            'dinh_muc_nvk_phai_thuc_hien': 'Định mức NVK (Giờ hành chính)',
            'nvk_da_thuc_hien': 'Đã làm NVK',
            'nvk_vuot_thieu': 'Vượt/Thiếu NVK',
            'hoan_thanh_gd': 'Hoàn thành GC',
            'hoan_thanh_nckh': 'Hoàn thành NCKH',
            'hoan_thanh_nvk': 'Hoàn thành NVK',
            'Trạng thái Chung': 'Trạng thái Chung'
        }
        if 'gc_give_to_dept' in df_display.columns and comp_mode == "Tập thể (theo Đơn vị)":
            col_mapping['gc_give_to_dept'] = 'Nhường cho Đơn vị'
            col_mapping['gc_receive_from_dept'] = 'Nhận từ Đơn vị'

        default_cols = ['Họ và tên', 'Nguồn', 'Chức danh', 'Đơn vị', 'Định mức thực tế GC', 'Vượt/Thiếu GC', 'Hoàn thành GC', 'Hoàn thành NCKH', 'Hoàn thành NVK', 'Trạng thái Chung']
        selected_col_names = st.multiselect("Chọn cột hiển thị", options=list(col_mapping.values()), default=default_cols)

        selected_cols = [k for k, v in col_mapping.items() if v in selected_col_names]

        df_table = df_display[selected_cols].copy()
        df_table.columns = [col_mapping[c] for c in selected_cols]

        def format_numeric(val):
            import math
            if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val):
                if val.is_integer() or val == int(val):
                    return f"{int(val)}"
                return f"{val:.1f}"
            return val

        def highlight_val(val):
            if isinstance(val, (int, float)):
                if val < 0:
                    return 'color: #b91c1c; font-weight: bold;'
                elif val > 0:
                    return 'color: #047857;'
            elif val == 'Đạt':
                return 'background-color: #ecfdf5; color: #047857; font-weight: bold;'
            elif val == 'Không đạt':
                return 'background-color: #fef2f2; color: #b91c1c; font-weight: bold;'
            elif val == 'Excel':
                return 'background-color: #e0f2fe; color: #0369a1; font-weight: bold; border-radius: 999px; padding: 0 8px;'
            elif val == 'Nhập lẻ':
                return 'background-color: #f0fdf4; color: #166534; font-weight: bold; border-radius: 999px; padding: 0 8px;'
            return ''

        config = {}
        if 'ID' in df_table.columns:
            config['ID'] = st.column_config.Column(pinned=True)
        if 'Họ và tên' in df_table.columns:
            config['Họ và tên'] = st.column_config.Column(pinned=True)

        float_cols = [col for col in [
            'Định mức gốc GC', 'Định mức thực tế GC', 'Số giờ được miễn giảm', 
            'Đã thực hiện (tổng GC)', 'Trong đó: Kế hoạch khác', 'Vượt/Thiếu GC', 
            'Định mức gốc NCKH', 'Định mức thực tế NCKH', 'Đã làm NCKH', 'Vượt/Thiếu NCKH',
            'Định mức NVK (Giờ hành chính)', 'Đã làm NVK', 'Vượt/Thiếu NVK',
            'Nhường cho Đơn vị', 'Nhận từ Đơn vị'
        ] if col in df_table.columns]

        format_dict = {col: format_numeric for col in float_cols}

        style_cols = [col for col in [
            'Số giờ được miễn giảm', 'Đã thực hiện (tổng GC)', 'Trong đó: Kế hoạch khác',
            'Vượt/Thiếu GC', 'Đã làm NCKH', 'Vượt/Thiếu NCKH', 'Vượt/Thiếu NVK', 
            'Hoàn thành GC', 'Hoàn thành NCKH', 'Hoàn thành NVK', 'Trạng thái Chung',
            'Nguồn', 'Nhường cho Đơn vị', 'Nhận từ Đơn vị'
        ] if col in df_table.columns]

        try:
            styled_df = df_table.style
            if float_cols:
                styled_df = styled_df.format(format_dict)
            if style_cols:
                styled_df = styled_df.map(highlight_val, subset=style_cols)
            st.dataframe(styled_df, width='stretch', column_config=config)
        except Exception as e:
            st.error(f"Lỗi render DataFrame: {e}")
            st.dataframe(df_table, width='stretch', column_config=config)

        # ── Transparency panel ─────────────────────────────────────────────────
        st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 32px 0;">', unsafe_allow_html=True)
        st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">manage_search</span> Tra cứu Công thức Tính Định mức</h3>', unsafe_allow_html=True)

        if not _HAS_FORMULA_BREAKDOWN or render_formula_card is None:
            st.info("Tính năng tra cứu công thức chưa sẵn sàng. Vui lòng cập nhật phiên bản mới nhất và khởi động lại ứng dụng.")
        else:
            st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 14px; margin-bottom: 16px;">Chọn một nhà giáo để xem chi tiết từng tham số được sử dụng trong tính toán: ngày lịch, ngày nghỉ lễ, ngày làm việc thực tế, số tuần, công thức GC/NCKH và các quy tắc miễn giảm.</p>', unsafe_allow_html=True)

            teacher_names = ['— Chọn nhà giáo —'] + sorted(df_display['name'].dropna().tolist())
            selected_teacher_name = st.selectbox(
                'Chọn nhà giáo để tra cứu công thức:',
                options=teacher_names,
                key='formula_teacher_select'
            )

            if selected_teacher_name != '— Chọn nhà giáo —':
                matched = df_display[df_display['name'] == selected_teacher_name]
                if not matched.empty:
                    tid_selected = int(matched.iloc[0]['id'])
                    with st.spinner('Đang tổng hợp chi tiết công thức...'):
                        breakdown = get_teacher_formula_breakdown(tid_selected, selected_tf_id)
                    render_formula_card(breakdown)

        st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 32px 0;">', unsafe_allow_html=True)
        _render_conversion_suggestions(df_display, selected_tf_id, conn)
    else:
        render_empty_state("Chưa có dữ liệu nhà giáo cho năm học này.")


