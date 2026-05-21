import streamlit as st
import pandas as pd
from calculations import calculate_teacher_metrics, get_conversion_limits, calculate_department_compensation
from database import get_connection
from components import render_metric_card, render_empty_state, render_warning_state, render_chip, render_sidebar

render_sidebar("dashboard")

st.title("Bảng điều khiển (Dashboard)")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Giám sát định mức theo thời gian thực và thực hiện quy đổi giờ theo Điều 12.</p>', unsafe_allow_html=True)

conn = get_connection()
df_tf = pd.read_sql_query("SELECT * FROM timeframes ORDER BY start_date DESC", conn)

if 'selected_tf_id' not in st.session_state:
    st.session_state['selected_tf_id'] = None

if st.session_state['selected_tf_id'] is None and not df_tf.empty:
    st.session_state['selected_tf_id'] = int(df_tf.iloc[0]['id'])

if not df_tf.empty:
    tf_options = {f"{row['name']} ({row['start_date']} đến {row['end_date']})": row['id'] for _, row in df_tf.iterrows()}
    current_key = [k for k, v in tf_options.items() if v == st.session_state['selected_tf_id']]
    current_key = current_key[0] if current_key else list(tf_options.keys())[0]

    col_tf, _ = st.columns([1, 2])
    tf_sel = col_tf.selectbox("Chọn Năm học", options=list(tf_options.keys()), index=list(tf_options.keys()).index(current_key))
    if tf_options[tf_sel] != st.session_state['selected_tf_id']:
        st.session_state['selected_tf_id'] = int(tf_options[tf_sel])
        st.rerun()

selected_tf_id = st.session_state['selected_tf_id']

if df_tf.empty:
    render_warning_state("Hệ thống chưa có Timeframe. Vui lòng tạo trong Cài đặt Hệ thống.")

if selected_tf_id:
    with st.spinner("Đang tính toán định mức và hệ số..."):
        df_teachers = calculate_teacher_metrics(timeframe_id=selected_tf_id)

    if not df_teachers.empty:
        hist_query = "SELECT teacher_id, value_text as dept_name FROM teacher_role_history WHERE record_type = 'DEPARTMENT' ORDER BY start_date DESC"
        df_dept_hist = pd.read_sql_query(hist_query, conn)
        df_dept_latest = df_dept_hist.drop_duplicates(subset=['teacher_id'], keep='first')

        df_display = pd.merge(df_teachers, df_dept_latest, left_on='id', right_on='teacher_id', how='left')
        df_display['dept_name'] = df_display['dept_name'].fillna('Chưa phân công')

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
            render_metric_card("Kế hoạch khác (GC)", f"{tong_nvk:,.1f}", icon="assignment")

        st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 32px 0;">', unsafe_allow_html=True)

        st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">swap_horiz</span> Gợi ý Quy đổi (Điều 12 Quy định T04)</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 14px; margin-bottom: 16px;">Hệ thống tự động phát hiện các nhà giáo thiếu định mức nhưng thừa giờ ở mảng khác để gợi ý quy đổi.</p>', unsafe_allow_html=True)

        has_suggestion = False
        for _, row in df_display.iterrows():
            limits = get_conversion_limits(row['id'], selected_tf_id)
            if not limits: continue

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
                    if col_btn.button(f"Đổi {limits['max_nckh_to_spend']:.1f} NCKH → {limits['gc_gained']:.1f} GC", key=f"n2g_{row['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO manual_conversions (teacher_id, timeframe_id, from_category, to_category, from_amount, to_amount) VALUES (?, ?, ?, ?, ?, ?)",
                                       (row['id'], selected_tf_id, 'NCKH', 'Giảng dạy', limits['max_nckh_to_spend'], limits['gc_gained']))
                        conn.commit()
                        st.success("Đã áp dụng quy đổi!")
                        st.rerun()

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
                    if col_btn.button(f"Đổi {limits['max_gc_to_spend']:.1f} GC → {limits['nckh_gained']:.1f} NCKH", key=f"g2n_{row['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO manual_conversions (teacher_id, timeframe_id, from_category, to_category, from_amount, to_amount) VALUES (?, ?, ?, ?, ?, ?)",
                                       (row['id'], selected_tf_id, 'Giảng dạy', 'NCKH', limits['max_gc_to_spend'], limits['nckh_gained']))
                        conn.commit()
                        st.success("Đã áp dụng quy đổi!")
                        st.rerun()
            elif limits['warning'] and row['nckh_vuot_thieu_sau_quy_doi'] < 0 and row['gc_vuot_thieu_sau_quy_doi'] > 0:
                has_suggestion = True
                st.warning(f"**{row['name']}**: Thừa GC, thiếu NCKH nhưng **{limits['warning']}**")
            elif limits['warning'] and row['gc_vuot_thieu_sau_quy_doi'] < 0 and row['nckh_vuot_thieu_sau_quy_doi'] > 0:
                has_suggestion = True
                st.warning(f"**{row['name']}**: Thừa NCKH, thiếu GC nhưng **{limits['warning']}**")

        if not has_suggestion:
            st.markdown('<p style="color: var(--md-on-surface-variant);">Không có gợi ý quy đổi nào tại thời điểm này. Các cán bộ đã hoàn thành hoặc chưa đủ điều kiện.</p>', unsafe_allow_html=True)
    else:
        render_empty_state("Chưa có dữ liệu nhà giáo cho năm học này.")

    st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 32px 0;">', unsafe_allow_html=True)
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">table_chart</span> Bảng Dữ liệu Chi tiết</h3>', unsafe_allow_html=True)

    if not df_teachers.empty:
        apply_dept_comp = st.checkbox("Áp dụng Bù định mức Đơn vị (Điều 12.3)")
        if apply_dept_comp:
            df_display = calculate_department_compensation(df_display)
            st.info("Đã áp dụng bù định mức đơn vị. Giờ thừa được chia sẻ giữa các giảng viên trong cùng bộ môn.")

        df_display['Trạng thái'] = df_display.apply(
            lambda row: "Đạt" if row['gc_vuot_thieu_sau_quy_doi'] >= 0 and row['nckh_vuot_thieu_sau_quy_doi'] >= 0 else "Không đạt",
            axis=1
        )

        col_mapping = {
            'id': 'ID',
            'name': 'Họ và tên',
            'title_name': 'Chức danh',
            'dept_name': 'Đơn vị',
            'applied_reductions': 'Miễn giảm áp dụng',
            'base_gc': 'Định mức gốc GD',
            'dinh_muc_gc_phai_thuc_hien': 'Định mức thực tế GD',
            'so_gio_duoc_mien_giam': 'Số giờ được miễn giảm',
            'tổng_gc_da_thuc_hien': 'Đã Giảng dạy (tổng GC)',
            'nvk_da_thuc_hien': 'Trong đó: Kế hoạch khác',
            'gc_vuot_thieu_sau_quy_doi': 'Vượt/Thiếu GD',
            'base_nckh': 'Định mức gốc NCKH',
            'dinh_muc_nckh_phai_thuc_hien': 'Định mức thực tế NCKH',
            'nckh_da_thuc_hien': 'Đã NCKH',
            'nckh_vuot_thieu_sau_quy_doi': 'Vượt/Thiếu NCKH',
            'Trạng thái': 'Trạng thái'
        }
        if 'gc_give_to_dept' in df_display.columns and apply_dept_comp:
            col_mapping['gc_give_to_dept'] = 'Nhường cho Đơn vị'
            col_mapping['gc_receive_from_dept'] = 'Nhận từ Đơn vị'

        selected_col_names = st.multiselect("Chọn cột hiển thị", options=list(col_mapping.values()), default=list(col_mapping.values()))

        selected_cols = [k for k, v in col_mapping.items() if v in selected_col_names]

        df_table = df_display[selected_cols].copy()
        df_table.columns = [col_mapping[c] for c in selected_cols]

        def highlight_val(val):
            if isinstance(val, (int, float)) and val < 0:
                return 'color: var(--md-red); font-weight: bold'
            elif isinstance(val, (int, float)) and val > 0:
                return 'color: var(--md-green)'
            elif val == 'Đạt':
                return 'background-color: var(--md-green-bg); color: var(--md-green); font-weight: bold'
            elif val == 'Không đạt':
                return 'background-color: var(--md-red-bg); color: var(--md-red); font-weight: bold'
            return ''

        config = {}
        if 'ID' in df_table.columns:
            config['ID'] = st.column_config.Column(pinned=True)
        if 'Họ và tên' in df_table.columns:
            config['Họ và tên'] = st.column_config.Column(pinned=True)

        try:
            st.dataframe(df_table.round(1).style.map(highlight_val), width='stretch', column_config=config)
        except Exception:
            st.dataframe(df_table.round(1), width='stretch', column_config=config)

conn.close()
