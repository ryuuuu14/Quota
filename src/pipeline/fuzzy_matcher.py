import functools
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Literal

from .models import MatchResult
from .synonym_registry import SynonymRegistry, LoadResult
from .matchers import CompositeMatcher

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = str(_PROJECT_ROOT / "config" / "synonyms.yaml")
_MATCHER_CONFIG_PATH = str(_PROJECT_ROOT / "config" / "matcher_config.yaml")
_registry_cache: Optional[SynonymRegistry] = None


def _get_registry() -> Optional[SynonymRegistry]:
    global _registry_cache
    if _registry_cache is None:
        result = SynonymRegistry.load(_CONFIG_PATH)
        if result.success:
            _registry_cache = result.registry
        else:
            logger.error(f"Failed to load synonym registry: {result.error}")
            return None
    return _registry_cache


def _clear_registry_cache():
    global _registry_cache
    _registry_cache = None


def reload_synonyms() -> LoadResult:
    _clear_registry_cache()
    return SynonymRegistry.load(_CONFIG_PATH)


def match_columns_v2(
    excel_headers: List[str],
    expected_columns: List[str],
    required_columns: Optional[List[str]] = None,
    template_mapping: Optional[Dict[str, str]] = None,
    template_mode: Literal["override", "fill_gaps", "merge_confidence", "separate"] = "merge_confidence",
    api_version: int = 2
) -> MatchResult:
    registry = _get_registry()
    if registry is None:
        return MatchResult(
            mappings=[],
            unmatched_excel_headers=[],
            duplicate_warnings=[],
            missing_required=[],
            synonym_config_hash="",
            api_version=api_version,
            error="Synonym registry not loaded"
        )

    matcher = CompositeMatcher(registry, registry.matcher_config.model_dump())
    return matcher.match_all(
        excel_headers=excel_headers,
        expected_columns=expected_columns,
        required_columns=required_columns,
        template_mapping=template_mapping,
        template_mode=template_mode
    )


def match_columns_v1(
    excel_headers: List[str],
    expected_columns: List[str]
) -> Dict[str, Optional[str]]:
    result = match_columns_v2(excel_headers, expected_columns)
    return result.to_legacy_dict()


def suggest_mappings(excel_headers: List[str], expected_columns: List[str]) -> Dict[str, Optional[str]]:
    return match_columns_v1(excel_headers, expected_columns)


def fuzzy_match_columns(excel_headers: List[str], expected_columns: List[str]) -> Dict[str, Optional[str]]:
    return match_columns_v1(excel_headers, expected_columns)


@functools.lru_cache(maxsize=32)
def _cached_match_v2(
    headers_tuple: tuple,
    expected_tuple: tuple,
    required_tuple: tuple,
    template_tuple: tuple,
    template_mode: str,
    api_version: int
) -> MatchResult:
    return match_columns_v2(
        excel_headers=list(headers_tuple),
        expected_columns=list(expected_tuple),
        required_columns=list(required_tuple) if required_tuple else None,
        template_mapping=dict(template_tuple) if template_tuple else None,
        template_mode=template_mode,
        api_version=api_version
    )


def match_columns(
    excel_headers: List[str],
    expected_columns: List[str],
    required_columns: Optional[List[str]] = None,
    template_mapping: Optional[Dict[str, str]] = None,
    template_mode: Literal["override", "fill_gaps", "merge_confidence", "separate"] = "merge_confidence",
    return_format: Literal["legacy", "structured"] = "legacy",
    api_version: int = 2
) -> Union[Dict[str, Optional[str]], MatchResult]:
    if return_format == "legacy":
        return match_columns_v1(excel_headers, expected_columns)

    headers_tuple = tuple(excel_headers)
    expected_tuple = tuple(expected_columns)
    required_tuple = tuple(required_columns) if required_columns else ()
    template_tuple = tuple(template_mapping.items()) if template_mapping else ()

    return _cached_match_v2(
        headers_tuple,
        expected_tuple,
        required_tuple,
        template_tuple,
        template_mode,
        api_version
    )


def audit_synonyms(db_connection=None) -> Dict:
    registry = _get_registry()
    if registry is None:
        return {"error": "Registry not loaded", "drift": True}

    from database import get_connection
    if db_connection is None:
        conn = get_connection()
    else:
        conn = db_connection

    try:
        import pandas as pd
        df_activities = pd.read_sql_query("SELECT * FROM activity_types", conn)
        df_timeframes = pd.read_sql_query("SELECT * FROM timeframes", conn)

        required_activity_cols = [
            "Mã GV", "Tên loại hoạt động", "Ngày thực hiện", "Số lượng",
            "Cấp lớp", "Loại lớp", "Số học viên", "Cấp đề tài",
            "Tác giả chính", "Giảng dạy tiếng nước ngoài", "Ghi chú"
        ]
        required_aggregate_cols = [
            "Mã GV", "Tổng GC thực hiện", "NCKH thực hiện",
            "Số giờ miễn giảm", "Định mức GC", "Ghi chú"
        ]
        expected_teacher_cols = [
            "Mã GV", "Họ tên", "Tổ bộ môn", "Nữ", "Loại hợp đồng",
            "Học hàm học vị", "Cấp bậc quân hàm", "Chức danh", 
            "Chức vụ", "Ngày bổ nhiệm chức vụ", "Ngày bổ nhiệm chức danh", "Đơn vị"
        ]
        expected_schedule_cols = [
            "Mã GV (Khóa)", "Họ tên (Khóa)", "Chức danh (Khóa)", "Đơn vị (Khóa)",
            "Tên môn học", "Loại", "Nhóm", "Sỉ số", "Tiết quy đổi",
            "Hệ số tín chỉ", "Ghi chú"
        ]

        all_expected = set(
            required_activity_cols + 
            required_aggregate_cols + 
            expected_teacher_cols + 
            expected_schedule_cols
        )
        synonym_keys = set(registry.expected_columns)

        missing_in_synonyms = all_expected - synonym_keys
        extra_in_synonyms = synonym_keys - all_expected

        return {
            "drift": len(missing_in_synonyms) > 0 or len(extra_in_synonyms) > 0,
            "missing_in_synonyms": sorted(missing_in_synonyms),
            "extra_in_synonyms": sorted(extra_in_synonyms),
            "synonym_config_hash": registry.config_hash,
            "total_synonym_groups": len(synonym_keys)
        }
    finally:
        if db_connection is None:
            conn.close()


if __name__ == "__main__":
    import sys
    import json
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) > 1 and sys.argv[1] == "audit":
        result = audit_synonyms()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1 if result.get("drift") else 0)