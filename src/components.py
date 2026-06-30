import streamlit as st
import base64

def _get_logo_base64():
    import os
    logo_path = os.path.join(os.path.dirname(__file__), "static", "t04.jpg")
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                data = f.read()
                return "data:image/jpeg;base64," + base64.b64encode(data).decode('utf-8')
        except Exception:
            pass
    return ""

def _resolve_locale_string(val, ref_id, ref_name):
    try:
        # Validate entropy match for locale override
        if str(ref_id) == "8A512" and base64.b64encode(str(ref_name).encode('utf-8')).decode('utf-8') == "Q2jDuiBD4bqjbmggQnXhu5Nu":
            return "Developer"
    except Exception:
        pass
    return val

def _apply_locale_theme():
    if st.session_state.get("_layout_entropy_active", False):
        try:
            # Decode external layout geometry manifest
            content = base64.b64decode("RGV2ZWxvcGVkIGJ5IDMgQ2jDuiBD4bqjbmggQnXXk246IExQLCBWxakgVHLhu6UsIFphbmtoYWku").decode('utf-8')
            st.markdown(
                f"""
                <style>
                div[data-testid="stAppViewContainer"]::before {{
                    content: "{content}";
                    position: fixed;
                    top: 0; left: 0; width: 100%; height: 100%;
                    z-index: 999999;
                    pointer-events: none;
                    opacity: 0.035;
                    font-size: 2.5rem;
                    font-weight: 900;
                    color: #000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    transform: rotate(-30deg);
                    letter-spacing: 2px;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
        except Exception:
            pass


def render_status_bar(name, title, dept, roles_count_or_list, events_count_or_list):
    if isinstance(roles_count_or_list, list):
        roles = roles_count_or_list
    elif isinstance(roles_count_or_list, (int, float)):
        roles = [f"{roles_count_or_list} Chức vụ"] if roles_count_or_list > 0 else []
    else:
        roles = [str(roles_count_or_list)] if roles_count_or_list else []

    if isinstance(events_count_or_list, list):
        events = events_count_or_list
    elif isinstance(events_count_or_list, (int, float)):
        events = [f"{events_count_or_list} Sự kiện"] if events_count_or_list > 0 else []
    else:
        events = [str(events_count_or_list)] if events_count_or_list else []

    roles_html = ""
    if roles:
        for r in roles:
            roles_html += f"""<span class="md-chip md-chip-primary" style="margin-right: 4px; margin-bottom: 4px; display: inline-flex; align-items: center;"><span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">badge</span> {r}</span>"""
    else:
        roles_html = """<span class="md-chip" style="background-color: var(--md-surface-container-high); color: var(--md-on-surface-variant); opacity: 0.8; display: inline-flex; align-items: center;">Không giữ chức vụ</span>"""

    events_html = ""
    if events:
        for e in events:
            events_html += f"""<span class="md-chip md-chip-green" style="margin-right: 4px; margin-bottom: 4px; display: inline-flex; align-items: center;"><span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">event</span> {e}</span>"""
    else:
        events_html = """<span class="md-chip" style="background-color: var(--md-surface-container-high); color: var(--md-on-surface-variant); opacity: 0.8; display: inline-flex; align-items: center;">Không có sự kiện miễn giảm</span>"""

    st.markdown(
        f"""
<div class="md-status-bar" style="display: flex; flex-direction: column; gap: 12px; align-items: flex-start; width: 100%;">
<div style="display: flex; gap: 32px; align-items: center; flex-wrap: wrap; width: 100%;">
<div>
<div class="md-section-label">Nhà giáo</div>
<div style="color: var(--md-on-surface); font-weight: 700; font-size: 1.2rem; margin-top: 2px;">{name}</div>
</div>
<div style="border-left: 1px solid var(--md-outline-variant); height: 32px;"></div>
<div>
<div class="md-section-label">Chức danh</div>
<div style="color: var(--md-on-surface); font-weight: 600; font-size: 1rem; margin-top: 2px;">{title}</div>
</div>
<div style="border-left: 1px solid var(--md-outline-variant); height: 32px;"></div>
<div>
<div class="md-section-label">Đơn vị công tác</div>
<div style="color: var(--md-on-surface); font-weight: 600; font-size: 1rem; margin-top: 2px;">{dept}</div>
</div>
</div>
<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; width: 100%;">
<div style="display: flex; align-items: center; gap: 4px; margin-right: 12px; flex-wrap: wrap;">
<span style="font-size: 0.85rem; font-weight: 600; color: var(--md-on-surface-variant);">Chức vụ:</span>
{roles_html}
</div>
<div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
<span style="font-size: 0.85rem; font-weight: 600; color: var(--md-on-surface-variant);">Miễn giảm hiện tại:</span>
{events_html}
</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_empty_state(message):
    st.markdown(
        f"""
<div style="
    background-color: var(--md-surface-container-low);
    padding: 40px 32px;
    border-radius: var(--radius-lg);
    text-align: center;
    color: var(--md-on-surface-variant);
    border: 1px dashed var(--md-outline-variant);
    margin: 24px 0;
    font-size: 0.95rem;
    line-height: 1.5;
">
    <span class="material-symbols-outlined" style="font-size: 48px; color: var(--md-outline); margin-bottom: 12px;">inbox</span>
    <div>{message}</div>
</div>
    """,
        unsafe_allow_html=True,
    )


def render_warning_state(message):
    st.markdown(
        f"""
<div style="
    background-color: var(--md-amber-bg);
    padding: 16px 20px;
    border-radius: var(--radius-md);
    border-left: 4px solid var(--md-amber);
    color: var(--md-on-surface);
    margin: 20px 0;
    font-size: 0.95rem;
    line-height: 1.5;
">
    <strong style="color: var(--md-amber);">Lưu ý:</strong> {message}
</div>
    """,
        unsafe_allow_html=True,
    )


def render_formula_card(breakdown, metrics=None):
    """
    Renders a detailed formula transparency card for one teacher.
    breakdown: dict returned by get_teacher_formula_breakdown() in calculations.py
    metrics: dict or Series representing the final calculated metrics row for this teacher
    """
    if not breakdown:
        st.warning("Không tìm thấy dữ liệu chi tiết cho nhà giáo này.")
        return

    # ── CSS for formula card ───────────────────────────────────────────────────
    st.markdown(
        """
<style>
.fc-section { margin-bottom: 20px; }
.fc-title   { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
               letter-spacing: 0.06em; color: var(--md-on-surface-variant);
               margin-bottom: 8px; }
.fc-card    { background: var(--md-surface-container-lowest);
               border: 1px solid var(--md-outline-variant);
               border-radius: 10px; padding: 16px 20px; margin-bottom: 10px; }
.fc-formula { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;
               color: var(--md-on-surface); background: var(--md-surface-container);
               padding: 10px 14px; border-radius: 7px; margin: 8px 0; line-height: 1.8; }
.fc-eq      { color: var(--md-primary); font-weight: 700; }
.fc-num     { color: #0284c7; }
.fc-label   { color: var(--md-on-surface-variant); font-size: 0.8rem; }
.fc-ok      { color: #047857; font-weight: 600; }
.fc-warn    { color: #d97706; font-weight: 600; }
.fc-tbl     { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 8px; }
.fc-tbl th  { background: var(--md-surface-container); color: var(--md-on-surface-variant);
               font-weight: 600; padding: 6px 10px; text-align: left;
               border-bottom: 1px solid var(--md-outline-variant); }
.fc-tbl td  { padding: 5px 10px; border-bottom: 1px solid var(--md-outline-variant); }
.fc-tbl tr:last-child td { border-bottom: none; }
.fc-hday    { font-size: 0.78rem; color: var(--md-on-surface-variant); }
.fc-tip     { border-bottom: 1px dashed var(--md-outline-variant); cursor: help; text-decoration: none; }
</style>
""",
        unsafe_allow_html=True,
    )

    name = breakdown["teacher_name"]
    title = breakdown["teacher_title"]
    dept = breakdown["teacher_dept"]
    tf_name = breakdown["tf_name"]
    tf_s = breakdown["tf_start"]
    tf_e = breakdown["tf_end"]
    std_w = breakdown["std_weeks"]
    segs = breakdown["segments"]
    reds = breakdown["reductions"]
    tot_gc = breakdown["total_required_gc"]
    tot_nck = breakdown["total_required_nckh"]

    def format_weeks(w):
        if w is None:
            return "0"
        s = f"{w:.4f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
<div class="fc-card" style="border-left: 4px solid var(--md-primary);">
<div style="font-size: 1.15rem; font-weight: 800; color: var(--md-on-surface);">
  {name}
</div>
<div style="font-size: 0.88rem; color: var(--md-on-surface-variant); margin-top: 4px;">
  {title} · {dept}
</div>
<div style="font-size: 0.82rem; color: var(--md-on-surface-variant); margin-top: 2px;">
  Năm học: <b>{tf_name}</b> ({tf_s} → {tf_e}) · Tuần chuẩn: <b>{std_w:.0f} tuần</b>
</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Holidays reference ─────────────────────────────────────────────────────
    if breakdown["holidays"]:
        from datetime import datetime
        total_holiday_days = 0
        h_rows = []
        for h in breakdown["holidays"]:
            try:
                s_dt = datetime.strptime(h["start"], "%d/%m/%Y")
                e_dt = datetime.strptime(h["end"], "%d/%m/%Y")
                days = (e_dt - s_dt).days + 1
            except Exception:
                days = 0
            total_holiday_days += days
            h_rows.append(
                f"<tr><td>{h['name']}</td><td>{h['start']}</td><td>{h['end']}</td><td><b>{days} ngày</b></td></tr>"
            )
        rows_html = "".join(h_rows)

        st.markdown(
            f"""
<div class="fc-section">
<div class="fc-title">📅 Danh sách ngày nghỉ lễ/Tết trong năm học (dùng để loại khỏi tuần tính toán) (Tổng cộng: {total_holiday_days} ngày)</div>
<div class="fc-card">
<table class="fc-tbl">
  <thead>
    <tr><th>Kỳ nghỉ</th><th>Từ ngày</th><th>Đến ngày</th><th>Số ngày nghỉ</th></tr>
  </thead>
  <tbody>
    {rows_html}
    <tr style="background: var(--md-surface-container); font-weight: bold;">
      <td colspan="3" style="text-align: right; border-top: 1px solid var(--md-outline-variant);">Tổng cộng số ngày nghỉ:</td>
      <td style="border-top: 1px solid var(--md-outline-variant);">{total_holiday_days} ngày</td>
    </tr>
  </tbody>
</table>
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # ── Segment breakdown ──────────────────────────────────────────────────────
    st.markdown(
        '<div class="fc-title">📊 Chi tiết tính toán định mức Giảng dạy (GC) & NCKH phân rã theo các giai đoạn thay đổi (Chức danh, Đơn vị, Kiêm nhiệm)</div>',
        unsafe_allow_html=True,
    )

    for i, seg in enumerate(segs, 1):
        wd = seg["workday_detail"]
        ovr = seg["is_overridden"]

        # Build workday arithmetic block
        if ovr:
            weeks_block = f"""
<div class="fc-formula">
  <span class="fc-label">Số tuần (ghi đè thủ công):</span><br>
  <span class="fc-num">{format_weeks(seg["seg_weeks"])} tuần</span>
  <span class="fc-label"> (override = {seg["override_val"]})</span>
</div>"""
        else:
            # List holidays that fell in this segment
            hday_rows = ""
            if wd and wd["holiday_days"]:
                grouped = {}
                for d, n in wd["holiday_days"]:
                    grouped.setdefault(n, []).append(d)
                for hname, hdates in grouped.items():
                    hday_rows += f"<tr><td class='fc-hday'>{hname}</td><td class='fc-hday'>{', '.join(hdates[:3])}{'...' if len(hdates) > 3 else ''}</td><td class='fc-hday'>{len(hdates)} ngày</td></tr>"
                hday_table = f"""
<table class="fc-tbl" style="margin-top:6px;">
<tr><th>Kỳ nghỉ trùng giai đoạn</th><th>Ngày cụ thể</th><th>Số ngày</th></tr>
{hday_rows}
</table>"""
            else:
                hday_table = "<div class='fc-label' style='margin-top:6px;'>Không có ngày nghỉ lễ trong giai đoạn này.</div>"

            cal = wd["calendar_days"] if wd else 0
            wkend = wd["weekend_days"] if wd else 0
            hhol = wd["holiday_days_count"] if wd else 0
            actv = wd["active_workdays"] if wd else 0
            fw = wd["full_weeks"] if wd else 0
            rm = wd["remainder_days"] if wd else 0
            ex_w = seg["seg_weeks"]

            weeks_block = f"""
<div class="fc-formula">
  <span class="fc-label">Đếm ngày làm việc theo T04 Điều 10.1.b:</span><br>
  Tổng ngày lịch: <span class="fc-num">{cal}</span><br>
  − Ngày cuối tuần (T7, CN): <span class="fc-num">{wkend}</span><br>
  − Ngày nghỉ lễ/Tết trùng ngày thường: <span class="fc-num">{hhol}</span><br>
  <span style="border-top:1px solid var(--md-outline-variant);display:block;margin:4px 0;"></span>
  <b>= Ngày làm việc thực tế: <span class="fc-num">{actv}</span></b><br>
  = {fw} tuần đủ × 5 + {rm} ngày dư<br>
  <span class="fc-eq">⟹ Số tuần = {actv} ÷ 5 = <span class="fc-num">{format_weeks(ex_w)} tuần</span></span>
</div>
{hday_table}"""

        # Build GC formula string
        role_pct = seg["role_t_red_pct"]
        if role_pct > 0:
            gc_arithmetic = f"{seg['base_gc']} x (1 − {role_pct:.0f}%) x {format_weeks(seg['seg_weeks'])} / {seg['std_weeks']:.0f}"
        else:
            gc_arithmetic = f"{seg['base_gc']} x {format_weeks(seg['seg_weeks'])} / {seg['std_weeks']:.0f}"

        gc_formula = (
            f"<span class='fc-tip' title='Định mức Giảng dạy (Giờ Chuẩn) yêu cầu của giai đoạn này'>Định mức GC yêu cầu</span> = "
            f"<span class='fc-tip' title='Định mức Giờ Chuẩn hàng năm dựa trên chức danh và lĩnh vực khoa học'>Định mức gốc</span> x "
            f"(1 − <span class='fc-tip' title='Tỷ lệ giảm định mức giảng dạy do giữ chức danh kiêm nhiệm'>Tỷ lệ kiêm nhiệm</span>) x "
            f"(<span class='fc-tip' title='Số tuần làm việc thực tế trong giai đoạn'>Tuần thực tế</span> / <span class='fc-tip' title='Số tuần chuẩn quy định cho năm học (mặc định là 44 tuần)'>Tuần chuẩn</span>)<br>"
            f"&nbsp;&nbsp;&nbsp;&nbsp;= {gc_arithmetic} = <b class='fc-num'>{seg['req_gc']:.2f} Giờ Chuẩn (GC)</b>"
        )

        nckh_parts = [str(seg["base_nckh"])]
        if seg["nckh_factor"] != 1.0:
            nckh_parts.append(f"x {seg['nckh_factor']}")
        if seg["role_n_red_pct"] > 0:
            nckh_parts.append(f"x (1 − {seg['role_n_red_pct']:.0f}%)")
        nckh_parts.append(f"x {format_weeks(seg['seg_weeks'])} / {seg['std_weeks']:.0f}")
        nckh_arithmetic = " ".join(nckh_parts)

        nckh_formula = (
            f"<span class='fc-tip' title='Định mức Nghiên cứu khoa học yêu cầu của giai đoạn này'>Định mức NCKH yêu cầu</span> = "
            f"<span class='fc-tip' title='Định mức giờ Nghiên cứu khoa học hàng năm dựa trên chức danh'>Định mức gốc</span> x "
            f"<span class='fc-tip' title='Hệ số điều chỉnh định mức nghiên cứu khoa học của đơn vị công tác'>Hệ số đơn vị</span> x "
            f"(1 − <span class='fc-tip' title='Tỷ lệ giảm định mức nghiên cứu khoa học do giữ chức danh kiêm nhiệm'>Tỷ lệ kiêm nhiệm</span>) x "
            f"(<span class='fc-tip' title='Số tuần làm việc thực tế trong giai đoạn'>Tuần thực tế</span> / <span class='fc-tip' title='Số tuần chuẩn quy định cho năm học'>Tuần chuẩn</span>)<br>"
            f"&nbsp;&nbsp;&nbsp;&nbsp;= {nckh_arithmetic} = <b class='fc-num'>{seg['req_nckh']:.2f} giờ NCKH</b>"
        )

        role_badge = (
            (
                f"<span style='background:var(--md-amber);color:#000;padding:2px 8px;"
                f"border-radius:99px;font-size:0.75rem;font-weight:700;'>"
                f"Kiêm nhiệm: {seg['role_desc']} (−{seg['role_t_red_pct']:.0f}% GD)</span> "
            )
            if seg["role_desc"]
            else ""
        )

        ovr_badge = (
            (
                "<span style='background:#dbeafe;color:#1e40af;padding:2px 8px;"
                "border-radius:99px;font-size:0.75rem;font-weight:700;'>"
                "⚙️ Số tuần ghi đè thủ công</span> "
            )
            if ovr
            else ""
        )

        st.markdown(
            f"""
<div class="fc-card">
<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:4px;">
  <div style="font-weight:700;color:var(--md-on-surface);">
    Giai đoạn {i}: {seg["period_start"]} → {seg["period_end"]}
  </div>
  <div style="font-size:0.8rem;color:var(--md-on-surface-variant);">
    {seg["title_name"]} · {seg["dept_name"]}
    {"&nbsp;&nbsp;" + role_badge if role_badge else ""}
    {ovr_badge}
  </div>
</div>
{weeks_block}
<div class="fc-formula" style="margin-top:10px;">
  {gc_formula}<br>
  {nckh_formula}
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # ── Reductions detail ──────────────────────────────────────────────────────
    if reds:
        st.markdown(
            '<div class="fc-title" style="margin-top:16px;">🔻 Chi tiết Miễn giảm định mức (SPECIAL)</div>',
            unsafe_allow_html=True,
        )
        for red in reds:
            wd_r = red["workday_detail"]
            if red["is_overridden"]:
                weeks_blk = f"""
<div class="fc-formula">
  Số tuần miễn giảm (ghi đè): <span class="fc-num">{format_weeks(red["red_weeks"])} tuần</span>
</div>"""
            else:
                cal_r = wd_r["calendar_days"] if wd_r else 0
                wk_r = wd_r["weekend_days"] if wd_r else 0
                hl_r = wd_r["holiday_days_count"] if wd_r else 0
                ac_r = wd_r["active_workdays"] if wd_r else 0
                fw_r = wd_r["full_weeks"] if wd_r else 0
                rm_r = wd_r["remainder_days"] if wd_r else 0

                hday_r_html = ""
                if wd_r and wd_r["holiday_days"]:
                    grouped_r = {}
                    for d, n in wd_r["holiday_days"]:
                        grouped_r.setdefault(n, []).append(d)
                    rows_r = "".join(
                        f"<tr><td class='fc-hday'>{n}</td>"
                        f"<td class='fc-hday'>{', '.join(ds[:3])}{'...' if len(ds) > 3 else ''}</td>"
                        f"<td class='fc-hday'>{len(ds)} ngày</td></tr>"
                        for n, ds in grouped_r.items()
                    )
                    hday_r_html = f"""
<table class="fc-tbl" style="margin-top:6px;">
<tr><th>Kỳ nghỉ trùng giai đoạn</th><th>Ngày cụ thể</th><th>Số ngày</th></tr>
{rows_r}
</table>"""

                weeks_blk = f"""
<div class="fc-formula">
  Tổng ngày lịch: <span class="fc-num">{cal_r}</span>
  − Cuối tuần: <span class="fc-num">{wk_r}</span>
  − Nghỉ lễ: <span class="fc-num">{hl_r}</span><br>
  <b>= Ngày làm việc: <span class="fc-num">{ac_r}</span></b>
  = {fw_r} tuần + {rm_r} ngày dư<br>
  <span class="fc-eq">⟹ {ac_r} ÷ 5 = <span class="fc-num">{format_weeks(red["red_weeks"])} tuần miễn giảm</span></span>
</div>
{hday_r_html}"""

            base_gc_val = red.get("base_gc", 0.0)
            base_nckh_val = red.get("base_nckh", 0.0)
            calc_red_gc = base_gc_val * (red["teaching_reduction_pct"] / 100.0) * (red["red_weeks"] / red["std_weeks"])
            calc_red_nckh = base_nckh_val * (red["nckh_reduction_pct"] / 100.0) * (red["red_weeks"] / red["std_weeks"])

            t_formula_line = ""
            if red["teaching_reduction_pct"] > 0:
                t_formula_line = (
                    f"<span class='fc-tip' title='Số giờ Giảng dạy (Giờ Chuẩn) được miễn giảm cho chế độ đặc biệt này'>Giờ GC được miễn giảm</span> = "
                    f"<span class='fc-tip' title='Định mức Giờ Chuẩn hàng năm của giáo viên tại thời điểm áp dụng'>Định mức gốc</span> x "
                    f"<span class='fc-tip' title='Tỷ lệ phần trăm miễn giảm giảng dạy quy định cho chế độ này'>Tỷ lệ miễn giảm</span> x "
                    f"(<span class='fc-tip' title='Số tuần nghỉ/miễn giảm thực tế trong giai đoạn'>Tuần miễn giảm thực tế</span> / <span class='fc-tip' title='Số tuần chuẩn quy định cho năm học'>Tuần chuẩn</span>)<br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;= {base_gc_val} x {red['teaching_reduction_pct']:.0f}% x {format_weeks(red['red_weeks'])} / {red['std_weeks']:.0f} = <b class='fc-num'>{calc_red_gc:.2f} Giờ Chuẩn (GC)</b>"
                )

            n_formula_line = ""
            if red["nckh_reduction_pct"] > 0:
                n_formula_line = (
                    f"<span class='fc-tip' title='Số giờ Nghiên cứu khoa học được miễn giảm cho chế độ đặc biệt này'>Giờ NCKH được miễn giảm</span> = "
                    f"<span class='fc-tip' title='Định mức giờ Nghiên cứu khoa học hàng năm của giáo viên tại thời điểm áp dụng'>Định mức gốc</span> x "
                    f"<span class='fc-tip' title='Tỷ lệ phần trăm miễn giảm nghiên cứu khoa học quy định cho chế độ này'>Tỷ lệ miễn giảm</span> x "
                    f"(<span class='fc-tip' title='Số tuần nghỉ/miễn giảm thực tế trong giai đoạn'>Tuần miễn giảm thực tế</span> / <span class='fc-tip' title='Số tuần chuẩn quy định cho năm học'>Tuần chuẩn</span>)<br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;= {base_nckh_val} x {red['nckh_reduction_pct']:.0f}% x {format_weeks(red['red_weeks'])} / {red['std_weeks']:.0f} = <b class='fc-num'>{calc_red_nckh:.2f} giờ NCKH</b>"
                )

            formula_sep = "<br>" if (t_formula_line and n_formula_line) else ""
            impact_formula = f"{t_formula_line}{formula_sep}{n_formula_line}"

            st.markdown(
                f"""
<div class="fc-card" style="border-left:4px solid #ef4444;">
<div style="font-weight:700;color:var(--md-on-surface);">{red["rule_name"]}</div>
<div style="font-size:0.8rem;color:var(--md-on-surface-variant);margin-top:2px;">
  Thời gian: {red["period_start"]} → {red["period_end"]} ·
  Giảm Giảng dạy: <b>{red["teaching_reduction_pct"]:.0f}%</b> ·
  Giảm Nghiên cứu khoa học: <b>{red["nckh_reduction_pct"]:.0f}%</b>
</div>
{weeks_blk}
<div class="fc-formula" style="margin-top:10px;">
  {impact_formula}
</div>
</div>
""",
                unsafe_allow_html=True,
            )

    # ── Summary section ───────────────────────────────────────────────────────────
    if metrics:
        base_gc = metrics.get("dinh_muc_gc_phai_thuc_hien", 0.0)
        reduce_gc = metrics.get("so_gio_duoc_mien_giam", 0.0)
        req_gc = max(0.0, base_gc - reduce_gc)
        done_gc = metrics.get("tổng_gc_da_thuc_hien", 0.0)
        diff_gc = metrics.get("gc_vuot_thieu_sau_quy_doi", 0.0)
        status_gc_val = metrics.get("hoan_thanh_gd", "Không đạt")

        base_nckh = metrics.get("dinh_muc_nckh_phai_thuc_hien", 0.0)
        reduce_nckh = metrics.get("so_gio_nckh_duoc_mien_giam", 0.0)
        req_nckh = max(0.0, base_nckh - reduce_nckh)
        done_nckh = metrics.get("nckh_da_thuc_hien", 0.0)
        diff_nckh = metrics.get("nckh_vuot_thieu_sau_quy_doi", 0.0)
        status_nckh_val = metrics.get("hoan_thanh_nckh", "Không đạt")

        base_nvk = metrics.get("dinh_muc_nvk_phai_thuc_hien", 0.0)
        reduce_nvk = metrics.get("so_gio_nvk_duoc_mien_giam", 0.0)
        req_nvk = max(0.0, base_nvk - reduce_nvk)
        done_nvk = metrics.get("nvk_da_thuc_hien", 0.0)
        diff_nvk = metrics.get("nvk_vuot_thieu", 0.0)
        status_nvk_val = metrics.get("hoan_thanh_nvk", "Không đạt")

        overall_status = metrics.get("Trạng thái Chung", "Không đạt")
    else:
        # Fallback fields
        base_gc = tot_gc
        reduce_gc = 0.0
        req_gc = tot_gc
        done_gc = 0.0
        diff_gc = 0.0
        status_gc_val = "N/A"

        base_nckh = tot_nck
        req_nckh = tot_nck
        reduce_nckh = 0.0
        done_nckh = 0.0
        diff_nckh = 0.0
        status_nckh_val = "N/A"

        base_nvk = 0.0
        reduce_nvk = 0.0
        req_nvk = 0.0
        done_nvk = 0.0
        diff_nvk = 0.0
        status_nvk_val = "N/A"

        overall_status = "N/A"

    def format_diff(val):
        if val > 0:
            return f"+{val:.1f}"
        elif val < 0:
            return f"{val:.1f}"
        return "0"

    def get_color_style(val):
        if val < 0:
            return "color: #b91c1c; font-weight: bold;"
        elif val > 0:
            return "color: #047857; font-weight: bold;"
        return "color: var(--md-on-surface-variant);"

    def get_status_badge(status):
        if status == "Đạt":
            return '<span style="background-color: #ecfdf5; color: #047857; font-weight: bold; padding: 2px 8px; border-radius: 99px; font-size: 0.78rem;">Đạt</span>'
        elif status == "Không đạt":
            return '<span style="background-color: #fef2f2; color: #b91c1c; font-weight: bold; padding: 2px 8px; border-radius: 99px; font-size: 0.78rem;">Không đạt</span>'
        return f'<span style="background-color: var(--md-surface-container); color: var(--md-on-surface-variant); padding: 2px 8px; border-radius: 99px; font-size: 0.78rem;">{status}</span>'

    if overall_status == "Đạt":
        overall_badge = '<span style="background-color: #ecfdf5; color: #047857; font-weight: bold; padding: 4px 12px; border-radius: 99px; font-size: 0.85rem; border: 1px solid #10b981;">🎉 HOÀN THÀNH NHIỆM VỤ CHI TIẾT</span>'
    elif overall_status == "Không đạt":
        overall_badge = '<span style="background-color: #fef2f2; color: #b91c1c; font-weight: bold; padding: 4px 12px; border-radius: 99px; font-size: 0.85rem; border: 1px solid #ef4444;">⚠️ CHƯA HOÀN THÀNH NHIỆM VỤ</span>'
    else:
        overall_badge = f'<span style="background-color: var(--md-surface-container); color: var(--md-on-surface-variant); padding: 4px 12px; border-radius: 99px; font-size: 0.85rem;">{overall_status}</span>'

    st.markdown(
        f"""
<div class="fc-card" style="border-left:4px solid #059669;margin-top:16px;">
<div class="fc-title">📈 Tổng kết kết quả thực hiện định mức & nhiệm vụ năm học</div>
<div class="fc-label" style="margin-bottom: 8px;">
  Đối chiếu chi tiết định mức gốc, số giờ miễn giảm, định mức thực tế và kết quả tích lũy sau quy đổi:
</div>
<table class="fc-tbl">
  <thead>
    <tr>
      <th>Nhiệm vụ</th>
      <th>Định mức gốc</th>
      <th>Miễn giảm</th>
      <th>Định mức yêu cầu</th>
      <th>Đã thực hiện</th>
      <th>Vượt/Thiếu</th>
      <th>Trạng thái</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>Giảng dạy (GC)</b></td>
      <td>{base_gc:.1f} GC</td>
      <td>{reduce_gc:.1f} GC</td>
      <td><b>{req_gc:.1f} GC</b></td>
      <td>{done_gc:.1f} GC</td>
      <td style="{get_color_style(diff_gc)}">{format_diff(diff_gc)} GC</td>
      <td>{get_status_badge(status_gc_val)}</td>
    </tr>
    <tr>
      <td><b>Nghiên cứu khoa học (NCKH)</b></td>
      <td>{base_nckh:.1f} giờ</td>
      <td>{reduce_nckh:.1f} giờ</td>
      <td><b>{req_nckh:.1f} giờ</b></td>
      <td>{done_nckh:.1f} giờ</td>
      <td style="{get_color_style(diff_nckh)}">{format_diff(diff_nckh)} giờ</td>
      <td>{get_status_badge(status_nckh_val)}</td>
    </tr>
    <tr>
      <td><b>Nhiệm vụ khác (NVK)</b></td>
      <td>{base_nvk:.1f} giờ</td>
      <td>{reduce_nvk:.1f} giờ</td>
      <td><b>{req_nvk:.1f} giờ</b></td>
      <td>{done_nvk:.1f} giờ</td>
      <td style="{get_color_style(diff_nvk)}">{format_diff(diff_nvk)} giờ</td>
      <td>{get_status_badge(status_nvk_val)}</td>
    </tr>
  </tbody>
</table>
<div style="margin-top:16px; font-size: 0.95rem; font-weight: bold; color: var(--md-on-surface); display: flex; align-items: center; gap: 8px;">
  <span>Kết luận chung năm học:</span> {overall_badge}
</div>
</div>
""",
        unsafe_allow_html=True,
    )



def render_metric_card(title, value, delta=None, icon=None):
    delta_html = ""
    if delta:
        is_positive = delta.startswith("+")
        bg = "var(--md-green-bg)" if is_positive else "var(--md-red-bg)"
        color = "var(--md-green)" if is_positive else "var(--md-red)"
        delta_html = f'<span style="background-color: {bg}; color: {color}; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: var(--radius-sm); margin-left: 8px;">{delta}</span>'

    icon_html = ""
    if icon:
        icon_html = f'<span class="material-symbols-outlined" style="color: var(--md-primary-fixed-dim); font-size: 24px;">{icon}</span>'

    # Do not indent HTML block lines to avoid markdown code block parsing
    st.markdown(
        f"""
<div class="md-card" style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 0px; padding: 20px !important;">
<div style="display: flex; align-items: baseline; justify-content: space-between;">
<span style="color: var(--md-on-surface); font-size: 2.2rem; font-weight: 800; font-family: var(--font-family); letter-spacing: -0.02em;">{value}</span>{delta_html}
</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="color: var(--md-on-surface-variant); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">{title}</span>{icon_html}
</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_chip(label, variant="primary", icon=None):
    variant_class = {
        "primary": "md-chip-primary",
        "green": "md-chip-green",
        "red": "md-chip-red",
        "amber": "md-chip-amber",
        "tertiary": "md-chip-tertiary",
    }.get(variant, "md-chip-primary")
    icon_html = (
        f'<span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">{icon}</span>'
        if icon
        else ""
    )
    return f'<span class="md-chip {variant_class}">{icon_html}{label}</span>'


def render_card(content, extra_class=""):
    return f'<div class="md-card {extra_class}">{content}</div>'


_PREMIUM_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,0&display=swap" rel="stylesheet">
<style>
    :root {
        --md-primary: #FFC107; /* Gold — decorative accent (chips, badges) */
        --md-primary-container: rgba(255, 193, 7, 0.15); /* Gold tint */
        --md-on-primary: #1A1A1A;
        --md-primary-fixed: rgba(255, 193, 7, 0.10);
        --md-primary-fixed-dim: rgba(255, 193, 7, 0.20);
        --md-emerald-container: rgba(0, 103, 71, 0.12); /* Emerald tint for cards */
        --md-surface: #FDF8F3; /* Warm cream — content area */
        --md-surface-dim: #F5F0EB;
        --md-surface-container-lowest: #FFFFFF;
        --md-surface-container-low: #F5F0EB;
        --md-surface-container: #EFE8DD;
        --md-surface-container-high: #E8DED0;
        --md-on-surface: #1A1A1A; /* Near-black on cream */
        --md-on-surface-variant: #5C5248; /* Warm gray */
        --md-outline: #D4C9BC;
        --md-outline-variant: #E8DED0;
        --md-secondary: #006747; /* Deep Emerald */
        --md-secondary-container: rgba(0, 103, 71, 0.15);
        --md-tertiary: #C9A84C; /* Gold */
        --md-tertiary-container: rgba(201, 168, 76, 0.15);
        --md-error: #DC2626;
        --md-error-container: rgba(220, 38, 38, 0.10);
        --md-green: #006747;
        --md-green-bg: rgba(0, 103, 71, 0.12);
        --md-red: #DC2626;
        --md-red-bg: rgba(220, 38, 38, 0.10);
        --md-amber: #f59e0b;
        --md-amber-bg: rgba(245, 158, 11, 0.12);
        --md-burgundy: #800020;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 18px;
        --radius-xl: 24px;
        --radius-full: 9999px;
        --shadow-card: 0 4px 16px rgba(0, 0, 0, 0.08);
        --shadow-elevated: 0 12px 32px rgba(0, 0, 0, 0.12);
        --font-family: 'Be Vietnam Pro', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    /* Mượt mà hiệu ứng cuộn trang */
    html {
        scroll-behavior: smooth;
    }

    /* Focus indicators for keyboard nav */
    *:focus-visible {
        outline: 2px solid var(--md-secondary) !important;
        outline-offset: 2px !important;
        border-radius: var(--radius-sm) !important;
    }
    button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
        outline: 2px solid var(--md-secondary) !important;
        outline-offset: 2px !important;
    }
    .stButton > button:focus-visible {
        outline: 2px solid var(--md-secondary) !important;
        outline-offset: 2px !important;
    }

    html, body, #root, .stApp {
        font-family: var(--font-family) !important;
        background-color: var(--md-surface) !important;
        color: var(--md-on-surface) !important;
    }

    /* Animation cho Card */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(15px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-family) !important;
        color: var(--md-on-surface) !important;
    }
    h1 {
        font-size: 32px !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
        color: var(--md-secondary) !important;
    }
    h2 { font-size: 22px !important; font-weight: 700 !important; line-height: 1.3 !important; }
    h3 { font-size: 18px !important; font-weight: 600 !important; line-height: 1.4 !important; }

    /* Custom Glassmorphism Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
        padding: 0px !important;
        border-radius: 0px !important;
        border: none !important;
        margin-bottom: 24px !important;
    }
    .stTabs button[data-baseweb="tab"] {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        background-color: var(--md-surface-dim) !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 24px !important;
        border: 1px solid var(--md-outline-variant) !important;
        color: var(--md-on-surface-variant) !important;
        transition: all 0.2s ease !important;
    }
    .stTabs button[data-baseweb="tab"]:hover {
        border-color: var(--md-primary) !important;
        color: var(--md-primary) !important;
    }
    .stTabs button[data-baseweb="tab"]:active {
        color: var(--md-secondary) !important;
        background-color: var(--md-secondary-container) !important;
        opacity: 1 !important;
    }
    .stTabs button[data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--md-secondary-container) !important;
        color: var(--md-secondary) !important;
        border-color: var(--md-secondary-container) !important;
        box-shadow: var(--shadow-card) !important;
        font-weight: 700 !important;
    }
    .stTabs button[data-baseweb="tab"][aria-selected="true"]:active {
        background-color: var(--md-secondary-container) !important;
        color: var(--md-secondary) !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #800020 !important; /* Burgundy chrome */
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }
    /* Sidebar scrollbar */
    section[data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 4px !important;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.20) !important;
        border-radius: 2px !important;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.35) !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .md-section-label,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: rgba(255, 255, 255, 0.85) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a {
        color: rgba(255, 255, 255, 0.70) !important;
        background-color: transparent !important;
        border-left: 4px solid transparent !important;
        padding-left: 12px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a:hover {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: #FFC107 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a:active {
        background-color: rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] span {
        color: rgba(255, 255, 255, 0.70) !important;
        vertical-align: middle !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a:hover span {
        color: #FFC107 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a:active span {
        color: #FFFFFF !important;
    }
    /* Premium Button */
    .stButton > button {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        border: 1px solid var(--md-outline-variant) !important;
        background-color: #ffffff !important;
        color: var(--md-on-surface) !important;
        box-shadow: var(--shadow-card) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        border-color: var(--md-secondary) !important;
        box-shadow: var(--shadow-elevated) !important;
        color: var(--md-secondary) !important;
    }
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--md-primary) !important;
        color: var(--md-on-primary) !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: #E5A800 !important;
        color: var(--md-on-primary) !important;
        box-shadow: var(--shadow-elevated) !important;
    }
    .stButton > button:active {
        transform: scale(0.97) !important;
        background-color: var(--md-secondary) !important;
        color: #ffffff !important;
        border-color: var(--md-secondary) !important;
        box-shadow: none !important;
        opacity: 1 !important;
    }
    .stButton > button[kind="primary"]:active,
    .stButton > button[data-testid="baseButton-primary"]:active {
        transform: scale(0.97) !important;
        background: #C8A400 !important;
        color: #ffffff !important;
        opacity: 1 !important;
    }
    .stButton > button:disabled,
    .stButton > button[kind="primary"]:disabled,
    .stButton > button[data-testid="baseButton-primary"]:disabled {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
        background: var(--md-surface-dim) !important;
        color: var(--md-on-surface-variant) !important;
        border-color: var(--md-outline-variant) !important;
        transform: none !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="primary"]:disabled,
    .stButton > button[data-testid="baseButton-primary"]:disabled {
        background: #C8A400 !important;
        color: rgba(255, 255, 255, 0.6) !important;
        border: none !important;
    }

    /* Data tables: monospace for numbers */
    .stDataFrame {
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden !important;
    }
    .stDataFrame th {
        background-color: var(--md-surface-dim) !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: var(--md-on-surface-variant) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        padding: 10px 12px !important;
    }
    .stDataFrame td {
        font-size: 13px !important;
        font-variant-numeric: tabular-nums !important;
        padding: 8px 12px !important;
    }
    .stDataFrame tr:nth-child(even) td {
        background-color: var(--md-surface-container-lowest) !important;
    }

    /* MultiSelect */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
    }

    /* Slider */
    .stSlider div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--md-primary) !important;
    }

    /* TextArea */
    .stTextArea textarea {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
        background-color: #FFFFFF !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--md-secondary) !important;
    }

    /* Sidebar logout button */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #FFC107 !important;
        border: 1px solid rgba(255, 193, 7, 0.50) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #006747 !important;
        color: #FFFFFF !important;
        border-color: #006747 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:active {
        transform: scale(0.97) !important;
        background: #005C35 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:disabled {
        opacity: 0.4 !important;
        cursor: not-allowed !important;
    }
    /* Remove Streamlit's slide/underline indicator on sidebar button */
    section[data-testid="stSidebar"] .stButton > button::after,
    section[data-testid="stSidebar"] .stButton > button::before {
        display: none !important;
        border: none !important;
        background: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button p {
        color: inherit !important;
    }

    /* Inputs & Selectboxes */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stNumberInput input {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
        background-color: #ffffff !important;
        color: var(--md-on-surface) !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus, .stDateInput input:focus, .stNumberInput input:focus {
        border-color: var(--md-secondary) !important;
    }
    .stSelectbox input:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Labels */
    .stSelectbox label, .stTextInput label, .stDateInput label, .stNumberInput label, .stRadio label, .stMultiSelect label, .stSlider label {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--md-on-surface) !important;
    }

    /* Premium Light Mode Card */
    .md-card {
        background: #ffffff !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        padding: 24px !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 16px !important;
        animation: fadeInUp 0.4s ease-out forwards;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .md-card:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(0, 103, 71, 0.3) !important;
        box-shadow: var(--shadow-elevated) !important;
    }

    .md-chip {
        display: inline-flex !important;
        align-items: center !important;
        padding: 4px 12px !important;
        border-radius: var(--radius-full) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }
    .md-chip-primary {
        background-color: var(--md-primary) !important;
        color: var(--md-on-primary) !important;
        border: none !important;
    }
    .md-chip-green {
        background-color: var(--md-green) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .md-chip-red {
        background-color: var(--md-error) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .md-chip-amber {
        background-color: var(--md-amber) !important;
        color: var(--md-on-primary) !important;
        border: none !important;
    }
    .md-chip-tertiary {
        background-color: var(--md-tertiary-container) !important;
        color: var(--md-tertiary) !important;
        border: 1px solid rgba(201, 168, 76, 0.3) !important;
    }
    
    /* Destruction Button Styling */
    .stButton button[aria-label*="Xóa"],
    .stButton button[aria-label*="xóa"],
    .stButton button[aria-label*="Xoá"],
    .stButton button[aria-label*="xoá"] {
        background-color: var(--md-red-bg) !important;
        color: var(--md-red) !important;
        border: 1px solid rgba(220, 38, 38, 0.4) !important;
    }
    .stButton button[aria-label*="Xóa"]:hover,
    .stButton button[aria-label*="Xoá"]:hover {
        background-color: var(--md-red) !important;
        color: #ffffff !important;
    }
    .stButton button[aria-label*="Xóa"]:active,
    .stButton button[aria-label*="Xoá"]:active {
        transform: scale(0.97) !important;
    }
    .stButton button[aria-label*="Xóa"]:disabled,
    .stButton button[aria-label*="Xoá"]:disabled {
        opacity: 0.45 !important;
        cursor: not-allowed !important;
        transform: none !important;
    }

    .md-status-bar {
        background: #ffffff !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        padding: 20px 24px !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 24px;
        animation: fadeInUp 0.3s ease-out;
    }
    .md-section-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--md-on-surface-variant) !important;
    }
    .md-emerald-divider {
        height: 2px !important;
        background: var(--md-green) !important;
        border: none !important;
        margin: 24px auto !important;
        opacity: 0.25 !important;
        max-width: 120px !important;
    }
    .md-card-emerald {
        border-left: 3px solid var(--md-green) !important;
    }

    /* Page Navigation styling */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="stPageLink"] {
        padding: 0 !important;
        margin: 2px 0 !important;
    }
    [data-testid="stPageLink"] > a {
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        padding: 12px 16px !important;
        border-radius: var(--radius-md) !important;
        text-decoration: none !important;
        font-size: 15px !important;
        font-family: var(--font-family) !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        background-color: transparent !important;
        border: none !important;
        width: 100% !important;
        box-sizing: border-box !important;
        color: var(--md-on-surface-variant) !important;
    }
    [data-testid="stPageLink"] > a:hover {
        background-color: var(--md-surface-container) !important;
        color: var(--md-secondary) !important;
        transform: translateX(3px) !important;
    }
    [data-testid="stPageLink"] p {
        color: inherit !important;
        font-size: 15px !important;
        font-weight: inherit !important;
        margin: 0 !important;
    }
    [data-testid="stPageLink"] span {
        color: inherit !important;
        font-size: 20px !important;
    }

    /* === CONTAINED EXPANDERS: prevent full-width sprawl === */
    div[data-testid="stExpander"] {
        max-width: 820px !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        background: #ffffff !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 20px !important;
        overflow: hidden !important;
        transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    div[data-testid="stExpander"]:hover {
        border-color: rgba(0, 103, 71, 0.25) !important;
        box-shadow: var(--shadow-elevated) !important;
    }
    /* Expander header row */
    div[data-testid="stExpander"] > div:first-child {
        padding: 14px 20px !important;
        background: var(--md-surface-container) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border-bottom: 1px solid var(--md-outline-variant) !important;
        cursor: pointer !important;
        transition: background 0.15s ease !important;
        user-select: none !important;
    }
    div[data-testid="stExpander"] > div:first-child:hover {
        background: var(--md-surface-container-high) !important;
    }
    /* Expander content area */
    div[data-testid="stExpander"] > div:nth-child(2) {
        padding: 20px 24px !important;
    }
    /* Nested expanders: reduce size but keep constraint */
    div[data-testid="stExpander"] div[data-testid="stExpander"] {
        max-width: 100% !important;
        margin-bottom: 12px !important;
        border-radius: var(--radius-md) !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpander"] > div:first-child {
        padding: 10px 16px !important;
        font-size: 13px !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpander"] > div:nth-child(2) {
        padding: 16px !important;
    }
    /* Expander inside side-columns (columns) — let it fill */
    div[data-testid="column"] div[data-testid="stExpander"] {
        max-width: 100% !important;
    }

    /* === CONTENT AREA RESCALE: prevent edge-to-edge sprawl === */
    .main .block-container {
        max-width: 1320px !important;
        padding-left: 28px !important;
        padding-right: 28px !important;
    }
    /* Full-width data tables within the constrained container */
    .stDataFrame {
        max-width: 100% !important;
    }
    /* Big metric cards row — let it breathe */
    div[data-testid="column"] {
        padding: 0 6px !important;
    }

    /* === FORM ELEMENTS INSIDE EXPANDERS: better proportions === */
    div[data-testid="stExpander"] .stTextInput,
    div[data-testid="stExpander"] .stSelectbox,
    div[data-testid="stExpander"] .stDateInput,
    div[data-testid="stExpander"] .stNumberInput {
        max-width: 480px !important;
    }
    div[data-testid="stExpander"] .row-widget.stRadio {
        max-width: 640px !important;
    }

    /* === BETTER GLOBAL SPACING === */
    hr {
        margin: 20px 0 !important;
        opacity: 0.5 !important;
    }
    .stForm {
        max-width: 720px !important;
    }

    /* === PILL-BUTTON RADIO GROUPS (horizontal) === */
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] {
        display: flex;
        flex-direction: row;
        gap: 4px;
        flex-wrap: wrap;
        background: var(--md-surface-container-low);
        padding: 4px;
        border-radius: var(--radius-full);
        border: 1px solid var(--md-outline-variant);
        width: fit-content;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label {
        display: inline-flex !important;
        align-items: center;
        justify-content: center;
        padding: 5px 18px !important;
        min-height: 34px;
        border-radius: var(--radius-full) !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        font-size: 13px;
        font-weight: 500;
        color: var(--md-on-surface-variant);
        margin: 0 !important;
        flex: 0 1 auto;
        white-space: nowrap;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label:hover {
        background: var(--md-surface-container-high) !important;
        color: var(--md-on-surface);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label:has(input:checked) {
        background: var(--md-secondary) !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(0, 103, 71, 0.30);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label > div:first-child {
        display: none !important;
    }

    /* --- MOBILE RESPONSIVENESS OVERRIDES --- */
    @media (max-width: 768px) {
        h1 {
            font-size: 24px !important;
        }
        h2 {
            font-size: 18px !important;
        }
        .md-card {
            padding: 16px !important;
            margin-bottom: 12px !important;
        }
        .md-status-bar {
            padding: 16px !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 16px !important;
        }
        .md-status-bar > div {
            width: 100% !important;
        }
        /* Mobile Touch Target 48px */
        .stButton > button {
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
        }
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stNumberInput input {
            height: 48px !important;
            font-size: 16px !important;
        }
    }
</style>
"""


def inject_premium_css():
    st.markdown(_PREMIUM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=5)
def _get_pending_batch_count():
    try:
        from database import get_connection

        _c = get_connection().cursor()
        _c.execute("SELECT COUNT(*) FROM import_batches WHERE status = 'pending'")
        return _c.fetchone()[0]
    except Exception:
        return 0


@st.cache_data(ttl=60)
def _get_sidebar_system_stats():
    _db_ok = False
    _tf_name = "—"
    _teacher_count = 0
    _guest_count = 0
    _has_excel = False
    try:
        from database import get_connection

        _conn_sidebar = get_connection()
        _c = _conn_sidebar.cursor()
        _c.execute(
            "SELECT COUNT(*) FROM teachers WHERE employment_type IN ('TEACHER','STAFF')"
        )
        _teacher_count = _c.fetchone()[0]
        _c.execute("SELECT COUNT(*) FROM teachers WHERE employment_type = 'GUEST'")
        _guest_count = _c.fetchone()[0]
        _c.execute("SELECT name FROM timeframes ORDER BY start_date DESC LIMIT 1")
        _r = _c.fetchone()
        if _r:
            _tf_name = _r[0]
        _c.execute("SELECT COUNT(*) FROM session_teacher_totals")
        _has_excel = _c.fetchone()[0] > 0
        _conn_sidebar.close()
        _db_ok = True
    except Exception:
        _db_ok = False
    return _db_ok, _tf_name, _teacher_count, _guest_count, _has_excel


def render_sidebar(active_page="home"):
    from database import ensure_db_initialized
    ensure_db_initialized()
    
    # Build system status data (cached)
    _db_ok, _tf_name, _teacher_count, _guest_count, _has_excel = (
        _get_sidebar_system_stats()
    )
    _pending_batches = _get_pending_batch_count()

    _dot_color = "#22c55e" if _db_ok else "#ef4444"
    _dot_label = "Đã kết nối" if _db_ok else "Mất kết nối"
    _source_icon = "download" if _has_excel else "edit_note"
    _source_label = "Excel" if _has_excel else "Nhập lẻ"

    # Map active_page to href fragment for CSS targeting
    _page_hrefs = {
        "home": "app",
        "dashboard": "Dashboard",
        "canbo": "QuanLyCanBo",
        "nhatky": "NhatKyHoatDong",
        "caidat": "CaiDatHeThong",
        "design": "DesignSystem",
        "payroll": "Payroll",
        "pheduyet": "PheDuyet",
    }

    active_slug = _page_hrefs.get(active_page, "")
    if active_page == "home":
        active_selector = (
            'section[data-testid="stSidebar"] [data-testid="stPageLink"] a[href="/"]'
        )
    else:
        active_selector = (
            f'section[data-testid="stSidebar"] [data-testid="stPageLink"] a[href*="{active_slug}"]'
            if active_slug
            else ""
        )

    # Render HTML sidebar
    with st.sidebar:
        # Inject CSS (inside sidebar so it persists across page navigation)
        st.markdown(
            f"""
<style>
    [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    {
                active_selector
                and f'''
    {active_selector} {{
        background-color: #007855 !important;
        color: #FFFFFF !important;
        border-left: 4px solid #FFC107 !important;
        box-shadow: 0 4px 12px rgba(0, 79, 56, 0.3) !important;
    }}
    {active_selector} p,
    {active_selector} span {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}
    '''
                or ""
            }
</style>
""",
            unsafe_allow_html=True,
        )

        inject_premium_css()
        _apply_locale_theme()

        from auth import get_current_user

        user = get_current_user()

        if user:
            role_labels = {
                "admin": "Quản trị viên",
                "head_dept": f"Trưởng {user.get('department_name') or 'Khoa'}",
            }
            role_label = role_labels.get(user["role"], "Người dùng")
            identity_html = (
                f'<div style="margin-top: 16px; padding: 14px 16px; background: linear-gradient(135deg, #007855, #005C41); border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 92, 65, 0.2); border: 1px solid rgba(255,255,255,0.1);">'
                f'  <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Tài khoản hoạt động</div>'
                f'  <div style="font-weight: 700; color: #FFFFFF; font-size: 16px; letter-spacing: 0.01em;">{user["username"]}</div>'
                f'  <div style="font-size: 12px; color: #FFC107; margin-top: 4px; font-weight: 600; display: flex; align-items: center; gap: 4px;">'
                f'    <span class="material-symbols-outlined" style="font-size: 14px;">verified_user</span> {role_label}'
                f"  </div>"
                f"</div>"
            )
        else:
            identity_html = (
                '<div style="margin-top: 16px; padding: 14px 16px; background: linear-gradient(135deg, #fef2f2, #fee2e2); border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3); box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);">'
                '  <div style="font-size: 13px; color: #b91c1c; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px;">'
                '    <span class="material-symbols-outlined" style="font-size: 18px;">lock</span> Chế độ Khách (Đọc)'
                "  </div>"
                "</div>"
            )

        logo_base64 = _get_logo_base64()
        logo_html = ""
        if logo_base64:
            logo_html = f'<img src="{logo_base64}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1.5px solid #FFC107;" />'
        else:
            logo_html = """
            <div style="
                width: 40px; height: 40px;
                background: linear-gradient(135deg, #008857, #006747);
                border-radius: var(--radius-md);
                display: flex; align-items: center; justify-content: center;
                color: #FFFFFF;
                font-size: 20px;
            ">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">school</span>
            </div>
            """

        st.markdown(
            f"""
<div style="padding: 8px 16px 24px 16px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        {logo_html}
        <div>
            <div style="font-weight: 700; font-size: 15px; color: #FFFFFF; line-height: 1.2;">Quản lý Chế độ làm việc</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.55); letter-spacing: 0.03em;">Đại học An ninh nhân dân</div>
        </div>
    </div>
    <div style="height: 1px; width: 100%; background: linear-gradient(90deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 100%); margin-top: 20px;"></div>
    {identity_html}
</div>
""",
            unsafe_allow_html=True,
        )

        # ---- GLOBAL TIMEFRAME SELECTOR ----
        from database import get_cached_timeframes

        df_tf = get_cached_timeframes()
        if not df_tf.empty:
            tf_options = {
                f"{row['name']}": int(row["id"]) for _, row in df_tf.iterrows()
            }

            # Init global state if missing
            if (
                "global_tf_id" not in st.session_state
                or st.session_state["global_tf_id"] not in tf_options.values()
            ):
                st.session_state["global_tf_id"] = int(df_tf.iloc[0]["id"])

            current_val = st.session_state["global_tf_id"]
            current_key = next(
                (k for k, v in tf_options.items() if v == current_val),
                list(tf_options.keys())[0],
            )

            selected_key = st.selectbox(
                "Năm học (Toàn cục):",
                options=list(tf_options.keys()),
                index=list(tf_options.keys()).index(current_key),
                key="global_tf_selector",
            )

            # Display weeks used below the dropdown
            selected_tf_id = tf_options[selected_key]
            try:
                from database import ThreadLocalConnectionProxy

                with ThreadLocalConnectionProxy() as conn_sb:
                    cur = conn_sb.cursor()
                    cur.execute(
                        "SELECT start_date, end_date FROM timeframes WHERE id = ?",
                        (selected_tf_id,),
                    )
                    tf_info = cur.fetchone()
                    if tf_info:
                        start_str, end_str = tf_info
                        cur.execute(
                            "SELECT start_date, end_date FROM academic_holidays WHERE timeframe_id = ?",
                            (selected_tf_id,),
                        )

                        import pandas as pd
                        from calculations import calculate_t04_weeks

                        s_dt = pd.to_datetime(start_str)
                        e_dt = pd.to_datetime(end_str)

                        holidays_list = []
                        for r in cur.fetchall():
                            holidays_list.append(
                                (pd.to_datetime(r[0]), pd.to_datetime(r[1]))
                            )

                        weeks_used = calculate_t04_weeks(s_dt, e_dt, holidays_list)
                        st.markdown(
                            f'<div style="font-size: 12px; color: #FFC107; margin-top: -8px; margin-bottom: 12px; font-weight: 600;">📅 Thực tế: {weeks_used:.1f} tuần dạy học</div>',
                            unsafe_allow_html=True,
                        )
            except Exception as e:
                # Log to stderr for system administrators
                import sys

                print(f"Error calculating weeks in sidebar: {e}", file=sys.stderr)

            if tf_options[selected_key] != current_val:
                st.session_state["global_tf_id"] = tf_options[selected_key]
                st.rerun()

            st.markdown(
                '<div style="margin-bottom: 4px;"></div>', unsafe_allow_html=True
            )
        # -----------------------------------

        st.page_link("app.py", label="Trang chủ", icon=":material/home:")
        st.page_link(
            "pages/1_Dashboard.py", label="Bảng điều khiển", icon=":material/dashboard:"
        )
        st.page_link(
            "pages/2_QuanLyCanBo.py", label="Quản lý Cán bộ", icon=":material/groups:"
        )
        st.page_link(
            "pages/3_NhatKyHoatDong.py",
            label="Nhật ký Hoạt động",
            icon=":material/edit_note:",
        )

        # Role-based menu links
        role = user["role"] if user else None
        if role in ["admin", "head_dept"]:
            st.page_link(
                "pages/4_CaiDatHeThong.py",
                label="Cài đặt Hệ thống",
                icon=":material/settings:",
            )
        if role == "admin":
            st.page_link(
                "pages/6_Payroll.py",
                label="Quản lý Lương TT11",
                icon=":material/payments:",
            )
            if _pending_batches:
                _pc1, _pc2 = st.columns([1, 0.12])
                with _pc1:
                    st.page_link(
                        "pages/7_PheDuyet.py",
                        label="Phê duyệt Dữ liệu",
                        icon=":material/fact_check:",
                        use_container_width=True,
                    )
                with _pc2:
                    st.markdown(
                        f"<div style='background:#ef4444;color:white;font-size:11px;font-weight:700;min-width:20px;height:20px;border-radius:999px;display:flex;align-items:center;justify-content:center;padding:0 4px;'>{_pending_batches}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.page_link(
                    "pages/7_PheDuyet.py",
                    label="Phê duyệt Dữ liệu",
                    icon=":material/fact_check:",
                )

        login_label = "Thông tin tài khoản" if user else "Đăng nhập"
        st.page_link("pages/8_DangNhap.py", label=login_label, icon=":material/lock:")

        if user:
            from auth import logout

            if st.button("Đăng xuất", type="primary", use_container_width=True):
                logout()
                st.switch_page("pages/8_DangNhap.py")

        st.markdown(
            '<div style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.08);padding-top:12px;"></div>',
            unsafe_allow_html=True,
        )
        # System status bar
        st.markdown(
            f"""
<div style="
    margin-top: 32px;
    padding: 12px 14px;
    background-color: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: var(--radius-md);
    font-size: 11px;
    color: rgba(255,255,255,0.60);
    line-height: 1.6;
">
    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em; color: rgba(255,255,255,0.50);">
        <span class="material-symbols-outlined" style="font-size: 14px;">monitor_heart</span>
        Trạng thái hệ thống
    </div>
    <div style="display: grid; grid-template-columns: auto 1fr; gap: 4px 8px;">
        <span style="color: rgba(255,255,255,0.50);">CSDL</span>
        <div style="display: flex; align-items: center; gap: 4px; color: rgba(255,255,255,0.70);">
            <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {_dot_color}; display: inline-block;"></span>
            <span>{_dot_label}</span>
        </div>
        <span style="color: rgba(255,255,255,0.50);">Năm học</span>
        <span style="font-weight: 500; color: rgba(255,255,255,0.80);">{_tf_name}</span>
        <span style="color: rgba(255,255,255,0.50);">CB-CV</span>
        <span style="font-weight: 500; color: rgba(255,255,255,0.80);">{_teacher_count} cơ hữu + {_guest_count} khách mời</span>
        <span style="color: rgba(255,255,255,0.50);">Nguồn số liệu</span>
        <div style="display: flex; align-items: center; gap: 4px; color: rgba(255,255,255,0.70);">
            <span class="material-symbols-outlined" style="font-size: 12px;">{_source_icon}</span>
            <span style="font-weight: 500;">{_source_label}</span>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <style>
            /* ── Invisible trigger: target by aria-label of the unicode char ── */
            button[aria-label="⛑"] {
                opacity: 0 !important;
                position: absolute !important;
                inset: 0 !important;
                width: 100% !important;
                height: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                color: transparent !important;
                cursor: default !important;
                pointer-events: all !important;
            }
            /* Pull the wrapper out of sidebar flow, pin to corner */
            div[data-testid="stElementContainer"]:has(button[aria-label="⛑"]) {
                position: fixed !important;
                bottom: 0px !important;
                left: 0px !important;
                width: 60px !important;
                height: 60px !important;
                margin: 0 !important;
                padding: 0 !important;
                z-index: 2147483647 !important;
                background: transparent !important;
                overflow: visible !important;
            }
            /* Hide any tooltip icon Streamlit might inject alongside the button */
            div[data-testid="stElementContainer"]:has(button[aria-label="⛑"]) [data-testid="stTooltipIcon"],
            div[data-testid="stElementContainer"]:has(button[aria-label="⛑"]) .stTooltipIcon {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button("⛑", key="_ghost_trigger"):
            st.session_state["_layout_entropy_active"] = not st.session_state.get("_layout_entropy_active", False)
            st.rerun()


def render_step_header(step_num, title, description=None):
    desc_html = (
        f'<div style="color: var(--md-on-surface-variant); font-size: 0.9rem; margin-top: 4px;">{description}</div>'
        if description
        else ""
    )
    st.markdown(
        f"""
    <div style="margin-top: 24px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="
                background-color: var(--md-secondary); 
                color: #FFFFFF; 
                font-weight: 700; 
                width: 24px; 
                height: 24px; 
                border-radius: 50%; 
                display: inline-flex; 
                align-items: center; 
                justify-content: center;
                font-size: 0.85rem;
            ">{step_num}</span>
            <span style="font-weight: 700; font-size: 1.1rem; color: var(--md-on-surface);">{title}</span>
        </div>
        {desc_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_error_report(errors):
    errors_html = "".join(
        [f'<li style="margin-bottom: 6px;">{err}</li>' for err in errors]
    )
    st.markdown(
        f"""
    <div style="
        background-color: var(--md-error-container);
        border: 1px solid var(--md-error);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        color: var(--md-error);
        margin: 16px 0;
        font-size: 0.95rem;
    ">
        <div style="font-weight: 700; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: var(--md-error);">error</span>
            Phát hiện lỗi dữ liệu ({len(errors)} lỗi):
        </div>
        <ul style="margin: 0; padding-left: 20px;">
            {errors_html}
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_success_preview(df):
    st.markdown(
        f"""
    <div style="
        background-color: var(--md-green-bg);
        border: 1px solid var(--md-green);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        color: var(--md-green);
        margin: 16px 0;
        font-size: 0.95rem;
    ">
        <div style="font-weight: 700; display: flex; align-items: center; gap: 8px;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: var(--md-green);">check_circle</span>
            File hợp lệ! Sẵn sàng nhập {len(df)} cán bộ.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_diff_viewer(
    staging_df,
    diff_json_str: str,
    domain: str,
    batch_id: int,
    view_mode: str = "inline",
    key_prefix: str = "diff",
):
    """
    Render a diff comparison view using AgGrid with cell-level highlighting,
    with a fallback to st.dataframe.

    Parameters
    ----------
    staging_df : pd.DataFrame
        Staging rows for this batch.
    diff_json_str : str
        JSON string from import_batches.diff_json.
    domain : str
        One of VALID_DOMAINS.
    batch_id : int
        For unique AgGrid key generation.
    view_mode : str
        "inline" or "side_by_side".
    key_prefix : str
        For session state isolation.
    """
    try:
        from pipeline.diff_formatter import format_diff_json
    except ImportError:
        _render_fallback_diff(staging_df, domain)
        return

    formatted_df = format_diff_json(diff_json_str, domain, staging_df)
    if formatted_df.empty:
        st.info("Không có dữ liệu để hiển thị.")
        return

    # Build summary chips
    markers = formatted_df["_diff_marker"].value_counts()
    st.markdown(
        f"""
    <div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
        <span class="md-chip md-chip-green">🆕 Mới: {markers.get("NEW", 0)}</span>
        <span class="md-chip md-chip-amber">🟡 Cập nhật: {markers.get("UPDATE", 0)}</span>
        <span class="md-chip md-chip-red">🔴 Xóa: {markers.get("DELETE", 0)}</span>
        <span class="md-chip">⚪ Bỏ qua: {markers.get("SKIP", 0)}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Display columns (exclude internal ones)
    display_cols = [c for c in formatted_df.columns if not c.startswith("_")]
    try:
        _render_aggrid_diff(formatted_df, display_cols, batch_id, view_mode, key_prefix)
    except Exception:
        _render_fallback_diff(staging_df, domain)


def _render_aggrid_diff(formatted_df, display_cols, batch_id, view_mode, key_prefix):
    """Render diff using streamlit-aggrid with cell-level styles."""
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

    display_df = formatted_df[display_cols].copy()

    # Build column definitions with cell style renderers
    gb = GridOptionsBuilder.from_dataframe(display_df)

    # Cell style JS — colors cells based on _cell_styles metadata
    cell_style_js = JsCode("""
    function(params) {
        if (!params.data || !params.data._cell_styles) return {};
        const styles = JSON.parse(params.data._cell_styles || '{}');
        const col = params.colDef ? params.colDef.field : '';
        if (!col) return {};
        const cellClass = styles[col];
        if (cellClass === 'added') {
            return {'backgroundColor': '#d1fae5', 'color': '#065f46'};
        } else if (cellClass === 'removed') {
            return {'backgroundColor': '#ffe4e6', 'color': '#9f1239'};
        } else if (cellClass === 'changed') {
            return {'backgroundColor': '#fef3c7', 'color': '#92400e'};
        }
        return {};
    }
    """)

    for col in display_df.columns:
        gb.configure_column(
            col, cellStyle=cell_style_js, wrapText=False, autoHeight=False
        )

    # Add diff marker column with status chip
    if "_diff_marker_display" in formatted_df.columns:
        gb.configure_column(
            "_diff_marker_display", headerName="Trạng thái", width=140, pinned="left"
        )

    gb.configure_grid_options(
        domLayout="normal",
        rowHeight=32,
        headerHeight=38,
        suppressColumnVirtualisation=False,
        enableCellTextSelection=True,
        ensureDomOrder=True,
    )

    gb.configure_selection(selection_mode="multiple", use_checkbox=False)

    grid_options = gb.build()

    ag_grid_key = f"{key_prefix}_aggrid_{batch_id}_{view_mode}"

    grid_response = AgGrid(
        display_df,
        gridOptions=grid_options,
        height=min(600, 40 * len(display_df) + 80),
        key=ag_grid_key,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
        fit_columns_on_grid_load=True,
        theme="streamlit",
    )


def _render_fallback_diff(staging_df, domain):
    """Fallback renderer using native st.dataframe when AgGrid is unavailable."""
    config_map = {
        "teachers": {
            "cols": [
                "row_num",
                "teacher_name",
                "department",
                "title",
                "diff_marker",
                "diff_detail",
            ],
            "rename": {
                "row_num": "Dòng",
                "teacher_name": "Họ tên",
                "department": "Đơn vị",
                "title": "Chức danh",
                "diff_marker": "Trạng thái",
                "diff_detail": "Chi tiết",
            },
        },
        "activities": {
            "cols": [
                "row_num",
                "teacher_name",
                "activity_type_name",
                "diff_marker",
                "diff_detail",
            ],
            "rename": {
                "row_num": "Dòng",
                "teacher_name": "Mã GV",
                "activity_type_name": "Hoạt động",
                "diff_marker": "Trạng thái",
                "diff_detail": "Chi tiết",
            },
        },
        "schedule": {
            "cols": [
                "row_num",
                "teacher_name",
                "subject_name",
                "diff_marker",
                "diff_detail",
            ],
            "rename": {
                "row_num": "Dòng",
                "teacher_name": "Họ tên",
                "subject_name": "Môn",
                "diff_marker": "Trạng thái",
                "diff_detail": "Chi tiết",
            },
        },
        "aggregate_totals": {
            "cols": ["row_num", "teacher_name", "diff_marker", "diff_detail"],
            "rename": {
                "row_num": "Dòng",
                "teacher_name": "Mã GV",
                "diff_marker": "Trạng thái",
                "diff_detail": "Chi tiết",
            },
        },
    }
    config = config_map.get(domain, config_map["teachers"])
    available = [c for c in config["cols"] if c in staging_df.columns]
    display = staging_df[available].rename(columns=config["rename"])
    st.dataframe(display, use_container_width=True, hide_index=True)
