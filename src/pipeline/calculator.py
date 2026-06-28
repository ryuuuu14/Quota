import pandas as pd
from database import get_connection

LOOKUP_TABLE = {
    "LT": [(0, 40, 1.0), (41, 60, 1.2), (61, 80, 1.4), (81, float("inf"), 1.5)],
    "TH": [(0, 40, 1.0), (41, 55, 1.2), (56, 70, 1.4), (71, float("inf"), 1.5)],
    "NN_CNTT": [(0, 25, 1.0), (26, 40, 1.2), (41, 60, 1.4), (61, float("inf"), 1.5)],
    "THẠC SĨ": [(0, 50, 1.3), (51, float("inf"), 1.5)],
    "TIẾN SĨ": [(0, float("inf"), 2.0)],
    "LLCT TRUNG CẤP": [(0, 50, 1.0), (51, float("inf"), 1.2)],
    "LLCT CAO CẤP": [(0, 50, 1.3), (51, float("inf"), 1.5)],
    "BỒI DƯỠNG": [(0, float("inf"), 1.0)],
}


def lookup_he_so_loai(loai, si_so):
    loai = loai.strip().upper()
    segs = LOOKUP_TABLE.get(loai, [(0, float("inf"), 1.0)])
    for lo, hi, hs in segs:
        if hi == float("inf"):
            if si_so >= lo:
                return hs
        elif lo <= si_so <= hi:
            return hs
    return 1.0


def calculate_rows(df):
    df = df.copy()
    df["he_so_lop_dong"] = df.apply(
        lambda r: lookup_he_so_loai(str(r["loai"]), int(r["si_so"])), axis=1
    )
    df["tiet_thuc_day"] = (
        df["tiet_quy_doi"].astype(float)
        * df["he_so_tin_chi"].astype(float)
        * df["he_so_lop_dong"]
    )
    return df


def aggregate_by_teacher(df_calculated):
    return (
        df_calculated.groupby("teacher_id")
        .agg(
            tong_mon=("subject_name", "count"),
            tong_tiet_quy_doi=("tiet_quy_doi", "sum"),
            tong_tiet_thuc_day=("tiet_thuc_day", "sum"),
            he_so_tin_chi_trung_binh=("he_so_tin_chi", "mean"),
        )
        .reset_index()
    )


def calculate_preview(timeframe_id, df_calculated, conn=None):
    from calculations import calculate_teacher_metrics

    if conn is None:
        conn = get_connection()

    agg = aggregate_by_teacher(df_calculated)

    session_rows = []
    for _, r in agg.iterrows():
        session_rows.append(
            {
                "teacher_id": int(r["teacher_id"]),
                "giang_day_truc_tiep": float(r["tong_tiet_thuc_day"]),
                "hdcm_bd": 0.0,
                "nckh_total": 0.0,
                "nvk_total": 0.0,
            }
        )
    df_session = pd.DataFrame(session_rows)

    df_metrics = calculate_teacher_metrics(
        timeframe_id=timeframe_id,
        df_session_override=df_session,
    )

    df_result = pd.merge(
        df_metrics, agg, left_on="id", right_on="teacher_id", how="left"
    )
    return df_result
