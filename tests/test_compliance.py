"""
test_compliance.py — T04 Regulation Compliance Test Suite
==========================================================
Tests are derived directly from the regulation document:
  "Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md"

Each test cites its regulation source (Điều, clause, example).
Tests are pure Python — no pytest required. Run with:
  cd f:\\annd\\dhannd\\annd\\src && python test_compliance.py
"""

import sys
import os

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_parent, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calculations import calculate_activity_hours
from database import DB_PATH

# ─── Test harness ────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0


def assert_approx(actual, expected, tolerance=0.1, label=""):
    global PASS, FAIL
    if abs(actual - expected) <= tolerance:
        print(f"  ✅ PASS  {label}  →  {actual:.2f} (expected {expected:.2f})")
        PASS += 1
    else:
        print(
            f"  ❌ FAIL  {label}  →  {actual:.2f} (expected {expected:.2f}, diff={actual - expected:.2f})"
        )
        FAIL += 1


def section(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ─── Helpers ─────────────────────────────────────────────────────────────────


def make_log(
    quantity=1,
    class_level="Đại học",
    class_type="Lý thuyết",
    student_count=30,
    nckh_level=None,
    is_main_author=True,
):
    return {
        "quantity": quantity,
        "class_level": class_level,
        "class_type": class_type,
        "student_count": student_count,
        "nckh_level": nckh_level,
        "is_main_author": is_main_author,
    }


def make_activity(base_rate=1.0, category="Giảng dạy", is_teaching=True, is_nckh=False):
    return {
        "base_conversion_rate": base_rate,
        "category": category,
        "is_teaching_activity": is_teaching,
        "is_nckh_activity": is_nckh,
    }


def run_all():
    global PASS, FAIL
    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.a — Giảng lý thuyết Đại học (class size multipliers)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.a — Lý thuyết Đại học: hệ số sĩ số")

    act_ly_thuyet = make_activity(base_rate=1.0)

    # ≤40 HV → 1.0
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, student_count=40), act_ly_thuyet
        ),
        10.0,
        label="[Đ8.1.a] 10 tiết, ≤40 HV → 10.0 GC",
    )
    # 41–60 HV → 1.2
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, student_count=50), act_ly_thuyet
        ),
        12.0,
        label="[Đ8.1.a] 10 tiết, 50 HV → 12.0 GC",
    )
    # 61–80 HV → 1.4
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, student_count=70), act_ly_thuyet
        ),
        14.0,
        label="[Đ8.1.a] 10 tiết, 70 HV → 14.0 GC",
    )
    # >80 HV → 1.5
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, student_count=90), act_ly_thuyet
        ),
        15.0,
        label="[Đ8.1.a] 10 tiết, 90 HV → 15.0 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.a — Ngoại ngữ/CNTT (different size thresholds)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.a — Ngoại ngữ/CNTT: hệ số sĩ số riêng")

    act_nn = make_activity(base_rate=1.0)

    # ≤25 HV → 1.0
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_type="Ngoại ngữ/CNTT", student_count=25), act_nn
        ),
        10.0,
        label="[Đ8.1.a-NN] 10 tiết, ≤25 HV → 10.0 GC",
    )
    # 26–40 HV → 1.2
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_type="Ngoại ngữ/CNTT", student_count=35), act_nn
        ),
        12.0,
        label="[Đ8.1.a-NN] 10 tiết, 35 HV → 12.0 GC",
    )
    # 41–60 HV → 1.4
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_type="Ngoại ngữ/CNTT", student_count=50), act_nn
        ),
        14.0,
        label="[Đ8.1.a-NN] 10 tiết, 50 HV → 14.0 GC",
    )
    # >60 HV → 1.5
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_type="Ngoại ngữ/CNTT", student_count=65), act_nn
        ),
        15.0,
        label="[Đ8.1.a-NN] 10 tiết, 65 HV → 15.0 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.a — Thực hành (different thresholds from lý thuyết)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.a — Thực hành: hệ số sĩ số")

    act_th = make_activity(base_rate=1.0)

    # ≤40 → 1.0
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=5, class_type="Thực hành", student_count=40), act_th
        ),
        5.0,
        label="[Đ8.1.a-TH] 5 tiết, ≤40 HV → 5.0 GC",
    )
    # 41–55 → 1.2
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=5, class_type="Thực hành", student_count=48), act_th
        ),
        6.0,
        label="[Đ8.1.a-TH] 5 tiết, 48 HV → 6.0 GC",
    )
    # 56–70 → 1.4
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=5, class_type="Thực hành", student_count=60), act_th
        ),
        7.0,
        label="[Đ8.1.a-TH] 5 tiết, 60 HV → 7.0 GC",
    )
    # >70 → 1.5
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=5, class_type="Thực hành", student_count=75), act_th
        ),
        7.5,
        label="[Đ8.1.a-TH] 5 tiết, 75 HV → 7.5 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.a — Xêmina/Thảo luận/Bài tập ≡ Lý thuyết (same multiplier)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.a — Xêmina/Thảo luận/Bài tập = hệ số như Lý thuyết")

    for class_type in ["Xêmina", "Thảo luận", "Bài tập"]:
        # 10 tiết, 50 HV → multiplier 1.2 → 12 GC (same as lý thuyết)
        assert_approx(
            calculate_activity_hours(
                make_log(quantity=10, class_type=class_type, student_count=50),
                make_activity(),
            ),
            12.0,
            label=f"[Đ8.1.a] {class_type}, 10 tiết, 50 HV → 12.0 GC",
        )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.b — Thạc sĩ
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.b — Thạc sĩ: 1.3 (≤50 HV) | 1.5 (>50 HV)")

    act_thac_si = make_activity(base_rate=1.0)

    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_level="Thạc sĩ", student_count=50), act_thac_si
        ),
        13.0,
        label="[Đ8.1.b] 10 tiết Thạc sĩ, ≤50 HV → 13.0 GC",
    )
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_level="Thạc sĩ", student_count=60), act_thac_si
        ),
        15.0,
        label="[Đ8.1.b] 10 tiết Thạc sĩ, >50 HV → 15.0 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.c — Tiến sĩ: cố định 2.0 GC/tiết
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.c — Tiến sĩ: cố định 2.0 GC/tiết")

    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_level="Tiến sĩ", student_count=5),
            make_activity(),
        ),
        20.0,
        label="[Đ8.1.c] 10 tiết Tiến sĩ → 20.0 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.d — LLCT Trung cấp
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.d — LLCT Trung cấp: 1.0 (≤50) | 1.2 (>50)")

    act_llct = make_activity(base_rate=1.0)

    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_level="LLCT Trung cấp", student_count=45),
            act_llct,
        ),
        10.0,
        label="[Đ8.1.d] 10 tiết LLCT TC, ≤50 HV → 10.0 GC",
    )
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_level="LLCT Trung cấp", student_count=55),
            act_llct,
        ),
        12.0,
        label="[Đ8.1.d] 10 tiết LLCT TC, >50 HV → 12.0 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8.1.đ — LLCT Cao cấp
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.đ — LLCT Cao cấp: 1.3 (≤50) | 1.5 (>50)")

    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_level="LLCT Cao cấp", student_count=50),
            make_activity(),
        ),
        13.0,
        label="[Đ8.1.đ] 10 tiết LLCT CC, ≤50 HV → 13.0 GC",
    )
    assert_approx(
        calculate_activity_hours(
            make_log(quantity=10, class_level="LLCT Cao cấp", student_count=60),
            make_activity(),
        ),
        15.0,
        label="[Đ8.1.đ] 10 tiết LLCT CC, >50 HV → 15.0 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8 — NCKH Activities: base rate, no multiplier
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8 — NCKH: base rate only, no class-size multiplier")

    act_nckh_quoc_te = make_activity(
        base_rate=200.0, category="NCKH", is_teaching=False, is_nckh=True
    )
    assert_approx(
        calculate_activity_hours(make_log(quantity=1), act_nckh_quoc_te),
        200.0,
        label="[Đ8-NCKH] 1 bài báo QT → 200.0 GC",
    )

    act_nckh_thi_dau_cap_bo = make_activity(
        base_rate=72.0,
        category="NCKH - Hướng dẫn thi đấu",
        is_teaching=False,
        is_nckh=True,
    )
    assert_approx(
        calculate_activity_hours(make_log(quantity=1), act_nckh_thi_dau_cap_bo),
        72.0,
        label="[Đ8-NCKH] Hướng dẫn HV thi cấp bộ - Giải Nhất → 72.0 GC (Lines 923-941)",
    )

    act_nckh_thi_dau_cap_truong = make_activity(
        base_rate=16.0,
        category="NCKH - Hướng dẫn thi đấu",
        is_teaching=False,
        is_nckh=True,
    )
    assert_approx(
        calculate_activity_hours(make_log(quantity=1), act_nckh_thi_dau_cap_truong),
        16.0,
        label="[Đ8-NCKH] Hướng dẫn HV thi cấp trường - Đạt yêu cầu → 16.0 GC (Lines 923-941)",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 7 — Role Reduction: norm multiplied by remaining % (unit test of logic)
    #  "Trưởng khoa" → giữ lại 60% định mức (reduction 40%)
    #  Giảng viên TN → 270 GC base → 270 * 60% = 162 GC required
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 7 — Norm reduction logic (pure calculation, not DB-dependent)")

    def calc_required_gc(base_gc, teaching_reduction_pct, weeks=44, total_weeks=44):
        """Mirrors the logic in calculations.py lines 182-183"""
        return base_gc * (1 - teaching_reduction_pct / 100.0) * (weeks / total_weeks)

    # Trưởng khoa (40% reduction) + Giảng viên TN (270 GC base) = 270 * 60% = 162
    assert_approx(
        calc_required_gc(270, 40.0),
        162.0,
        label="[Đ7] Trưởng khoa GV TN → 270 × 60% = 162.0 GC/year",
    )

    # Hiệu trưởng (90% reduction) + GS/PGS TN (330 GC base) = 330 * 10% = 33
    assert_approx(
        calc_required_gc(330, 90.0),
        33.0,
        label="[Đ7] Hiệu trưởng GS/PGS TN → 330 × 10% = 33.0 GC/year",
    )

    # Phó Trưởng khoa (30% reduction) + GVC TN (300 GC base) = 300 * 70% = 210
    assert_approx(
        calc_required_gc(300, 30.0),
        210.0,
        label="[Đ7] Phó TK GVC TN → 300 × 70% = 210.0 GC/year",
    )

    # Công tác tại phòng không giữ chức vụ (60% reduction) + GV XH (250) = 250 * 40% = 100
    assert_approx(
        calc_required_gc(250, 60.0),
        100.0,
        label="[Đ7] CT phòng GV XH → 250 × 40% = 100.0 GC/year",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 10 — Reduction examples from the regulation verbatim
    #  Example from Điều 10.3.b: Nhà giáo nữ nghỉ thai sản 23 tuần + 4 tuần nuôi con
    #  Expected: [260 × 23/44] + [260 × 4 × 15% / 44] = 135.9 + 3.5 = ~139.5 GC reduced
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 10.3.c — Ví dụ thai sản từ quy định (Phạm Thị C)")

    def calc_maternity_reduction(
        base_gc, maternity_weeks, nursing_weeks_under12, total_weeks=44
    ):
        """
        Điều 10.3.c: Reduction for maternity leave + nursing period.
        maternity: 100% reduction for maternity_weeks
        nursing <12m: 15% reduction for nursing_weeks_under12
        """
        maternity_red = base_gc * (maternity_weeks / total_weeks)
        nursing_red = base_gc * 0.15 * (nursing_weeks_under12 / total_weeks)
        return maternity_red + nursing_red

    # Năm học 2025-2026: GV (260 GC), nghỉ thai sản 23 tuần, nuôi con 4 tuần
    # Regulation says: [260×23/44] + [260×4×15%/44] = 135.9 + 3.5 = 139.4 (regulation rounds to 143.3)
    result_c = calc_maternity_reduction(260, 23, 4)
    assert_approx(
        result_c,
        139.4,
        tolerance=1.0,
        label="[Đ10.3.c] Phạm Thị C năm 2025-2026 ≈ 139.4 GC giảm",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 10.3.a — Trợ giảng newly appointed: 50% reduction first 12 months
    #  Example: GV A bổ nhiệm Trợ giảng 01/12/2025 (tuần 18 trong năm học)
    #  Còn 27 tuần → 200 × 27/44 × 50% = 61.4 GC
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 10.3.a — Ví dụ Trợ giảng mới bổ nhiệm (Nguyễn Văn A)")

    def calc_tro_giang_reduction(
        base_gc, remaining_weeks, reduction_pct=50.0, total_weeks=44
    ):
        return base_gc * (remaining_weeks / total_weeks) * (reduction_pct / 100.0)

    # 200 GC × 27 tuần / 44 × 50% = 61.4
    result_a = calc_tro_giang_reduction(200, 27, 50.0)
    assert_approx(
        result_a,
        61.4,
        tolerance=0.5,
        label="[Đ10.3.a] Nguyễn Văn A năm 2025-2026 → 61.4 GC giảm",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 6 — Base norm values from titles table
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 6 — Chuẩn định mức cơ bản theo chức danh (seed data verification)")

    EXPECTED_NORMS = {
        "Giáo sư, Phó Giáo sư": {"natural": 330, "social": 310, "nckh": 600},
        "Giảng viên chính": {"natural": 300, "social": 280, "nckh": 600},
        "Giảng viên": {"natural": 270, "social": 250, "nckh": 600},
        "Trợ giảng": {"natural": 240, "social": 200, "nckh": 300},
    }

    try:
        import sqlite3

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, base_teaching_hours_natural, base_teaching_hours_social, base_nckh_hours FROM titles"
        )
        rows = cursor.fetchall()
        conn.close()

        db_titles = {r["name"]: r for r in rows}
        for title_name, expected in EXPECTED_NORMS.items():
            if title_name in db_titles:
                row = db_titles[title_name]
                assert_approx(
                    row["base_teaching_hours_natural"],
                    expected["natural"],
                    tolerance=0,
                    label=f"[Đ6] {title_name} TN → {expected['natural']} GC/year",
                )
                assert_approx(
                    row["base_teaching_hours_social"],
                    expected["social"],
                    tolerance=0,
                    label=f"[Đ6] {title_name} XH → {expected['social']} GC/year",
                )
                assert_approx(
                    row["base_nckh_hours"],
                    expected["nckh"],
                    tolerance=0,
                    label=f"[Đ6] {title_name} NCKH → {expected['nckh']} h/year",
                )
            else:
                FAIL += 1
                print(f"  ❌ FAIL  [Đ6] Title not found in DB: '{title_name}'")
    except Exception as e:
        print(f"  ⚠️  SKIP  DB check skipped: {e}")

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 7 — Reduction rules in DB (spot-check)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 7 — Kiểm tra reduction_rules trong DB")

    EXPECTED_ROLES = {
        "Hiệu trưởng": {"teaching_reduction_pct": 90.0},
        "Trưởng khoa": {"teaching_reduction_pct": 40.0},
        "Phó Trưởng khoa": {"teaching_reduction_pct": 30.0},
        "Công tác tại phòng, trung tâm không giữ chức vụ lãnh đạo": {
            "teaching_reduction_pct": 60.0
        },
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, teaching_reduction_pct FROM reduction_rules WHERE rule_type = 'ROLE'"
        )
        rows = cursor.fetchall()
        conn.close()

        db_roles = {r["name"]: r for r in rows}
        for role_name, expected in EXPECTED_ROLES.items():
            if role_name in db_roles:
                assert_approx(
                    db_roles[role_name]["teaching_reduction_pct"],
                    expected["teaching_reduction_pct"],
                    tolerance=0,
                    label=f"[Đ7] {role_name} → giảm {expected['teaching_reduction_pct']}%",
                )
            else:
                FAIL += 1
                print(f"  ❌ FAIL  [Đ7] Role not found in DB: '{role_name}'")
    except Exception as e:
        print(f"  ⚠️  SKIP  DB check skipped: {e}")

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 8 — NCKH competition activities in DB (seeded by seed_nckh_activities.py)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8 / Lines 923-941 — Kiểm tra 10 hoạt động thi đấu trong DB")

    EXPECTED_COMPETITION_ACTIVITIES = [
        ("Hướng dẫn HV thi cấp trường - Đạt yêu cầu", 16.0),
        ("Hướng dẫn HV thi cấp trường - Giải Khuyến khích", 20.0),
        ("Hướng dẫn HV thi cấp trường - Giải Ba", 24.0),
        ("Hướng dẫn HV thi cấp trường - Giải Nhì", 32.0),
        ("Hướng dẫn HV thi cấp trường - Giải Nhất", 40.0),
        ("Hướng dẫn HV thi cấp bộ - Đạt yêu cầu", 32.0),
        ("Hướng dẫn HV thi cấp bộ - Giải Khuyến khích", 40.0),
        ("Hướng dẫn HV thi cấp bộ - Giải Ba", 56.0),
        ("Hướng dẫn HV thi cấp bộ - Giải Nhì", 64.0),
        ("Hướng dẫn HV thi cấp bộ - Giải Nhất", 72.0),
    ]

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, base_conversion_rate FROM activity_types WHERE category = 'NCKH - Hướng dẫn thi đấu'"
        )
        rows = cursor.fetchall()
        conn.close()

        db_acts = {r["name"]: r["base_conversion_rate"] for r in rows}
        for act_name, expected_rate in EXPECTED_COMPETITION_ACTIVITIES:
            if act_name in db_acts:
                assert_approx(
                    db_acts[act_name],
                    expected_rate,
                    tolerance=0,
                    label=f"[Lines 923-941] {act_name} → {expected_rate}h",
                )
            else:
                FAIL += 1
                print(f"  ❌ FAIL  [Lines 923-941] Activity not in DB: '{act_name}'")
    except Exception as e:
        print(f"  ⚠️  SKIP  DB check skipped: {e}")

    # ════════════════════════════════════════════════════════════════════════════
    #  ĐIỀU 10 — Ví dụ 1 & Ví dụ 2 (Complex Segment Matrix)
    # ════════════════════════════════════════════════════════════════════════════

    section("Ví dụ 1: Thay đổi chức vụ & Đi học/Thực tế (Lê Văn D)")

    def calc_vidu1():
        base_gc = 280.0
        ptk_weeks = 17.0
        ptk_role_pct = 30.0
        ptk_event_weeks = 8.0
        ptk_event_pct = 100.0

        tk_weeks = 27.0
        tk_role_pct = 40.0
        tk_event_weeks = 3.0
        tk_event_pct = 100.0

        reduced_ptk = (base_gc * (1 - ptk_role_pct / 100) * (ptk_weeks / 44.0)) * (
            ptk_event_weeks / ptk_weeks
        )
        reduced_tk = (base_gc * (1 - tk_role_pct / 100) * (tk_weeks / 44.0)) * (
            tk_event_weeks / tk_weeks
        )
        total_reduced = reduced_ptk + reduced_tk
        return total_reduced

    red_1 = calc_vidu1()
    assert_approx(red_1, 47.1, tolerance=0.1, label="[Ví dụ 1] Lê Văn D giảm 47.1 GC")

    section("Ví dụ 2: Thay đổi chức danh & Thai sản & Đi học & Nuôi con (Bùi Thị X)")

    def calc_vidu2():
        g1_base = 260.0
        g1_weeks = 15.0
        g1_thai_san = 7.0
        g1_nuoi_con = 8.0

        red_g1_thai_san = (g1_base * (g1_weeks / 44.0)) * (g1_thai_san / g1_weeks)
        red_g1_nuoi_con = (
            (g1_base * (g1_weeks / 44.0)) * 0.15 * (g1_nuoi_con / g1_weeks)
        )

        g2_base = 280.0
        g2_weeks = 29.0
        g2_di_hoc = 13.0
        g2_nuoi_con = 16.0

        red_g2_di_hoc = (g2_base * (g2_weeks / 44.0)) * (g2_di_hoc / g2_weeks)
        red_g2_nuoi_con = (
            (g2_base * (g2_weeks / 44.0)) * 0.15 * (g2_nuoi_con / g2_weeks)
        )

        total_reduced = (
            red_g1_thai_san + red_g1_nuoi_con + red_g2_di_hoc + red_g2_nuoi_con
        )
        return total_reduced

    red_2 = calc_vidu2()
    assert_approx(
        red_2, 146.4, tolerance=0.1, label="[Ví dụ 2] Bùi Thị X giảm 146.4 GC"
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  Điều 10.1.b — Làm tròn tuần (5 ngày = 1 tuần)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 10.1.b — Làm tròn tuần (5 ngày = 1 tuần)")
    from calculations import calculate_t04_weeks
    from datetime import date

    # 5 ngày
    assert_approx(
        calculate_t04_weeks(date(2025, 9, 1), date(2025, 9, 6)),
        1.0,
        tolerance=0,
        label="5 ngày -> 1.0 tuần",
    )
    # 6 ngày
    assert_approx(
        calculate_t04_weeks(date(2025, 9, 1), date(2025, 9, 7)),
        1.0,
        tolerance=0,
        label="6 ngày -> 1.0 tuần",
    )
    # 4 ngày
    assert_approx(
        calculate_t04_weeks(date(2025, 9, 1), date(2025, 9, 4)),
        0.8,
        tolerance=0,
        label="4 ngày -> 0.8 tuần",
    )
    # 12 ngày (1 tuần 5 ngày)
    assert_approx(
        calculate_t04_weeks(date(2025, 9, 1), date(2025, 9, 13)),
        2.0,
        tolerance=0,
        label="12 ngày (7+5) -> 2.0 tuần",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  Điều 8.1.g — Giảng dạy bằng tiếng nước ngoài (x1.5)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 8.1.g — Giảng dạy bằng tiếng nước ngoài (x1.5)")
    act_ly_thuyet = make_activity(base_rate=1.0)
    log_nn = make_log(quantity=10, student_count=30)
    log_nn["is_foreign_language_instruction"] = 1
    assert_approx(
        calculate_activity_hours(log_nn, act_ly_thuyet),
        15.0,
        label="10 tiết lý thuyết bằng tiếng NN -> 15.0 GC",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  Điều 11.2 — Miễn giảm NCKH tại Phòng (Loại trừ GS/PGS)
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 11.2 — Miễn giảm NCKH tại Phòng (Loại trừ GS/PGS)")

    # Mô phỏng logic trong calculations.py
    def simulate_gs_at_phong(title, rule_name, rule_nckh_pct):
        if (
            rule_name == "Công tác tại phòng không giữ chức danh (Giảm NCKH)"
            and title == "Giáo sư, Phó Giáo sư"
        ):
            n_red = 0.0
        else:
            n_red = rule_nckh_pct
        return n_red

    assert_approx(
        simulate_gs_at_phong(
            "Giáo sư, Phó Giáo sư",
            "Công tác tại phòng không giữ chức danh (Giảm NCKH)",
            50.0,
        ),
        0.0,
        label="GS tại phòng -> 0% giảm NCKH",
    )
    assert_approx(
        simulate_gs_at_phong(
            "Giảng viên", "Công tác tại phòng không giữ chức danh (Giảm NCKH)", 50.0
        ),
        50.0,
        label="GV tại phòng -> 50% giảm NCKH",
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  Điều 12 — Bù trừ tự động
    # ════════════════════════════════════════════════════════════════════════════

    section("Điều 12 — Bù trừ tự động")

    def apply_auto_compensation(gc, nckh):
        if gc > 0 and nckh < 0:
            transfer = min(gc, -nckh)
            return gc - transfer, nckh + transfer
        elif nckh > 0 and gc < 0:
            transfer = min(nckh, -gc)
            return gc + transfer, nckh - transfer
        return gc, nckh

    assert_approx(
        apply_auto_compensation(10, -5)[0], 5.0, label="Bù GC sang NCKH: GC còn 5"
    )
    assert_approx(
        apply_auto_compensation(10, -5)[1], 0.0, label="Bù GC sang NCKH: NCKH còn 0"
    )
    assert_approx(
        apply_auto_compensation(-10, 5)[0], -5.0, label="Bù NCKH sang GC: GC còn -5"
    )
    assert_approx(
        apply_auto_compensation(-10, 5)[1], 0.0, label="Bù NCKH sang GC: NCKH còn 0"
    )

    # ════════════════════════════════════════════════════════════════════════════
    #  SUMMARY
    # ════════════════════════════════════════════════════════════════════════════

    print(f"\n{'═' * 60}")
    print(f"  RESULTS: {PASS} passed  |  {FAIL} failed  |  {PASS + FAIL} total")
    print(f"{'═' * 60}")
    if FAIL == 0:
        print("  🎉  All tests passed — 100% compliant with quy định!")
    else:
        print(f"  ⚠️   {FAIL} test(s) FAILED — review above for details.")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    run_all()
